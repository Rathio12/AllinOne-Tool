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
            # Use sys.executable to ensure we install to the correct environment
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("--- Installation successful. Restarting... ---\n")
            # Restart the script
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            print(f"--- Error installing dependencies: {e} ---")
            print("--- Please run: pip install rich psutil ---")
            sys.exit(1)

if __name__ == "__main__" or __name__ == "allinone":
    # Run bootstrap before any local imports of rich/psutil
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

# ═══════════════════════════════════════════════════════════════
#  WINAPI & CONSTANTS
# ═══════════════════════════════════════════════════════════════

console = Console()

# WinAPI Definitions
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
        # hibernate, force, disable_wakeup
        ctypes.windll.powrprof.SetSuspendState(int(hibernate), 0, 0)

    @staticmethod
    def empty_working_sets():
        # Trims working sets of all processes
        # Requires SE_DEBUG_NAME privilege for other processes
        try:
            processes = psutil.pids() if PSUTIL else []
            count = 0
            for pid in processes:
                try:
                    # PROCESS_QUERY_INFORMATION (0x0400) | PROCESS_SET_QUOTA (0x0100)
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
        # 80 = SystemMemoryListInformation, 4 = MemoryPurgeStandbyList
        # This is a bit complex for pure ctypes without a buffer, 
        # but we can use PowerShell for this specific one as it's safer and "native" enough.
        # However, for "optimization", we'll use a direct NtSetSystemInformation call if possible.
        try:
            # MemoryPurgeStandbyList = 4
            # SYSTEM_MEMORY_LIST_COMMAND = 80
            # ntstatus = NtSetSystemInformation(80, &command, 4)
            command = ctypes.c_int(4)
            status = ctypes.windll.ntdll.NtSetSystemInformation(80, ctypes.byref(command), 4)
            return status == 0
        except:
            return False

    @staticmethod
    def flush_dns():
        # DnsFlushResolverCache is undocumented but available in dnsapi.dll
        try:
            return ctypes.windll.dnsapi.DnsFlushResolverCache() != 0
        except:
            return False

    @staticmethod
    def empty_recycle_bin():
        # SHEmptyRecycleBinW(HWND, RootPath, Flags)
        # Flags: SHERB_NOCONFIRMATION (1), SHERB_NOPROGRESSUI (2), SHERB_NOSOUND (4)
        try:
            return ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1 | 2 | 4) == 0
        except:
            return False

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
    "1": ("⏱  Timer & Power",      "#00ffff"),
    "2": ("🧹  RAM & Cache Cleaner", "#ff88ff"),
    "3": ("💾  Disk Utilities",      "#ffff00"),
    "4": ("⚙️  Process Manager",     "#00ff88"),
    "5": ("📊  System Monitor",      "#ff8800"),
    "6": ("🌐  Network Tools",       "#4488ff"),
    "7": ("🗑️  Junk File Cleaner",   "#ff4444"),
    "8": ("🔋  Battery & Power",     "#88ffff"),
    "9": ("ℹ️  System Info",         "#ffffff"),
    "0": ("🚪  Exit",               "#666666"),
}

# ═══════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════

def clr():
    os.system("cls")

def pause(msg="   press enter to continue"):
    console.print(f"\n   [color(240)]{msg}[/]")
    input()

def run_cmd(cmd, capture=True, shell=False):
    try:
        r = subprocess.run(cmd, capture_output=capture, text=True, timeout=60, shell=shell)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), 1

