"""Tests for the repo hygiene gates.

Each test builds a throwaway git repository, copies the gates into it, and runs
them there, so the checkout under test is never modified and every case is
reproducible. The gates are shell scripts on purpose — they run in the
toolchain-free CI checks job — and they are git plumbing around the index, so
the tests drive them through real git state rather than mocking it:

  ci/check_tracked_artifacts.sh  build output and machine binaries
  ci/check_lf_endings.sh         CRLF blobs in scripts and pinned files
  ci/hooks/pre-commit            both gates on the staged paths
  ci/install_hooks.sh            core.hooksPath enablement
  ci/binary_magic.py             the batch parser behind the staged scan

Run directly:  python3 -m pytest ci/test_repo_gates.py -q
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BASH = shutil.which("bash")

pytestmark = pytest.mark.skipif(BASH is None, reason="the gates need a POSIX shell")

COPIED = (
    "ci/check_tracked_artifacts.sh",
    "ci/check_lf_endings.sh",
    "ci/binary_magic.py",
    "ci/hooks/pre-commit",
    "ci/install_hooks.sh",
    ".gitattributes",
)

ELF = b"\x7fELF\x02\x01\x01\x00"
MACHO = b"\xcf\xfa\xed\xfe"
PNG = b"\x89PNG\r\n\x1a\n"


def _run(argv, repo, **kwargs):
    return subprocess.run(argv, cwd=str(repo), capture_output=True, text=True, **kwargs)


def _git(repo, *args):
    result = _run(["git", *args], repo)
    assert result.returncode == 0, "git {} failed: {}".format(" ".join(args), result.stderr)
    return result.stdout


def _write(repo, rel, data):
    path = Path(repo) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data)
    return path


def _stage_blob(repo, rel, data):
    """Place `data` in the index under `rel` byte for byte.

    A normal `git add` runs the eol filter, which would rewrite CRLF away and
    hide the very blobs these tests need to construct.
    """
    hashed = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=str(repo),
                            input=data, capture_output=True, check=True)
    sha = hashed.stdout.decode().strip()
    _git(repo, "update-index", "--add", "--cacheinfo", "100644,{},{}".format(sha, rel))


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    for rel in COPIED:
        destination = root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, destination)
        destination.chmod(0o755)

    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "core.autocrlf", "false")
    _git(root, "config", "commit.gpgsign", "false")
    _git(root, "config", "user.email", "gates@example.invalid")
    _git(root, "config", "user.name", "Gate Tests")
    _write(root, "README.md", "hello\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _artifacts(repo, *args):
    return _run([BASH, str(Path(repo) / "ci/check_tracked_artifacts.sh"), *args], repo)


def _lf(repo, *args):
    return _run([BASH, str(Path(repo) / "ci/check_lf_endings.sh"), *args], repo)


def _hook(repo):
    return _run([BASH, str(Path(repo) / "ci/hooks/pre-commit")], repo)


# --------------------------------------------------------------------------- #
# build output and machine binaries
# --------------------------------------------------------------------------- #

def test_artifacts_pass_on_a_clean_tree(repo):
    result = _artifacts(repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no build output" in result.stdout


def test_artifacts_reject_staged_build_output(repo):
    _write(repo, "obj/demo.stamp", "")
    _git(repo, "add", "-f", "obj/demo.stamp")

    result = _artifacts(repo, "--staged")

    assert result.returncode == 1
    assert "obj/demo.stamp" in result.stdout
    assert "generated build/test output" in result.stdout


def test_artifacts_reject_extensionless_binary(repo):
    _stage_blob(repo, "tool", ELF + b"\x00")

    result = _artifacts(repo, "--staged")

    assert result.returncode == 1
    assert "machine binary is tracked: tool" in result.stdout


def test_artifacts_reject_binary_git_calls_text(repo):
    """A four-byte Mach-O has no NUL, so git's -I heuristic calls it text.

    Splitting the tree by that heuristic used to hide it from the scan.
    """
    _stage_blob(repo, "short_tool", MACHO)

    result = _artifacts(repo, "--staged")

    assert result.returncode == 1
    assert "short_tool" in result.stdout


def test_artifacts_reject_binary_in_the_full_scan(repo):
    """The full scan reads the checkout copy, the staged scan reads the index.

    Both paths have their own magic check, so both need a test.
    """
    _write(repo, "tool", ELF + b"\x00")
    _git(repo, "add", "-f", "tool")

    result = _artifacts(repo)

    assert result.returncode == 1
    assert "machine binary is tracked: tool" in result.stdout


def test_artifacts_allow_text_and_image_assets(repo):
    _stage_blob(repo, "notes.txt", b"hello\n")
    _stage_blob(repo, "logo.png", PNG)

    result = _artifacts(repo, "--staged")

    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_tolerate_submodule_gitlink(repo):
    sha = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "update-index", "--add", "--cacheinfo", "160000,{},vendor/lib".format(sha))

    result = _artifacts(repo, "--staged")

    assert result.returncode == 0
    assert "Traceback" not in result.stderr


def test_artifacts_reject_tracked_and_ignored_file(repo):
    _write(repo, ".gitignore", "*.tmp\n")
    _write(repo, "scratch.tmp", "x\n")
    _git(repo, "add", ".gitignore")
    _git(repo, "add", "-f", "scratch.tmp")
    _git(repo, "commit", "-q", "-m", "ignored file")

    result = _artifacts(repo)

    assert result.returncode == 1
    assert "scratch.tmp" in result.stdout


# --------------------------------------------------------------------------- #
# line endings
# --------------------------------------------------------------------------- #

def test_lf_pass_on_a_clean_tree(repo):
    result = _lf(repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "stored as LF" in result.stdout


def test_lf_reject_crlf_blob_in_a_pinned_file(repo):
    _stage_blob(repo, "ci/script.sh", b"#!/bin/sh\r\necho hi\r\n")

    result = _lf(repo, "--staged")

    assert result.returncode == 1
    assert "ci/script.sh" in result.stdout
    assert "CRLF" in result.stdout


def test_lf_reject_shebang_file_without_a_pin(repo):
    _write(repo, "tool", "#!/bin/sh\necho hi\n")
    _git(repo, "add", "tool")

    result = _lf(repo, "--staged")

    assert result.returncode == 1
    assert "tool" in result.stdout
    assert "no rule pins" in result.stdout


def test_lf_staged_change_without_pinned_files(repo):
    """Regression: an empty pinned set fed a blank path into the array.

    The gate aborted with `index_eol: bad array subscript`, which would have
    blocked every commit that stages only unpinned files.
    """
    _write(repo, "notes.txt", "hello\n")
    _git(repo, "add", "notes.txt")

    result = _lf(repo, "--staged")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "bad array subscript" not in result.stderr


def test_lf_fails_closed_without_attributes(repo):
    _git(repo, "rm", "-q", ".gitattributes")

    result = _lf(repo)

    assert result.returncode == 1
    assert "no longer pins" in result.stderr


# --------------------------------------------------------------------------- #
# hook and installer
# --------------------------------------------------------------------------- #

def test_hook_blocks_a_staged_artifact(repo):
    _write(repo, "obj/demo.stamp", "")
    _git(repo, "add", "-f", "obj/demo.stamp")

    result = _hook(repo)

    assert result.returncode == 1
    assert "--no-verify" in result.stdout


def test_hook_passes_a_clean_tree(repo):
    result = _hook(repo)
    assert result.returncode == 0, result.stdout + result.stderr


def test_install_hooks_is_idempotent(repo):
    first = _run([BASH, str(Path(repo) / "ci/install_hooks.sh")], repo)
    assert first.returncode == 0
    assert _git(repo, "config", "--get", "core.hooksPath").strip() == "ci/hooks"

    second = _run([BASH, str(Path(repo) / "ci/install_hooks.sh")], repo)
    assert second.returncode == 0
    assert "already enabled" in second.stdout


# --------------------------------------------------------------------------- #
# batch parser
# --------------------------------------------------------------------------- #

def test_binary_magic_parser_handles_missing_and_submodule(repo, tmp_path):
    requests = ["missing/path", "vendor/lib", "notes.txt", "tool"]
    _stage_blob(repo, "notes.txt", b"hello\n")
    _stage_blob(repo, "tool", ELF)
    sha = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "update-index", "--add", "--cacheinfo", "160000,{},vendor/lib".format(sha))

    request_file = tmp_path / "requests.txt"
    request_file.write_text("\n".join(requests) + "\n")
    batch = subprocess.run(["git", "cat-file", "--batch"], cwd=str(repo),
                           input="".join(":{}\n".format(r) for r in requests).encode(),
                           capture_output=True, check=True)

    parsed = subprocess.run(
        [sys.executable, str(Path(repo) / "ci/binary_magic.py"), str(request_file)],
        input=batch.stdout, capture_output=True)

    assert parsed.returncode == 0, parsed.stderr.decode()
    # One answer per request, in order, and only the ELF blob is a hit.
    assert parsed.stdout.decode().split() == ["tool"]
