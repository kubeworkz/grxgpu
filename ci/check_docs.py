#!/usr/bin/env python3
"""Check that a cited path:line range contains the text the document names.

A citation is a backticked target such as
`docs/proposals/g100_production_baseline.md:299-302`, or the shorthand
`:299-302` that inherits the last full path on the same line. A target may be
written relative to the citing document, to the repository root, or as a bare
file name that is unique in the tree. The range must exist, and when the
citation carries a quoted snippet that snippet must occur inside the range:

  - a heading citation such as `### B1 — ECC row (`path:207`)` takes the first
    `Before:` fence in its section as the named text; a heading containing
    ", phrase" switches to a whitespace-insensitive substring check;
  - an inline citation may quote its text in double quotes on the same line.

Citations whose links point at sources outside the checkout (Mesa's vortexpipe,
gem5) are skipped: the repository cannot resolve them.

Run: python3 ci/check_docs.py docs/proposals/g100_t0_ecc_d1_32_7_amendment.md
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

PATH = r"[A-Za-z0-9_./-]+\.(?:md|sv|v|toml|txt|py|sh|c|cpp|h|cc|in|ld|s)"
EXTERNAL_TREES = ("src/gallium/drivers/vortexpipe/",)
CITE_RE = re.compile(r"`(?P<path>" + PATH + r")?:(?P<ranges>\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*)`")
QUOTE_RE = re.compile(r'"([^"\n]+)"')
HEADING_RE = re.compile(r"^#{1,6} ")
FENCE_RE = re.compile(r"^```[A-Za-z]*\s*$")


def parse_ranges(spec):
    for part in spec.split(","):
        if "-" in part:
            first, last = part.split("-", 1)
            yield int(first), int(last)
        else:
            yield int(part), int(part)


def build_index(root):
    """Tracked files, so a bare `VX_cache_data.sv` can be resolved once."""
    try:
        listed = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                                capture_output=True, check=True).stdout.decode()
        return [root / entry for entry in listed.split("\0") if entry]
    except (OSError, subprocess.CalledProcessError):
        return None


def citation_link(line, start, stop):
    found = re.match(r"\s*\]\(\s*([^)#\s]+)", line[start:stop])
    return found.group(1) if found else None


def is_external(linked, root):
    """True only for links outside the checkout or under a known external tree."""
    if root not in linked.parents:
        return True
    relative = linked.relative_to(root).as_posix()
    return relative.startswith(EXTERNAL_TREES)


def external_names(doc, root, lines):
    """Source names this document cites outside the checkout."""
    names = set()
    for line in lines:
        matches = list(CITE_RE.finditer(line))
        for position, match in enumerate(matches):
            stop = matches[position + 1].start() if position + 1 < len(matches) else len(line)
            link = citation_link(line, match.end(), stop)
            if not link:
                continue
            linked = (doc.parent / link).resolve()
            if is_external(linked, root):
                names.add(Path(link).name)
                names.add(Path(match.group("path") or link).name)
    return names


def resolve(doc, root, rel, index, link=None):
    if link:
        linked = (doc.parent / link).resolve()
        if linked.is_file():
            return linked
    for base in (doc.parent, root):
        candidate = base / rel
        if candidate.is_file():
            return candidate.resolve()
    name = Path(rel).name
    if index is not None:
        found = [path for path in index if path.name.endswith(name)]
    else:
        found = [path for path in root.rglob("*" + name)
                 if path.is_file() and not {"build", ".git", "__pycache__"} & set(path.parts)]
    if len(found) > 1:
        exact = [path for path in found if path.as_posix().endswith("/" + rel.lstrip("./"))]
        found = exact if len(exact) == 1 else found
    return found[0].resolve() if len(found) == 1 else None


def heading_snippet(lines, index):
    """Return (mode, text) for the citation heading at `index`, or None.

    The named text is the first fenced block after a `Before:` line before the
    next heading. A ", phrase" annotation means the block is an excerpt, not
    whole lines.
    """
    line = lines[index]
    if not HEADING_RE.match(line):
        return None
    end = len(lines)
    for probe in range(index + 1, len(lines)):
        if HEADING_RE.match(lines[probe]):
            end = probe
            break
    position = None
    for probe in range(index + 1, end):
        if lines[probe].strip() == "Before:":
            position = probe
            break
    if position is None:
        return None
    for probe in range(position + 1, end):
        if FENCE_RE.match(lines[probe]):
            block = []
            for body in range(probe + 1, end):
                if lines[body].strip() == "```":
                    mode = "phrase" if ", phrase" in line else "block"
                    return mode, "\n".join(block)
                block.append(lines[body])
            return None
    return None


def inline_quote(line, start, stop):
    """A quote is only attributed when it sits in the parenthetical after the citation."""
    parenthetical = re.match(r"\s*\(([^()]*)\)", line[start:stop])
    if parenthetical is None:
        return None
    found = QUOTE_RE.search(parenthetical.group(1))
    return found.group(1) if found else None


def normalize(text):
    return " ".join(text.split())


def block_in_range(block, range_lines):
    wanted = block.splitlines()
    if not wanted:
        return True
    for start in range(len(range_lines) - len(wanted) + 1):
        if range_lines[start:start + len(wanted)] == wanted:
            return True
    return False


def check_document(doc, root, errors, index):
    lines = doc.read_text(encoding="utf-8").splitlines()
    external = external_names(doc, root, lines)
    checked = 0
    for number, line in enumerate(lines):
        last_path = None
        matches = list(CITE_RE.finditer(line))
        for position, match in enumerate(matches):
            checked += 1
            rel = match.group("path")
            if rel:
                last_path = rel
            elif last_path is None:
                continue  # prose shorthand such as "the audit's `:108`" has no path to check
            stop = matches[position + 1].start() if position + 1 < len(matches) else len(line)
            link = citation_link(line, match.end(), stop)
            target = resolve(doc, root, rel or last_path, index, link)
            if target is None:
                if Path(rel or last_path).name in external:
                    continue
                errors.append((doc, number + 1, match.group(0), "target file does not exist"))
                continue
            if link and root not in target.parents:
                continue
            target_lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
            for first, last in parse_ranges(match.group("ranges")):
                if first < 1 or last < first:
                    errors.append((doc, number + 1, match.group(0), "invalid range"))
                    continue
                if last > len(target_lines):
                    errors.append((doc, number + 1, match.group(0),
                                   "range ends past {} ({} lines)".format(target.name, len(target_lines))))
                    continue
                range_lines = target_lines[first - 1:last]
                snippet = heading_snippet(lines, number)
                if snippet is None:
                    quote = inline_quote(line, match.end(), stop)
                    snippet = ("phrase", quote) if quote else None
                if not snippet:
                    continue
                mode, wanted = snippet
                if mode == "phrase":
                    inside = normalize(wanted) in normalize("\n".join(range_lines))
                else:
                    inside = block_in_range(wanted, range_lines)
                if not inside:
                    errors.append((doc, number + 1, match.group(0),
                                   "range does not contain the quoted text"))
    return checked


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check cited path:line ranges against their named text.")
    parser.add_argument("paths", nargs="*", help="Markdown files or directories (default: docs)")
    parser.add_argument("--root", default=".", help="repository root for path resolution")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    inputs = args.paths or ["docs"]
    docs = []
    for entry in inputs:
        path = (Path.cwd() / entry).resolve()
        if path.is_dir():
            docs.extend(sorted(path.rglob("*.md")))
        elif path.is_file():
            docs.append(path)
        else:
            print("check_docs: {} does not exist".format(entry), file=sys.stderr)
            return 2

    index = build_index(root)
    errors = []
    citations = sum(check_document(doc, root, errors, index) for doc in docs)
    for doc, line, cite, problem in errors:
        print("{}:{}: {}: {}".format(doc.relative_to(root) if root in doc.parents else doc, line, cite, problem))
    if errors:
        print("check_docs: FAIL - {} of {} citations failed".format(len(errors), citations), file=sys.stderr)
        return 1
    noun = "file" if len(docs) == 1 else "files"
    print("check_docs: OK - {} citations in {} {}".format(citations, len(docs), noun))
    return 0


if __name__ == "__main__":
    sys.exit(main())
