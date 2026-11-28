#!/usr/bin/env python3
"""Fail when an overlay facade drives the wrong side of a flat block's port.

The hierarchy-block build cannot carry interfaces or modports across a block
boundary, so each block is compiled as `<name>_flat`, whose ports are packed
vectors, and wrapped in an interface-preserving facade that recreates the
interfaces internally. The facade's copy-out block looks almost exactly like
the flat block's own block of the same name, and the two drive opposite sides:

    flat (reads its local interface):   assign mem_bus_req_valid[i] = mem_bus_if[i].req_valid;
    facade (owns the interface):        assign mem_bus_if[i].req_valid = mem_bus_req_valid[i];

Copying the flat's version into the facade inverts every handshake and still
elaborates: the request leaves, the response never arrives, and the requester
waits forever. Nothing shows it until a model build (about three hours) or a
run that hangs, so check the direction here instead.

Pairs are discovered, not listed: every `*_flat.sv` in the overlay directory
must be wrapped by exactly one facade, and a facade that names a `*_flat`
module with no file beside it, or that drives an interface while wrapping no
flat block at all, is an error. A new facade/flat pair is therefore checked as
soon as it lands, without editing this file.

Only `assign` statements are checked. A port connection in the instantiation
(`.mem_bus_req_valid (mem_bus_if[i].req_valid)`) is always consistent, because
the direction comes from the port declaration itself.
"""

import argparse
import re
import sys
from pathlib import Path

PORT_DECL = re.compile(
    r"^\s*(input|output)\s+(?:wire\s+|reg\s+|logic\s+)?(?:\[[^\]]*\]\s*)*([A-Za-z_]\w*)\s*,?\s*$",
    re.M,
)
ASSIGN = re.compile(r"^\s*assign\s+([^=;]+?)\s*=\s*([^;]+?)\s*;\s*$")
INTERFACE_REF = re.compile(r"^([A-Za-z_]\w*_if)(?:\[[^\]]*\])?\.(.+)$")
PORT_REF = re.compile(r"^([A-Za-z_]\w*)(?:\[[^\]]*\])?$")
MODULE_DECL = re.compile(r"^\s*module\s+([A-Za-z_]\w*)", re.M)
FLAT_REF = re.compile(r"^\s*([A-Za-z_]\w*_flat)\s*(?:#\s*\(|\w+\s*\()", re.M)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def error(message):
    print("check_overlay_facades: ERROR: " + message)
    return 1


def flat_port_directions(text):
    """Map each flat port name to 'input' or 'output'."""
    return {match.group(2): match.group(1) for match in PORT_DECL.finditer(text)}


def facade_assignments(text):
    """Yield (line number, destination, source) for each single-line assign."""
    for number, line in enumerate(text.splitlines(), start=1):
        match = ASSIGN.match(line)
        if match:
            yield number, " ".join(match.group(1).split()), " ".join(match.group(2).split())


def classify(side):
    """Return ('interface', name, field), ('port', name) or None."""
    interface = INTERFACE_REF.match(side)
    if interface:
        return ("interface", interface.group(1), interface.group(2))
    port = PORT_REF.match(side)
    if port:
        return ("port", port.group(1))
    return None


def drives_an_interface(text):
    """True when the file assigns to an interface member, i.e. it acts as a facade."""
    for _, destination, _ in facade_assignments(text):
        if classify(destination) and classify(destination)[0] == "interface":
            return True
    return False


def instantiates(text, module):
    return re.search(
        r"\b" + re.escape(module) + r"\b\s*(?:#\s*\(|\w+\s*\()", text
    ) is not None


