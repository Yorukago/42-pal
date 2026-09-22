#!/usr/bin/env python3
"""Import a community ExamShell exercise bank into data/exercises/.

Usage:
    python3 tools/import_exam_bank.py <src_dir> <rank_tag> [--dry-run]

<src_dir>  a checkout containing Exercises_dict.py, whose EXERCISES maps
           exercise name -> {level, subject, function, tests}, where each test
           is a (args_list, expected_value) pair.
<rank_tag> the rank these land under, e.g. exam04.

Existing <rank_tag>_*.json files are replaced, so a re-run is idempotent.
Used originally to import github.com/SaraFreitas-dev/42-Python-ExamShell-Rank03.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "exercises"

DIFFICULTY = {1: "easy", 2: "easy", 3: "medium", 4: "medium", 5: "hard", 6: "hard"}


def split_subject(subject):
    """Return (header, body) — body is everything after the ---- rule."""
    parts = re.split(r"^-{10,}\s*$", subject, maxsplit=1, flags=re.M)
    if len(parts) == 2:
        return parts[0].strip("\n"), parts[1].strip("\n")
    return "", subject.strip("\n")


def header_field(header, field, default):
    m = re.search(rf"{field}\s*:\s*(.+)", header)
    return m.group(1).strip() if m else default


def prototype(body, fn):
    """The 'def fn(...)' line the subject declares."""
    m = re.search(
        r"^\s*(def\s+%s\s*\(.*?\)\s*(?:->\s*[^\s:]+)?\s*:)" % re.escape(fn), body, flags=re.M
    )
    return m.group(1).strip() if m else f"def {fn}(...):"


def short_desc(body, limit=110):
    """First paragraph, collapsed to a single line."""
    text = re.sub(r"\s+", " ", " ".join(body.split("\n\n", 1)[0].split()))
    if len(text) > limit:
        text = text[: limit - 3].rsplit(" ", 1)[0] + "..."
    return text


def build(name, ex, rank_tag):
    header, body = split_subject(ex["subject"])
    fn = ex["function"]
    lvl = ex["level"]

    return {
        "name": name,
        "rank": rank_tag,
        "level": f"level{lvl}",
        "lang": "python",
        "difficulty": DIFFICULTY.get(lvl, "medium"),
        "short_desc": short_desc(body),
        "description": body,
        "prototype": prototype(body, fn),
        "function": fn,
        "notes": [
            f"File to submit: {header_field(header, 'Expected files', name + '.py')}",
            f"Allowed functions: {header_field(header, 'Allowed functions', 'None')}",
            "Return the value — do not print it.",
        ],
        "test_cases": [],
        "checker": "python_call",
        "checker_calls": [
            {
                "call": f"{fn}({', '.join(repr(a) for a in args)})",
                "expected": repr(expected),
            }
            for args, expected in ex["tests"]
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir")
    ap.add_argument("rank_tag")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.src_dir).resolve()
    if not (src / "Exercises_dict.py").exists():
        sys.exit(f"error: no Exercises_dict.py in {src}")

    sys.path.insert(0, str(src))
    from Exercises_dict import EXERCISES

    stale = sorted(OUT.glob(f"{args.rank_tag}_*.json"))
    if not args.dry_run:
        for p in stale:
            p.unlink()
    print(f"{'would remove' if args.dry_run else 'removed'} {len(stale)} existing {args.rank_tag} files")

    for name, ex in sorted(EXERCISES.items()):
        doc = build(name, ex, args.rank_tag)
        dest = OUT / f"{args.rank_tag}_{name}.json"
        if not args.dry_run:
            dest.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        print(f"  {dest.name:46s} {doc['level']:8s} {len(doc['checker_calls']):>3} calls")

    print(f"\n{len(EXERCISES)} exercises -> {OUT.relative_to(REPO)}/")
    print("Verify with: python3 tools/check_bank.py")


main()
