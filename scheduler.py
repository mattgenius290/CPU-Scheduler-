# ╔══════════════════════════════════════════════════════════════════════╗
# ║         CPU SCHEDULING SIMULATOR                                     ║
# ║         NAME: MATEO, JUAN PAULO G.                                   ║
# ║         SECTION: BSCS 3A                                             ║
# ╚══════════════════════════════════════════════════════════════════════╝

import os
import subprocess
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.patches as patch_module

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ANSI ESCAPE CODES  ── replaces colorama, zero external dependencies
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ANSI:
    RESET        = "[0m"
    BOLD         = "[1m"
    DIM          = "[2m"
    RED          = "[31m"
    WHITE        = "[97m"
    CYAN         = "[96m"
    YELLOW       = "[93m"
    GREEN        = "[92m"
    LIGHT_CYAN   = "[96m"
    LIGHT_YELLOW = "[93m"
    LIGHT_GREEN  = "[92m"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  THEME  ── all color / symbol constants live here
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Theme:
    BORDER   = ANSI.CYAN
    TITLE    = ANSI.LIGHT_YELLOW
    LABEL    = ANSI.LIGHT_CYAN
    VALUE    = ANSI.LIGHT_GREEN
    PROMPT   = ANSI.YELLOW
    WARN     = ANSI.RED
    MUTED    = ANSI.WHITE
    RESET    = ANSI.RESET
    DIM      = ANSI.DIM

    # Box-drawing chars 
    TL = "╭";  TR = "╮";  BL = "╰";  BR = "╯"
    H  = "─";  V  = "│";  LT = "├";  RT = "┤"
    MT = "┬";  MB = "┴";  XX = "┼"

    # Icons
    ICO_CPU  = "⚙ "
    ICO_PROC = "◈ "
    ICO_CLK  = "◷ "
    ICO_STAR = "✦ "
    ICO_WARN = "⚠ "
    ICO_OK   = "✔ "
    ICO_ERR  = "✘ "
    ICO_ARR  = "▶ "

T = Theme   # short alias

WIDTH = 68   # inner content width

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DISPLAY HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def clr():
    cmd = ["cmd", "/c", "cls"] if os.name == "nt" else ["clear"]
    subprocess.run(cmd, check=False)

def ruler(left=T.LT, right=T.RT):
    print(T.BORDER + left + T.H * WIDTH + right + ANSI.RESET)

def top_bar():
    print(T.BORDER + T.TL + T.H * WIDTH + T.TR + ANSI.RESET)

def bot_bar():
    print(T.BORDER + T.BL + T.H * WIDTH + T.BR + ANSI.RESET)

def mid_bar():
    ruler(T.LT, T.RT)

def row(text, color=None, align="left"):
    inner = WIDTH
    color = color or T.MUTED
    if align == "center":
        content = text.center(inner)
    elif align == "right":
        content = text.rjust(inner)
    else:
        content = text.ljust(inner)
    print(T.BORDER + T.V + color + content + ANSI.RESET + T.BORDER + T.V + ANSI.RESET)

def blank_row():
    row("")

def banner(title: str, icon: str = "") -> None:
    top_bar()
    row(f"{icon}{title}", T.TITLE, "center")
    bot_bar()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  INPUT HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def ask(prompt: str, lo: int = 0) -> int:
    """Ask for an integer. Returns -1 as cancel signal."""
    while True:
        try:
            val: int = int(input(T.PROMPT + f"  {T.ICO_ARR}{prompt} " + ANSI.RESET))
        except (ValueError, TypeError):
            print(T.WARN + f"  {T.ICO_ERR}Enter a whole number." + ANSI.RESET)
            continue
        if val == -1:
            return -1
        if val < lo:
            print(T.WARN + f"  {T.ICO_WARN}Minimum allowed value is {lo}." + ANSI.RESET)
            continue
        return val