def bytes_to_human(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

def notify(msg: str):
    try:
        subprocess.run(["msg", "*", msg], capture_output=True)
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
    admin_tag = "[bold #ff4444] ADMIN [/]" if WinAPI.is_admin() else "[dim] USER [/]"
    return Panel(
        Align.center(Text(LOGO, style=f"bold {color}")),
        box=box.DOUBLE,
        border_style=color,
        subtitle=f"{admin_tag} [dim {color}]{subtitle}[/]",
        subtitle_align="right",
        padding=(0, 1),
    )

def section_header(title: str, color: str, subtitle: str = "V4.0"):
    clr()
    console.print(logo_panel(color, subtitle))
    console.print()
    console.print(Rule(f"[bold {color}]{title}[/]", style=color))
    console.print()

def render_bar(val, total, width=40, color="#00ffff"):
    ratio  = min(val / total, 1.0) if total else 0
    filled = round(ratio * width)
    t = Text()
    t.append("█" * filled,           style=f"bold {color}")
    t.append("░" * (width - filled), style="color(238)")
    t.append(f"  {ratio*100:4.1f}%", style="bold white")
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
    return Text("● OK", style="bold #00ff88") if ok else Text("● FAIL", style="bold #ff4444")

# ═══════════════════════════════════════════════════════════════
#  MODULES
# ═══════════════════════════════════════════════════════════════

def main_menu() -> str:
    clr()
    color = "#00ffff"
    console.print(logo_panel(color, "WINDOWS NATIVE · V4.0"))
    console.print()
    console.print(Rule(f"[bold {color}]main menu[/]", style=color))
    console.print()

    grid = Table.grid(padding=(0, 4))
    grid.add_column(style=f"bold {color}", min_width=3)
    grid.add_column(style="color(240)", min_width=3)
    grid.add_column(style="white")

    for k, (label, _) in MODULES.items():
        grid.add_row(k, "·", label)

    console.print(Align.center(grid))
    console.print()
    console.print(Rule(style="color(238)"))
    console.print()
    choice = Prompt.ask(
        "   [bold #00ffff]>[/]",
        choices=list(MODULES.keys()),
        show_choices=False,
    )
    return choice

# ── MODULE 1: TIMER ──────────────────────────────────────────────

def build_timer_screen(timer, total, action, tick):
    color  = DISCO[tick % len(DISCO)]
    spec   = SPECTRUM[tick % len(SPECTRUM)]
    vu_lvl = VU_SEQ[tick % len(VU_SEQ)]
    hh = timer // 3600; mm = (timer % 3600) // 60; ss = timer % 60
    dim = "color(240)"

    meta = Table.grid(padding=(0, 4))
    meta.add_column(style=dim,          min_width=9)
    meta.add_column(style="bold white", min_width=16)
    meta.add_row("engine",  "WINAPI_V4")
    meta.add_row("session", "● optimized")
    meta.add_row("action",  Text(action.lower(), style=f"bold {color}"))
    meta.add_row("clock",   datetime.now().strftime("%H:%M:%S"))

    clock    = Align.center(Text(f"{hh:02d}:{mm:02d}:{ss:02d}", style=f"bold {color}", justify="center"))
    ratio    = timer / total if total else 0
    filled   = round(ratio * 52)
    prog_t   = Text()
    prog_t.append("█" * filled,       style=f"bold {color}")
    prog_t.append("░" * (52-filled),  style="color(238)")
    prog_t.append(f"  {ratio*100:5.1f}%", style="bold white")

    vu_row = Table.grid(padding=(0, 1))
    vu_row.add_column(min_width=16)
    vu_row.add_column()
    vu_row.add_row(Text("  ◈  vu meter", style=dim), render_vu(vu_lvl))

    body = Table.grid(padding=(0, 0))
    body.add_column(min_width=72)
    def gap(n=1):
        for _ in range(n): body.add_row(Text(""))
    def sep(): body.add_row(Rule(style=dim))

    gap(); body.add_row(Align.center(meta)); gap(); sep(); gap()
    body.add_row(clock); gap()
    body.add_row(Align.center(prog_t)); gap(); sep(); gap()
    body.add_row(Text("  ♫  spectrum", style=dim)); gap()
    body.add_row(Align.center(Text(spec, style=f"bold {color}", justify="center"))); gap()
    body.add_row(vu_row); gap(); sep(); gap()
    body.add_row(Align.center(Text("ctrl+c  abort", style=dim))); gap()

    root = Table.grid()
    root.add_column()
    root.add_row(logo_panel(color))
    root.add_row(Panel(body, box=box.SIMPLE_HEAD, border_style=dim, padding=(0, 2)))
    return root

def module_timer():
    durations = {"1": ("30 min", 1800), "2": ("45 min", 2700), "3": ("1 hr", 3600), "4": ("2 hr", 7200), "5": ("custom", 0)}
    actions = {"1": "Shutdown", "2": "Restart", "3": "Sleep", "4": "Hibernate", "5": "Lock Screen", "6": "Just Notify"}

    section_header("timer · duration", "#00ffff")
    for k, (l, _) in durations.items(): console.print(f"   [bold #00ffff]{k}[/] · {l}")
    choice = Prompt.ask("\n   [#00ffff]>[/]", choices=list(durations.keys()), show_choices=False)
    total = IntPrompt.ask("   [#00ffff]minutes[/]") * 60 if choice == "5" else durations[choice][1]

    section_header("timer · action", "#ff00ff")
    for k, l in actions.items(): console.print(f"   [bold #ff00ff]{k}[/] · {l}")
    choice = Prompt.ask("\n   [#ff00ff]>[/]", choices=list(actions.keys()), show_choices=False)
    action = actions[choice]

    timer = total; tick = 0
    try:
        with Live(build_timer_screen(timer, total, action, tick), console=console, screen=True) as live:
            while timer > 0:
                live.update(build_timer_screen(timer, total, action, tick))
                time.sleep(1); timer -= 1; tick += 1
    except KeyboardInterrupt: return

    if action == "Just Notify": notify("Timer complete"); pause()
    else: run_power_action(action)

# ── MODULE 2: RAM ──────────────────────────────────────────────

def module_ram():
    section_header("ram & cache cleaner", "#ff88ff")
    
    def get_stats():
        if not PSUTIL: return "psutil missing", "0", "0"
        m = psutil.virtual_memory()
        return bytes_to_human(m.total), bytes_to_human(m.used), bytes_to_human(m.available), m.percent

    total, used, free, pct = get_stats()
    t = Table.grid(padding=(0, 3))
    t.add_row("[dim]Total RAM[/]", total, render_bar(used_val:=psutil.virtual_memory().used if PSUTIL else 0, psutil.virtual_memory().total if PSUTIL else 1, color="#ff88ff"))
    t.add_row("[dim]Used RAM[/]",  used,  f"[bold #ff4444]{pct}%[/]")
    t.add_row("[dim]Free RAM[/]",  free,  "")
    console.print(Align.center(t))
    console.print("\n" + Rule(style="color(238)") + "\n")

    opts = {
        "1": "Trim all process working sets (WinAPI)",
        "2": "Clear Standby List (WinAPI Native)",
        "3": "Flush DNS Cache (WinAPI)",
        "4": "Clear Windows File Cache (System)",
        "5": "Do All Optimizations",
        "0": "Back"
    }
    for k, v in opts.items(): console.print(f"   [bold #ff88ff]{k}[/] · {v}")
    choice = Prompt.ask("\n   [#ff88ff]>[/]", choices=list(opts.keys()), show_choices=False)
    if choice == "0": return

    m1 = psutil.virtual_memory() if PSUTIL else None
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as prog:
        if choice in ("1", "5"):
            prog.add_task("Trimming working sets...", total=None)
            count = WinAPI.empty_working_sets()
            console.print(f"   [bold #00ff88]✓[/] Trimmed {count} processes")
        
        if choice in ("2", "5"):
            prog.add_task("Clearing standby list...", total=None)
            if WinAPI.clear_standby_list(): console.print("   [bold #00ff88]✓[/] Standby list cleared")
            else: console.print("   [bold #ff4444]![/] Standby list clear failed (Admin required)")

        if choice in ("3", "5"):
            prog.add_task("Flushing DNS...", total=None)
            if WinAPI.flush_dns(): console.print("   [bold #00ff88]✓[/] DNS cache flushed")
            else: console.print("   [bold #ff4444]![/] DNS flush failed")

        if choice in ("4", "5"):
            prog.add_task("Cleaning file cache...", total=None)
            # PowerShell command for system-wide file cache clearing (requires admin)
            run_cmd(["powershell", "-Command", "Clear-Bccache"], shell=True)
            console.print("   [bold #00ff88]✓[/] File cache command sent")

    if PSUTIL:
        m2 = psutil.virtual_memory()
        freed = max(0, m2.available - m1.available)
        console.print(f"\n   [dim]RAM freed:[/] [bold #00ff88]{bytes_to_human(freed)}[/]")
        console.print(f"   [dim]Current Free RAM:[/] [bold #00ff88]{bytes_to_human(m2.available)}[/]")
    
    pause()

# ── MODULE 3: DISK ─────────────────────────────────────────────

def module_disk():
    section_header("disk utilities", "#ffff00")
    if PSUTIL:
        t = Table(box=box.SIMPLE_HEAD, border_style="color(238)", header_style="bold #ffff00")
        t.add_column("Drive"); t.add_column("Type"); t.add_column("Total"); t.add_column("Free"); t.add_column("Usage")
        for p in psutil.disk_partitions():
            try:
                u = psutil.disk_usage(p.mountpoint)
                t.add_row(p.device, p.fstype, bytes_to_human(u.total), bytes_to_human(u.free), render_bar(u.used, u.total, 20))
            except: continue
        console.print(t)

    console.print("\n   [bold #ffff00]1[/] · Optimize/Defrag Drives\n   [bold #ffff00]2[/] · Check Disk Health (WMI)\n   [bold #ffff00]3[/] · Run System File Checker (SFC)\n   [bold #ffff00]4[/] · Schedule Boot Scan (Chkdsk)\n   [bold #ffff00]0[/] · Back")
    choice = Prompt.ask("\n   [#ffff00]>[/]", choices=["0","1","2","3","4"], show_choices=False)

    if choice == "1":
        console.print("   [dim]Starting defrag/optimization...[/]")
        run_cmd(["defrag", "/C", "/O"], capture=False)
    elif choice == "2":
        out, _ = run_cmd(["wmic", "diskdrive", "get", "status,model"])
        console.print(f"\n[bold]Disk Status:[/]\n{out}")
    elif choice == "3":
        if not WinAPI.is_admin(): console.print("   [bold #ff4444]Admin required for SFC[/]")
        else: run_cmd(["sfc", "/scannow"], capture=False)
    elif choice == "4":
        if not WinAPI.is_admin(): console.print("   [bold #ff4444]Admin required for Chkdsk[/]")
        else: run_cmd(["chkdsk", "C:", "/f", "/r", "/x"], capture=False, shell=True)
    
    if choice != "0": pause()

# ── MODULE 4: PROCESS ──────────────────────────────────────────

def module_process():
    section_header("process manager", "#00ff88")
    if not PSUTIL: console.print("psutil missing"); pause(); return

    console.print("   [bold #00ff88]1[/] · Top CPU\n   [bold #00ff88]2[/] · Top RAM\n   [bold #00ff88]3[/] · Kill by PID\n   [bold #00ff88]0[/] · Back")
    choice = Prompt.ask("\n   [#00ff88]>[/]", choices=["0","1","2","3"], show_choices=False)

    if choice in ("1", "2"):
        key = "cpu_percent" if choice == "1" else "memory_percent"
        procs = sorted([p.info for p in psutil.process_iter(['pid','name','cpu_percent','memory_percent'])], key=lambda x: x[key] or 0, reverse=True)[:20]
        t = Table(header_style="bold #00ff88", box=box.SIMPLE)
        t.add_column("PID"); t.add_column("Name"); t.add_column("CPU%"); t.add_column("MEM%")
        for p in procs: t.add_row(str(p['pid']), p['name'], f"{p['cpu_percent']:.1f}", f"{p['memory_percent']:.1f}")
        console.print(t)
        pause()
    elif choice == "3":
        pid = IntPrompt.ask("   PID")
        try: psutil.Process(pid).terminate(); console.print("   [bold #00ff88]✓ Terminated[/]")
        except Exception as e: console.print(f"   [#ff4444]{e}[/]")
        pause()

# ── MODULE 5: MONITOR ──────────────────────────────────────────

def module_monitor():
    if not PSUTIL: return
    try:
        with Live(None, console=console, screen=True, refresh_per_second=2) as live:
            tick = 0
            while True:
                cpu = psutil.cpu_percent(percpu=True)
                mem = psutil.virtual_memory()
                
                t = Table.grid(padding=(0, 2))
                t.add_row(Text("CPU USAGE", style="bold #ff8800"))
                for i, p in enumerate(cpu[:8]): t.add_row(f"Core {i}", render_bar(p, 100, 30, "#00ff88"))
                t.add_row("", "")
                t.add_row(Text("MEMORY", style="bold #ff8800"))
                t.add_row("RAM", render_bar(mem.used, mem.total, 30, "#ff88ff"))
                
                panel = Panel(Align.center(t), title="[bold]LIVE MONITOR[/]", border_style="#ff8800")
                live.update(panel)
                time.sleep(0.5); tick += 1
    except KeyboardInterrupt: pass

# ── MODULE 6: NETWORK ──────────────────────────────────────────

def module_network():
    section_header("network tools", "#4488ff")
    console.print("   [bold #4488ff]1[/] · Ping (Native)\n   [bold #4488ff]2[/] · Tracert\n   [bold #4488ff]3[/] · Network Reset\n   [bold #4488ff]4[/] · IP Config\n   [bold #4488ff]0[/] · Back")
    choice = Prompt.ask("\n   [#4488ff]>[/]", choices=["0","1","2","3","4"], show_choices=False)

    if choice == "1":
        host = Prompt.ask("   Host", default="8.8.8.8")
        run_cmd(["ping", host], capture=False)
    elif choice == "2":
        host = Prompt.ask("   Host", default="8.8.8.8")
        run_cmd(["tracert", host], capture=False)
    elif choice == "3":
        if Confirm.ask("   [#ff4444]Reset network stack? (Requires Admin/Reboot)[/]"):
            run_cmd(["netsh", "winsock", "reset"], capture=False)
            run_cmd(["netsh", "int", "ip", "reset"], capture=False)
            run_cmd(["ipconfig", "/release"], capture=False)
            run_cmd(["ipconfig", "/renew"], capture=False)
            run_cmd(["ipconfig", "/flushdns"], capture=False)
    elif choice == "4":
        out, _ = run_cmd(["ipconfig", "/all"])
        console.print(f"\n[dim]{out}[/]")
    
    if choice != "0": pause()

# ── MODULE 7: JUNK ─────────────────────────────────────────────

def module_junk():
    section_header("junk file cleaner", "#ff4444")
    
    junk_targets = [
        os.environ.get("TEMP", ""),
        os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Temp"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
        os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Prefetch"),
        os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "SoftwareDistribution\\Download"),
    ]

    console.print("   [bold #ff4444]1[/] · Scan & Clean Junk Folders\n   [bold #ff4444]2[/] · Empty Recycle Bin (WinAPI)\n   [bold #ff4444]3[/] · Run Disk Cleanup (cleanmgr)\n   [bold #ff4444]0[/] · Back")
    choice = Prompt.ask("\n   [#ff4444]>[/]", choices=["0","1","2","3"], show_choices=False)

    if choice == "1":
        total_freed = 0
        for path in junk_targets:
            if not os.path.exists(path): continue
            console.print(f"   [dim]Cleaning {path}...[/]")
            for root, dirs, files in os.walk(path):
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        total_freed += os.path.getsize(fp)
                        os.remove(fp)
                    except: continue
        console.print(f"   [bold #00ff88]✓ Freed {bytes_to_human(total_freed)}[/]")
    elif choice == "2":
        if WinAPI.empty_recycle_bin(): console.print("   [bold #00ff88]✓ Recycle Bin emptied[/]")
        else: console.print("   [bold #ff4444]![/] Failed to empty bin")
    elif choice == "3":
        subprocess.Popen(["cleanmgr", "/sagerun:1"])
        console.print("   [dim]Disk Cleanup started in background...[/]")
    
    if choice != "0": pause()

