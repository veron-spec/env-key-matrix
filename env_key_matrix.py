#!/usr/bin/env python3
"""Compare variable names across dotenv files without exposing their values."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ASSIGNMENT_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


def scan_file(path: Path) -> tuple[set[str], list[dict[str, int | str]]]:
    keys: set[str] = set()
    issues: list[dict[str, int | str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return keys, [{"line": 0, "kind": "read-error"}]
    for number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = ASSIGNMENT_RE.match(line)
        if not match:
            issues.append({"line": number, "kind": "malformed-line"})
            continue
        key = match.group(1)
        if key in keys:
            issues.append({"line": number, "kind": "duplicate-key", "key": key})
        keys.add(key)
    return keys, issues


def compare(paths: list[Path]) -> tuple[list[dict], list[dict]]:
    key_sets: list[set[str]] = []
    issues: list[dict] = []
    for path in paths:
        keys, file_issues = scan_file(path)
        key_sets.append(keys)
        issues.extend({"file": str(path), **issue} for issue in file_issues)
    all_keys = sorted(set().union(*key_sets))
    rows = [
        {"key": key, "present_in": [str(path) for path, keys in zip(paths, key_sets) if key in keys]}
        for key in all_keys
    ]
    return rows, issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare dotenv variable names without printing values.")
    parser.add_argument("files", nargs="+", type=Path, help="two or more dotenv files to compare")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    if len(args.files) < 2:
        parser.error("provide at least two dotenv files")
    missing = [str(path) for path in args.files if not path.is_file()]
    if missing:
        print("error: input file not found", file=sys.stderr)
        return 2
    rows, issues = compare(args.files)
    if args.as_json:
        print(json.dumps({"files": [str(path) for path in args.files], "keys": rows, "issues": issues}, indent=2))
    else:
        names = [path.name for path in args.files]
        width = max([3, *(len(row["key"]) for row in rows)])
        print(f"{'KEY':<{width}}  " + "  ".join(names))
        for row in rows:
            present = set(row["present_in"])
            markers = ["yes" if str(path) in present else "-" for path in args.files]
            print(f"{row['key']:<{width}}  " + "  ".join(markers))
        for issue in issues:
            location = f"{issue['file']}:{issue['line']}"
            detail = f" {issue['key']}" if "key" in issue else ""
            print(f"{location}: {issue['kind']}{detail}")
        print(f"Compared {len(args.files)} files; {len(rows)} unique keys; {len(issues)} issue(s)")
    drift = any(len(row["present_in"]) != len(args.files) for row in rows)
    return 1 if issues or drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
