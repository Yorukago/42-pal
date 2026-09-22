#!/usr/bin/env python3
"""
examshell — a 42-style exam training tool
"""
import os
import sys
import json
import shutil
import time
import random
import subprocess
import atexit
import threading
from pathlib import Path

# ANSI colors
RED = "\033[1;31m"
GRN = "\033[1;32m"
YEL = "\033[1;33m"
BLU = "\033[1;34m"
MAG = "\033[1;35m"
CYN = "\033[1;36m"
WHT = "\033[1;37m"
B = "\033[1m"
D = "\033[2m"
RST = "\033[0m"

def clean_pycache(base_path=Path(__file__).parent, rmtree=shutil.rmtree):
    """Remove all __pycache__ directories generated during the session."""
    try:
        for p in base_path.rglob("__pycache__"):
            if p.is_dir():
                rmtree(p, ignore_errors=True)
    except Exception:
        pass

atexit.register(clean_pycache)

def clear():
    os.system("clear")

def banner():
    print(f"""{BLU}{B}
  ███████╗██╗  ██╗ █████╗ ███╗   ███╗███████╗██╗  ██╗███████╗██╗     ██╗
  ██╔════╝╚██╗██╔╝██╔══██╗████╗ ████║██╔════╝██║  ██║██╔════╝██║     ██║
  █████╗   ╚███╔╝ ███████║██╔████╔██║███████╗███████║█████╗  ██║     ██║
  ██╔══╝   ██╔██╗ ██╔══██║██║╚██╔╝██║╚════██║██╔══██║██╔══╝  ██║     ██║
  ███████╗██╔╝ ██╗██║  ██║██║ ╚═╝ ██║███████║██║  ██║███████╗███████╗███████╗
  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝
{WHT}  42-style exam trainer · C · Python · C++{RST}""")

def divider():
    print(f"{D}{'─' * 50}{RST}")

def prompt(msg="→", choices=None):
    if msg in ["choice", "rank", "level"]:
        prompt_label = "choose"
    else:
        prompt_label = msg

    if prompt_label.endswith("?") or prompt_label.endswith(".") or "Enter" in prompt_label:
        prompt_str = f"  {prompt_label} "
    else:
        prompt_str = f"  {prompt_label} → "

    while True:
        try:
            val = input(prompt_str).strip()
            if not choices:
                return val
            if val in choices:
                return val
            print(f"  {RED}Please enter one of: {', '.join(choices)}{RST}")
        except (KeyboardInterrupt, EOFError):
            return "q"

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"  {RED}Error loading {path.name}: {e}{RST}")
        return None

def get_exercises(lang=None, rank=None, level=None):
    base_dir = Path(__file__).parent / "data" / "exercises"
    exercises = []
    for p in base_dir.glob("*.json"):
        ex = load_json(p)
        if ex:
            ex["_file"] = p
            if lang and ex.get("lang") != lang:
                continue
            if rank and ex.get("rank") != rank:
                continue
            if level and ex.get("level") != level:
                continue
            exercises.append(ex)
    return sorted(exercises, key=lambda x: (x.get("rank", ""), x.get("level", ""), x.get("name", "")))

def get_resource_path(ex):
    base = Path(__file__).parent / "data" / "resources" / ex.get("rank", "") / ex.get("level", "") / ex.get("name", "")
    if base.exists():
        return base
    return None

def lang_color(lang):
    if lang == "c":
        return RED
    elif lang == "python":
        return GRN
    elif lang == "c++":
        return CYN
    return WHT

def make_submit_dir(ex):
    submit_base = Path(__file__).parent / "rendu" / ex.get("name", "")
    submit_base.mkdir(parents=True, exist_ok=True)
    
    # QoL: automatically create the empty exercise file if it doesn't exist
    lang = ex.get("lang", "c")
    ext = ".c" if lang == "c" else (".py" if lang == "python" else ".cpp")
    sol_file = submit_base / f"{ex.get('name')}{ext}"
    if not sol_file.exists():
        sol_file.touch()
        
    return submit_base

