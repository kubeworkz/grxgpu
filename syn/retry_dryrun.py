#!/usr/bin/env python3
"""Dry-run the ci-retry workflow classifier against a live CI run.

Extracts the embedded python from /tmp/ci-retry.yml, stubs the GITHUB_*
environment, neuters the rerun POST (print-only), and executes it.
"""
import os
import re
import subprocess
import sys

src = open("/tmp/ci-retry.yml").read().replace("\r\n", "\n")
m = re.search(r"python3 - <<'PYEOF'\n(.*?)\n          PYEOF", src, re.S)
if not m:
    sys.exit("could not extract embedded python from ci-retry.yml")
code = m.group(1)
code = "\n".join(line[10:] if line.startswith(" " * 10) else line for line in code.splitlines())

# dry-run mode: mark flag + neuter the actual rerun POST
code = code.replace(
    'def req(path, method="GET", expect_json=True):',
    'DRYRUN=True\ndef req(path, method="GET", expect_json=True):', 1)
code = code.replace(
    '    conclusion = d.get("conclusion")',
    '    conclusion = "failure"  # DRYRUN override: exercise the classifier even mid-run', 1)
code = code.replace(
    'st, resp = req("/repos/%s/actions/runs/%d/rerun-failed-jobs" % (repo, run_id), method="POST", expect_json=False)',
    'st, resp = (202, "DRYRUN-NOOP") if DRYRUN else req("/repos/%s/actions/runs/%d/rerun-failed-jobs" % (repo, run_id), method="POST", expect_json=False)', 1)
assert "DRYRUN-NOOP" in code, "rerun stub not applied"

run_id = sys.argv[1] if len(sys.argv) > 1 else "35519467948"
os.environ.update({
    "EVENT_NAME": "workflow_dispatch",
    "INPUT_RUN_ID": run_id,
    "GITHUB_REPOSITORY": "kubeworkz/grxgpu",
    "API": "https://api.github.com",
    "GITHUB_STEP_SUMMARY": "/tmp/retry_summary_dry.md",
})
out = subprocess.check_output(
    ["git", "credential", "fill"],
    input=b"protocol=https\nhost=github.com\n\n",
).decode()
tok = [l.split("=", 1)[1] for l in out.splitlines() if l.startswith("password=")][0]
os.environ["GH_TOKEN"] = tok

exec(compile(code, "ci-retry", "exec"))
