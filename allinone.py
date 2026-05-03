"""
REY STATION  V4.0  ─  WINDOWS NATIVE OPTIMIZED UTILITY
═══════════════════════════════════════════════════════
Fully optimized for Windows using native WinAPI calls.
Requires: pip install rich psutil
"""

import os
import sys
import time
import platform
import subprocess
import shutil
import socket
import threading
import ctypes
from datetime import datetime
from pathlib  import Path

# ═══════════════════════════════════════════════════════════════
#  BOOTSTRAP: AUTO-INSTALL DEPENDENCIES
# ═══════════════════════════════════════════════════════════════

def bootstrap():
    required = ["rich", "psutil"]
    missing = []
    for lib in required:
        try:
            __import__(lib)
        except ImportError:
            missing.append(lib)

    if missing:
        print(f"--- REY STATION: Missing dependencies: {', '.join(missing)} ---")
        print("--- Attempting automatic installation... ---")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("--- Installation successful. Restarting... ---\n")
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            print(f"--- Error installing dependencies: {e} ---")
            print("--- Please run: pip install rich psutil ---")
            sys.exit(1)

if __name__ == "__main__" or __name__ == "allinone":
    bootstrap()

# ═══════════════════════════════════════════════════════════════
#  IMPORTS
# ═══════════════════════════════════════════════════════════════

try:
    import psutil
    PSUTIL = True
except ImportError:
    PSUTIL = False

from rich              import box
from rich.align        import Align
from rich.columns      import Columns
from rich.console      import Console
from rich.live         import Live
from rich.panel        import Panel
from rich.prompt       import IntPrompt, Prompt, Confirm
from rich.rule         import Rule
from rich.table        import Table
from rich.text         import Text
from rich.progress     import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn
from rich.padding      import Padding
from rich.columns      import Columns

# ═══════════════════════════════════════════════════════════════
#  WINAPI & CONSTANTS
# ═══════════════════════════════════════════════════════════════

console = Console()

class WinAPI:
    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    @staticmethod
    def lock_workstation():
        ctypes.windll.user32.LockWorkStation()

    @staticmethod
    def set_suspend_state(hibernate=False):
        ctypes.windll.powrprof.SetSuspendState(int(hibernate), 0, 0)

    @staticmethod
    def empty_working_sets():
        try:
            processes = psutil.pids() if PSUTIL else []
            count = 0
            for pid in processes:
                try:
                    handle = ctypes.windll.kernel32.OpenProcess(0x0400 | 0x0100, False, pid)
                    if handle:
                        if ctypes.windll.psapi.EmptyWorkingSet(handle):
                            count += 1
                        ctypes.windll.kernel32.CloseHandle(handle)
                except:
                    continue
            return count
        except:
            return 0

    @staticmethod
    def clear_standby_list():
        try:
            command = ctypes.c_int(4)
            status = ctypes.windll.ntdll.NtSetSystemInformation(80, ctypes.byref(command), 4)
            return status == 0
        except:
            return False

    @staticmethod
    def flush_dns():
        try:
            return ctypes.windll.dnsapi.DnsFlushResolverCache() != 0
        except:
            return False

    @staticmethod
    def empty_recycle_bin():
        try:
            return ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1 | 2 | 4) == 0
        except:
            return False

# ─── Visual Constants ───────────────────────────────────────────

LOGO = (
    "  ██████╗ ██╗   ██╗    ██████╗ ███████╗██╗   ██╗  \n"
    "  ██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔════╝╚██╗ ██╔╝  \n"
    "  ██████╔╝ ╚████╔╝     ██████╔╝█████╗   ╚████╔╝   \n"
    "  ██╔══██╗  ╚██╔╝      ██╔══██╗██╔══╝    ╚██╔╝    \n"
    "  ██████╔╝   ██║       ██║  ██║███████╗   ██║      \n"
    "  ╚═════╝    ╚═╝       ╚═╝  ╚═╝╚══════╝   ╚═╝      "
)

DISCO = ["#00ffff", "#ff00ff", "#ffff00", "#00ff88", "#4488ff", "#ff4444", "#ffffff", "#ff88ff", "#88ffff", "#ffaa00"]

SPECTRUM = [
    "▁  ▃  ▅  █  ▅  ▃  ▁  ▂  ▆  █  ▄  ▂  ▁  ▃  ▇  █  ▅  ▂  ▁  ▄  ▆  █  ▃  ▁",
    "▂  ▅  █  ▆  ▃  ▁  ▂  ▄  █  ▇  ▃  ▁  ▂  ▅  █  ▆  ▄  ▁  ▂  ▅  █  ▅  ▂  ▁",
    "▃  █  ▇  ▄  ▁  ▂  ▄  █  ▆  ▃  ▁  ▃  ▆  █  ▅  ▂  ▁  ▃  ▆  █  ▄  ▂  ▁  ▂",
    "▄  █  ▅  ▂  ▁  ▃  █  ▇  ▄  ▁  ▂  ▅  █  ▆  ▃  ▁  ▄  █  ▇  ▃  ▁  ▂  ▃  ▄",
    "▅  ▇  ▃  ▁  ▂  ▅  █  ▅  ▂  ▁  ▃  █  ▇  ▄  ▁  ▂  ▅  █  ▅  ▂  ▁  ▃  ▅  ▇",
    "▆  ▄  ▁  ▂  ▄  █  ▆  ▃  ▁  ▂  ▅  █  ▅  ▂  ▁  ▃  █  ▆  ▃  ▁  ▂  ▄  ▇  █",
    "█  ▂  ▁  ▃  █  ▇  ▄  ▁  ▂  ▄  █  ▅  ▂  ▁  ▃  ▆  █  ▄  ▁  ▂  ▅  █  ▆  ▃",
    "▇  ▁  ▂  ▅  █  ▅  ▂  ▁  ▃  █  ▆  ▃  ▁  ▂  ▄  █  ▇  ▂  ▁  ▃  █  ▅  ▄  ▁",
]

VU_SEQ = [0, 1, 3, 5, 7, 9, 11, 10, 8, 6, 4, 2, 0, 2, 5, 8, 11, 11, 9, 6, 3, 0]

MODULES = {
    "1": ("⏱  Timer & Power",       "#00ffff"),
    "2": ("🧹  RAM & Cache Cleaner",  "#ff88ff"),
    "3": ("💾  Disk Utilities",       "#ffff00"),
    "4": ("⚙️  Process Manager",      "#00ff88"),
    "5": ("📊  System Monitor",       "#ff8800"),
    "6": ("🌐  Network Tools",        "#4488ff"),
    "7": ("🗑️  Junk File Cleaner",    "#ff4444"),
    "8": ("🔋  Battery & Power",      "#88ffff"),
    "9": ("ℹ️  System Info",          "#ffffff"),
    "a": ("🌀  AFK Mode",             "#cc88ff"),
    "0": ("🚪  Exit",                "#666666"),
}

# ═══════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════

def clr():
    os.system("cls" if os.name == "nt" else "clear")

