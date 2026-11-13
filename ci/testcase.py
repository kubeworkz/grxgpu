#!/usr/bin/env python3
"""Vortex test cases — the model and the CLI.

Loads ci/testcases/*.yaml into concrete test cases, and exposes the planner CLI
(`lint` / `matrix` / `select`) the CI workflow uses. Pure logic with no pytest
dependency (only PyYAML), so the lightweight ci.yml plan job and the pytest
harness (ci/test_runner.py) both build on it. See docs/designs/continuous_integration.md.

A *case* (class Spec) is one declarative test. A testcases file lists entries per
category; an entry with `drivers: [...]` expands to one case per driver. `xlen` is
an outer dimension — cases are filtered against the ambient build tree's XLEN,
never expanded here (build32/ and build64/ are separate trees).

  testcase.py lint
      validate every case; exit non-zero on any error
  testcase.py matrix [--drivers=simx,rtlsim] [--tier=smoke,full] [--xlen=32] [--changed-from=REF]
      JSON (category x driver x xlen) cells for the GitHub matrix
  testcase.py select --changed-from=REF
      categories whose touches[] intersect the diff (path-scaling)
  testcase.py verilate [--all] [--dry-run]
      generate each selected case's Verilator model once; ids arrive on stdin
      from `pytest --collect-only`, so selection stays pytest's
"""

import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys

import yaml

TESTCASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testcases")

# Execution driver name (matches blackbox.sh --driver= and `make run-<d>`) ->
# user-facing marker / slice name (what --drivers="...,xrtsim,opaesim" selects).
_DRIVER_TO_MARKER = {"xrt": "xrtsim", "opae": "opaesim"}
# Execution driver name -> its sim source directory under sim/.
_DRIVER_TO_SIMDIR = {"simx": "simx", "rtlsim": "rtlsim", "xrt": "xrtsim", "opae": "opaesim"}
VALID_DRIVERS = set(_DRIVER_TO_SIMDIR)
# Drivers whose sim is a Verilator model, i.e. one `make … verilate` can prepare.
VERILATOR_DRIVERS = {"rtlsim", "xrt", "opae"}
VALID_VIA = {"blackbox", "make-run", "script"}
VALID_CHECK = {"model_parity", "perf_gate"}

# simx<->rtlsim cycle-parity default: both timing models must agree within 5%.
DEFAULT_PARITY_TOLERANCE = 0.05


def driver_marker(driver):
    """User-facing marker name for an execution driver (xrt->xrtsim, ...)."""
    return _DRIVER_TO_MARKER.get(driver, driver)


