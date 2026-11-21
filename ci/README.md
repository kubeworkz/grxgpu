# ci/

Scripts the pipeline runs. The build, test and toolchain recipes are in
[docs/continuous_integration.md](../docs/continuous_integration.md); this page
covers the toolchain-free `checks` job in
[.github/workflows/ci.yml](../.github/workflows/ci.yml).

## Checks job

| Gate | Rejects | Run it |
| --- | --- | --- |
| `check_tracked_artifacts.sh` | build output and machine binaries in the index | `./ci/check_tracked_artifacts.sh` |
| `check_lf_endings.sh` | CRLF in scripts and LF-pinned files | `./ci/check_lf_endings.sh` |
| `check_docs.py` | cited `path:line` ranges that are missing, past the end of the file, or do not contain the text the document names | `python3 ci/check_docs.py docs` |

The same job then runs `test_repo_gates.py` (the hygiene gates, exercised in
throwaway repositories) and `test_check_docs.py` (the citation gate) with
`python3 -m pytest`. Both gates are cheap and run on every event, including
docs-only changes.

`hooks/pre-commit`, enabled by `install_hooks.sh`, runs both hygiene gates on
the staged paths and the citation gate on staged Markdown; staging
`.gitignore` or `.gitattributes` switches it to the full tree. The hygiene
gates read the index, while the citation gate reads the checkout copy of each
staged file, so a partially staged doc is checked as it currently reads. It
skips the citation gate with a warning when no working `python3`/`python` is on
PATH.

## Docs citation gate

A citation is a backticked target such as
`docs/proposals/g100_production_baseline.md:299-302` or a comma list such as
`VX_dm_sba.sv:48,58,82`. A shorthand such as
`:299-302` inherits the last full path on its line; a bare `:108` with no path
on its line is prose shorthand and is not checked.

Targets resolve against the citing document's directory, then the repository
root, then a unique tracked file name, so a bare `VX_cache_data.sv` finds
`hw/rtl/cache/VX_cache_data.sv`. The range must exist in the file, and when the
citation carries quoted text that text must occur inside the range:

- a heading citation, `### B1 — ECC row (\`path:207\`)`, takes the first
  `Before:` fenced block in its section as the named text and matches it
  line for line; a heading containing `, phrase` switches to a
  whitespace-insensitive substring check;
- an inline citation takes a double-quoted phrase from the parenthetical
  immediately after it.

The checker only reads documents. It prints one `file:line: citation: problem`
line per failure and exits 1, which fails the job.

```bash
python3 ci/check_docs.py docs
python3 -m pytest ci/test_check_docs.py -q
```