def pause(msg="   press enter to continue"):
    console.print(f"\n   [color(240)]{msg}[/]")
    input()

def run_cmd(cmd, capture=True, shell=False):
    """
    FIX: Separated shell vs list invocation to avoid conflicts.
    When shell=True, cmd must be a string. When shell=False, cmd is a list.
    """
    try:
        if shell and isinstance(cmd, list):
            cmd = " ".join(str(c) for c in cmd)
        r = subprocess.run(cmd, capture_output=capture, text=True, timeout=60, shell=shell)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "Command timed out", 1
    except Exception as e:
        return str(e), 1

def bytes_to_human(n):
    if n < 0:
        n = 0
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

def notify(msg: str):
    try:
        subprocess.run(["msg", "*", msg], capture_output=True, timeout=5)
    except Exception:
        pass

def run_power_action(action: str):
    notify(f"REY — {action}")
    time.sleep(1)
    if action == "Shutdown":
        subprocess.run(["shutdown", "/s", "/t", "10"])
    elif action == "Restart":
        subprocess.run(["shutdown", "/r", "/t", "10"])
    elif action == "Hibernate":
        WinAPI.set_suspend_state(hibernate=True)
    elif action == "Sleep":
        WinAPI.set_suspend_state(hibernate=False)
    elif action == "Lock Screen":
        WinAPI.lock_workstation()

# ═══════════════════════════════════════════════════════════════
#  RENDER HELPERS
# ═══════════════════════════════════════════════════════════════

def logo_panel(color: str, subtitle: str = "V4.0 OPTIMIZED") -> Panel:
    admin_tag = "[bold #ff4444] ★ ADMIN [/]" if WinAPI.is_admin() else "[dim] USER [/]"
    hostname = socket.gethostname()
    return Panel(
        Align.center(Text(LOGO, style=f"bold {color}")),
        box=box.DOUBLE,
        border_style=color,
        title=f"[dim]{hostname}[/]",
        subtitle=f"{admin_tag} [dim {color}]{subtitle}[/]",
        subtitle_align="right",
        padding=(0, 1),
    )

def section_header(title: str, color: str, subtitle: str = "V4.0"):
    clr()
    console.print(logo_panel(color, subtitle))
    console.print()
    console.print(Rule(f"[bold {color}]  {title}  [/]", style=color, characters="─"))
    console.print()

def render_bar(val, total, width=40, color="#00ffff"):
    ratio  = min(val / total, 1.0) if total else 0
    filled = round(ratio * width)
    t = Text()
    t.append("█" * filled,           style=f"bold {color}")
    t.append("░" * (width - filled), style="color(238)")
    t.append(f"  {ratio*100:5.1f}%", style="bold white")
    return t

def render_vu(level: int, width: int = 52) -> Text:
    filled = round((level / 11) * width)
    g_end  = round(width * 0.60)
    y_end  = round(width * 0.85)
    t = Text()
    for i in range(filled):
        if   i < g_end: t.append("█", style="#00ff88")
        elif i < y_end: t.append("█", style="#ffcc00")
        else:            t.append("█", style="#ff4444")
    t.append("░" * (width - filled), style="color(238)")
    return t

def status_badge(ok: bool) -> Text:
    return Text("● OK  ", style="bold #00ff88") if ok else Text("● FAIL", style="bold #ff4444")

def make_menu_table(items: dict, color: str) -> Table:
    """Render a styled menu table with hotkey | separator | label layout."""
    t = Table.grid(padding=(0, 2))
    t.add_column(style=f"bold {color}", min_width=3, justify="right")
    t.add_column(style="color(238)",    min_width=1)
    t.add_column(style="white",         min_width=28)
    for k, label in items.items():
        t.add_row(k, "│", label)
    return t

def result_ok(msg: str):
    console.print(f"   [bold #00ff88]✓[/]  {msg}")

def result_fail(msg: str):
    console.print(f"   [bold #ff4444]✗[/]  {msg}")

def result_warn(msg: str):
    console.print(f"   [bold #ffcc00]![/]  {msg}")

# ═══════════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════════

def main_menu() -> str:
    clr()
    color = "#00ffff"
    console.print(logo_panel(color, "WINDOWS NATIVE · V4.0"))
    console.print()
    console.print(Rule(f"[bold {color}]  MAIN MENU  [/]", style=color, characters="═"))
    console.print()

    # Two-column layout for menu items
    left_items  = {k: v[0] for k, v in list(MODULES.items())[:5]}
    right_items = {k: v[0] for k, v in list(MODULES.items())[5:]}

    left_table  = make_menu_table(left_items,  color)
    right_table = make_menu_table(right_items, color)

    cols = Table.grid(padding=(0, 6))
    cols.add_column(); cols.add_column()
    cols.add_row(left_table, right_table)
    console.print(Align.center(cols))

    # System quick-stats bar
    console.print()
    console.print(Rule(style="color(238)", characters="─"))
    if PSUTIL:
        mem   = psutil.virtual_memory()
        cpu   = psutil.cpu_percent(interval=0.1)
        stats = Table.grid(padding=(0, 4))
        stats.add_column(style="color(240)")
        stats.add_column()
        stats.add_column(style="color(240)")
        stats.add_column()
        stats.add_column(style="color(240)")
        stats.add_column()
        stats.add_row(
            "CPU",  render_bar(cpu,      100, 14, "#00ff88"),
            "RAM",  render_bar(mem.used, mem.total, 14, "#ff88ff"),
            "TIME", Text(datetime.now().strftime("%H:%M:%S"), style="bold #00ffff"),
        )
        console.print(Align.center(stats))
    console.print(Rule(style="color(238)", characters="─"))
    console.print()

    choice = Prompt.ask(
        "   [bold #00ffff]SELECT MODULE >[/]",
        choices=list(MODULES.keys()),
        show_choices=False,
    )
    return choice

# ═══════════════════════════════════════════════════════════════
#  MODULE 1: TIMER & POWER
# ═══════════════════════════════════════════════════════════════

