"""Tests for ci/check_docs.py.

The cases use the real ECC amendment text and quoted snippets, copied into a
throwaway tree and perturbed there, so the requirement documents are never
edited. Each mutated citation changes only the line range and expects a
containment failure.

Run directly:  python3 -m pytest ci/test_check_docs.py -q
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "ci/check_docs.py"
BASELINE = ROOT / "docs/proposals/g100_production_baseline.md"
CHECKLIST = ROOT / "docs/grxgpu_g100_t0_tapeout_checklist.md"
D1 = ROOT / "docs/proposals/g100_t0_ecc_d1_32_7_amendment.md"
D3 = ROOT / "docs/proposals/g100_t0_ecc_d3_error_reporting_amendment.md"
SIGNOFF = ROOT / "docs/evidence/g100-t0-ecc-s0-2026-11-20/signoff.md"

ECC_RECORDS = (
    "docs/proposals/g100_t0_ecc_d1_32_7_amendment.md",
    "docs/proposals/g100_t0_ecc_d3_error_reporting_amendment.md",
    "docs/proposals/g100_t0_ecc_closure_plan.md",
    "docs/evidence/g100-t0-ecc-s0-2026-11-20/signoff.md",
    "docs/grxgpu_g100_t0_g1_evidence_audit.md",
)


def run(root, *paths):
    return subprocess.run([sys.executable, str(CHECKER), *paths],
                          cwd=str(root), capture_output=True, text=True)


def write(root, rel, text):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def tree(tmp_path, amendment, name):
    write(tmp_path, "docs/proposals/g100_production_baseline.md", BASELINE.read_text(encoding="utf-8"))
    write(tmp_path, "docs/proposals/g100_t0_tapeout_checklist.md", CHECKLIST.read_text(encoding="utf-8"))
    text = amendment.read_text(encoding="utf-8")
    return text, write(tmp_path, "docs/proposals/{}.md".format(name), text)


def test_ecc_records_pass():
    result = run(ROOT, *ECC_RECORDS)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "check_docs: OK" in result.stdout
    assert "in 5 files" in result.stdout


def test_success_summary_uses_singular_file():
    result = run(ROOT, "docs/proposals/g100_t0_ecc_d1_32_7_amendment.md")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "in 1 file" in result.stdout
    assert "1 files" not in result.stdout


def test_truncated_paragraph_range_fails(tmp_path):
    text, doc = tree(tmp_path, D1, "d1_bad")
    assert text.count("`g100_production_baseline.md:299-302`") == 1
    doc.write_text(text.replace(":299-302", ":299-301"), encoding="utf-8")
    result = run(tmp_path, "docs/proposals/d1_bad.md")
    assert result.returncode == 1, result.stdout
    assert "range does not contain the quoted text" in result.stdout


def test_off_by_two_range_fails(tmp_path):
    text, doc = tree(tmp_path, D3, "d3_bad")
    assert text.count("`g100_t0_tapeout_checklist.md:283-285`") == 1
    doc.write_text(text.replace(":283-285", ":280-282"), encoding="utf-8")
    result = run(tmp_path, "docs/proposals/d3_bad.md")
    assert result.returncode == 1, result.stdout
    assert ":280-282" in result.stdout
    assert "range does not contain the quoted text" in result.stdout


def test_inline_quote_outside_range_fails(tmp_path):
    tree(tmp_path, D1, "unused")
    write(tmp_path, "docs/proposals/quote.md",
          'See `g100_production_baseline.md:300` ("raises a fault the debug path can read").\n')
    result = run(tmp_path, "docs/proposals/quote.md")
    assert result.returncode == 1, result.stdout
    assert "range does not contain the quoted text" in result.stdout


def test_inline_quote_inside_range_passes(tmp_path):
    tree(tmp_path, D1, "unused")
    write(tmp_path, "docs/proposals/quote.md",
          'See `g100_production_baseline.md:301` ("raises a fault the debug path can read").\n')
    result = run(tmp_path, "docs/proposals/quote.md")
    assert result.returncode == 0, result.stdout + result.stderr


def test_quote_across_wrapped_lines_passes(tmp_path):
    tree(tmp_path, D1, "unused")
    write(tmp_path, "docs/proposals/quote.md",
          'See `g100_production_baseline.md:300-301` ("A correctable error increments a counter; '
          'an uncorrectable one raises a fault").\n')
    result = run(tmp_path, "docs/proposals/quote.md")
    assert result.returncode == 0, result.stdout + result.stderr


def test_source_range_past_end_fails(tmp_path):
    write(tmp_path, "docs/src/target.c", "int first;\nint second;\n")
    write(tmp_path, "docs/note.md", "See `target.c:5-9` in the source.\n")
    result = run(tmp_path, "docs/note.md")
    assert result.returncode == 1, result.stdout
    assert "range ends past target.c" in result.stdout


def test_missing_linked_in_repo_source_fails(tmp_path):
    write(tmp_path, "docs/note.md", "See [`target.c:3`](src/target.c#L3).\n")
    result = run(tmp_path, "docs/note.md")
    assert result.returncode == 1, result.stdout
    assert "target file does not exist" in result.stdout


def test_missing_target_fails(tmp_path):
    write(tmp_path, "docs/proposals/missing.md", "See `absent.md:3` for the claim.\n")
    result = run(tmp_path, "docs/proposals/missing.md")
    assert result.returncode == 1, result.stdout
    assert "target file does not exist" in result.stdout


def test_range_past_end_fails(tmp_path):
    tree(tmp_path, D1, "unused")
    write(tmp_path, "docs/proposals/eof.md", "See `g100_production_baseline.md:99999`.\n")
    result = run(tmp_path, "docs/proposals/eof.md")
    assert result.returncode == 1, result.stdout
    assert "range ends past" in result.stdout


def test_shorthand_inherits_path(tmp_path):
    tree(tmp_path, D1, "unused")
    write(tmp_path, "docs/proposals/short.md",
          "See `g100_production_baseline.md:207` and `:211`, then `:46`.\n")
    result = run(tmp_path, "docs/proposals/short.md")
    assert result.returncode == 0, result.stdout + result.stderr


def test_bare_shorthand_is_ignored(tmp_path):
    tree(tmp_path, D1, "unused")
    write(tmp_path, "docs/proposals/short.md", "See `:301` only, with no path on the line.\n")
    result = run(tmp_path, "docs/proposals/short.md")
    assert result.returncode == 0, result.stdout + result.stderr


def test_bare_file_name_resolves(tmp_path):
    write(tmp_path, "docs/proposals/g100_production_baseline.md", "first\nsecond phrase here\n")
    write(tmp_path, "docs/proposals/bare.md", 'See `g100_production_baseline.md:2` (line, "phrase here").\n')
    result = run(tmp_path, "docs/proposals/bare.md")
    assert result.returncode == 0, result.stdout + result.stderr


def test_signoff_passes_after_the_range_fix():
    result = run(ROOT, str(SIGNOFF.relative_to(ROOT)))
    assert result.returncode == 0, result.stdout + result.stderr
