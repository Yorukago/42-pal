# 42-pal! 🐚

A polished, terminal-based 42 Exam trainer for C, Python, and C++. Optimized for local practice and studying.

---

## Quick Start

Just run the following command in the root folder to boot the shell:
```bash
make
```

*The root `Makefile` automatically initializes local folders, establishes correct submission symlinks, and boots the terminal console immediately!*

---

## Features

### 🟢 Training Mode
* **Level Submenus**: Exercises are dynamically parsed and grouped into unique levels (e.g. *Level 0*, *Level 1*, etc.).
* **Starting Exercise Picker**: Pick exactly which exercise you want to start practicing from!
* **Sequential Loop with Skips**: Advances sequentially through remaining tasks. Simply use the custom `[n] skip to next` option to advance.
* **Live Progress Stats Bar**: Shows your position, passed count (`✓`), and skipped count (`~`) in real-time under the banner:
  ```text
  📊  Progress: [X/X]  ✓0  ~0
  ```
* **Scorecard Tally Screen**: Celebrates completion and displays a full summary scorecard upon ending or skipping your training level:
  ```text
  LEVEL TRAINING SESSION TALLY (LEVEL X)
  ──────────────────────────────────────────────────
  Total exercises:   10
  Passed (✓):        8
  Skipped (~):       1
  Remaining:         1
  ```

### 🔴 Exam Mode
* **Thread-Based Countdown Timer**: A live ticking 3-hour timer running on a background thread.
* **Random Exercise Assignment**: Select a Rank and be dynamically assigned randomized exercises per level.
* **No Skipping**: Solve the current challenge or forfeit the level!
* **Final Exam Scorecard**: Complete statistics on time used, success rate, and final passed/failed status.

### ⚡ Quality of Life (QoL)
* **Automatic Starter File Creation**: When you choose an exercise, examshell automatically establishes the directory *and* touches (creates) the empty solution file (`.c`, `.cpp`, or `.py`) inside the submission directory:
  ```text
  examshell/rendu/<exercise_name>/<exercise_name>.ext
  ```
  This eliminates manual touch actions, allowing you to instantly write code!
* **Safety First**: Prior to touching, examshell verifies if the file exists, ensuring your written solutions are never overwritten or deleted!
* **Late-Shutdown Safety**: Silent `atexit` garbage collection guarantees a completely clean interpreter exit without traceback warnings.

### 🔵 Knowledge Corner
* **Orthodox Canonical Class Form (OCCF)**: Visual diagrams and complete templates for C++.
* **Git Safety Guide**: Critical tips and BRANCH strategies to survive exam rules.
* **Multi-Language Search**: High-speed, tag-based index searching across C, C++, Python, and general Tips & Tricks.

---

## Project Structure

```text
examshell/
├── examshell.py          ← Premium Python Engine
├── Makefile              ← Directory setup and launch manager
├── README.md             ← Stunning documentation
├── .gitignore            ← Production gitignore rules
├── rendu/                ← submission directories (auto-generated)
├── tools/
│   ├── import_exam_site.py  ← import a bank from a 42exam.net subject site
│   ├── import_exam_bank.py  ← import a community ExamShell bank
│   └── check_bank.py        ← validate the bank / grade reference solutions
└── data/
    ├── exercises/        ← .json exercise files
    │   ├── exam03_py_shadow_merge.json
    │   └── ...
    └── knowledge/        ← .json knowledge docs
        ├── c.json
        ├── python.json
        ├── c++.json
        ├── git.json
        └── tips.json
```

---

## How to Add Exercises

Add a `.json` file to `data/exercises/`:
```json
{
  "name": "my_exercise",
  "lang": "c",
  "difficulty": "easy",
  "level": "level0",
  "rank": "rank02",
  "description": "Full problem description shown to the user.",
  "prototype": "int my_function(char *s)",
  "notes": ["Hint 1", "Hint 2"],
  "test_cases": [
    {
      "label": "test name",
      "stdin": "input to feed via stdin",
      "expected_output": "expected stdout output"
    }
  ]
}
```

### Python checker (Exam 03 Style)
For Python exercises that test function logic directly, set `"checker": "python_call"`.
The submitted file is loaded in a subprocess, each `call` is evaluated against its
`expected` value, and anything the solution prints is discarded:

```json
{
  "name": "py_inter",
  "rank": "exam03",
  "level": "level1",
  "lang": "python",
  "function": "inter",
  "checker": "python_call",
  "checker_calls": [
    { "call": "inter('hello', 'world')", "expected": "'lo'" },
    { "call": "inter('abc', 'xyz')",     "expected": "''" }
  ]
}
```

