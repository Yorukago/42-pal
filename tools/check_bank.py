#!/usr/bin/env python3
"""Sanity-check data/exercises/ — run after importing a bank.

Usage:
    python3 tools/check_bank.py [rank_tag ...]        # default: every rank
    python3 tools/check_bank.py exam04 --solutions <dir>

With --solutions, every python_call exercise is graded against a reference
solution named <name>.py found anywhere under <dir>. That is the real proof
an imported bank is correct: the vectors must pass the known-good answers.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# "prototype" is deliberately not required: plenty of C exercises are whole
# programs rather than functions. Filenames aren't checked either — examshell
# globs *.json and reads "rank" from inside, so they're cosmetic.
REQUIRED = ["name", "rank", "level", "lang", "description"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ranks", nargs="*")
    ap.add_argument("--solutions", help="directory of reference solutions to grade against")
    args = ap.parse_args()

    problems = []
    by_rank = defaultdict(lambda: defaultdict(list))
    seen_names = defaultdict(list)

    for path in sorted((REPO / "data" / "exercises").glob("*.json")):
        try:
            ex = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            problems.append(f"{path.name}: invalid JSON — {e}")
            continue

        rank = ex.get("rank", "?")
        if args.ranks and rank not in args.ranks:
            continue

        for key in REQUIRED:
            if not ex.get(key):
                problems.append(f"{path.name}: missing/empty '{key}'")

        seen_names[(rank, ex.get("name"))].append(path.name)
        by_rank[rank][ex.get("level", "?")].append(ex.get("name"))

        if ex.get("checker") == "python_call":
            if not ex.get("checker_calls"):
                problems.append(f"{path.name}: python_call with no checker_calls (auto-passes!)")
            if not ex.get("function"):
                problems.append(f"{path.name}: python_call with no 'function'")
            for c in ex.get("checker_calls", []):
                for k in ("call", "expected"):
                    if k not in c:
                        problems.append(f"{path.name}: checker_call missing '{k}'")
                        continue
                try:
                    compile(c[k], "<x>", "eval")
                except SyntaxError:
                    problems.append(f"{path.name}: {k} is not a Python expression — {c[k]!r}")
        elif ex.get("lang") == "python" and not ex.get("test_cases"):
            problems.append(f"{path.name}: python exercise with no tests of any kind (auto-passes!)")

    for (rank, name), files in seen_names.items():
        if len(files) > 1:
            problems.append(f"duplicate name {rank}/{name}: {', '.join(files)}")

    print("LEVEL LADDER")
    for rank in sorted(by_rank):
        levels = sorted(by_rank[rank], key=lambda l: (len(l), l))
        total = sum(len(v) for v in by_rank[rank].values())
        print(f"  {rank:8s} {total:>3} exercises   " + "  ".join(
            f"{l}:{len(by_rank[rank][l])}" for l in levels))
        nums = sorted(int(l[5:]) for l in levels if l.startswith("level") and l[5:].isdigit())
        gaps = [n for n in range(min(nums), max(nums)) if n not in nums] if nums else []
        if gaps:
            print(f"           {'':3} gap: no level{', level'.join(map(str, gaps))}")

    if args.solutions:
        import examshell
        sols = {p.stem: p for p in Path(args.solutions).rglob("*.py")}
        print("\nREFERENCE SOLUTIONS")
        for path in sorted((REPO / "data" / "exercises").glob("*.json")):
            ex = json.loads(path.read_text())
            if ex.get("checker") != "python_call":
                continue
            if args.ranks and ex.get("rank") not in args.ranks:
                continue
            sol = sols.get(ex["name"])
            if not sol:
                print(f"  ?? {ex['name']:34s} no reference solution found")
                problems.append(f"{ex['name']}: no reference solution in {args.solutions}")
                continue
            ok, res = examshell.run_python_calls(sol, ex["checker_calls"])
            n_ok = sum(1 for r in res if r["ok"])
            print(f"  {'ok' if ok else 'XX'} {ex['name']:34s} {n_ok}/{len(res)}")
            if not ok:
                problems.append(f"{ex['name']}: reference solution fails {len(res) - n_ok} vector(s)")
                for r in res:
                    if not r["ok"]:
                        print(f"        {r['case']}  expected {r['expected']}  got {r['got']}")

    print()
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("bank looks good.")


main()