# ── MODULE 8: BATTERY ──────────────────────────────────────────

def module_battery():
    section_header("battery & power", "#88ffff")
    if PSUTIL and psutil.sensors_battery():
        b = psutil.sensors_battery()
        console.print(f"   [bold]Status:[/] {'Plugged In' if b.power_plugged else 'Battery'}")
        console.print(f"   [bold]Level:[/]  {b.percent}%")
        console.print(render_bar(b.percent, 100, 40, "#00ff88" if b.percent > 20 else "#ff4444"))
    
    console.print("\n   [bold #88ffff]1[/] · High Performance\n   [bold #88ffff]2[/] · Balanced\n   [bold #88ffff]3[/] · Power Saver\n   [bold #88ffff]0[/] · Back")
    choice = Prompt.ask("\n   [#88ffff]>[/]", choices=["0","1","2","3"], show_choices=False)
    
    plans = {"1": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", "2": "381b4222-f694-41f0-9685-ff5bb260df2e", "3": "a1841308-3541-4fab-bc81-f71556f20b4a"}
    if choice in plans:
        run_cmd(["powercfg", "/setactive", plans[choice]])
        console.print("   [bold #00ff88]✓ Power plan updated[/]")
        pause()

# ── MODULE 9: SYSINFO ──────────────────────────────────────────

def module_sysinfo():
    section_header("system info", "#ffffff")
    t = Table.grid(padding=(0, 3))
    t.add_row("OS", platform.platform())
    t.add_row("CPU", platform.processor())
    t.add_row("Memory", bytes_to_human(psutil.virtual_memory().total) if PSUTIL else "N/A")
    t.add_row("User", os.getlogin())
    t.add_row("Admin", str(WinAPI.is_admin()))
    console.print(Align.center(t))
    
    console.print("\n   [bold #ffffff]1[/] · Export System Info (msinfo32)\n   [bold #ffffff]0[/] · Back")
    choice = Prompt.ask("\n   [#ffffff]>[/]", choices=["0","1"], show_choices=False)
    if choice == "1":
        subprocess.Popen(["msinfo32"])
        console.print("   [dim]msinfo32 launched...[/]")
        pause()

# ═══════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════

def main():
    if not WinAPI.is_admin():
        console.print(Panel("[bold #ffcc00]WARNING:[/] Running without Administrator privileges.\nSome native tools (RAM/Disk/Junk) will be limited.", border_style="#ffcc00"))
        time.sleep(2)

    dispatch = {
        "1": module_timer, "2": module_ram, "3": module_disk,
        "4": module_process, "5": module_monitor, "6": module_network,
        "7": module_junk, "8": module_battery, "9": module_sysinfo
    }

    while True:
        choice = main_menu()
        if choice == "0": break
        if choice in dispatch:
            try: dispatch[choice]()
            except KeyboardInterrupt: pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)