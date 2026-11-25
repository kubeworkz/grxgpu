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

Only `assign` statements are checked. A port connection in the instantiation
(`.mem_bus_req_valid (mem_bus_if[i].req_valid)`) is always consistent, because
the direction comes from the port declaration itself.
"""

import argparse
import re
import sys
from pathlib import Path

# Facade file, then the flat block file it wraps. The facade takes the flat
# block's name, so the pair is what the staging script installs together.
PAIRS = (
    ("VX_cluster.sv", "VX_cluster_flat.sv"),
    ("VX_l3cache_bridge.sv", "VX_l3cache_flat.sv"),
)

PORT_DECL = re.compile(
    r"^\s*(input|output)\s+(?:wire\s+|reg\s+|logic\s+)?(?:\[[^\]]*\]\s*)*([A-Za-z_]\w*)\s*,?\s*$",
    re.M,
)
ASSIGN = re.compile(r"^\s*assign\s+([^=;]+?)\s*=\s*([^;]+?)\s*;\s*$")
INTERFACE_REF = re.compile(r"^([A-Za-z_]\w*_if)(?:\[[^\]]*\])?\.(.+)$")
PORT_REF = re.compile(r"^([A-Za-z_]\w*)(?:\[[^\]]*\])?$")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def flat_port_directions(text):
    """Map each flat port name to 'input' or 'output'."""
    directions = {}
    for match in PORT_DECL.finditer(text):
        directions[match.group(2)] = match.group(1)
    return directions


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


def check_pair(directory, facade_name, flat_name):
    facade_path = directory / facade_name
    flat_path = directory / flat_name
    for path in (facade_path, flat_path):
        if not path.exists():
            raise SystemExit(
                "check_overlay_facades: ERROR: missing overlay file {}\n"
                "The facade and its flat block are installed together; a checkout with\n"
                "one and not the other cannot be checked.".format(path)
            )

    directions = flat_port_directions(read(flat_path))
    facade_text = read(facade_path)

    failures, checked = [], 0
    for number, destination, source in facade_assignments(facade_text):
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
            failures.append(
                (
                    facade_name,
                    number,
                    port_name,
                    directions[port_name],
                    destination,
                    source,
                )
            )
    return failures, checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        default=str(Path(__file__).resolve().parent.parent / ".buildonly"),
        help="directory holding the overlay .sv files (default: <repo>/.buildonly)",
    )
    args = parser.parse_args()
    directory = Path(args.dir)

    all_failures, total_checked = [], 0
    for facade_name, flat_name in PAIRS:
        failures, checked = check_pair(directory, facade_name, flat_name)
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
        print("check_overlay_facades: ERROR: no facade assignment matched a flat")
        print("block port, so nothing was verified. Either the overlay changed")
        print("shape or this checker no longer parses it; fix the checker rather")
        print("than letting it pass silently.")
        return 1

    print("check_overlay_facades: OK - {} pair(s), {} assignment(s) drive the side "
          "their flat port declares".format(len(PAIRS), total_checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