class Spec:
    """One concrete test case: a single (category, driver, configs, shape) point."""

    def __init__(self, category, entry, driver, defaults):
        self.category = category
        self.driver = driver
        self.via = entry.get("via", "blackbox")
        self.app = entry.get("app", "")
        self.args = entry.get("args", "")
        self.expected_instrs = entry.get("instrs")
        # Verbatim extra blackbox flags the structured fields don't model
        # (e.g. --debug=3 --perf=6 --scope --nohup --log=...).
        self.flags = entry.get("flags", "")
        self.shape = dict(entry.get("shape", {}))
        self.tier = entry.get("tier", defaults.get("tier", "smoke"))
        self.needs = list(entry.get("needs", defaults.get("needs", [])))
        self.touches = list(entry.get("touches", defaults.get("touches", [])))
        self.xlens = [int(x) for x in entry.get("xlen", defaults.get("xlen", [32, 64]))]
        self.configs = _merge_configs(defaults.get("configs", ""), entry)
        # Known-issue marker: a non-empty reason flags this case as a tracked
        # expected-failure (pytest xfail). The case still runs and reports, but
        # its failure does not fail CI. Falls back to the file-level default so a
        # wholly-broken category can mark every case in one place.
        self.known_issue = entry.get("known_issue", defaults.get("known_issue", ""))
        # sharding: 'shards: N' (or 'shards: {N: <authored ids>}') splits the
        # category into N matrix cells so no cell exceeds the 6h GH Actions
        # per-job cap. Case -> shard via stable md5(category:id) hash, so the
        # assignment is deterministic across runs and machines.
        shards = entry.get("shards", defaults.get("shards", ""))
        if isinstance(shards, dict):
            self.shard_groups = {int(k): list(v) for k, v in shards.items()}
            self.shards = max(self.shard_groups) + 1  # keys are 0-based indices
            self.shard_index = next(i for i, g in self.shard_groups.items()
                                    if entry["id"] in g)
        elif shards:
            self.shards = int(shards)
            self.shard_index = int(hashlib.md5(
                (category + ":" + entry["id"]).encode()).hexdigest()[:8], 16) % self.shards
        else:
            self.shards = 1
            self.shard_index = 0
        # check: model_parity — one case that runs the SAME app/args/configs on
        # both simx and rtlsim and asserts the reported cycle counts agree within
        # `tolerance`. Not driver-expanded: the case is pinned to the rtlsim
        # driver (it elaborates the RTL, so build/matrix placement is right) and
        # the runner drives simx as the second leg itself.
        self.check = entry.get("check", "")
        # model_parity / perf_gate are 32-bit-only gates: the SimX timing model
        # and the perf baselines are validated against RV32 rtlsim; RV64 is not
        # gated. Pin the check gates to xlen 32 regardless of the category file's
        # default (which still governs that file's functional cases), so 64-bit
        # coverage can't creep back in per-file.
        if self.check in ("model_parity", "perf_gate"):
            self.xlens = [32]
        self.tolerance = float(entry.get("tolerance",
                                         defaults.get("tolerance", DEFAULT_PARITY_TOLERANCE)))
        self.authored_drivers = ("driver" in entry) or ("drivers" in entry)
        # make-run / script fields
        self.dir = entry.get("dir", "")
        self.target = entry.get("target", "")
        self.run = entry.get("run", "")
        self.vars = dict(entry.get("vars", {}))
        # Stable, unique id: <category>:<authored-id>:<marker-driver>
        self.id = "{}:{}:{}".format(category, entry["id"], self.marker_driver)

    @property
    def marker_driver(self):
        return driver_marker(self.driver) if self.driver else None

    @property
    def needs_sim(self):
        """Whether a sim build is required (driverless via:script cases self-build)."""
        return self.via != "script" and self.driver is not None

    @property
    def sim_dir(self):
        return "sim/" + _DRIVER_TO_SIMDIR[self.driver]

    def build_key(self):
        """What determines a *sim build*. `via` is deliberately excluded so a
        make-run case and a blackbox case with the same (driver, configs) share
        one sim build. xlen is implicit in the ambient tree. vars.CONFIGS
        participates: make-run specs thread extra sim flags through vars (e.g.
        amo.yaml's isa-conformance cluster bound), and two specs whose only
        difference is that flag must not share one sim build.
        """
        return (self.driver, self.configs, self.vars.get("CONFIGS"))

    def markers(self):
        """pytest marker names for `-m` selection (one per value)."""
        m = [self.category, self.tier]
        if self.shards > 1:
            m.append("shard{}of{}".format(self.shard_index, self.shards))
        if self.marker_driver:
            m.append(self.marker_driver)
        if self.check:
            m.append(self.check)
        m += ["needs_{}".format(n) for n in self.needs]
        return m

    def applies_to_xlen(self, xlen):
        return int(xlen) in self.xlens

    def build_command(self, xlen):
        """argv + env to build this case's sim once (shared across build_key).

        make-run specs hand extra make variables to their run target via
        `vars:`; a vars.CONFIGS is a *sim* flag set (the run targets only run a
        pre-built binary), so it must reach the sim build here too — otherwise
        the sim silently compiles without it (e.g. the isa-conformance cluster
        bound, leaving the TOML-default shape: rtlsim Verilate OOMs a runner
        and simx loses cross-core atomics at per-core private L1 LLCs).
        """
        cfgs = self.configs
        vcfg = self.vars.get("CONFIGS")
        if vcfg:
            cfgs = (cfgs + " " + vcfg) if cfgs else vcfg
        env = {"CONFIGS": _subst(cfgs, xlen)} if cfgs else {}
        return ["make", "-C", self.sim_dir], env

    def run_command(self, xlen, driver=None):
        """argv + env to execute this case at the given ambient xlen. `driver`
        overrides the case's own driver (the cycle-parity runner uses it to
        drive both legs of one case)."""
        env = {"CONFIGS": _subst(self.configs, xlen)} if self.configs else {}
        if self.via == "blackbox":
            argv = ["./ci/blackbox.sh", "--driver=" + (driver or self.driver),
                    "--app=" + self.app]
            argv += _shape_flags(self.shape)
            if self.args:
                argv.append("--args=" + self.args)
            if self.flags:
                argv += self.flags.split()
            return argv, env
        if self.via == "make-run":
            targets = self.target.format(driver=self.driver, xlen=xlen)
            argv = ["make", "-C", self.dir] + targets.split() if isinstance(
                targets, str) else ["make", "-C", self.dir] + targets
            argv += ["{}={}".format(k, v) for k, v in self.vars.items()]
            return argv, env
        if self.via == "script":
            # run through a shell so multi-step `cmd1 && cmd2` scripts work.
            return ["bash", "-c", _subst(self.run, xlen)], env
        raise ValueError("unknown via: {!r}".format(self.via))

    def model_build(self, xlen):
        """argv + env that generate this case's Verilator model, or None.

        Must reproduce the flags the run gives the sim build byte for byte: the
        sim Makefile's stamp compares the flag set, so any difference would
        re-verilate. Mirrors blackbox.sh — shape knobs and --perf become
        CONFIGS, --debug/--scope/--saif become make variables, and RTL drivers
        model the bounded topology. make-run cases build the sim tree directly,
        so they use the fixture's command shape.
        """
        if not self.needs_sim or self.driver not in VERILATOR_DRIVERS:
            return None
        env = {}
        if self.via == "blackbox":
            flags = self.flags.split()
            if "--nohup" in flags:
                return None  # builds into a private temp dir; nothing to reuse
            cfgs = _subst(self.configs, xlen)
            for knob, define in (("clusters", "-DVX_CFG_NUM_CLUSTERS={}"),
                                 ("cores", "-DVX_CFG_NUM_CORES={}"),
                                 ("warps", "-DVX_CFG_NUM_WARPS={}"),
                                 ("threads", "-DVX_CFG_NUM_THREADS={}")):
                if self.shape.get(knob):
                    cfgs = _add_opt(cfgs, define.format(self.shape[knob]))
            for knob, define in (("l2cache", "-DVX_CFG_L2_ENABLE"),
                                 ("l3cache", "-DVX_CFG_L3_ENABLE")):
                if self.shape.get(knob):
                    cfgs = _add_opt(cfgs, define)
            if self.shape.get("scope"):
                env["SCOPE"] = "1"
            for flag in flags:
                if flag.startswith("--perf="):
                    cfgs = _add_opt(cfgs, "-DPERF_ENABLE")
                elif flag.startswith("--debug="):
                    env["DEBUG"] = flag.split("=", 1)[1]
                elif flag == "--scope":
                    env["SCOPE"] = "1"
                elif flag == "--saif":
                    env["SAIF"] = "1"
            if self.driver in ("rtlsim", "opae") and \
                    os.environ.get("RTL_UNBOUND") != "1" and \
                    "VX_CFG_NUM_CLUSTERS" not in cfgs and \
                    "VX_CFG_NUM_CORES" not in cfgs:
                cfgs += " -DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=4"
            argv = ["make", "-C", "sw/runtime/" + self.driver, "verilate"]
        else:
            cfgs = self.configs
            vcfg = self.vars.get("CONFIGS")
            if vcfg:
                cfgs = (cfgs + " " + vcfg) if cfgs else vcfg
            cfgs = _subst(cfgs, xlen)
            argv = ["make", "-C", self.sim_dir, "verilate"]
        if cfgs:
            env["CONFIGS"] = cfgs
        return argv, env