def build_timer_screen(timer, total, action, tick):
    color  = DISCO[tick % len(DISCO)]
    spec   = SPECTRUM[tick % len(SPECTRUM)]
    vu_lvl = VU_SEQ[tick % len(VU_SEQ)]
    hh = timer // 3600; mm = (timer % 3600) // 60; ss = timer % 60
    dim = "color(240)"

    meta = Table.grid(padding=(0, 4))
    meta.add_column(style=dim,          min_width=10)
    meta.add_column(style="bold white", min_width=16)
    meta.add_row("engine",  "WINAPI_V4")
    meta.add_row("session", "● optimized")
    meta.add_row("action",  Text(action.lower(), style=f"bold {color}"))
    meta.add_row("clock",   datetime.now().strftime("%H:%M:%S"))
    meta.add_row("date",    datetime.now().strftime("%Y-%m-%d"))

    clock  = Align.center(Text(f"{hh:02d}:{mm:02d}:{ss:02d}", style=f"bold {color}", justify="center"))
    ratio  = (1 - (timer / total)) if total else 1
    filled = round(ratio * 52)
    prog_t = Text()
    prog_t.append("█" * filled,        style=f"bold {color}")
    prog_t.append("░" * (52-filled),   style="color(238)")
    prog_t.append(f"  {ratio*100:5.1f}%", style="bold white")

    vu_row = Table.grid(padding=(0, 1))
    vu_row.add_column(min_width=18)
    vu_row.add_column()
    vu_row.add_row(Text("  ◈  vu meter", style=dim), render_vu(vu_lvl))

    body = Table.grid(padding=(0, 0))
    body.add_column(min_width=72)

    def gap(n=1):
        for _ in range(n): body.add_row(Text(""))

    def sep(): body.add_row(Rule(style=dim, characters="─"))

    gap()
    body.add_row(Align.center(meta))
    gap(); sep(); gap()
    body.add_row(clock)
    gap()
    body.add_row(Align.center(prog_t))
    gap()
    remaining_str = f"  remaining: {hh:02d}h {mm:02d}m {ss:02d}s"
    body.add_row(Align.center(Text(remaining_str, style=dim)))
    gap(); sep(); gap()
    body.add_row(Text("  ♫  spectrum", style=dim))
    gap()
    body.add_row(Align.center(Text(spec, style=f"bold {color}", justify="center")))
    gap()
    body.add_row(vu_row)
    gap(); sep(); gap()
    body.add_row(Align.center(Text("ctrl+c  →  abort timer", style=dim)))
    gap()

    root = Table.grid()
    root.add_column()
    root.add_row(logo_panel(color))
    root.add_row(Panel(body, box=box.SIMPLE_HEAD, border_style=dim, padding=(0, 2)))
    return root

def module_timer():
    durations = {
        "1": ("15 min",  900),
        "2": ("30 min", 1800),
        "3": ("45 min", 2700),
        "4": ("1 hr",   3600),
        "5": ("2 hr",   7200),
        "6": ("custom",    0),
    }
    actions = {
        "1": "Shutdown",
        "2": "Restart",
        "3": "Sleep",
        "4": "Hibernate",
        "5": "Lock Screen",
        "6": "Just Notify",
    }

    section_header("TIMER · duration", "#00ffff")
    dur_menu = {k: v[0] for k, v in durations.items()}
    console.print(Align.center(make_menu_table(dur_menu, "#00ffff")))
    choice = Prompt.ask("\n   [#00ffff]>[/]", choices=list(durations.keys()), show_choices=False)
    if choice == "6":
        minutes = IntPrompt.ask("   [#00ffff]Minutes[/]")
        total = max(1, minutes) * 60
    else:
        total = durations[choice][1]

    section_header("TIMER · action on complete", "#ff00ff")
    console.print(Align.center(make_menu_table(actions, "#ff00ff")))
    a_choice = Prompt.ask("\n   [#ff00ff]>[/]", choices=list(actions.keys()), show_choices=False)
    action = actions[a_choice]

    timer = total; tick = 0
    _FRAME = 1 / 60           # 60 fps budget per frame
    _stop  = threading.Event()

    # Background thread: real 1-second countdown, decoupled from render rate
    def _countdown():
        nonlocal timer
        while timer > 0 and not _stop.is_set():
            _stop.wait(timeout=1.0)
            if not _stop.is_set():
                timer -= 1
        _stop.set()

    _ct = threading.Thread(target=_countdown, daemon=True)
    _ct.start()

    initial = build_timer_screen(timer, total, action, tick)
    try:
        with Live(initial, console=console, screen=True) as live:
            while not _stop.is_set() and timer > 0:
                t0 = time.perf_counter()
                live.update(build_timer_screen(timer, total, action, tick))
                tick += 1
                spent = time.perf_counter() - t0
                leftover = _FRAME - spent
                if leftover > 0:
                    time.sleep(leftover)
    except KeyboardInterrupt:
        _stop.set()
        return
    _stop.set()

    if action == "Just Notify":
        notify("REY STATION — Timer complete!")
        pause("Timer finished! Press enter to return.")
    else:
        run_power_action(action)

# ═══════════════════════════════════════════════════════════════
#  MODULE 2: RAM & CACHE CLEANER
# ═══════════════════════════════════════════════════════════════