* `call` and `expected` are both **Python expressions**, evaluated and compared with `==`.
* `expected` is a literal, so strings need their quotes: `"'lo'"`, not `"lo"`.
* The solution's `if __name__ == "__main__":` block is **not** executed.
* A file that fails to import reports one `loading your file` failure; a solution that
  hangs is killed after 10s.

> A `python_call` exercise with an empty `checker_calls` list falls through to
> "no automated tests" and auto-passes — always ship the calls.

---

## Python exams (Rank 03+)

From Rank 03 onward the 42 exam is Python. Both banks are imported from the
official subject sites and graded by `python_call`, using the exam's real
assignment names — so the file examshell creates for you (`py_hidenp.py`) is the
file the real grader asks for.

**`exam03` — 14 exercises, levels 1–6** (source: `rank03.42exam.net`)

| Level | Exercises |
|:--|:--|
| 1 | `py_bracket_validator`, `py_cryptic_sorter` |
| 2 | `py_echo_validator`, `py_mirror_matrix` |
| 3 | `py_hidenp`, `py_inter`, `py_number_base_converter`, `py_pattern_tracker` |
| 4 | `py_anagram`, `py_shadow_merge`, `py_string_permutation_checker` |
| 5 | `py_string_sculptor`, `py_twist_sequence` |
| 6 | `py_whisper_cipher` |

**`exam04` — 7 exercises, levels 1–4** (source: `rank04.42exam.net`)

| Level | Exercises |
|:--|:--|
| 1 | `py_array_rotation_detector`, `py_constellation_mapper` |
| 2 | `py_list_intersection_finder`, `py_merge_sorted_lists` |
| 3 | `py_package_dependency_resolver`, `py_palindrome_partitioner` |
| 4 | `py_sliding_window_maximum` |

**`exam05` — 7 exercises, levels 1–3** (source: `rank05.42exam.net`)

| Level | Exercises |
|:--|:--|
| 1 | `py_compress_decompress`, `py_spiral_matrix` |
| 2 | `py_graph_cycle_detector`, `py_island_matrix_counter`, `py_room_scheduler` |
| 3 | `py_prism_detector`, `py_word_ladder` |

> ⚠️ **`exam05` is more thinly tested than the others.** No community solution
> set exists for Rank 05, so its 17 vectors are only the site's own examples —
> 2 or 3 per exercise, against 14 on average for `exam03`. They were validated
> against reference implementations, but those were written from the same
> subject text, so a misleading subject would not be caught. Treat a pass here
> as weaker evidence than a pass on `exam03`/`exam04`.
>
> `py_compress_decompress` asks for **two** functions (`compress` and
> `decompress`); only the first appears in the `prototype` field, but both are
> described in the subject and both are graded.

Passing means clearing every level — one exercise per level, as in the real exam.

Several exercises carry a **Forbidden** note in their hints: `py_cryptic_sorter`
may not use `sorted()` or `list.sort()`, `py_merge_sorted_lists` may not use
`heapq.merge()`, and so on. These come from the official subjects and are the
point of the exercise; the checker does not enforce them, so mind them yourself.

From Rank 03 onward the real exam is Python, but the older C exams are still
worth drilling, so each rank offers whichever variants exist on disk:

```text
[2] Rank 03 (C — GNL, algorithms / Python — Common Core)
[3] Rank 04 (C — processes, syscalls)        ← no exam04_*.json yet
```

The picker is data-driven (`RANK_VARIANTS` in `examshell.py`) — a rank with only
one variant present skips the C-or-Python sub-prompt, and dropping
`exam04_*.json` files into `data/exercises/` makes the Python option appear on
its own. To import a new bank:

```bash
# from an official subject site (preferred — carries levels, signatures,
# difficulty and the Forbidden lists)
python3 tools/import_exam_site.py https://rank05.42exam.net/js/data.js exam05

# from a community ExamShell repo with an Exercises_dict.py
python3 tools/import_exam_bank.py path/to/ExamShell-Rank05 exam05

# either way, prove the vectors survived by grading known-good solutions
python3 tools/check_bank.py exam05 --solutions path/to/solutions
```

`import_exam_site.py` takes `--extra-vectors FILE`, a JSON map of
`{exercise_name: [{call, expected}, ...]}`, to merge extra test cases from a
community repo on top of the official ones (deduplicated). That is how the
current banks were built: official levels and constraints, widened test
coverage.

`check_bank.py` is the one that matters: it grades every imported exercise
against the bank's own reference solutions, which is what proves the test
vectors survived the import.