def _subst(text, xlen):
    """Resolve the ambient-xlen placeholders in a config/run string:
    {xlen} -> 32/64, {xsize} -> XLEN/8 (the legacy $XLEN / $XSIZE)."""
    return text.replace("{xlen}", str(xlen)).replace("{xsize}", str(int(xlen) // 8))


def _add_opt(base, flag):
    """Append a define the way blackbox.sh's add_option does."""
    return (base + " " + flag) if base else flag


def _merge_configs(default, entry):
    """`configs` overrides the default; `configs+` appends to it."""
    if "configs" in entry:
        return entry["configs"]
    if "configs+" in entry:
        return (default + " " + entry["configs+"]).strip()
    return default


def _shape_flags(shape):
    flags = []
    for knob in ("clusters", "cores", "warps", "threads"):
        if shape.get(knob):
            flags.append("--{}={}".format(knob, shape[knob]))
    for boolean in ("l2cache", "l3cache", "scope"):
        if shape.get(boolean):
            flags.append("--" + boolean)
    return flags


def load_category(path):
    """Expand one testcases YAML file into concrete cases."""
    with open(path) as fh:
        doc = yaml.safe_load(fh)
    category = doc["category"]
    defaults = doc.get("defaults", {})
    cases = []
    for entry in doc.get("tests", []):
        # via:script cases may be driverless (host/synthesis); everything else
        # has a driver or a drivers list. A check: case is never driver-expanded
        # — it is one case pinned to rtlsim that runs both drivers itself.
        if entry.get("check"):
            drivers = ["rtlsim"]
        else:
            drivers = entry.get("drivers") or ([entry["driver"]] if "driver" in entry else [None])
        for driver in drivers:
            cases.append(Spec(category, entry, driver, defaults))
    return cases


def load_all(testcases_dir=TESTCASES_DIR):
    """Load every ci/testcases/*.yaml into a flat list of concrete cases."""
    cases = []
    for path in sorted(glob.glob(os.path.join(testcases_dir, "*.yaml"))):
        cases.extend(load_category(path))
    return cases


def execute(argv, env_extra=None, cwd=None):
    """Run argv with CONFIGS et al. merged into the environment; return exit code."""
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(argv, env=env, cwd=cwd).returncode


def execute_capture(argv, env_extra=None, cwd=None):
    """Like execute(), but also return the combined stdout/stderr text. Output
    is still echoed line-by-line so CI logs keep the full run."""
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.Popen(argv, env=env, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors="replace")
    lines = []
    for line in proc.stdout:
        sys.stdout.write(line)
        lines.append(line)
    proc.stdout.close()
    return proc.wait(), "".join(lines)


# --------------------------------------------------------------------------- #
# Planner CLI — lint / matrix / select. Reads the same data the harness runs,
# but needs no pytest or build env, so the ci.yml plan job can call it.
# --------------------------------------------------------------------------- #

# A changed file under one of these prefixes FORCES the listed sim driver(s)
# into the run regardless of the event tier — the RTL is shared by every sim
# backend and simx (a separate C++ model) cannot exercise it, so an RTL change
# with simx-only coverage is effectively untested. rtlsim is the cheapest driver
# that elaborates the RTL; AFU/host-surface paths additionally need xrt/opae.
_DRIVER_PATHS = [
    ("hw/rtl/afu/", ("rtlsim", "xrt", "opae")),
    ("hw/rtl/", ("rtlsim",)),
    ("hw/dpi/", ("rtlsim",)),
    ("sim/rtlsim/", ("rtlsim",)),
    ("sim/xrtsim/", ("xrt",)),
    ("sim/opaesim/", ("opae",)),
    ("third_party/cvfpu/", ("rtlsim",)),
    ("third_party/hardfloat/", ("rtlsim",)),
    # Config inputs regenerate the RTL parameters, so exercise the RTL too.
    ("VX_config.toml", ("rtlsim",)),
    ("VX_types.toml", ("rtlsim",)),
    ("vortex_opae.toml", ("opae",)),
]


def drivers_for_changes(changed):
    """Set of execution-driver names a diff forces in (path->driver escalation)."""
    out = set()
    for f in changed:
        for prefix, drvs in _DRIVER_PATHS:
            if f.startswith(prefix):
                out.update(drvs)
    return out


def _changed_files(ref):
    """Files changed vs `ref`, or None if the diff is indeterminate (bad/zero
    base, missing history) — callers treat None as 'fall back to full coverage'."""
    out = subprocess.run(["git", "diff", "--name-only", ref + "...HEAD"],
                         capture_output=True, text=True)
    if out.returncode != 0:  # fall back to a two-dot diff if no merge base
        out = subprocess.run(["git", "diff", "--name-only", ref],
                             capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return [line for line in out.stdout.splitlines() if line]


def _touched(case, changed):
    return any(f.startswith(prefix) for prefix in case.touches for f in changed)


def _filter(cases, args):
    drivers = set(args.drivers.split(",")) if getattr(args, "drivers", None) else None
    tiers = set(args.tier.split(",")) if getattr(args, "tier", None) else None
    changed = _changed_files(args.changed_from) if getattr(args, "changed_from", None) else None
    out = []
    for c in cases:
        if drivers and c.marker_driver not in drivers:
            continue
        if tiers and c.tier not in tiers:
            continue
        # Path-scaling: only a case that DECLARES touches is subject to the diff
        # filter. A case with no touches has no path opinion and always runs, so
        # enabling --changed-from never silently drops an un-annotated category.
        if changed is not None and c.touches and not _touched(c, changed):
            continue
        out.append(c)
    return out


def cmd_matrix(args):
    # One GitHub matrix cell per (category, driver, xlen): the build tree is
    # per-xlen, so xlen is flattened out (not a per-cell list).
    xfilter = {int(x) for x in args.xlen.split(",")} if getattr(args, "xlen", None) else None
    cells = {}
    for c in _filter(load_all(), args):
        drv = c.marker_driver or "host"
        for xlen in c.xlens:
            if xfilter and xlen not in xfilter:
                continue
            key = (c.category, drv, xlen,
                   c.shard_index if c.shards > 1 else None)
            cell = cells.setdefault(key, {
                "category": c.category, "driver": drv, "xlen": xlen, "needs": set(),
                "shard": c.shard_index if c.shards > 1 else None,
                "shards": c.shards if c.shards > 1 else None,
            })
            cell["needs"].update(c.needs)
    out = []
    for cell in cells.values():
        cell["needs"] = sorted(cell["needs"])
        if cell.get("shard") is None:
            cell.pop("shard")
            cell.pop("shards")
        out.append(cell)
    out.sort(key=lambda c: (c["category"], c["driver"], c["xlen"]))
    print(json.dumps(out))
    return 0


def cmd_select(args):
    print(" ".join(sorted({c.category for c in _filter(load_all(), args)})))
    return 0


def cmd_drivers(args):
    """Execution drivers a diff forces in (path->driver escalation). Prints 'ALL'
    when the diff is indeterminate (zero/empty/missing base) so the caller falls
    back to full driver coverage rather than under-testing."""
    ref = getattr(args, "changed_from", None)
    if not ref or set(ref) <= set("0"):
        print("ALL")
        return 0
    changed = _changed_files(ref)
    if changed is None:
        print("ALL")
        return 0
    print(",".join(sorted(drivers_for_changes(changed))))
    return 0


def cmd_verilate(args):
    """Generate each selected case's Verilator model once, before the run.

    Case ids arrive on stdin from `pytest --collect-only`, so the selection is
    pytest's own — there is no second implementation of the marker expression.
    """
    xlen = int(os.environ.get("VX_XLEN", "32"))
    text = "" if args.all else sys.stdin.read()
    selected = {line.strip() for line in text.splitlines() if line.strip()}
    cases = [c for c in load_all() if c.applies_to_xlen(xlen)]
    if selected:
        known = {c.id for c in cases}
        for unknown in sorted(selected - known):
            sys.stderr.write("model-prep: ignoring unknown case id {}\n".format(unknown))
        cases = [c for c in cases if c.id in selected]
    jobs, seen = [], set()
    for case in cases:
        job = case.model_build(xlen)
        if job is None:
            continue
        argv, env = job
        key = (tuple(argv), tuple(sorted(env.items())))
        if key not in seen:
            seen.add(key)
            jobs.append((case.id, argv, env))
    print("model-prep: {} configuration(s) for {} selected case(s)".format(
        len(jobs), len(cases)), flush=True)
    for case_id, argv, env in jobs:
        print("model-prep: {}: {}: {}".format(
            case_id,
            " ".join("{}={}".format(k, v) for k, v in sorted(env.items())) or "-",
            " ".join(argv)), flush=True)
    if args.dry_run:
        return 0
    for case_id, argv, env in jobs:
        rc = execute(argv, env)
        if rc != 0:
            sys.stderr.write("model-prep: {}: verilation failed (exit {})\n".format(
                case_id, rc))
            return rc
    return 0


def cmd_lint(args):
    cases = load_all()
    errors, seen = [], {}
    for c in cases:
        if c.id in seen:
            errors.append("duplicate id: {}".format(c.id))
        seen[c.id] = c
        if c.via not in VALID_VIA:
            errors.append("{}: invalid via {!r}".format(c.id, c.via))
        if c.driver is not None and c.driver not in VALID_DRIVERS:
            errors.append("{}: invalid driver {!r}".format(c.id, c.driver))
        if c.via == "blackbox" and not c.app:
            errors.append("{}: blackbox case missing 'app'".format(c.id))
        if c.via == "make-run" and not (c.dir and c.target):
            errors.append("{}: make-run case needs 'dir' and 'target'".format(c.id))
        if c.via == "script" and not c.run:
            errors.append("{}: script case missing 'run'".format(c.id))
        if any(int(x) not in (32, 64) for x in c.xlens):
            errors.append("{}: xlen must be 32 and/or 64".format(c.id))
        if c.check:
            if c.check not in VALID_CHECK:
                errors.append("{}: invalid check {!r}".format(c.id, c.check))
            if c.via != "blackbox":
                errors.append("{}: check cases must be via blackbox".format(c.id))
            if c.authored_drivers:
                errors.append("{}: check cases must not set driver/drivers "
                              "(the runner drives simx and rtlsim)".format(c.id))
            if not (0.0 < c.tolerance < 1.0):
                errors.append("{}: tolerance must be in (0, 1)".format(c.id))
    if errors:
        for e in errors:
            sys.stderr.write("LINT ERROR: " + e + "\n")
        return 1
    print("OK: {} test cases across {} categories".format(
        len(cases), len({c.category for c in cases})))
    return 0


def cmd_sims(args):
    """Emit the sorted driver set implied by a cells JSON array.

    Used by the CI plan job to report which sim drivers the selected test
    cells need (host cells need no driver lib and are excluded).
    """
    cells = json.loads(args.cells) if args.cells else []
    drivers = sorted({c["driver"] for c in cells if c.get("driver") and c["driver"] != "host"})
    print(",".join(drivers))


def main(argv=None):
    p = argparse.ArgumentParser(description="Vortex test-case planner")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("matrix", help="emit JSON (category x driver x xlen) cells")
    m.add_argument("--drivers")
    m.add_argument("--tier")
    m.add_argument("--xlen")
    m.add_argument("--changed-from", dest="changed_from")
    m.set_defaults(func=cmd_matrix)

    s = sub.add_parser("select", help="categories whose touches[] hit a diff")
    s.add_argument("--drivers")
    s.add_argument("--tier")
    s.add_argument("--changed-from", dest="changed_from")
    s.set_defaults(func=cmd_select)

    d = sub.add_parser("drivers", help="drivers a diff forces in (path->driver)")
    d.add_argument("--changed-from", dest="changed_from")
    d.set_defaults(func=cmd_drivers)

    v = sub.add_parser("verilate", help="generate selected cases' Verilator models once")
    v.add_argument("--all", action="store_true",
                   help="prepare every case, not just the ids on stdin")
    v.add_argument("--dry-run", action="store_true",
                   help="print the commands without running them")
    v.set_defaults(func=cmd_verilate)

    m2 = sub.add_parser("sims", help="driver set implied by a cells JSON array")
    m2.add_argument("--cells", default="[]")
    m2.set_defaults(func=cmd_sims)

    sub.add_parser("lint", help="validate the test cases").set_defaults(func=cmd_lint)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