def pause(msg="Press Enter to continue..."):
    input(T.LABEL + f"\n  {T.ICO_CLK}{msg}" + ANSI.RESET)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA MODEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PCB:
    """Process Control Block — holds all scheduling data for one process."""
    __slots__ = ("name","at","bt","prio","rem","ct")

    def __init__(self, name, at, bt, prio=0):
        self.name  = name
        self.at    = at       # arrival time
        self.bt    = bt       # burst time
        self.prio  = prio     # priority value
        self.rem   = bt       # remaining burst
        self.ct    = 0        # completion time (filled by scheduler)

    # ── computed metrics ──────────────────────────────────────────────
    @property
    def tat(self):   return self.ct - self.at
    @property
    def wt(self):    return self.tat - self.bt

    def snapshot(self):
        """Return a deep copy."""
        p = PCB(self.name, self.at, self.bt, self.prio)
        p.rem = self.rem
        p.ct  = self.ct
        return p

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GANTT SEQUENCE  (list of (label, start, end))
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GanttSeq:
    def __init__(self):
        self._seq = []

    def add(self, label, start, end):
        if self._seq and self._seq[-1][0] == label:
            self._seq[-1] = (label, self._seq[-1][1], end)
        else:
            self._seq.append((label, start, end))

    def idle(self, start, end):
        self.add("IDLE", start, end)

    @property
    def data(self):
        return list(self._seq)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COLOR MAP FOR GANTT CHART
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_CHART_COLS = [
    "#74C7EC","#89DCEB","#94E2D5","#A6E3A1","#B9F8CA",
    "#F9E2AF","#FAB387","#EBA0AC","#CBA6F7","#F38BA8",
    "#89B4FA","#B4BEFE",
]

def build_color_map(procs: list) -> dict:
    m = {p.name: _CHART_COLS[i % len(_CHART_COLS)] for i, p in enumerate(procs)}
    m["IDLE"] = "#585B70"
    return m

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PRIORITY UTILITIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def prio_sort_key(proc: "PCB", mode: int) -> int:
    return proc.prio if mode == 1 else -proc.prio

def is_more_urgent(new_prio, cur_prio, mode):
    return new_prio < cur_prio if mode == 1 else new_prio > cur_prio