def compile_c(src_file, out_file):
    res = subprocess.run(["gcc", "-Wall", "-Wextra", "-Werror", str(src_file), "-o", str(out_file)], capture_output=True, text=True)
    return res.returncode == 0, res.stderr

def compile_cpp(src_file, out_file):
    res = subprocess.run(["g++", "-Wall", "-Wextra", "-Werror", "-std=c++17", str(src_file), "-o", str(out_file)], capture_output=True, text=True)
    return res.returncode == 0, res.stderr

def run_binary(bin_file, stdin_data=""):
    try:
        res = subprocess.run([str(bin_file)], input=stdin_data, capture_output=True, text=True, timeout=5)
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"

def run_python(py_file, stdin_data=""):
    try:
        res = subprocess.run(["python3", str(py_file)], input=stdin_data, capture_output=True, text=True, timeout=5)
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"

PY_CALL_HARNESS = r"""
import contextlib, io, json, runpy, sys

sol_path, calls_json = sys.argv[1], sys.argv[2]
calls = json.loads(calls_json)
sink = io.StringIO()

try:
    with contextlib.redirect_stdout(sink):
        ns = runpy.run_path(sol_path, run_name="examshell_solution")
except BaseException as e:
    print(json.dumps({"fatal": "%s: %s" % (type(e).__name__, e)}))
    sys.exit(0)

out = []
for c in calls:
    entry = {"call": c["call"], "expected": c["expected"]}
    try:
        with contextlib.redirect_stdout(sink):
            got = eval(c["call"], ns)
        exp = eval(c["expected"], {})
        entry["got"] = repr(got)
        entry["ok"] = bool(got == exp)
    except BaseException as e:
        entry["got"] = "%s: %s" % (type(e).__name__, e)
        entry["ok"] = False
    out.append(entry)
print(json.dumps(out))
"""