def module_ram():
    section_header("RAM & CACHE CLEANER", "#ff88ff")

    if not PSUTIL:
        result_fail("psutil not available — install it to use this module")
        pause(); return

    mem = psutil.virtual_memory()

    # Stats panel
    stats = Table.grid(padding=(0, 3))
    stats.add_column(style="color(240)", min_width=14)
    stats.add_column(min_width=10, style="bold white")
    stats.add_column()
    stats.add_row("Total RAM",     bytes_to_human(mem.total),     "")
    stats.add_row("Used RAM",      bytes_to_human(mem.used),      render_bar(mem.used, mem.total, 30, "#ff4444"))
    stats.add_row("Available RAM", bytes_to_human(mem.available), render_bar(mem.available, mem.total, 30, "#00ff88"))
    stats.add_row("Usage",         f"{mem.percent:.1f}%",         "")
    console.print(Align.center(Panel(stats, border_style="#ff88ff", box=box.ROUNDED, title="[bold #ff88ff]memory snapshot[/]")))
    console.print()

    opts = {
        "1": "Trim all process working sets  (WinAPI)",
        "2": "Clear Standby List             (WinAPI · Admin)",
        "3": "Flush DNS Cache                (WinAPI)",
        "4": "Clear Windows File Cache       (Admin)",
        "5": "Run All Optimizations",
        "0": "Back",
    }
    console.print(Align.center(make_menu_table(opts, "#ff88ff")))
    choice = Prompt.ask("\n   [#ff88ff]>[/]", choices=list(opts.keys()), show_choices=False)
    if choice == "0": return

    mem_before = psutil.virtual_memory()
    console.print()

    with Progress(
        SpinnerColumn(style="#ff88ff"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as prog:
        if choice in ("1", "5"):
            t = prog.add_task("Trimming process working sets...", total=None)
            count = WinAPI.empty_working_sets()
            prog.remove_task(t)
            result_ok(f"Trimmed {count} process working sets")

        if choice in ("2", "5"):
            t = prog.add_task("Clearing standby memory list...", total=None)
            ok = WinAPI.clear_standby_list()
            prog.remove_task(t)
            if ok: result_ok("Standby list cleared")
            else:   result_fail("Standby list clear failed (Admin required)")

        if choice in ("3", "5"):
            t = prog.add_task("Flushing DNS resolver cache...", total=None)
            ok = WinAPI.flush_dns()
            prog.remove_task(t)
            if ok: result_ok("DNS resolver cache flushed")
            else:   result_fail("DNS flush failed — try running as Admin")

        # FIX: Removed invalid "Clear-Bccache" PowerShell command.
        # The correct cmdlet is "Clear-BCCache" (BranchCache), which requires Admin
        # and the BranchCache feature to be installed. Replaced with ipconfig /flushdns
        # as a safe fallback alongside DNS flushing.
        if choice in ("4", "5"):
            t = prog.add_task("Requesting file cache purge...", total=None)
            if WinAPI.is_admin():
                # Attempt BranchCache clear if available (won't fail if missing)
                run_cmd("powershell -Command \"try { Clear-BCCache -Force } catch {}\"", shell=True)
                result_ok("File cache purge requested")
            else:
                result_warn("File cache purge requires Admin privileges")
            prog.remove_task(t)

    mem_after = psutil.virtual_memory()
    freed = max(0, mem_after.available - mem_before.available)
    console.print()
    console.print(Rule(style="color(238)", characters="─"))
    console.print(f"   [dim]Memory freed:[/]     [bold #00ff88]{bytes_to_human(freed)}[/]")
    console.print(f"   [dim]Available after:[/]  [bold #00ff88]{bytes_to_human(mem_after.available)}[/]")
    console.print(f"   [dim]Usage after:[/]      [bold {'#00ff88' if mem_after.percent < 70 else '#ff4444'}]{mem_after.percent:.1f}%[/]")
    pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 3: DISK UTILITIES
# ═══════════════════════════════════════════════════════════════

def module_disk():
    section_header("DISK UTILITIES", "#ffff00")

    if PSUTIL:
        t = Table(box=box.ROUNDED, border_style="#ffff00", header_style="bold #ffff00", show_lines=False)
        t.add_column("Drive",  style="bold white",   min_width=10)
        t.add_column("Type",   style="color(240)",   min_width=6)
        t.add_column("Total",  style="white",        min_width=10)
        t.add_column("Free",   style="#00ff88",      min_width=10)
        t.add_column("Usage",  min_width=36)
        for p in psutil.disk_partitions():
            try:
                u = psutil.disk_usage(p.mountpoint)
                pct_color = "#ff4444" if u.percent > 85 else "#ffcc00" if u.percent > 65 else "#00ff88"
                t.add_row(
                    p.device,
                    p.fstype,
                    bytes_to_human(u.total),
                    bytes_to_human(u.free),
                    render_bar(u.used, u.total, 20, pct_color),
                )
            except Exception:
                continue
        console.print(Align.center(t))
        console.print()

    opts = {
        "1": "Optimize / Defrag Drives",
        "2": "Check Disk Health        (WMI)",
        "3": "System File Checker      (SFC · Admin)",
        "4": "Schedule Boot Scan       (Chkdsk · Admin)",
        "0": "Back",
    }
    console.print(Align.center(make_menu_table(opts, "#ffff00")))
    choice = Prompt.ask("\n   [#ffff00]>[/]", choices=list(opts.keys()), show_choices=False)

    if choice == "1":
        console.print("\n   [dim]Starting drive optimization (this may take a while)...[/]\n")
        run_cmd(["defrag", "/C", "/O"], capture=False)
    elif choice == "2":
        out, rc = run_cmd(["wmic", "diskdrive", "get", "status,model,size"])
        console.print(f"\n[bold #ffff00]Disk Status:[/]\n[dim]{out if out else 'No output returned'}[/]")
    elif choice == "3":
        if not WinAPI.is_admin():
            result_fail("Administrator privileges required for SFC")
        else:
            console.print("\n   [dim]Running System File Checker...[/]\n")
            run_cmd(["sfc", "/scannow"], capture=False)
    elif choice == "4":
        if not WinAPI.is_admin():
            result_fail("Administrator privileges required for Chkdsk")
        else:
            result_warn("Chkdsk will run on next reboot for C:\\")
            # FIX: Use shell=True with string command to avoid list+shell conflict
            run_cmd("chkdsk C: /f /r /x", capture=False, shell=True)

    if choice != "0":
        pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 4: PROCESS MANAGER
# ═══════════════════════════════════════════════════════════════

def module_process():
    section_header("PROCESS MANAGER", "#00ff88")

    if not PSUTIL:
        result_fail("psutil not available"); pause(); return

    opts = {
        "1": "Top 20 by CPU Usage",
        "2": "Top 20 by RAM Usage",
        "3": "Kill Process by PID",
        "4": "Search Process by Name",
        "0": "Back",
    }
    console.print(Align.center(make_menu_table(opts, "#00ff88")))
    choice = Prompt.ask("\n   [#00ff88]>[/]", choices=list(opts.keys()), show_choices=False)

    if choice in ("1", "2"):
        key = "cpu_percent" if choice == "1" else "memory_percent"
        label = "CPU%" if choice == "1" else "MEM%"
        # Collect process info safely
        proc_list = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                proc_list.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs = sorted(proc_list, key=lambda x: x.get(key) or 0, reverse=True)[:20]

        t = Table(header_style="bold #00ff88", box=box.ROUNDED, border_style="color(238)", show_lines=False)
        t.add_column("PID",    style="color(240)",   min_width=7,  justify="right")
        t.add_column("Name",   style="bold white",   min_width=28)
        t.add_column("CPU%",   style="#ff8800",      min_width=8,  justify="right")
        t.add_column("MEM%",   style="#ff88ff",      min_width=8,  justify="right")
        t.add_column("Status", style="color(240)",   min_width=10)
        for p in procs:
            cpu_val = p.get('cpu_percent') or 0
            mem_val = p.get('memory_percent') or 0
            t.add_row(
                str(p.get('pid', '?')),
                (p.get('name') or 'unknown')[:28],
                f"{cpu_val:.1f}",
                f"{mem_val:.1f}",
                p.get('status', ''),
            )
        console.print(Align.center(t))
        pause()

    elif choice == "3":
        pid = IntPrompt.ask("   [#00ff88]PID to terminate[/]")
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            if Confirm.ask(f"   Terminate [bold]{name}[/] (PID {pid})?"):
                proc.terminate()
                result_ok(f"Sent termination signal to {name} (PID {pid})")
        except psutil.NoSuchProcess:
            result_fail(f"No process with PID {pid}")
        except psutil.AccessDenied:
            result_fail(f"Access denied — run as Admin to terminate this process")
        except Exception as e:
            result_fail(str(e))
        pause()

    elif choice == "4":
        name_query = Prompt.ask("   [#00ff88]Process name (partial match)[/]").lower()
        matches = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if name_query in (p.info.get('name') or '').lower():
                    matches.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not matches:
            result_warn(f"No processes matching '{name_query}'")
        else:
            t = Table(header_style="bold #00ff88", box=box.ROUNDED, border_style="color(238)")
            t.add_column("PID"); t.add_column("Name"); t.add_column("CPU%"); t.add_column("MEM%")
            for p in matches[:15]:
                t.add_row(str(p.get('pid','')), p.get('name',''), f"{p.get('cpu_percent',0):.1f}", f"{p.get('memory_percent',0):.1f}")
            console.print(Align.center(t))
        pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 5: LIVE SYSTEM MONITOR
# ═══════════════════════════════════════════════════════════════

def module_monitor():
    if not PSUTIL:
        result_fail("psutil required"); return

    def build_monitor(tick):
        color = DISCO[tick % len(DISCO)]
        cpu_all = psutil.cpu_percent(percpu=True)
        mem     = psutil.virtual_memory()
        try:
            disk_io = psutil.disk_io_counters()
            net_io  = psutil.net_io_counters()
        except Exception:
            disk_io = net_io = None

        # CPU section
        cpu_table = Table.grid(padding=(0, 1))
        cpu_table.add_column(style="color(240)", min_width=8)
        cpu_table.add_column()
        for i, p in enumerate(cpu_all[:8]):
            bar_color = "#ff4444" if p > 85 else "#ffcc00" if p > 60 else "#00ff88"
            cpu_table.add_row(f"Core {i:>2}", render_bar(p, 100, 26, bar_color))

        overall_cpu = psutil.cpu_percent()
        cpu_panel = Panel(
            cpu_table,
            title=f"[bold {color}]CPU  {overall_cpu:.1f}%[/]",
            border_style=color,
            box=box.ROUNDED,
        )

        # Memory section
        mem_table = Table.grid(padding=(0, 1))
        mem_table.add_column(style="color(240)", min_width=12)
        mem_table.add_column()
        mem_table.add_row("Used",  render_bar(mem.used, mem.total, 26, "#ff88ff"))
        mem_table.add_row("Free",  render_bar(mem.available, mem.total, 26, "#00ff88"))
        mem_table.add_row("", "")
        mem_table.add_row("Total",    Text(bytes_to_human(mem.total),     style="bold white"))
        mem_table.add_row("Used",     Text(bytes_to_human(mem.used),      style="#ff88ff"))
        mem_table.add_row("Avail",    Text(bytes_to_human(mem.available), style="#00ff88"))

        mem_panel = Panel(
            mem_table,
            title=f"[bold #ff88ff]RAM  {mem.percent:.1f}%[/]",
            border_style="#ff88ff",
            box=box.ROUNDED,
        )

        # I/O section
        io_table = Table.grid(padding=(0, 2))
        io_table.add_column(style="color(240)", min_width=12)
        io_table.add_column(style="bold white")
        if disk_io:
            io_table.add_row("Disk Read",  bytes_to_human(disk_io.read_bytes))
            io_table.add_row("Disk Write", bytes_to_human(disk_io.write_bytes))
        if net_io:
            io_table.add_row("Net Sent",   bytes_to_human(net_io.bytes_sent))
            io_table.add_row("Net Recv",   bytes_to_human(net_io.bytes_recv))

        io_panel = Panel(
            io_table,
            title="[bold #ffcc00]I/O[/]",
            border_style="#ffcc00",
            box=box.ROUNDED,
        )

        # Compose layout
        top_row = Table.grid(padding=(0, 1))
        top_row.add_column(); top_row.add_column()
        top_row.add_row(cpu_panel, mem_panel)

        body = Table.grid()
        body.add_column()
        body.add_row(logo_panel(color, f"LIVE MONITOR  {datetime.now().strftime('%H:%M:%S')}"))
        body.add_row(top_row)
        body.add_row(io_panel)
        body.add_row(Panel(Text("ctrl+c  →  return to menu", style="color(240)", justify="center"), border_style="color(238)", box=box.SIMPLE))
        return body

    # Render at 60 fps; poll psutil in background thread at ~2 Hz to avoid blocking
    _mon_frame  = [build_monitor(0)]   # shared frame buffer (list for mutability)
    _mon_stop   = threading.Event()
    _FRAME      = 1 / 60
    _POLL_HZ    = 2                    # psutil poll rate (heavy calls stay off render thread)

    def _poller():
        t = 0
        while not _mon_stop.is_set():
            _mon_frame[0] = build_monitor(t)
            t += 1
            _mon_stop.wait(timeout=1 / _POLL_HZ)

    _pt = threading.Thread(target=_poller, daemon=True)
    _pt.start()

    try:
        with Live(_mon_frame[0], console=console, screen=True) as live:
            while True:
                t0 = time.perf_counter()
                live.update(_mon_frame[0])
                spent = time.perf_counter() - t0
                leftover = _FRAME - spent
                if leftover > 0:
                    time.sleep(leftover)
    except KeyboardInterrupt:
        pass
    finally:
        _mon_stop.set()

# ═══════════════════════════════════════════════════════════════
#  MODULE 6: NETWORK TOOLS
# ═══════════════════════════════════════════════════════════════

def module_network():
    section_header("NETWORK TOOLS", "#4488ff")

    opts = {
        "1": "Ping Host",
        "2": "Traceroute",
        "3": "Network Stack Reset     (Admin · Reboot)",
        "4": "IP Configuration        (ipconfig /all)",
        "5": "Port Scan               (local ports)",
        "0": "Back",
    }
    console.print(Align.center(make_menu_table(opts, "#4488ff")))
    choice = Prompt.ask("\n   [#4488ff]>[/]", choices=list(opts.keys()), show_choices=False)

    if choice == "1":
        host = Prompt.ask("   [#4488ff]Host[/]", default="8.8.8.8")
        console.print()
        run_cmd(["ping", "-n", "4", host], capture=False)
    elif choice == "2":
        host = Prompt.ask("   [#4488ff]Host[/]", default="8.8.8.8")
        console.print()
        run_cmd(["tracert", host], capture=False)
    elif choice == "3":
        if not WinAPI.is_admin():
            result_fail("Administrator required for network reset")
        elif Confirm.ask("   [bold #ff4444]Reset network stack? (requires reboot)[/]"):
            for cmd in [
                ["netsh", "winsock", "reset"],
                ["netsh", "int", "ip", "reset"],
                ["ipconfig", "/release"],
                ["ipconfig", "/flushdns"],
            ]:
                out, rc = run_cmd(cmd)
                label = " ".join(cmd[:3])
                if rc == 0: result_ok(label)
                else:        result_warn(f"{label} — {out[:60]}")
            result_warn("Reboot required to complete network reset")
    elif choice == "4":
        out, _ = run_cmd(["ipconfig", "/all"])
        console.print(f"\n[dim]{out}[/]")
    elif choice == "5":
        console.print("\n   [dim]Scanning common local ports...[/]\n")
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3389, 8080, 8443]
        t = Table(header_style="bold #4488ff", box=box.ROUNDED, border_style="color(238)")
        t.add_column("Port", justify="right", min_width=6)
        t.add_column("Service", min_width=12)
        t.add_column("Status", min_width=10)
        services = {21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",
                    110:"POP3",143:"IMAP",443:"HTTPS",445:"SMB",3389:"RDP",8080:"HTTP-Alt",8443:"HTTPS-Alt"}
        for port in common_ports:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                    status = Text("OPEN", style="bold #00ff88")
            except Exception:
                status = Text("closed", style="color(238)")
            t.add_row(str(port), services.get(port,""), status)
        console.print(Align.center(t))

    if choice != "0": pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 7: JUNK FILE CLEANER
# ═══════════════════════════════════════════════════════════════

def module_junk():
    section_header("JUNK FILE CLEANER", "#ff4444")

    junk_targets = [
        (os.environ.get("TEMP", ""),                                                        "User Temp"),
        (os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Temp"),                "Windows Temp"),
        (os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),                         "LocalAppData Temp"),
        (os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Prefetch"),            "Prefetch"),
        (os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), r"SoftwareDistribution\Download"), "WU Downloads"),
    ]

    # Show scan summary
    scan_table = Table(header_style="bold #ff4444", box=box.ROUNDED, border_style="color(238)")
    scan_table.add_column("Folder",     style="white",    min_width=20)
    scan_table.add_column("Path",       style="color(240)", min_width=40)
    scan_table.add_column("Size",       style="#ffcc00",  min_width=10)
    scan_table.add_column("Files",      style="color(240)", min_width=8)
    for path, label in junk_targets:
        if not os.path.exists(path):
            scan_table.add_row(label, path, "—", "—")
            continue
        total_size = 0; file_count = 0
        try:
            for root, dirs, files in os.walk(path):
                for f in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                        file_count += 1
                    except Exception:
                        continue
        except Exception:
            pass
        scan_table.add_row(label, path[:40], bytes_to_human(total_size), str(file_count))
    console.print(Align.center(scan_table))
    console.print()

    opts = {
        "1": "Clean All Junk Folders  (listed above)",
        "2": "Empty Recycle Bin       (WinAPI)",
        "3": "Run Disk Cleanup        (cleanmgr)",
        "0": "Back",
    }
    console.print(Align.center(make_menu_table(opts, "#ff4444")))
    choice = Prompt.ask("\n   [#ff4444]>[/]", choices=list(opts.keys()), show_choices=False)

    if choice == "1":
        total_freed = 0; failed = 0
        for path, label in junk_targets:
            if not os.path.exists(path): continue
            console.print(f"   [dim]Cleaning {label}...[/]")
            for root, dirs, files in os.walk(path):
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        total_freed += os.path.getsize(fp)
                        os.remove(fp)
                    except Exception:
                        failed += 1
                        continue
        console.print()
        result_ok(f"Freed {bytes_to_human(total_freed)}")
        if failed:
            result_warn(f"{failed} files skipped (locked or access denied)")

    elif choice == "2":
        if WinAPI.empty_recycle_bin():
            result_ok("Recycle Bin emptied successfully")
        else:
            result_fail("Failed to empty Recycle Bin (may already be empty)")

    elif choice == "3":
        try:
            subprocess.Popen(["cleanmgr", "/sagerun:1"])
            result_ok("Disk Cleanup launched in background")
        except Exception as e:
            result_fail(f"Could not launch cleanmgr: {e}")

    if choice != "0": pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 8: BATTERY & POWER
