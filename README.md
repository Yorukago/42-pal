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
For Python exercises that test function logic directly:
```json
{
  "checker": "python_call",
  "checker_calls": [
    {
      "call": "my_function(42)",
      "expected": "84"
    }
  ]
}
```