def run_python_calls(sol_file, calls):
    """Import the submitted file and evaluate each checker call against its expected value."""
    try:
        res = subprocess.run(
            ["python3", "-c", PY_CALL_HARNESS, str(sol_file), json.dumps(calls)],
            capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        return False, [{"case": "python_call", "expected": "finish in 10s", "got": "timeout", "ok": False}]

    lines = [l for l in res.stdout.splitlines() if l.strip()]
    if not lines:
        err = res.stderr.strip() or "(no output)"
        return False, [{"case": "python_call", "expected": "test results", "got": err, "ok": False}]

    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError:
        return False, [{"case": "python_call", "expected": "test results", "got": lines[-1], "ok": False}]

    if isinstance(payload, dict) and "fatal" in payload:
        return False, [{"case": "loading your file", "expected": "imports cleanly", "got": payload["fatal"], "ok": False}]

    results = [
        {"case": r["call"], "expected": r["expected"], "got": r["got"], "ok": r["ok"], "pre": True}
        for r in payload
    ]
    return all(r["ok"] for r in results), results

def check_exercise(ex):
    submit_dir = Path(__file__).parent / "rendu" / ex.get("name", "")
    lang = ex.get("lang", "c")
    ext = ".c" if lang == "c" else (".py" if lang == "python" else ".cpp")
    sol_file = submit_dir / f"{ex.get('name')}{ext}"
    
    if not sol_file.exists():
        return False, [{"case": "file check", "expected": f"a {lang} file", "got": "nothing submitted", "ok": False}]
        
    res_path = get_resource_path(ex)
    if res_path and (res_path / "tester.sh").exists():
        env = os.environ.copy()
        env["EXAMSHELL"] = "1"
        try:
            res = subprocess.run(["bash", "tester.sh"], cwd=str(res_path), capture_output=True, text=True, timeout=30, env=env)
            output = res.stdout if res.stdout else (res.stderr if res.stderr else "(no output)")
            passed = "PASSED" in output
            return passed, [{"case": "real tester.sh", "expected": "PASSED 🎉", "got": output.strip(), "ok": passed}]
        except subprocess.TimeoutExpired:
            return False, [{"case": "real tester.sh", "expected": "finish in 30s", "got": "timeout", "ok": False}]
            
    results = []
    if lang in ["c", "c++"]:
        bin_file = submit_dir / "a.out"
        if bin_file.exists():
            bin_file.unlink()
            
        compiled = False
        err = ""
        if lang == "c":
            compiled, err = compile_c(sol_file, bin_file)
        else:
            compiled, err = compile_cpp(sol_file, bin_file)
            
        if not compiled:
            return False, [{"case": "compilation", "expected": "success", "got": err, "ok": False}]
            
        test_cases = ex.get("test_cases", [])
        if not test_cases:
            return True, [{"case": "no automated tests", "expected": "manual check", "got": "submit your file and verify manually", "ok": True}]
            
        all_ok = True
        for idx, tc in enumerate(test_cases):
            stdin = tc.get("stdin", "")
            expected = tc.get("expected_output", "")
            label = tc.get("label", f"test {idx + 1}")
            
            code, stdout, stderr = run_binary(bin_file, stdin)
            ok = (stdout.strip() == expected.strip())
            results.append({"case": label, "expected": expected, "got": stdout if ok else f"{stdout}\n{stderr}", "ok": ok})
            if not ok:
                all_ok = False
                
        if bin_file.exists():
            bin_file.unlink()
            
        return all_ok, results
        
    elif lang == "python":
        if ex.get("checker") == "python_call":
            calls = ex.get("checker_calls", [])
            if not calls:
                return True, [{"case": "no automated tests", "expected": "manual check", "got": "submit your file and verify manually", "ok": True}]
            return run_python_calls(sol_file, calls)

        test_cases = ex.get("test_cases", [])
        if not test_cases:
            return True, [{"case": "no automated tests", "expected": "manual check", "got": "submit your file and verify manually", "ok": True}]
            
        all_ok = True
        for idx, tc in enumerate(test_cases):
            stdin = tc.get("stdin", "")
            expected = tc.get("expected_output", "")
            label = tc.get("label", f"test {idx + 1}")
            
            code, stdout, stderr = run_python(sol_file, stdin)
            ok = (stdout.strip() == expected.strip())
            results.append({"case": label, "expected": expected, "got": stdout if ok else f"{stdout}\n{stderr}", "ok": ok})
            if not ok:
                all_ok = False
                
        return all_ok, results
        
    return True, []

def show_check_results(results):
    for r in results:
        status = f"{GRN}✓{RST}" if r["ok"] else f"{RED}✗{RST}"
        print(f"  {status} {B}{r['case']}{RST}")
        if not r["ok"]:
            # python_call results arrive pre-formatted; everything else gets repr'd
            exp = r["expected"] if r.get("pre") else repr(r["expected"])
            got = r["got"] if r.get("pre") else repr(r["got"])
            print(f"      {D}expected:{RST} {exp}")
            print(f"      {RED}     got:{RST} {got}")

class ExamTimer(threading.Thread):
    def __init__(self, duration_sec):
        super().__init__()
        self.duration = duration_sec
        self.start_time = time.time()
        self.daemon = True
        self._expired = False
        
    def run(self):
        while time.time() - self.start_time < self.duration:
            time.sleep(1)
        self._expired = True
        
    def expired(self):
        return self._expired or (time.time() - self.start_time >= self.duration)
        
    def remaining(self):
        rem = self.duration - (time.time() - self.start_time)
        return max(0, int(rem))
        
    def remaining_str(self):
        rem = self.remaining()
        hours = rem // 3600
        minutes = (rem % 3600) // 60
        seconds = rem % 60
        color = RED if rem < 600 else (YEL if rem < 1800 else GRN)
        return f"{color}{hours:02d}:{minutes:02d}:{seconds:02d}{RST}"

def run_exercise(ex, timer=None, is_training=False, progress_str=None):
    submit_dir = make_submit_dir(ex)
    
    while True:
        clear()
        banner()
        divider()
        
        if timer:
            print(f"  ⏱  {B}Time Remaining:{RST} {timer.remaining_str()}")
            divider()
            
        if progress_str:
            print(f"  📊  {B}Progress:{RST} {progress_str}")
            divider()
            
        lang = ex.get("lang", "c")
        print(f"  {B}Exercise:{RST} {ex.get('name')}  [{lang_color(lang)}{lang.upper()}{RST}]  Difficulty: {ex.get('difficulty')}")
        divider()
        print(ex.get("description", ""))
        divider()
        if ex.get("prototype"):
            print(f"  {B}Prototype:{RST}\n  {CYN}{ex.get('prototype')}{RST}")
            divider()
            
        print(f"  {B}Submit directory:{RST} {submit_dir}")
        ext = ".c" if lang == "c" else (".py" if lang == "python" else ".cpp")
        print(f"  {YEL}Place your file {ex.get('name')}{ext} in the folder above, then choose:{RST}")
        
        if is_training:
            print("  [s] submit & check   [n] skip to next   [v] view exercise again   [q] quit")
            choices = ["s", "n", "v", "q"]
        else:
            print("  [s] submit & check   [v] view exercise again   [q] quit")
            choices = ["s", "v", "q"]
        divider()
        
        choice = prompt("choice", choices)
        if choice == "q":
            if prompt("Really quit this exercise? (y/n)", ["y", "n"]) == "y":
                return None if not is_training else "quit"
        elif choice == "n" and is_training:
            return "skipped"
        elif choice == "v":
            continue
        elif choice == "s":
            print(f"  {CYN}Checking...{RST}")
            passed, results = check_exercise(ex)
            show_check_results(results)
            divider()
            if passed:
                print(f"  {GRN}{B}✓ All tests passed!{RST}")
                input("  Press Enter to continue...")
                return True if not is_training else "passed"
            else:
                print(f"  {RED}{B}✗ Some tests failed.{RST}")
                if prompt("Retry? (y/n)", ["y", "n"]) == "n":
                    return False if not is_training else "skipped"

# Rank 02 is C only. From Rank 03 onward the real exam moved to Python, but the
# old C exam is still worth drilling — so each rank offers whichever variants
# actually have exercises on disk. Dropping exam04_*.json into data/exercises/
# is all it takes to light up the Python option for Rank 04.
RANK_VARIANTS = [
    ("Rank 02", [
        ("rank02", "C — strings, bits, lists", "Rank 02 (C — strings, bits, lists)"),
    ]),
    ("Rank 03", [
        ("rank03", "C — GNL, algorithms", "Old Rank 03 (C — GNL, algorithms)"),
        ("exam03", "Python — Common Core", "New Rank 03 (Python — Common Core)"),
    ]),
    ("Rank 04", [
        ("rank04", "C — processes, syscalls", "Old Rank 04 (C — processes, syscalls)"),
        ("exam04", "Python — Common Core", "New Rank 04 (Python — Common Core)"),
    ]),
    ("Rank 05", [
        ("rank05", "C++ — OOP, OCCF, templates", "Old Rank 05 (C++ — OOP, OCCF, templates)"),
        ("exam05", "Python — Common Core", "New Rank 05 (Python — Common Core)"),
    ]),
]

def select_rank(title="SELECT RANK", preamble=None, include_all=False):
    """Rank picker shared by training and exam mode.

    `preamble` is a list of lines redrawn above the menu after each clear, so
    callers keep their own screen furniture (the exam rules, say).

    Returns a rank tag to filter on, None for "all ranks", or "q" to go back.
    Ranks with no exercises are hidden; a rank with only one variant on disk
    skips the C-or-Python sub-prompt entirely.
    """
    while True:
        available = []
        for label, variants in RANK_VARIANTS:
            present = [v for v in variants if get_exercises(rank=v[0])]
            if present:
                available.append((label, present))

        if not available:
            print(f"  {RED}No exercises found.{RST}")
            time.sleep(1.5)
            return "q"

        clear()
        banner()
        divider()
        print(f"  {B}{title}{RST}")
        divider()
        for line in preamble or []:
            print(line)
        if preamble:
            divider()
        print("  Choose rank:")
        for idx, (label, variants) in enumerate(available):
            desc = " / ".join(short for _, short, _ in variants)
            print(f"  [{idx + 1}] {label} ({desc})")
        all_key = str(len(available) + 1)
        if include_all:
            print(f"  [{all_key}] All ranks")
        print("  [q] Back")
        divider()

        choices = [str(i + 1) for i in range(len(available))]
        if include_all:
            choices.append(all_key)
        choices.append("q")

        choice = prompt("rank", choices)
        if choice == "q":
            return "q"
        if include_all and choice == all_key:
            return None

        label, variants = available[int(choice) - 1]
        if len(variants) == 1:
            return variants[0][0]

        clear()
        banner()
        divider()
        print(f"  {B}SELECT {label.upper()} EXAM TYPE{RST}")
        divider()
        for idx, (_, _, menu_label) in enumerate(variants):
            print(f"  [{idx + 1}] {menu_label}")
        print("  [q] Back")
        divider()

        type_choice = prompt("choice", [str(i + 1) for i in range(len(variants))] + ["q"])
        if type_choice == "q":
            continue
        return variants[int(type_choice) - 1][0]

def training_mode():
    while True:
        rank_filter = select_rank(title="TRAINING MODE", include_all=True)
        if rank_filter == "q":
            return

        rank_label = rank_filter.upper() if rank_filter else "ALL RANKS"
        
        exercises = get_exercises(rank=rank_filter)
        if not exercises:
            print(f"  {RED}No exercises found.{RST}")
            time.sleep(1.5)
            continue
            
        levels = sorted(list(set(ex.get("level", "") for ex in exercises if ex.get("level"))))
        
        while True:
            clear()
            banner()
            divider()
            print(f"  {B}TRAINING MODE — SELECT LEVEL ({rank_label}){RST}")
            divider()
            for idx, lvl in enumerate(levels):
                print(f"  [{idx + 1}] {lvl.capitalize()}")
            print("  [q] Back")
            divider()
            
            choices = [str(i + 1) for i in range(len(levels))] + ["q"]
            lvl_choice = prompt("level", choices)
            if lvl_choice == "q":
                break
                
            selected_level = levels[int(lvl_choice) - 1]
            lvl_exercises = [ex for ex in exercises if ex.get("level") == selected_level]
            
            while True:
                clear()
                banner()
                divider()
                print(f"  {B}SELECT STARTING EXERCISE ({selected_level.upper()}):{RST}")
                divider()
                for idx, ex in enumerate(lvl_exercises):
                    has_tester = "✓" if get_resource_path(ex) else "·"
                    print(f"  [{idx + 1:2d}] {ex.get('name'):<30} [{lang_color(ex.get('lang'))}{ex.get('lang').upper():^6}{RST}] ({has_tester})")
                print("  [q] Back")
                divider()
                
                choices = [str(i + 1) for i in range(len(lvl_exercises))] + ["q"]
                start_choice = prompt("Select exercise # to start from", choices)
                if start_choice == "q":
                    break
                    
                start_idx = int(start_choice) - 1
                current_idx = start_idx
                passed_count = 0
                skipped_count = 0
                
                while current_idx < len(lvl_exercises):
                    ex = lvl_exercises[current_idx]
                    progress_str = f"[{current_idx + 1}/{len(lvl_exercises)}]  {GRN}✓{passed_count}{RST}  {YEL}~{skipped_count}{RST}"
                    res = run_exercise(ex, is_training=True, progress_str=progress_str)
                    if res == "quit":
                        break
                    elif res == "passed":
                        passed_count += 1
                        current_idx += 1
                    elif res == "skipped":
                        skipped_count += 1
                        current_idx += 1
                        
                if current_idx >= len(lvl_exercises):
                    clear()
                    banner()
                    divider()
                    print(f"  {GRN}{B}🎉 All of the exercises of {selected_level} are done!{RST}")
                    divider()
                    time.sleep(1.5)
                    
                clear()
                banner()
                divider()
                print(f"  {B}LEVEL TRAINING SESSION TALLY ({selected_level.upper()}){RST}")
                divider()
                print(f"  Total exercises:   {len(lvl_exercises)}")
                print(f"  Passed (✓):        {GRN}{passed_count}{RST}")
                print(f"  Skipped (~):       {YEL}{skipped_count}{RST}")
                completed = passed_count + skipped_count
                remaining = len(lvl_exercises) - completed
                print(f"  Remaining:         {remaining}")
                divider()
                if passed_count == len(lvl_exercises):
                    print(f"  {GRN}{B}👑 PERFECT! All exercises completed successfully!{RST}")
                elif passed_count + skipped_count == len(lvl_exercises):
                    print(f"  {GRN}{B}🎉 Level complete! Keep practicing skips to master them!{RST}")
                else:
                    print(f"  {YEL}{B}👍 Session ended. You completed {passed_count} exercises!{RST}")
                divider()
                input("  Press Enter to return...")

def exam_mode():
    while True:
        rules = [
            "  Rules:",
            "  · 3 hour timer, starts now",
            "  · Exercises are assigned randomly per level",
            "  · No skipping — solve the current one or fail the level",
            "  · You can quit at any time",
        ]
        rank_filter = select_rank(title="EXAM MODE", preamble=rules)
        if rank_filter == "q":
            return
        
        levels = sorted(
            {ex.get("level", "") for ex in get_exercises(rank=rank_filter) if ex.get("level")},
            key=lambda l: (len(l), l),
        )
        if not levels:
            print(f"  {RED}No exercises found for that rank.{RST}")
            time.sleep(1.5)
            continue
        
        clear()
        banner()
        divider()
        print(f"  {B}EXAM MODE — {rank_filter.upper()}{RST}")
        divider()
        for line in rules:
            print(line)
        divider()
        print(f"  {len(levels)} levels: {', '.join(levels)}")
        divider()
        if prompt("Ready? Timer starts on Enter. (y/n)", ["y", "n"]) != "y":
            continue
            
        timer = ExamTimer(10800)
        timer.start()
        
        results = []
        exam_failed = False
        
        for lvl in levels:
            lvl_exs = get_exercises(rank=rank_filter, level=lvl)
            if not lvl_exs:
                continue
                
            ex = random.choice(lvl_exs)
            passed = run_exercise(ex, timer)
            
            if timer.expired():
                break
                
            if passed is None:
                break
                
            results.append({"name": ex.get("name"), "passed": passed})
            if not passed:
                exam_failed = True
                break
                
        clear()
        banner()
        divider()
        if timer.expired():
            print(f"  {RED}{B}⏰ TIME'S UP!{RST}")
        print(f"  {B}Exam ended.{RST}")
        divider()
        print("  Results:")
        score = 0
        for r in results:
            status = f"{GRN}✓{RST}" if r["passed"] else f"{RED}✗{RST}"
            print(f"  {status} {r['name']}")
            if r["passed"]:
                score += 1
                
        divider()
        pct = (score / len(results)) * 100 if results else 0
        print(f"  Score: {score}/{len(results)} ({pct:.1f}%)")
        time_used = 10800 - timer.remaining()
        used_m = time_used // 60
        used_s = time_used % 60
        print(f"  Time used: {used_m}m {used_s}s")
        divider()
        
        if score == len(results) and len(results) > 0 and not exam_failed:
            print(f"  {GRN}{B}✓ PASSED{RST} — nice work!\n")
        else:
            print(f"  {RED}{B}✗ FAILED{RST} — keep grinding, you got this!\n")
            
        prompt("Press Enter to continue...")
        break

# (file stem in data/knowledge/, menu label). Listed explicitly so the order is
# deliberate — but a file missing from here is browsable only through Search,
# which is how git.json went unreachable for a while. Add new files here too.
KNOWLEDGE_SECTIONS = [
    ("c", "C"),
    ("python", "Python"),
    ("c++", "C++"),
    ("algorithms", "Algorithms & Techniques"),
    ("git", "Git Survival"),
    ("tips", "Exam & Life Tips"),
]

def knowledge_corner():
    while True:
        clear()
        banner()
        divider()
        print(f"  {B}KNOWLEDGE CORNER{RST}")
        divider()
        print("  Select a section:")
        for idx, (_, label) in enumerate(KNOWLEDGE_SECTIONS):
            print(f"  [{idx + 1}] {label}")
        search_key = str(len(KNOWLEDGE_SECTIONS) + 1)
        print(f"  [{search_key}] Search all topics")
        print("  [q] Back")
        divider()

        choices = [str(i + 1) for i in range(len(KNOWLEDGE_SECTIONS))] + [search_key, "q"]
        choice = prompt("choice", choices)
        if choice == "q":
            return

        if choice == search_key:
            search_knowledge(prompt("Search"))
        else:
            browse_knowledge(KNOWLEDGE_SECTIONS[int(choice) - 1][0])

def browse_knowledge(lang):
    p = Path(__file__).parent / "data" / "knowledge" / f"{lang}.json"
    doc = load_json(p)
    if not doc:
        print(f"  {RED}No knowledge docs for {lang} yet.{RST}")
        time.sleep(1.5)
        return
        
    entries = doc.get("entries", [])
    while True:
        clear()
        banner()
        divider()
        print(f"  {B}{lang.upper()} — Knowledge Corner{RST}")
        divider()
        
        for idx, entry in enumerate(entries):
            print(f"  [{idx + 1:2d}] {entry.get('title')}")
        divider()
        print("  [q] Back")
        divider()
        
        choices = [str(i + 1) for i in range(len(entries))] + ["q"]
        choice = prompt("View #", choices)
        if choice == "q":
            break
            
        show_entry(entries[int(choice) - 1], lang)

def show_entry(entry, lang):
    clear()
    banner()
    divider()
    print(f"  {B}{entry.get('title')}{RST}")
    divider()
    print(entry.get("content", ""))
    divider()
    
    if entry.get("code"):
        print(f"  ┌─ code ──────────────────────────────")
        for line in entry.get("code").split("\n"):
            print(f"  │ {line}")
        print(f"  └─────────────────────────────────────")
        divider()
        
    if entry.get("tips"):
        print(f"  {YEL}Tips:{RST}")
        for t in entry.get("tips"):
            print(f"  → {t}")
        divider()
        
    prompt("Press Enter to go back...")

def search_knowledge(query):
    base_dir = Path(__file__).parent / "data" / "knowledge"
    results = []
    
    for p in base_dir.glob("*.json"):
        doc = load_json(p)
        if doc:
            for entry in doc.get("entries", []):
                title = entry.get("title", "").lower()
                content = entry.get("content", "").lower()
                tags = " ".join(entry.get("tags", [])).lower()
                
                if query.lower() in title or query.lower() in content or query.lower() in tags:
                    results.append({"lang": p.stem, "entry": entry})
                    
    if not results:
        print(f"  {RED}No results for '{query}'.{RST}")
        prompt("Press Enter...")
        return
        
    while True:
        clear()
        banner()
        divider()
        print(f"  {B}Results for '{query}':{RST}")
        divider()
        
        for idx, r in enumerate(results):
            print(f"  [{idx + 1:2d}] [{r['lang'].upper()}] {r['entry'].get('title')}")
        divider()
        print("  [q] Back")
        divider()
        
        choices = [str(i + 1) for i in range(len(results))] + ["q"]
        choice = prompt("View #", choices)
        if choice == "q":
            break
            
        res = results[int(choice) - 1]
        show_entry(res["entry"], res["lang"])

def main():
    while True:
        clear()
        banner()
        divider()
        print("  [1]  Training Mode     · pick exercises, submit, get feedback")
        print("  [2]  Exam Mode         · 3h timer, random exercises, pass/fail")
        print("  [3]  Knowledge Corner  · syntax refs, OCCF, C++ guides, tips & tricks")
        print("  [q]  Quit")
        divider()
        
        choice = prompt("choice", ["1", "2", "3", "q"])
        if choice == "q":
            print(f"\n  {GRN}bye! keep grinding 💪{RST}\n")
            break
        elif choice == "1":
            training_mode()
        elif choice == "2":
            exam_mode()
        elif choice == "3":
            knowledge_corner()

if __name__ == '__main__':
    main()
