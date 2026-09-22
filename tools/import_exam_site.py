#!/usr/bin/env python3
"""Import an exam bank from a 42exam.net site into data/exercises/.

Usage:
    python3 tools/import_exam_site.py <source> <rank_tag> [options]

<source>    https://rank04.42exam.net/js/data.js, or a local copy of it.
<rank_tag>  the rank these land under, e.g. exam04.

Options:
    --lang CODE            description language (default: en)
    --extra-vectors FILE   JSON {exercise_name: [{call, expected}, ...]} merged
                           in alongside the site's own examples, deduplicated.
    --dry-run

The site ships its bank as `var SUBJECTS = [...]` — a JS object literal with
bare keys, so it needs a string-aware pass before it will parse as JSON.
Existing <rank_tag>_*.json files are replaced, so re-running is idempotent.
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "exercises"


def js_to_json(src):
    """Quote bare object keys and drop trailing commas, ignoring string contents."""
    out, i, n = [], 0, len(src)
    while i < n:
        ch = src[i]
        if ch in "\"'":
            quote, j = ch, i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == quote:
                    break
                j += 1
            raw = src[i : j + 1]
            if quote == "'":
                raw = json.dumps(raw[1:-1].replace("\\'", "'"))
            out.append(raw)
            i = j + 1
            continue
        m = re.match(r"([A-Za-z_$][\w$]*)\s*:", src[i:])
        if m and (not out or out[-1].strip()[-1:] in "{," or not out[-1].strip()):
            out.append(f'"{m.group(1)}":')
            i += m.end()
            continue
        out.append(ch)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_subjects(source):
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source, timeout=30) as r:
            src = r.read().decode("utf-8")
    else:
        src = Path(source).read_text()
    m = re.search(r"var SUBJECTS\s*=\s*(\[.*?\])\s*;?\s*$", src, re.S)
    if not m:
        sys.exit("error: no `var SUBJECTS = [...]` found in source")
    return json.loads(js_to_json(m.group(1)))


def build(subj, rank_tag, lang, extra):
    name = subj["name"]
    desc = subj["description"]
    if isinstance(desc, dict):
        desc = desc.get(lang) or desc.get("en") or next(iter(desc.values()))

    fn = re.match(r"def\s+(\w+)", subj["signature"])
    fn = fn.group(1) if fn else name

    notes = [f"File to submit: {subj.get('file', name + '.py')}"]
    forbidden = subj.get("forbidden") or []
    if forbidden:
        notes.append("Forbidden: " + ", ".join(forbidden))
    notes.append("Return the value — do not print it.")

    calls, seen = [], set()
    for e in subj.get("examples", []):
        key = (e["input"].strip(), e["output"].strip())
        if key not in seen:
            seen.add(key)
            calls.append({"call": key[0], "expected": key[1]})
    for e in extra.get(name, []):
        key = (e["call"].strip(), e["expected"].strip())
        if key not in seen:
            seen.add(key)
            calls.append({"call": key[0], "expected": key[1]})

    short = re.sub(r"\s+", " ", desc.split("\n\n")[0]).strip()
    if len(short) > 110:
        short = short[:107].rsplit(" ", 1)[0] + "..."

    return {
        "name": name,
        "rank": rank_tag,
        "level": f"level{subj['level']}",
        "lang": "python",
        "difficulty": subj.get("difficulty", "medium"),
        "short_desc": short,
        "description": desc,
        "prototype": subj["signature"],
        "function": fn,
        "notes": notes,
        "test_cases": [],
        "checker": "python_call",
        "checker_calls": calls,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("rank_tag")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--extra-vectors")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    subjects = load_subjects(args.source)
    extra = json.loads(Path(args.extra_vectors).read_text()) if args.extra_vectors else {}

    stale = sorted(OUT.glob(f"{args.rank_tag}_*.json"))
    if not args.dry_run:
        for p in stale:
            p.unlink()
    print(f"{'would remove' if args.dry_run else 'removed'} {len(stale)} existing {args.rank_tag} files")

    for subj in sorted(subjects, key=lambda s: (s["level"], s["name"])):
        doc = build(subj, args.rank_tag, args.lang, extra)
        dest = OUT / f"{args.rank_tag}_{doc['name']}.json"
        if not args.dry_run:
            dest.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        n_site = len(subj.get("examples", []))
        n_all = len(doc["checker_calls"])
        extra_note = f" (+{n_all - n_site} merged)" if n_all > n_site else ""
        print(f"  {dest.name:44s} {doc['level']:8s} {n_all:>3} calls{extra_note}")

    print(f"\n{len(subjects)} exercises -> {OUT.relative_to(REPO)}/")
    print(f"Verify with: python3 tools/check_bank.py {args.rank_tag} --solutions <dir>")


main()
