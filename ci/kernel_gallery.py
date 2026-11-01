#!/usr/bin/env python3
# Copyright © 2019-2026
#
# Licensed under the Apache License, Version 2.0 (the "License").
"""Run the kernel gallery (ci/kernel_gallery.yaml) on SimX and write it out.

Each gallery entry names a catalog case; this runs that case's own command
(ci/testcase.py run_command, driver simx) from the build tree, as the CI cells
do, and records the runtime's `PERF: instrs=…, cycles=…, IPC=…` summary, the
exit status and the log. The kernel sources the entry lists are copied beside
the results so a reader sees the code that ran.

  cd build32 && python3 ci/kernel_gallery.py OUT_DIR [--only CASE ...]

OUT_DIR gets results.json, logs/<slug>.log and src/<app>/<file>. Exit status is
non-zero if any kernel failed; every kernel is still run and recorded.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import testcase as tc  # noqa: E402
import yaml  # noqa: E402

PERF_RE = re.compile(r"^PERF: instrs=(\d+), cycles=(\d+), IPC=([0-9.]+)", re.M)
CORE_RE = re.compile(r"^PERF: core(\d+): instrs=(\d+), cycles=(\d+), IPC=([0-9.]+)", re.M)
XLEN = 32
TIMEOUT = int(os.environ.get("GALLERY_TIMEOUT", "1800"))
LOG_LINES = 400


def slug(case_ref):
    return re.sub(r"[^A-Za-z0-9]+", "-", case_ref).strip("-").lower()


def find_case(cases, ref):
    category, cid = ref.split(":", 1)
    hits = [c for c in cases if c.category == category and c.id.split(":")[1] == cid]
    if not hits:
        raise SystemExit("kernel_gallery: no catalog case {}".format(ref))
    return hits[0]


def trim(text):
    lines = text.splitlines()
    if len(lines) <= 2 * LOG_LINES:
        return text
    cut = len(lines) - 2 * LOG_LINES
    return "\n".join(lines[:LOG_LINES] + ["... [{} lines cut] ...".format(cut)] + lines[-LOG_LINES:]) + "\n"


def run(case, shape, out):
    argv, env = case.run_command(XLEN, driver="simx")
    if not any(k in case.shape for k in ("clusters", "cores")):
        argv[3:3] = tc._shape_flags(shape)  # after --driver and --app
    full_env = dict(os.environ, **env)
    t0 = time.time()
    try:
        p = subprocess.run(argv, env=full_env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=TIMEOUT)
        rc, text = p.returncode, p.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired as e:
        rc, text = "timeout", (e.stdout or b"").decode("utf-8", "replace")
    secs = round(time.time() - t0, 1)
    perf = PERF_RE.findall(text)
    cores = CORE_RE.findall(text)
    failed_marker = re.search(r"^FAILED!?$|Found \d+ errors", text, re.M)
    ok = rc == 0 and bool(perf) and not failed_marker
    return argv, env, rc, secs, text, perf, cores, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()

    with open(os.path.join(HERE, "kernel_gallery.yaml")) as fh:
        spec = yaml.safe_load(fh)
    cases = tc.load_all(os.path.join(HERE, "testcases"))
    out = a.out
    os.makedirs(os.path.join(out, "logs"), exist_ok=True)
    os.makedirs(os.path.join(out, "src"), exist_ok=True)

    kernels = []
    for k in spec["kernels"]:
        if a.only and k["case"] not in a.only:
            continue
        case = find_case(cases, k["case"])
        name = slug(k["case"])
        print("== {} ({})".format(k["title"], k["case"]), flush=True)
        argv, env, rc, secs, text, perf, cores, ok = run(case, spec["default_shape"], out)
        with open(os.path.join(out, "logs", name + ".log"), "w") as fh:
            fh.write("$ {}{}\n".format(
                "CONFIGS=\"{}\" ".format(env["CONFIGS"]) if env.get("CONFIGS") else "", " ".join(argv)))
            fh.write(trim(text))
        sources = []
        for f in k.get("show", []):
            src = os.path.join("tests", "regression", case.app, f)
            if os.path.isfile(src):
                dst = os.path.join(out, "src", case.app, f)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
                sources.append({"file": f, "path": "src/{}/{}".format(case.app, f),
                                "repo_path": "tests/regression/{}/{}".format(case.app, f)})
        instrs, cycles, ipc = (int(perf[-1][0]), int(perf[-1][1]), float(perf[-1][2])) if perf else (None, None, None)
        print("   {} in {}s: instrs={} cycles={} IPC={}".format(
            "PASS" if ok else "FAIL", secs, instrs, cycles, ipc), flush=True)
        kernels.append({
            "slug": name, "case": k["case"], "title": k["title"], "about": k["about"],
            "app": case.app, "args": case.args, "configs": env.get("CONFIGS", ""),
            "shape": case.shape or spec["default_shape"],
            "command": " ".join(argv), "status": "pass" if ok else "fail", "exit": rc,
            "seconds": secs, "instrs": instrs, "cycles": cycles, "ipc": ipc,
            "cores": [{"core": int(c), "instrs": int(i), "cycles": int(cy), "ipc": float(p)}
                      for c, i, cy, p in cores],
            "check": case.check, "tolerance": case.tolerance if case.check == "model_parity" else None,
            "known_issue": case.known_issue,
            "log": "logs/{}.log".format(name), "sources": sources,
        })

    server, repo, run_id = (os.environ.get(v, "") for v in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"))
    result = {
        "repo": repo, "commit": os.environ.get("GITHUB_SHA", ""),
        "run_url": "{}/{}/actions/runs/{}".format(server, repo, run_id) if run_id else "",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "driver": "simx", "xlen": XLEN, "default_shape": spec["default_shape"],
        "kernels": kernels,
    }
    with open(os.path.join(out, "results.json"), "w") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")
    bad = [k["case"] for k in kernels if k["status"] != "pass"]
    print("kernel_gallery: {} of {} passed{}".format(
        len(kernels) - len(bad), len(kernels), "; failed: " + ", ".join(bad) if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