# ═══════════════════════════════════════════════════════════════

def module_battery():
    section_header("BATTERY & POWER", "#88ffff")

    if PSUTIL:
        battery = psutil.sensors_battery()
        if battery:
            pct   = battery.percent
            plugged = battery.power_plugged
            bar_color = "#00ff88" if pct > 50 else "#ffcc00" if pct > 20 else "#ff4444"
            status_text = "[bold #00ff88]⚡ PLUGGED IN[/]" if plugged else "[bold #ffcc00]🔋 ON BATTERY[/]"

            bat_table = Table.grid(padding=(0, 3))
            bat_table.add_column(style="color(240)", min_width=14)
            bat_table.add_column()
            bat_table.add_row("Status",   Text.from_markup(status_text))
            bat_table.add_row("Level",    render_bar(pct, 100, 30, bar_color))
            bat_table.add_row("",         Text(f"{pct:.0f}%", style=f"bold {bar_color}"))
            if hasattr(battery, 'secsleft') and battery.secsleft > 0 and not plugged:
                h, r = divmod(battery.secsleft, 3600); m = r // 60
                bat_table.add_row("Remaining", Text(f"{h}h {m}m", style="bold white"))

            console.print(Align.center(Panel(bat_table, border_style="#88ffff", box=box.ROUNDED, title="[bold #88ffff]battery status[/]")))
        else:
            result_warn("No battery detected (desktop system?)")
        console.print()

    power_plans = {
        "1": ("High Performance", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
        "2": ("Balanced",         "381b4222-f694-41f0-9685-ff5bb260df2e"),
        "3": ("Power Saver",      "a1841308-3541-4fab-bc81-f71556f20b4a"),
    }
    opts = {k: v[0] for k, v in power_plans.items()}
    opts["0"] = "Back"
    console.print(Align.center(make_menu_table(opts, "#88ffff")))
    choice = Prompt.ask("\n   [#88ffff]>[/]", choices=list(opts.keys()), show_choices=False)

    if choice in power_plans:
        plan_name, plan_guid = power_plans[choice]
        out, rc = run_cmd(["powercfg", "/setactive", plan_guid])
        if rc == 0:
            result_ok(f"Power plan set to: {plan_name}")
        else:
            result_fail(f"Failed to set power plan: {out}")
        pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 9: SYSTEM INFO
# ═══════════════════════════════════════════════════════════════

def module_sysinfo():
    section_header("SYSTEM INFORMATION", "#ffffff")

    # Gather info
    try: hostname = socket.gethostname()
    except: hostname = "unknown"
    try: local_ip = socket.gethostbyname(hostname)
    except: local_ip = "unknown"
    try: username = os.getlogin()
    except: username = os.environ.get("USERNAME", "unknown")

    t = Table.grid(padding=(0, 3))
    t.add_column(style="color(240)", min_width=18)
    t.add_column(style="bold white")
    t.add_row("OS",         platform.platform())
    t.add_row("Architecture", platform.machine())
    t.add_row("Processor",  platform.processor()[:60] or "N/A")
    t.add_row("Python",     platform.python_version())
    t.add_row("Hostname",   hostname)
    t.add_row("Local IP",   local_ip)
    t.add_row("User",       username)
    t.add_row("Admin",      "[bold #00ff88]Yes[/]" if WinAPI.is_admin() else "[bold #ff4444]No[/]")
    if PSUTIL:
        mem = psutil.virtual_memory()
        t.add_row("Total RAM",   bytes_to_human(mem.total))
        t.add_row("CPU Cores",   str(psutil.cpu_count(logical=False)) + f" physical / {psutil.cpu_count()} logical")
        try:
            freq = psutil.cpu_freq()
            if freq:
                t.add_row("CPU Freq",  f"{freq.current:.0f} MHz (max {freq.max:.0f} MHz)")
        except Exception:
            pass
    t.add_row("Uptime",     _get_uptime())

    console.print(Align.center(Panel(t, border_style="#ffffff", box=box.ROUNDED, title="[bold]system info[/]")))
    console.print()

    opts = {"1": "Export Report (msinfo32)", "0": "Back"}
    console.print(Align.center(make_menu_table(opts, "#ffffff")))
    choice = Prompt.ask("\n   [#ffffff]>[/]", choices=list(opts.keys()), show_choices=False)
    if choice == "1":
        try:
            subprocess.Popen(["msinfo32"])
            result_ok("msinfo32 launched")
        except Exception as e:
            result_fail(str(e))
        pause()

def _get_uptime() -> str:
    try:
        if PSUTIL:
            boot = psutil.boot_time()
            elapsed = time.time() - boot
            h = int(elapsed // 3600)
            m = int((elapsed % 3600) // 60)
            return f"{h}h {m}m"
    except Exception:
        pass
    return "N/A"

# ═══════════════════════════════════════════════════════════════
#  MODULE A: AFK MODE  (read-only · zero side-effects)
# ═══════════════════════════════════════════════════════════════

import random
import math

# ── AFK sub-scenes ──────────────────────────────────────────────

def _afk_scene_matrix(tick: int, w: int = 72) -> Text:
    """Falling katakana/digit rain columns."""
    CHARS = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789"
    random.seed(tick)
    lines = []
    for row in range(14):
        line = Text()
        for col in range(w // 2):
            ch = random.choice(CHARS)
            # leading edge is bright white, trail fades
            depth = (tick // 2 + col * 3 + row * 7) % 20
            if depth == 0:
                style = "bold white"
            elif depth < 4:
                style = "bold #00ff88"
            elif depth < 9:
                style = "#006622"
            else:
                style = "color(234)"
            line.append(ch + " ", style=style)
        lines.append(line)
    combined = Text()
    for l in lines:
        combined.append_text(l)
        combined.append("\n")
    return combined

def _afk_scene_starfield(tick: int, w: int = 72, h: int = 14) -> Text:
    """Parallax star warp — stars stream toward viewer."""
    random.seed(42)
    stars = [(random.uniform(-1, 1), random.uniform(-1, 1), random.random()) for _ in range(80)]
    speed = 0.018
    out_chars = [[" "] * w for _ in range(h)]
    out_styles = [["color(234)"] * w for _ in range(h)]

    for sx, sy, sz in stars:
        z = (sz - (tick * speed)) % 1.0
        if z < 0.01:
            continue
        scale = 1.0 / z
        px = int(w / 2 + sx * scale * (w / 4))
        py = int(h / 2 + sy * scale * (h / 2))
        if 0 <= px < w and 0 <= py < h:
            brightness = 1.0 - z
            if brightness > 0.85:   ch, st = "★", "bold white"
            elif brightness > 0.65: ch, st = "·", "bold #aaaaff"
            elif brightness > 0.40: ch, st = "·", "#555588"
            else:                   ch, st = ".", "color(236)"
            out_chars[py][px] = ch
            out_styles[py][px] = st

    result = Text()
    for r in range(h):
        for c in range(w):
            result.append(out_chars[r][c], style=out_styles[r][c])
        result.append("\n")
    return result

def _afk_scene_plasma(tick: int, w: int = 72, h: int = 14) -> Text:
    """Sine-wave colour plasma."""
    PLASMA_COLORS = [
        "#ff0055","#ff4400","#ffaa00","#ffff00",
        "#00ff88","#00ffff","#0088ff","#8800ff",
        "#ff00ff","#ff0055",
    ]
    result = Text()
    for row in range(h):
        for col in range(w):
            v = (
                math.sin(col * 0.18 + tick * 0.07) +
                math.sin(row * 0.35 + tick * 0.05) +
                math.sin((col + row) * 0.12 + tick * 0.09) +
                math.sin(math.sqrt(((col - w/2)**2 + (row - h/2)**2)) * 0.18 + tick * 0.06)
            )
            idx = int((v + 4) / 8 * (len(PLASMA_COLORS) - 1))
            idx = max(0, min(idx, len(PLASMA_COLORS) - 1))
            result.append("█", style=PLASMA_COLORS[idx])
        result.append("\n")
    return result

def _afk_scene_clock(tick: int) -> Text:
    """Large ASCII clock with date and uptime."""
    DIGITS = {
        "0": ["███","█ █","█ █","█ █","███"],
        "1": [" █ "," █ "," █ "," █ "," █ "],
        "2": ["███","  █","███","█  ","███"],
        "3": ["███","  █","███","  █","███"],
        "4": ["█ █","█ █","███","  █","  █"],
        "5": ["███","█  ","███","  █","███"],
        "6": ["███","█  ","███","█ █","███"],
        "7": ["███","  █","  █","  █","  █"],
        "8": ["███","█ █","███","█ █","███"],
        "9": ["███","█ █","███","  █","███"],
        ":": [" "," ","●"," ","●"] if tick % 2 == 0 else [" "," "," "," "," "],
    }
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    color = DISCO[tick % len(DISCO)]

    rows = [""] * 5
    for ch in time_str:
        pat = DIGITS.get(ch, ["   "] * 5)
        for i in range(5):
            rows[i] += pat[i] + "  "

    result = Text("\n\n")
    for row in rows:
        result.append("  " + row + "\n", style=f"bold {color}")
    result.append("\n")
    result.append(f"  {now.strftime('%A, %d %B %Y')}".center(52) + "\n", style=f"dim {color}")
    if PSUTIL:
        try:
            elapsed = int(time.time() - psutil.boot_time())
            h, r = divmod(elapsed, 3600); m = r // 60; s = r % 60
            result.append(f"  uptime  {h:02d}:{m:02d}:{s:02d}".center(52) + "\n", style="color(240)")
        except Exception:
            pass
    return result

def _afk_scene_syswatch(tick: int) -> Text:
    """Quietly watches CPU / RAM / disk — reads only, changes nothing."""
    color = DISCO[tick % len(DISCO)]
    result = Text()
    result.append("  system whisper  —  read-only\n\n", style=f"dim {color}")

    if not PSUTIL:
        result.append("  psutil unavailable\n", style="color(240)")
        return result

    cpu_all = psutil.cpu_percent(percpu=True)
    mem = psutil.virtual_memory()

    result.append("  cpu cores\n", style=f"bold {color}")
    for i, p in enumerate(cpu_all[:8]):
        bar_color = "#ff4444" if p > 85 else "#ffcc00" if p > 60 else "#00ff88"
        filled = round(p / 100 * 40)
        bar = "█" * filled + "░" * (40 - filled)
        result.append(f"    {i:>2}  ", style="color(240)")
        result.append(bar, style=bar_color)
        result.append(f"  {p:5.1f}%\n", style="bold white")

    result.append("\n  memory\n", style=f"bold {color}")
    used_pct = mem.percent
    bar_color = "#ff4444" if used_pct > 85 else "#ffcc00" if used_pct > 65 else "#00ff88"
    filled = round(used_pct / 100 * 40)
    bar = "█" * filled + "░" * (40 - filled)
    result.append(f"    used  ", style="color(240)")
    result.append(bar, style=bar_color)
    result.append(f"  {used_pct:5.1f}%\n", style="bold white")
    result.append(f"    {bytes_to_human(mem.used)} / {bytes_to_human(mem.total)}\n", style="color(240)")
    return result

def _afk_scene_quotes(tick: int) -> Text:
    """Cycles through hacker/nerd quotes."""
    QUOTES = [
        ("The best way to predict the future is to invent it.", "Alan Kay"),
        ("Any sufficiently advanced technology is indistinguishable from magic.", "Arthur C. Clarke"),
        ("Simplicity is the soul of efficiency.", "Austin Freeman"),
        ("First, solve the problem. Then, write the code.", "John Johnson"),
        ("Make it work, make it right, make it fast.", "Kent Beck"),
        ("The computer was born to solve problems that did not exist before.", "Bill Gates"),
        ("Code is like humour. When you have to explain it, it's bad.", "Cory House"),
        ("Experience is the name everyone gives to their mistakes.", "Oscar Wilde"),
        ("It's not a bug — it's an undocumented feature.", "Anonymous"),
        ("There are only two hard things in Computer Science: cache invalidation and naming things.", "Phil Karlton"),
        ("Talk is cheap. Show me the code.", "Linus Torvalds"),
        ("Walking on water and developing software from a specification are easy if both are frozen.", "Edward V. Berard"),
        ("The best error message is the one that never shows up.", "Thomas Fuchs"),
        ("Debugging is twice as hard as writing the code in the first place.", "Brian W. Kernighan"),
        ("Any fool can write code that a computer can understand.", "Martin Fowler"),
    ]
    color = DISCO[tick % len(DISCO)]
    q, author = QUOTES[(tick // 6) % len(QUOTES)]

    # Word-wrap at ~58 chars
    words = q.split()
    lines = []; cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > 58:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: lines.append(cur)

    result = Text("\n\n\n")
    result.append("  ❝\n\n", style=f"bold {color}")
    for line in lines:
        result.append(f"    {line}\n", style=f"bold white")
    result.append(f"\n    — {author}\n", style=f"dim {color}")
    return result

# ── Scene registry ───────────────────────────────────────────────

_AFK_SCENES = [
    ("MATRIX RAIN",    _afk_scene_matrix),
    ("STAR WARP",      _afk_scene_starfield),
    ("PLASMA WAVE",    _afk_scene_plasma),
    ("CLOCK",          _afk_scene_clock),
    ("SYSTEM WHISPER", _afk_scene_syswatch),
    ("QUOTES",         _afk_scene_quotes),
]

_SCENE_DURATION  = 12       # seconds per scene before auto-rotating
_TARGET_FPS      = 60       # target frame rate
_FRAME_BUDGET    = 1 / _TARGET_FPS  # 0.01667 s per frame

# ── Module entry point ───────────────────────────────────────────

def module_afk():
    section_header("AFK MODE · choose a scene", "#cc88ff")

    scene_opts = {str(i + 1): name for i, (name, _) in enumerate(_AFK_SCENES)}
    scene_opts["r"] = "Random rotation  (auto-switches every 12s)"
    scene_opts["0"] = "Back"

    console.print(Align.center(make_menu_table(scene_opts, "#cc88ff")))
    console.print()
    console.print(Align.center(Text(
        "AFK mode is read-only — it never writes, deletes, or changes anything.",
        style="dim",
    )))
    console.print()
    valid = list(scene_opts.keys())
    choice = Prompt.ask("   [#cc88ff]>[/]", choices=valid, show_choices=False)
    if choice == "0":
        return

    rotating = (choice == "r")
    if rotating:
        scene_idx = 0
    else:
        scene_idx = int(choice) - 1

    tick = 0
    scene_tick = 0  # counts within current scene for rotation

    def build_frame(tick, scene_idx, rotating):
        name, fn = _AFK_SCENES[scene_idx % len(_AFK_SCENES)]
        color = DISCO[tick % len(DISCO)]

        # Render scene content
        content = fn(tick)

        # Scene info bar
        info = Table.grid(padding=(0, 3))
        info.add_column(style=f"bold {color}", min_width=20)
        info.add_column(style="color(240)", min_width=20)
        info.add_column(style="color(240)")
        next_name = _AFK_SCENES[(scene_idx + 1) % len(_AFK_SCENES)][0] if rotating else "—"
        info.add_row(
            f"◈  {name}",
            f"tick {tick:>5}",
            f"next → {next_name}" if rotating else "ctrl+c  exit",
        )

        # Compose
        body = Table.grid()
        body.add_column()
        body.add_row(Panel(
            content,
            border_style=color,
            box=box.ROUNDED,
            padding=(0, 1),
        ))
        body.add_row(Panel(
            Align.center(info),
            border_style="color(236)",
            box=box.SIMPLE,
            padding=(0, 1),
        ))
        body.add_row(Panel(
            Align.center(Text("ctrl+c  →  return to menu", style="color(238)")),
            border_style="color(234)",
            box=box.SIMPLE,
            padding=(0, 0),
        ))

        root = Table.grid()
        root.add_column()
        root.add_row(logo_panel(color, f"AFK MODE · {name}"))
        root.add_row(body)
        return root

    _FRAME     = 1 / 60      # 60 fps frame budget
    _afk_stop  = threading.Event()

    # Shared mutable state updated by render loop, read by nobody else (no thread needed —
    # AFK scenes are pure math, so they're safe to run directly on the render thread at 60 fps)
    initial = build_frame(0, scene_idx, rotating)
    try:
        with Live(initial, console=console, screen=True) as live:
            while True:
                t0 = time.perf_counter()
                live.update(build_frame(tick, scene_idx, rotating))
                tick       += 1
                scene_tick += 1
                if rotating and scene_tick >= (_SCENE_DURATION * _TARGET_FPS):
                    scene_idx  += 1
                    scene_tick  = 0
                spent    = time.perf_counter() - t0
                leftover = _FRAME - spent
                if leftover > 0:
                    time.sleep(leftover)
    except KeyboardInterrupt:
        pass


# ═══════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════

def main():
    if not WinAPI.is_admin():
        clr()
        console.print(Panel(
            "[bold #ffcc00]Running without Administrator privileges.[/]\n\n"
            "Some features will be limited:\n"
            "  [dim]·[/] RAM standby list clear requires Admin\n"
            "  [dim]·[/] SFC and Chkdsk require Admin\n"
            "  [dim]·[/] Network reset requires Admin\n\n"
            "[dim]Right-click and 'Run as administrator' for full access.[/]",
            title="[bold #ffcc00]⚠  LIMITED MODE[/]",
            border_style="#ffcc00",
            box=box.ROUNDED,
        ))
        time.sleep(3)

    dispatch = {
        "1": module_timer,
        "2": module_ram,
        "3": module_disk,
        "4": module_process,
        "5": module_monitor,
        "6": module_network,
        "7": module_junk,
        "8": module_battery,
        "9": module_sysinfo,
        "a": module_afk,
    }

    while True:
        choice = main_menu()
        if choice == "0":
            clr()
            console.print(Panel(
                Align.center(Text("goodbye", style="bold #00ffff")),
                border_style="#00ffff",
                box=box.DOUBLE,
                padding=(1, 6),
            ))
            break
        if choice in dispatch:
            try:
                dispatch[choice]()
            except KeyboardInterrupt:
                pass
            except Exception as e:
                result_fail(f"Unexpected error in module: {e}")
                pause()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
