#!/usr/bin/env python3
"""Generate the conformance corpus from its manifest.

Usage:
    python generate.py --list
    python generate.py --out build/corpus
    python generate.py --out build/corpus --only rt-

The case list, categories and expectations come from
docs/proposals/pdk_corpus_manifest.yaml. Layer numbers and rule limits come
from the JSON tables passed with --layers and --rules; the shipped examples are
placeholders and say so.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import generators  # noqa: E402
import geometry  # noqa: E402

REPO_ROOT = HERE.parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "docs/proposals/pdk_corpus_manifest.yaml"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_table(path):
    table = json.loads(Path(path).read_text(encoding="utf-8"))
    if table.get("_placeholder"):
        print(f"note: {Path(path).name} is a placeholder table, not PDK data")
    return table


def flatten(manifest):
    cases = []
    for category in manifest["categories"]:
        for case in category["cases"]:
            entry = dict(case)
            entry["category"] = category["id"]
            cases.append(entry)
    return cases


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--layers", default=str(HERE / "layers.example.json"))
    parser.add_argument("--rules", default=str(HERE / "rules.example.json"))
    parser.add_argument("--out", default=str(REPO_ROOT / "build/corpus"))
    parser.add_argument("--only", default=None, help="generate ids with this prefix")
    parser.add_argument("--list", action="store_true", help="report cases and exit")
    args = parser.parse_args(argv)

    manifest = yaml.safe_load(Path(args.manifest).read_text(encoding="utf-8"))
    layers_doc = load_table(args.layers)
    rules_doc = load_table(args.rules)

    layers = layers_doc["layers"]
    dbu_um = layers_doc["dbu_um"]
    grid_um = rules_doc["grid_um"]
    rules = dict(rules_doc["rules"])
    rules["grid_um"] = grid_um

    cases = flatten(manifest)
    unknown = [c["id"] for c in cases if c["category"] not in generators.FAMILIES]
    if unknown:
        print(f"error: no generator for {unknown}", file=sys.stderr)
        return 2

    if args.list:
        for category in manifest["categories"]:
            ids = [c["id"] for c in category["cases"]]
            print(f"{category['id']:<18} {len(ids):>3}  {' '.join(ids)}")
        print(f"{'total':<18} {len(cases):>3}")
        return 0

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    written, provided = [], []

    for case in cases:
        if args.only and not case["id"].startswith(args.only):
            continue
        if case.get("status") == "exists":
            provided.append({
                "id": case["id"],
                "artifact": case.get("artifact"),
                "reason": "supplied, not generated",
            })
            continue
        builder = generators.build(case, geometry.Builder, layers, dbu_um,
                                   grid_um, rules)
        path = out / f"{case['id']}.gds"
        builder.write(path)
        written.append({
            "id": case["id"],
            "category": case["category"],
            "expect": case["expect"],
            "family": case.get("family"),
            "gds": path.name,
            "shapes": builder.count(),
            "sha256": digest(path),
        })

    run = {
        "manifest": {
            "path": str(Path(args.manifest)),
            "sha256": digest(args.manifest),
            "cases": len(cases),
        },
        "layers": {
            "path": str(Path(args.layers)),
            "sha256": digest(args.layers),
            "placeholder": bool(layers_doc.get("_placeholder")),
        },
        "rules": {
            "path": str(Path(args.rules)),
            "sha256": digest(args.rules),
            "placeholder": bool(rules_doc.get("_placeholder")),
        },
        "written": len(written),
        "provided": provided,
        "cases": written,
    }
    (out / "run.json").write_text(json.dumps(run, indent=2) + "\n",
                                  encoding="utf-8")
    print(f"wrote {len(written)} layouts to {out} "
          f"({len(provided)} supplied, {len(cases)} in manifest)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
