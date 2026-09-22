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
│   ├── import_exam_bank.py  ← import a community bank into data/exercises/
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

## Exam 03 (Rank 03 Python)

The `exam03` rank mirrors the current 42 Rank 03 Python exam: **14 exercises across
levels 1–6**, graded by `python_call`. Subjects, function names and test vectors are
taken from the real exam, so the file you submit matches what the real grader asks for:

| Level | Exercises |
|:--|:--|
| 1 | `py_cryptic_sorter`, `py_inter` |
| 2 | `py_echo_validator`, `py_mirror_matrix` |
| 3 | `py_hidenp`, `py_number_base_converter`, `py_pattern_tracker` |
| 4 | `py_anagram`, `py_shadow_merge`, `py_string_permutation_checker` |
| 5 | `py_string_sculptor`, `py_twist_sequence` |
| 6 | `py_bracket_validator`, `py_whisper_cipher` |

As in the real exam, passing means clearing **6/6** — one exercise per level.

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
python3 tools/import_exam_bank.py path/to/ExamShell-Rank04 exam04
python3 tools/check_bank.py exam04 --solutions path/to/ExamShell-Rank04/solutions
```

`check_bank.py` is the one that matters: it grades every imported exercise
against the bank's own reference solutions, which is what proves the test
vectors survived the import.