def prio_rule_text(mode):
    return (
        "Smallest value  =  Highest priority"
        if mode == 1
        else "Largest value  =  Highest priority"
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SCHEDULING ALGORITHMS
#  Each returns a GanttSeq and mutates pcb.ct on the working copies.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _advance_idle(seq: GanttSeq, now: int, jobs: list, key) -> int:
    """Jump clock to next arrival, inserting an IDLE block. Returns new time."""
    nxt: int = min(key(p) for p in jobs)
    seq.idle(now, nxt)
    return nxt


def algo_fcfs(jobs: list) -> GanttSeq:
    jobs.sort(key=lambda p: (p.at, p.name))
    seq = GanttSeq()
    now: int = 0
    for job in jobs:
        if now < job.at:
            seq.idle(now, job.at)
            now = job.at
        seq.add(job.name, now, now + job.bt)
        now += job.bt
        job.ct = now
    return seq


def algo_sjf(jobs: list) -> GanttSeq:
    jobs.sort(key=lambda p: (p.at, p.name))
    seq  = GanttSeq()
    now: int = 0
    done: set = set()
    while len(done) < len(jobs):
        avail = [p for p in jobs if p.at <= now and p.name not in done]
        if not avail:
            now = _advance_idle(seq, now, [p for p in jobs if p.name not in done],
                                key=lambda p: p.at)
            continue
        pick = min(avail, key=lambda p: (p.bt, p.at, p.name))
        seq.add(pick.name, now, now + pick.bt)
        now += pick.bt
        pick.ct = now
        done.add(pick.name)
    return seq


def algo_srt(jobs: list) -> GanttSeq:
    jobs.sort(key=lambda p: (p.at, p.name))
    seq = GanttSeq()
    now: int = 0
    while any(p.rem > 0 for p in jobs):
        avail = [p for p in jobs if p.at <= now and p.rem > 0]
        if not avail:
            now = _advance_idle(seq, now, [p for p in jobs if p.rem > 0],
                                key=lambda p: p.at)
            continue
        pick = min(avail, key=lambda p: (p.rem, p.at, p.name))
        seq.add(pick.name, now, now + 1)
        now += 1
        pick.rem -= 1
        if pick.rem == 0:
            pick.ct = now
    return seq


def algo_rr(jobs: list, quantum: int) -> GanttSeq:
    jobs.sort(key=lambda p: (p.at, p.name))
    seq      = GanttSeq()
    now: int = 0
    idx: int = 0
    queue: deque = deque()
    while queue or idx < len(jobs):
        while idx < len(jobs) and jobs[idx].at <= now:
            queue.append(jobs[idx])
            idx += 1
        if not queue:
            seq.idle(now, jobs[idx].at)
            now = jobs[idx].at
            continue
        job      = queue.popleft()
        run: int = min(quantum, job.rem)
        seq.add(job.name, now, now + run)
        now     += run
        job.rem -= run
        while idx < len(jobs) and jobs[idx].at <= now:
            queue.append(jobs[idx])
            idx += 1
        if job.rem > 0:
            queue.append(job)
        else:
            job.ct = now
    return seq


def algo_priority(jobs: list, preemptive: bool, mode: int) -> GanttSeq:
    jobs.sort(key=lambda p: (p.at, p.name))
    seq      = GanttSeq()
    now: int = 0
    while any(p.rem > 0 for p in jobs):
        avail = [p for p in jobs if p.at <= now and p.rem > 0]
        if not avail:
            now = _advance_idle(seq, now, [p for p in jobs if p.rem > 0],
                                key=lambda p: p.at)
            continue
        pick = min(avail, key=lambda p: (prio_sort_key(p, mode), p.at, p.name))
        if not preemptive:
            seq.add(pick.name, now, now + pick.rem)
            now      += pick.rem
            pick.rem  = 0
            pick.ct   = now
        else:
            seq.add(pick.name, now, now + 1)
            now      += 1
            pick.rem -= 1
            if pick.rem == 0:
                pick.ct = now
    return seq


def algo_prio_rr(jobs: list, quantum: int, mode: int) -> GanttSeq:
    jobs.sort(key=lambda p: (p.at, p.name))
    seq           = GanttSeq()
    now: int      = 0
    idx: int      = 0
    done_cnt: int = 0
    buckets: dict = {}

    def load_arrived() -> None:
        nonlocal idx
        while idx < len(jobs) and jobs[idx].at <= now:
            pr: int = jobs[idx].prio
            if pr not in buckets:
                buckets[pr] = deque()
            buckets[pr].append(jobs[idx])
            idx += 1

    while done_cnt < len(jobs):
        load_arrived()
        live = [pr for pr, q in buckets.items() if q]
        if not live:
            if idx < len(jobs):
                seq.idle(now, jobs[idx].at)
                now = jobs[idx].at
                load_arrived()
            continue

        best: int    = min(live) if mode == 1 else max(live)
        job           = buckets[best].popleft()
        tick: int     = 0
        bumped: bool  = False

        while tick < quantum and job.rem > 0:
            seq.add(job.name, now, now + 1)
            now      += 1
            job.rem  -= 1
            tick     += 1
            load_arrived()
            new_live = [pr for pr, q in buckets.items() if q]
            if new_live:
                top: int = min(new_live) if mode == 1 else max(new_live)
                if is_more_urgent(top, best, mode):
                    bumped = True
                    break

        if job.rem > 0:
            if best not in buckets:
                buckets[best] = deque()
            if bumped:
                buckets[best].appendleft(job)
            else:
                buckets[best].append(job)
        else:
            job.ct    = now
            done_cnt += 1

    return seq

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROCESS INPUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def input_processes():
    banner("  INPUT PROCESSES  ", T.ICO_PROC)
    blank_row()
    row(f"  {T.ICO_WARN}Enter  -1  at any prompt to restart from scratch.", T.MUTED)
    blank_row()
    bot_bar()

    n: int = ask("How many processes?  (min 3)", lo=3)
    if n == -1:
        return None

    process_list: list = []
    for i in range(n):
        print()
        top_bar()
        row(f"  {T.ICO_CPU}Process  P{i+1}", T.LABEL)
        mid_bar()

        at: int = ask("Arrival  Time           :", lo=0)
        if at == -1:
            return None

        bt: int = ask("Burst    Time           :", lo=1)
        if bt == -1:
            return None

        pv: int = ask("Priority Value  (0=N/A) :", lo=0)
        if pv == -1:
            return None

        bot_bar()
        process_list.append(PCB(f"P{i+1}", at, bt, pv))

    return process_list


def ask_prio_mode():
    print()
    banner("  PRIORITY RULE  ", T.ICO_STAR)
    blank_row()
    row(f"  {T.ICO_ARR}1.  Smallest priority value  →  runs first", T.VALUE)
    row(f"  {T.ICO_ARR}2.  Largest  priority value  →  runs first", T.VALUE)
    blank_row()
    bot_bar()
    while True:
        m = ask("Select rule (1 or 2):", lo=1)
        if m in (1, 2): return m
        print(T.WARN + f"  {T.ICO_ERR}Choose 1 or 2." + ANSI.RESET)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RESULTS TABLE  ── different layout: colored column headers + row zebra
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_COL_W  = 9
_COLS   = ["PID","AT","BT","PV","WT","TAT","CT"]

def _fmt_row(vals, color):
    cells = "".join(str(v).ljust(_COL_W) for v in vals)
    row(f"  {cells}", color)

def print_table(procs: list) -> None:
    print()
    banner("  RESULTS TABLE  ", T.ICO_STAR)
    blank_row()

    # header
    _fmt_row(_COLS, T.LABEL)
    mid_bar()

    total_wt = total_tat = 0
    for i, p in enumerate(procs):
        row_color = T.VALUE if i % 2 == 0 else T.MUTED
        _fmt_row([p.name, p.at, p.bt, p.prio, p.wt, p.tat, p.ct], row_color)
        total_wt  += p.wt
        total_tat += p.tat

    mid_bar()
    count = len(procs)

    # averages
    blank_row()
    row(f"  {T.ICO_OK}Average Waiting Time      :  {total_wt/count:.2f}", T.TITLE)
    row(f"  {T.ICO_OK}Average Turnaround Time   :  {total_tat/count:.2f}", T.TITLE)
    blank_row()
    bot_bar()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GANTT CHART  ── different style: gradient label, tight layout, legend
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def draw_gantt(seq: GanttSeq, title: str, cmap: dict) -> None:
    blocks = seq.data
    fig, ax = plt.subplots(figsize=(max(10, len(blocks)), 2.8))
    fig.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#181825")

    ticks: set = set()
    seen: dict = {}

    for label, s, e in blocks:
        c: str = cmap.get(label, "#888")
        ax.barh(0, e - s, left=s, color=c, edgecolor="#CDD6F4",
                linewidth=0.8, height=0.55)
        ax.text((s + e) / 2, 0, label, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="#1E1E2E")
        ticks.update([s, e])
        if label not in seen:
            seen[label] = patch_module.Patch(color=c, label=label)

    sorted_ticks = sorted(ticks)
    ax.set_xticks(sorted_ticks)
    ax.set_xlim(sorted_ticks[0], sorted_ticks[-1])
    ax.tick_params(colors="#CDD6F4", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#45475A")
    ax.set_yticks([])
    ax.set_title(f"⚙  Gantt Chart  —  {title}",
                 color="#CDD6F4", fontsize=11, fontweight="bold", pad=10)
    ax.grid(axis="x", color="#45475A", linestyle="--", linewidth=0.6)
    ax.legend(handles=list(seen.values()), loc="upper right",
              fontsize=8, framealpha=0.3,
              labelcolor="#CDD6F4", facecolor="#313244")
    plt.tight_layout()
    plt.show()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ALGORITHM MENU
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_MENU = [
    (1, "FCFS                       First Come First Served"),
    (2, "SJF                        Shortest Job First (Non-Preemptive)"),
    (3, "SRT                        Shortest Remaining Time (Preemptive)"),
    (4, "RR                         Round Robin"),
    (5, "PRIORITY-NP                Priority  —  Non-Preemptive"),
    (6, "PRIORITY-P                 Priority  —  Preemptive"),
    (7, "PRIORITY + RR              Priority with Round Robin"),
    (0, "EXIT                       Quit the simulator"),
]

def show_menu():
    print()
    banner("  ALGORITHM MENU  ", T.ICO_CPU)
    blank_row()
    for num, label in _MENU:
        c = T.WARN if num == 0 else T.VALUE
        row(f"  [{num}]  {label}", c)
    blank_row()
    bot_bar()


def run_selected(choice, jobs):
    """Route choice → algorithm. Returns (GanttSeq, label) or None."""
    if choice == 1:
        return algo_fcfs(jobs), "FCFS"

    if choice == 2:
        return algo_sjf(jobs), "SJF (Non-Preemptive)"

    if choice == 3:
        return algo_srt(jobs), "SRT (Preemptive)"

    if choice == 4:
        q = ask("Time Quantum:", lo=1)
        if q == -1: return None
        return algo_rr(jobs, q), f"Round Robin  |  Q = {q}"

    if choice in (5, 6):
        mode  = ask_prio_mode()
        label = prio_rule_text(mode)
        kind  = "Non-Preemptive" if choice == 5 else "Preemptive"
        seq   = algo_priority(jobs, preemptive=(choice == 6), mode=mode)
        return seq, f"Priority ({kind})  |  {label}"

    if choice == 7:
        mode  = ask_prio_mode()
        label = prio_rule_text(mode)
        q     = ask("Time Quantum:", lo=1)
        if q == -1: return None
        seq   = algo_prio_rr(jobs, q, mode)
        return seq, f"Priority + RR  |  {label}  |  Q = {q}"

    return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    while True:
        clr()
        # ── splash ──────────────────────────────────────────────────
        top_bar()
        blank_row()
        row("C P U   S C H E D U L I N G   S I M U L A T O R", T.TITLE, "center")
        blank_row()
        row("FCFS  •  SJF  •  SRT  •  RR  •  Priority  •  Priority+RR",
            T.LABEL, "center")
        blank_row()
        bot_bar()

        # ── collect process data ────────────────────────────────────
        base = input_processes()
        if base is None:
            continue

        cmap = build_color_map(base)

        # ── inner algorithm loop ────────────────────────────────────
        while True:
            show_menu()
            choice = ask("Select algorithm number:")

            if choice == 0:
                clr()
                banner("  GOODBYE  ", T.ICO_OK)
                return

            working = [p.snapshot() for p in base]
            result  = run_selected(choice, working)

            if result is None:
                continue

            gantt_seq, display_name = result

            print_table(working)

            pause("Press Enter to view the Gantt chart →")

            draw_gantt(gantt_seq, display_name, cmap)

            # ── after-run prompt ────────────────────────────────────
            print()
            banner("  WHAT NEXT?  ", T.ICO_STAR)
            blank_row()
            row(f"  {T.ICO_ARR}1.  Run a different algorithm on the same processes", T.VALUE)
            row(f"  {T.ICO_ARR}2.  Enter a new set of processes", T.VALUE)
            row(f"  {T.ICO_ARR}3.  Exit the simulator", T.WARN)
            blank_row()
            bot_bar()

            again = ask("Your choice:")

            if again == 1:
                continue
            elif again == 2:
                break
            else:
                clr()
                banner("  GOODBYE  ", T.ICO_OK)
                return


if __name__ == "__main__":
    main()