def discover(directory):
    """Return (flats, facades, problems) for the overlay directory.

    flats:    module name -> path of `<module>.sv`
    facades:  module name -> paths of the files that instantiate it
    problems: human-readable reasons the overlay is not consistently installed
    """
    flat_files = sorted(directory.glob("*_flat.sv"))
    flats = {}
    problems = []
    for path in flat_files:
        declared = MODULE_DECL.search(read(path))
        module = declared.group(1) if declared else path.stem
        if module in flats:
            problems.append(
                "{} is declared by both {} and {}; only one of them could be "
                "checked".format(module, flats[module].name, path.name)
            )
        flats[module] = path

    facades = {module: [] for module in flats}
    for path in sorted(directory.glob("*.sv")):
        if path in flat_files:
            continue
        text = read(path)
        named = sorted({module for module in flats if instantiates(text, module)})
        absent = sorted({module for module in FLAT_REF.findall(text)} - set(flats))
        for module in absent:
            problems.append(
                "{} instantiates {}, but {}.sv is not in the overlay directory"
                .format(path.name, module, module)
            )
        if not named and not absent and drives_an_interface(text):
            problems.append(
                "{} drives an interface but wraps no *_flat block; every facade must "
                "instantiate one".format(path.name)
            )
        for module in named:
            facades[module].append(path)

    for module, paths in facades.items():
        if not paths:
            problems.append(
                "{}.sv has no facade: nothing in the overlay directory "
                "instantiates {}".format(module, module)
            )
        elif len(paths) > 1:
            problems.append(
                "{} is instantiated by more than one file ({}); a flat block has "
                "exactly one facade".format(
                    module, ", ".join(path.name for path in paths))
            )
    return flats, facades, problems


def check_pair(facade_path, flat_path):
    """Return (failures, checked) for one facade/flat pair."""
    directions = flat_port_directions(read(flat_path))
    failures, checked = [], 0
    for number, destination, source in facade_assignments(read(facade_path)):
        ends = (classify(destination), classify(source))
        interfaces = [end for end in ends if end and end[0] == "interface"]
        ports = [end for end in ends if end and end[0] == "port"]
        if len(interfaces) != 1 or len(ports) != 1:
            continue
        port_name = ports[0][1]
        if port_name not in directions:
            continue
        checked += 1
        driven_side = "interface" if ends[0][0] == "interface" else "port"
        # A flat output is driven by the block, so the facade must drive the
        # interface from it. A flat input is consumed by the block, so the
        # facade must drive the port net from the interface.
        expected = "interface" if directions[port_name] == "output" else "port"
        if driven_side != expected:
            failures.append((
                facade_path.name, number, port_name, directions[port_name],
                destination, source,
            ))
    return failures, checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        default=str(Path(__file__).resolve().parent.parent / ".buildonly"),
        help="directory holding the overlay .sv files (default: <repo>/.buildonly)",
    )
    directory = Path(parser.parse_args().dir).resolve()
    if not directory.is_dir():
        return error("{} is not a directory".format(directory))

    flats, facades, problems = discover(directory)
    if problems:
        print("ERROR: the overlay facade/flat pairs are inconsistent:")
        for problem in problems:
            print("  " + problem)
        print()
        print("Each *_flat.sv needs exactly one facade that instantiates it, and a")
        print("facade needs its flat block beside it. Pairing is by instantiation,")
        print("not by file name.")
        return 1

    if not flats:
        return error(
            "no *_flat.sv block in {}: the overlay is not installed, or the flat "
            "blocks were renamed and this check now verifies nothing".format(directory)
        )

    all_failures, total_checked = [], 0
    for module in sorted(facades):
        facade_path = facades[module][0]
        failures, checked = check_pair(facade_path, flats[module])
        all_failures.extend(failures)
        total_checked += checked

    if all_failures:
        print("ERROR: overlay facade drives the wrong side of a flat block port:")
        for name, number, port, direction, destination, source in all_failures:
            print("  {}:{}  {} is an {} of the flat block".format(
                name, number, port, direction))
            print("      assign {} = {};".format(destination, source))
            print("      the facade must drive {}".format(
                "the interface from the port" if direction == "output"
                else "the port net from the interface"))
        print()
        print("These assignments mirror the flat block's own block, where the")
        print("interface is local and read. At the facade the interface is the")
        print("exported port, so every direction is the other way round. The")
        print("design still elaborates; only a model build or a hung run shows it.")
        print()
        print("Check the flat block's port declarations for the authoritative")
        print("direction of each signal.")
        return 1

    if total_checked == 0:
        print("check_overlay_facades: ERROR: {} pair(s) found, but no facade assignment".format(
            len(facades)))
        print("matched a flat block port, so nothing was verified. Either the overlay")
        print("changed shape or this checker no longer parses it; fix the checker")
        print("rather than letting it pass silently.")
        return 1

    print("check_overlay_facades: OK - {} pair(s) discovered in {}, {} assignment(s) "
          "drive the side their flat port declares".format(
              len(facades), directory.name, total_checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
