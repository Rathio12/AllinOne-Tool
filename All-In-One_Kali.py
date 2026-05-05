"""
REY STATION  V4.0  ─  CROSS-PLATFORM EDITION
═════════════════════════════════════════════
Auto-detects OS and switches all commands, APIs, and platform logic.
Supports: Windows · Kali/Debian · Arch · Fedora/RHEL · macOS
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
import math
import random
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
#  PLATFORM DETECTION  (runs before anything else)
# ═══════════════════════════════════════════════════════════════

_sys = platform.system()          # 'Windows' | 'Linux' | 'Darwin'
_rel = platform.release().lower()
_IS_WIN   = _sys == "Windows"
_IS_MAC   = _sys == "Darwin"
_IS_LINUX = _sys == "Linux"

# Detect Linux distro family
_DISTRO_ID   = ""
_DISTRO_LIKE = ""
_IS_KALI     = False
_IS_ARCH     = False
_IS_FEDORA   = False
_IS_DEBIAN   = False

if _IS_LINUX:
    try:
        with open("/etc/os-release") as fh:
            _osr = dict(
                line.strip().split("=", 1)
                for line in fh
                if "=" in line
            )
        _DISTRO_ID   = _osr.get("ID",         "").strip('"').lower()
        _DISTRO_LIKE = _osr.get("ID_LIKE",    "").strip('"').lower()
        _DISTRO_NAME = _osr.get("PRETTY_NAME","").strip('"')
        _IS_KALI   = "kali"   in _DISTRO_ID or "kali"   in _DISTRO_LIKE
        _IS_ARCH   = "arch"   in _DISTRO_ID or "arch"   in _DISTRO_LIKE
        _IS_FEDORA = "fedora" in _DISTRO_ID or "rhel"   in _DISTRO_LIKE or "centos" in _DISTRO_LIKE
        _IS_DEBIAN = "debian" in _DISTRO_ID or "debian" in _DISTRO_LIKE or _IS_KALI
    except Exception:
        _DISTRO_NAME = "Unknown Linux"
else:
    _DISTRO_NAME = _sys

# ─── OS summary tag for UI ──────────────────────────────────────
if _IS_WIN:
    _OS_TAG   = "WINDOWS"
    _OS_COLOR = "#00aaff"
elif _IS_KALI:
    _OS_TAG   = "KALI LINUX"
    _OS_COLOR = "#3399ff"
elif _IS_ARCH:
    _OS_TAG   = "ARCH LINUX"
    _OS_COLOR = "#00bfff"
elif _IS_FEDORA:
    _OS_TAG   = "FEDORA/RHEL"
    _OS_COLOR = "#4488ff"
elif _IS_DEBIAN:
    _OS_TAG   = "DEBIAN LINUX"
    _OS_COLOR = "#cc44ff"
elif _IS_MAC:
    _OS_TAG   = "macOS"
    _OS_COLOR = "#aaaaff"
else:
    _OS_TAG   = "LINUX"
    _OS_COLOR = "#44ffaa"

# ═══════════════════════════════════════════════════════════════
#  BOOTSTRAP: AUTO-INSTALL DEPENDENCIES
# ═══════════════════════════════════════════════════════════════

def bootstrap():
    required = ["rich", "psutil"]
    import importlib.util
    missing  = [lib for lib in required if not importlib.util.find_spec(lib)]
    if not missing:
        return

    print(f"--- REY STATION: Missing: {', '.join(missing)} ---")
    print("--- Attempting automatic installation... ---")
    pip_base = [sys.executable, "-m", "pip", "install"]
    if _IS_LINUX or _IS_MAC:
        pip_base.append("--break-system-packages")
    try:
        subprocess.check_call(pip_base + missing)
        print("--- Installation successful. Restarting... ---\n")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"--- pip failed: {e} ---")
        # Offer distro package manager fallback on Linux
        if _IS_DEBIAN or _IS_KALI:
            print("--- Try: sudo apt install python3-rich python3-psutil ---")
        elif _IS_ARCH:
            print("--- Try: sudo pacman -S python-rich python-psutil ---")
        elif _IS_FEDORA:
            print("--- Try: sudo dnf install python3-rich python3-psutil ---")
        sys.exit(1)

bootstrap()

# ═══════════════════════════════════════════════════════════════
#  IMPORTS (after bootstrap ensures deps exist)
# ═══════════════════════════════════════════════════════════════

import psutil
PSUTIL = True

from rich          import box
from rich.align    import Align
from rich.console  import Console
from rich.live     import Live
from rich.panel    import Panel
from rich.prompt   import IntPrompt, Prompt, Confirm
from rich.rule     import Rule
from rich.table    import Table
from rich.text     import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# ═══════════════════════════════════════════════════════════════
#  PLATFORM ABSTRACTION LAYER
#  All OS-specific logic lives here. Modules call PlatformAPI.*
# ═══════════════════════════════════════════════════════════════

class PlatformAPI:
    """Single place for every OS-divergent operation."""

    # ── Privilege detection ─────────────────────────────────────
    @staticmethod
    def is_admin() -> bool:
        if _IS_WIN:
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                return False
        else:
            return os.geteuid() == 0

    # ── Screen clear ────────────────────────────────────────────
    @staticmethod
    def clear():
        os.system("cls" if _IS_WIN else "clear")

    # ── RAM / cache operations ──────────────────────────────────
    @staticmethod
    def trim_working_sets() -> int:
        """Trim process memory. Returns count of affected processes."""
        if _IS_WIN:
            try:
                import ctypes, ctypes.wintypes
                count = 0
                for pid in psutil.pids():
                    try:
                        handle = ctypes.windll.kernel32.OpenProcess(
                            0x0400 | 0x0100, False, pid
                        )
                        if handle:
                            ctypes.windll.psapi.EmptyWorkingSet(handle)
                            ctypes.windll.kernel32.CloseHandle(handle)
                            count += 1
                    except Exception:
                        continue
                return count
            except Exception:
                return 0
        elif _IS_LINUX:
            # Drop caches requires root; attempt echo 3 > /proc/sys/vm/drop_caches
            if PlatformAPI.is_admin():
                try:
                    with open("/proc/sys/vm/drop_caches", "w") as f:
                        f.write("3\n")
                    return len(psutil.pids())
                except Exception:
                    return 0
            else:
                return 0
        elif _IS_MAC:
            # macOS: purge command (requires sudo)
            rc = subprocess.run(["purge"], capture_output=True).returncode
            return len(psutil.pids()) if rc == 0 else 0
        return 0

    @staticmethod
    def clear_standby_list() -> bool:
        if _IS_WIN:
            try:
                import ctypes
                cmd = ctypes.c_int(4)
                return ctypes.windll.ntdll.NtSetSystemInformation(
                    80, ctypes.byref(cmd), 4
                ) == 0
            except Exception:
                return False
        elif _IS_LINUX:
            # sync + drop_caches achieves a similar effect
            try:
                subprocess.run(["sync"], check=True)
                with open("/proc/sys/vm/drop_caches", "w") as f:
                    f.write("3\n")
                return True
            except Exception:
                return False
        return False

    @staticmethod
    def flush_dns() -> bool:
        if _IS_WIN:
            try:
                import ctypes
                return ctypes.windll.dnsapi.DnsFlushResolverCache() != 0
            except Exception:
                return False
        elif _IS_LINUX:
            # systemd-resolved
            r = subprocess.run(
                ["resolvectl", "flush-caches"],
                capture_output=True
            )
            if r.returncode == 0:
                return True
            # nscd fallback
            r2 = subprocess.run(
                ["nscd", "-i", "hosts"],
                capture_output=True
            )
            return r2.returncode == 0
        elif _IS_MAC:
            r = subprocess.run(
                ["dscacheutil", "-flushcache"],
                capture_output=True
            )
            subprocess.run(
                ["killall", "-HUP", "mDNSResponder"],
                capture_output=True
            )
            return r.returncode == 0
        return False

    @staticmethod
    def clear_file_cache() -> tuple:
        """Returns (success:bool, message:str)"""
        if _IS_WIN:
            try:
                subprocess.run(
                    'powershell -Command "try { Clear-BCCache -Force } catch {}"',
                    shell=True, capture_output=True
                )
                return True, "BranchCache / file cache purge requested"
            except Exception as e:
                return False, str(e)
        elif _IS_LINUX:
            if not PlatformAPI.is_admin():
                return False, "Root required — run with sudo"
            try:
                subprocess.run(["sync"], check=True)
                with open("/proc/sys/vm/drop_caches", "w") as f:
                    f.write("3\n")
                return True, "Page cache, dentries and inodes dropped"
            except Exception as e:
                return False, str(e)
        elif _IS_MAC:
            r = subprocess.run(["purge"], capture_output=True)
            return r.returncode == 0, "macOS purge executed"
        return False, "Not supported on this platform"

    # ── Lock / suspend / power ──────────────────────────────────
    @staticmethod
    def lock_screen():
        if _IS_WIN:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
        elif _IS_LINUX:
            # Try common lockers in order
            for cmd in [
                ["loginctl", "lock-session"],
                ["xdg-screensaver", "lock"],
                ["gnome-screensaver-command", "--lock"],
                ["xlock", "-mode", "blank"],
                ["slock"],
            ]:
                if shutil.which(cmd[0]):
                    subprocess.Popen(cmd)
                    return
        elif _IS_MAC:
            subprocess.Popen([
                "/System/Library/CoreServices/Menu Extras/User.menu/"
                "Contents/Resources/CGSession", "-suspend"
            ])

    @staticmethod
    def suspend():
        if _IS_WIN:
            import ctypes
            ctypes.windll.powrprof.SetSuspendState(0, 0, 0)
        elif _IS_LINUX:
            subprocess.run(["systemctl", "suspend"])
        elif _IS_MAC:
            subprocess.run(["pmset", "sleepnow"])

    @staticmethod
    def hibernate():
        if _IS_WIN:
            import ctypes
            ctypes.windll.powrprof.SetSuspendState(1, 0, 0)
        elif _IS_LINUX:
            subprocess.run(["systemctl", "hibernate"])
        elif _IS_MAC:
            subprocess.run(["pmset", "hibernatenow"])

    @staticmethod
    def shutdown(delay_secs: int = 10):
        if _IS_WIN:
            subprocess.run(["shutdown", "/s", "/t", str(delay_secs)])
        elif _IS_LINUX or _IS_MAC:
            subprocess.run(["shutdown", "-h", f"+{delay_secs // 60 or 1}"])

    @staticmethod
    def restart(delay_secs: int = 10):
        if _IS_WIN:
            subprocess.run(["shutdown", "/r", "/t", str(delay_secs)])
        elif _IS_LINUX or _IS_MAC:
            subprocess.run(["shutdown", "-r", f"+{delay_secs // 60 or 1}"])

    # ── Recycle bin / trash ─────────────────────────────────────
    @staticmethod
    def empty_trash() -> bool:
        if _IS_WIN:
            try:
                import ctypes
                return ctypes.windll.shell32.SHEmptyRecycleBinW(
                    None, None, 1 | 2 | 4
                ) == 0
            except Exception:
                return False
        elif _IS_LINUX:
            trash_dirs = [
                Path.home() / ".local/share/Trash/files",
                Path.home() / ".local/share/Trash/info",
                Path("/root/.local/share/Trash/files"),
                Path("/root/.local/share/Trash/info"),
            ]
            ok = False
            for d in trash_dirs:
                if d.exists():
                    try:
                        for item in d.iterdir():
                            if item.is_file():
                                item.unlink()
                            elif item.is_dir():
                                shutil.rmtree(item, ignore_errors=True)
                        ok = True
                    except Exception:
                        pass
            return ok
        elif _IS_MAC:
            trash = Path.home() / ".Trash"
            ok = False
            if trash.exists():
                for item in trash.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        else:
                            shutil.rmtree(item, ignore_errors=True)
                        ok = True
                    except Exception:
                        pass
            return ok
        return False

    # ── Disk utilities ──────────────────────────────────────────
    @staticmethod
    def optimize_drives(capture=False):
        """Returns (cmd_list, use_shell)"""
        if _IS_WIN:
            return ["defrag", "/C", "/O"], False
        elif _IS_LINUX:
            # e4defrag for ext4; fstrim for SSDs
            return ["fstrim", "-av"], False
        elif _IS_MAC:
            return None, False  # macOS handles defrag automatically

    @staticmethod
    def disk_health_cmd():
        if _IS_WIN:
            return ["wmic", "diskdrive", "get", "status,model,size"], False
        elif _IS_LINUX:
            if shutil.which("smartctl"):
                return ["smartctl", "--scan"], False
            return ["lsblk", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT"], False
        elif _IS_MAC:
            return ["diskutil", "info", "disk0"], False
        return None, False

    @staticmethod
    def file_system_check():
        """Returns command to check filesystem integrity."""
        if _IS_WIN:
            return "sfc /scannow", True
        elif _IS_LINUX:
            return "dmesg | grep -i 'error\\|fail\\|corrupt' | tail -40", True
        elif _IS_MAC:
            return "diskutil verifyVolume /", True
        return None, False

    @staticmethod
    def schedule_disk_scan():
        if _IS_WIN:
            return "chkdsk C: /f /r /x", True
        elif _IS_LINUX:
            return "sudo fsck -Af -M", True
        elif _IS_MAC:
            return "diskutil repairVolume /", True
        return None, False

    # ── Network ─────────────────────────────────────────────────
    @staticmethod
    def ping_cmd(host: str) -> list:
        if _IS_WIN:
            return ["ping", "-n", "4", host]
        else:
            return ["ping", "-c", "4", host]

    @staticmethod
    def traceroute_cmd(host: str) -> list:
        if _IS_WIN:
            return ["tracert", host]
        elif _IS_LINUX:
            if shutil.which("traceroute"):
                return ["traceroute", host]
            return ["tracepath", host]
        elif _IS_MAC:
            return ["traceroute", host]
        return ["traceroute", host]

    @staticmethod
    def network_reset_cmds() -> list:
        """Returns list of (label, cmd_list_or_str, shell) tuples."""
        if _IS_WIN:
            return [
                ("winsock reset",   ["netsh", "winsock", "reset"], False),
                ("ip reset",        ["netsh", "int", "ip", "reset"], False),
                ("release ip",      ["ipconfig", "/release"], False),
                ("flush dns",       ["ipconfig", "/flushdns"], False),
            ]
        elif _IS_LINUX:
            cmds = []
            if shutil.which("systemctl"):
                cmds.append(("restart NetworkManager",
                              ["systemctl", "restart", "NetworkManager"], False))
            if shutil.which("ip"):
                cmds.append(("flush ip cache",
                              "ip route flush cache", True))
            if shutil.which("resolvectl"):
                cmds.append(("flush dns",
                              ["resolvectl", "flush-caches"], False))
            return cmds
        elif _IS_MAC:
            return [
                ("flush dns",
                 ["dscacheutil", "-flushcache"], False),
                ("restart mDNSResponder",
                 ["killall", "-HUP", "mDNSResponder"], False),
            ]
        return []

    @staticmethod
    def ipconfig_cmd() -> list:
        if _IS_WIN:
            return ["ipconfig", "/all"]
        else:
            cmds = []
            if shutil.which("ip"):
                return ["ip", "addr", "show"]
            return ["ifconfig", "-a"]

    # ── Junk / temp paths ───────────────────────────────────────
    @staticmethod
    def junk_targets() -> list:
        """Returns list of (path_str, label) tuples."""
        if _IS_WIN:
            return [
                (os.environ.get("TEMP", ""),                                                  "User Temp"),
                (os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Temp"),           "Windows Temp"),
                (os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),                    "LocalAppData Temp"),
                (os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Prefetch"),       "Prefetch"),
                (os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                              r"SoftwareDistribution\Download"),                               "WU Downloads"),
            ]
        elif _IS_LINUX:
            home = str(Path.home())
            targets = [
                ("/tmp",                               "Global /tmp"),
                (f"{home}/.cache",                    "User Cache (~/.cache)"),
                ("/var/tmp",                           "Var Tmp"),
                ("/var/log",                           "System Logs"),
            ]
            if _IS_DEBIAN or _IS_KALI:
                targets.append(("/var/cache/apt/archives", "APT Package Cache"))
            elif _IS_ARCH:
                targets.append(("/var/cache/pacman/pkg",   "Pacman Package Cache"))
            elif _IS_FEDORA:
                targets.append(("/var/cache/dnf",          "DNF Cache"))
            return targets
        elif _IS_MAC:
            home = str(Path.home())
            return [
                ("/private/tmp",             "System /tmp"),
                (f"{home}/Library/Caches",  "User Library Caches"),
                ("/Library/Caches",          "System Library Caches"),
                ("/private/var/log",         "System Logs"),
            ]
        return [("/tmp", "Temp")]

    # ── Package-manager cache clean ─────────────────────────────
    @staticmethod
    def clean_pkg_cache() -> tuple:
        """Returns (ok:bool, msg:str)"""
        if _IS_DEBIAN or _IS_KALI:
            r = subprocess.run(["apt-get", "clean"], capture_output=True)
            r2 = subprocess.run(["apt-get", "autoremove", "-y"], capture_output=True)
            return r.returncode == 0, "apt-get clean + autoremove"
        elif _IS_ARCH:
            if shutil.which("paccache"):
                subprocess.run(["paccache", "-r"], capture_output=True)
            r = subprocess.run(["pacman", "-Sc", "--noconfirm"], capture_output=True)
            return r.returncode == 0, "pacman -Sc cache cleaned"
        elif _IS_FEDORA:
            r = subprocess.run(["dnf", "clean", "all"], capture_output=True)
            return r.returncode == 0, "dnf clean all"
        elif _IS_MAC:
            if shutil.which("brew"):
                subprocess.run(["brew", "cleanup"], capture_output=True)
                return True, "brew cleanup done"
            return False, "Homebrew not found"
        return False, "No supported package manager found"

    # ── Disk cleanup launcher ───────────────────────────────────
    @staticmethod
    def launch_disk_cleanup():
        if _IS_WIN:
            subprocess.Popen(["cleanmgr", "/sagerun:1"])
            return True, "cleanmgr launched"
        elif _IS_LINUX:
            if shutil.which("bleachbit"):
                subprocess.Popen(["bleachbit"])
                return True, "BleachBit launched"
            return False, "BleachBit not found — install with: apt install bleachbit"
        elif _IS_MAC:
            return False, "Use macOS Storage Management (System Settings > General > Storage)"
        return False, "Not available"

    # ── Power plans ─────────────────────────────────────────────
    @staticmethod
    def set_power_plan(plan: str) -> tuple:
        """plan: 'performance' | 'balanced' | 'powersave'"""
        if _IS_WIN:
            guids = {
                "performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
                "balanced":    "381b4222-f694-41f0-9685-ff5bb260df2e",
                "powersave":   "a1841308-3541-4fab-bc81-f71556f20b4a",
            }
            guid = guids.get(plan)
            if not guid:
                return False, "Unknown plan"
            r = subprocess.run(["powercfg", "/setactive", guid], capture_output=True)
            return r.returncode == 0, f"Set to {plan}"
        elif _IS_LINUX:
            governor_map = {
                "performance": "performance",
                "balanced":    "schedutil",
                "powersave":   "powersave",
            }
            gov = governor_map.get(plan, "schedutil")
            cpu_dirs = list(Path("/sys/devices/system/cpu").glob("cpu[0-9]*"))
            ok = False
            for cpu in cpu_dirs:
                gov_path = cpu / "cpufreq" / "scaling_governor"
                if gov_path.exists():
                    try:
                        gov_path.write_text(gov + "\n")
                        ok = True
                    except PermissionError:
                        return False, "Root required to set CPU governor"
            if ok:
                return True, f"CPU governor set to {gov} on {len(cpu_dirs)} cores"
            # Fallback: cpupower
            if shutil.which("cpupower"):
                r = subprocess.run(
                    ["cpupower", "frequency-set", "-g", gov],
                    capture_output=True
                )
                return r.returncode == 0, f"cpupower governor set to {gov}"
            return False, "No CPU frequency scaling support found"
        elif _IS_MAC:
            # macOS manages power automatically; only sleep delay is settable
            delay_map = {"performance": "0", "balanced": "10", "powersave": "5"}
            delay = delay_map.get(plan, "10")
            r = subprocess.run(
                ["pmset", "-a", "sleep", delay],
                capture_output=True
            )
            return r.returncode == 0, f"pmset sleep delay set to {delay} min"
        return False, "Not supported"

    # ── Battery ─────────────────────────────────────────────────
    @staticmethod
    def battery_info() -> dict:
        """Returns dict with keys: percent, plugged, secsleft, available"""
        if not PSUTIL:
            return {"available": False}
        b = psutil.sensors_battery()
        if not b:
            return {"available": False}
        return {
            "available": True,
            "percent":   b.percent,
            "plugged":   b.power_plugged,
            "secsleft":  b.secsleft if b.secsleft and b.secsleft > 0 else None,
        }

    # ── System info ─────────────────────────────────────────────
    @staticmethod
    def get_uptime() -> str:
        if PSUTIL:
            try:
                elapsed = time.time() - psutil.boot_time()
                h = int(elapsed // 3600)
                m = int((elapsed % 3600) // 60)
                return f"{h}h {m}m"
            except Exception:
                pass
        if _IS_LINUX or _IS_MAC:
            try:
                out = subprocess.run(
                    ["uptime", "-p"], capture_output=True, text=True
                ).stdout.strip()
                return out or "N/A"
            except Exception:
                pass
        return "N/A"

    @staticmethod
    def get_extra_info() -> dict:
        """Platform-specific extra fields for System Info panel."""
        info = {}
        if _IS_LINUX:
            info["Distro"] = _DISTRO_NAME
            # Kernel
            try:
                info["Kernel"] = platform.release()
            except Exception:
                pass
            # Package count
            pkg = _count_packages()
            if pkg:
                info["Packages"] = pkg
        elif _IS_MAC:
            info["macOS"] = platform.mac_ver()[0]
            if shutil.which("brew"):
                try:
                    r = subprocess.run(
                        ["brew", "list", "--formula"],
                        capture_output=True, text=True
                    )
                    info["Brew pkgs"] = str(len(r.stdout.splitlines()))
                except Exception:
                    pass
        elif _IS_WIN:
            info["Edition"] = platform.version()
        return info

    # ── Notify ──────────────────────────────────────────────────
    @staticmethod
    def notify(msg: str):
        if _IS_WIN:
            try:
                subprocess.run(["msg", "*", msg], capture_output=True, timeout=5)
            except Exception:
                pass
        elif _IS_LINUX:
            for tool in [
                ["notify-send", "REY STATION", msg],
                ["wall", msg],
            ]:
                if shutil.which(tool[0]):
                    try:
                        subprocess.run(tool, capture_output=True, timeout=5)
                        return
                    except Exception:
                        continue
        elif _IS_MAC:
            try:
                subprocess.run(
                    ["osascript", "-e",
                     f'display notification "{msg}" with title "REY STATION"'],
                    capture_output=True, timeout=5
                )
            except Exception:
                pass


def _count_packages() -> str:
    """Try to count installed packages on Linux."""
    if _IS_DEBIAN or _IS_KALI:
        try:
            r = subprocess.run(["dpkg", "-l"], capture_output=True, text=True)
            return str(len([l for l in r.stdout.splitlines() if l.startswith("ii")]))
        except Exception:
            pass
    elif _IS_ARCH:
        try:
            r = subprocess.run(["pacman", "-Q"], capture_output=True, text=True)
            return str(len(r.stdout.splitlines()))
        except Exception:
            pass
    elif _IS_FEDORA:
        try:
            r = subprocess.run(["rpm", "-qa"], capture_output=True, text=True)
            return str(len(r.stdout.splitlines()))
        except Exception:
            pass
    return ""


# ═══════════════════════════════════════════════════════════════
#  SHARED UTILITIES
# ═══════════════════════════════════════════════════════════════

console = Console()

def clr():
    PlatformAPI.clear()

def pause(msg="   press enter to continue"):
    console.print(f"\n   [color(240)]{msg}[/]")
    input()

def run_cmd(cmd, capture=True, shell=False):
    try:
        if shell and isinstance(cmd, list):
            cmd = " ".join(str(c) for c in cmd)
        r = subprocess.run(
            cmd, capture_output=capture, text=True,
            timeout=120, shell=shell
        )
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "Command timed out", 1
    except Exception as e:
        return str(e), 1

def bytes_to_human(n):
    if n < 0: n = 0
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

def run_power_action(action: str):
    PlatformAPI.notify(f"REY — {action} in ~1 min")
    time.sleep(1)
    if   action == "Shutdown":    PlatformAPI.shutdown()
    elif action == "Restart":     PlatformAPI.restart()
    elif action == "Hibernate":   PlatformAPI.hibernate()
    elif action == "Sleep":       PlatformAPI.suspend()
    elif action == "Lock Screen": PlatformAPI.lock_screen()

# ═══════════════════════════════════════════════════════════════
#  VISUAL CONSTANTS
# ═══════════════════════════════════════════════════════════════

LOGO = (
    "  ██████╗ ██╗   ██╗    ██████╗ ███████╗██╗   ██╗  \n"
    "  ██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔════╝╚██╗ ██╔╝  \n"
    "  ██████╔╝ ╚████╔╝     ██████╔╝█████╗   ╚████╔╝   \n"
    "  ██╔══██╗  ╚██╔╝      ██╔══██╗██╔══╝    ╚██╔╝    \n"
    "  ██████╔╝   ██║       ██║  ██║███████╗   ██║      \n"
    "  ╚═════╝    ╚═╝       ╚═╝  ╚═╝╚══════╝   ╚═╝      "
)

DISCO    = ["#00ffff","#ff00ff","#ffff00","#00ff88","#4488ff",
            "#ff4444","#ffffff","#ff88ff","#88ffff","#ffaa00"]
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
VU_SEQ   = [0,1,3,5,7,9,11,10,8,6,4,2,0,2,5,8,11,11,9,6,3,0]

MODULES = {
    "1": ("⏱  Timer & Power",        "#00ffff"),
    "2": ("🧹  RAM & Cache Cleaner",  "#ff88ff"),
    "3": ("💾  Disk Utilities",        "#ffff00"),
    "4": ("⚙️  Process Manager",      "#00ff88"),
    "5": ("📊  System Monitor",        "#ff8800"),
    "6": ("🌐  Network Tools",         "#4488ff"),
    "7": ("🗑️  Junk File Cleaner",     "#ff4444"),
    "8": ("🔋  Battery & Power",       "#88ffff"),
    "9": ("ℹ️  System Info",           "#ffffff"),
    "a": ("🌀  AFK Mode",              "#cc88ff"),
    "0": ("🚪  Exit",                  "#666666"),
}

# ═══════════════════════════════════════════════════════════════
#  RENDER HELPERS
# ═══════════════════════════════════════════════════════════════

def render_bar(val, total, width=40, color="#00ffff"):
    ratio  = min(val / total, 1.0) if total else 0
    filled = round(ratio * width)
    t = Text()
    t.append("█" * filled,            style=f"bold {color}")
    t.append("░" * (width - filled),  style="color(238)")
    t.append(f"  {ratio*100:5.1f}%",  style="bold white")
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

def logo_panel(color: str, subtitle: str = "V4.0 CROSS-PLATFORM") -> Panel:
    is_root = PlatformAPI.is_admin()
    priv_tag = (
        "[bold #ff4444] ★ ROOT [/]" if is_root and not _IS_WIN else
        "[bold #ff4444] ★ ADMIN [/]" if is_root else
        "[dim] USER [/]"
    )
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "unknown"
    return Panel(
        Align.center(Text(LOGO, style=f"bold {color}")),
        box=box.DOUBLE,
        border_style=color,
        title=f"[dim]{hostname}[/]  [dim {_OS_COLOR}]{_OS_TAG}[/]",
        subtitle=f"{priv_tag} [dim {color}]{subtitle}[/]",
        subtitle_align="right",
        padding=(0, 1),
    )

def section_header(title: str, color: str, subtitle: str = "V4.0"):
    clr()
    console.print(logo_panel(color, subtitle))
    console.print()
    console.print(Rule(f"[bold {color}]  {title}  [/]", style=color, characters="─"))
    console.print()

def make_menu_table(items: dict, color: str) -> Table:
    t = Table.grid(padding=(0, 2))
    t.add_column(style=f"bold {color}", min_width=3,  justify="right")
    t.add_column(style="color(238)",    min_width=1)
    t.add_column(style="white",         min_width=28)
    for k, label in items.items():
        t.add_row(k, "│", label)
    return t

def result_ok(msg):   console.print(f"   [bold #00ff88]✓[/]  {msg}")
def result_fail(msg): console.print(f"   [bold #ff4444]✗[/]  {msg}")
def result_warn(msg): console.print(f"   [bold #ffcc00]![/]  {msg}")

# ═══════════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════════

def main_menu() -> str:
    clr()
    color = "#00ffff"
    console.print(logo_panel(color, f"{_OS_TAG} · V4.0"))
    console.print()
    console.print(Rule(f"[bold {color}]  MAIN MENU  [/]", style=color, characters="═"))
    console.print()

    left_items  = {k: v[0] for k, v in list(MODULES.items())[:5]}
    right_items = {k: v[0] for k, v in list(MODULES.items())[5:]}

    cols = Table.grid(padding=(0, 6))
    cols.add_column(); cols.add_column()
    cols.add_row(make_menu_table(left_items, color),
                 make_menu_table(right_items, color))
    console.print(Align.center(cols))

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
            "CPU",  render_bar(cpu,       100,        14, "#00ff88"),
            "RAM",  render_bar(mem.used,  mem.total,  14, "#ff88ff"),
            "TIME", Text(datetime.now().strftime("%H:%M:%S"), style="bold #00ffff"),
        )
        console.print(Align.center(stats))
    console.print(Rule(style="color(238)", characters="─"))
    console.print()

    return Prompt.ask(
        "   [bold #00ffff]SELECT MODULE >[/]",
        choices=list(MODULES.keys()),
        show_choices=False,
    )

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
    meta.add_column(style=dim, min_width=10)
    meta.add_column(style="bold white", min_width=16)
    meta.add_row("platform", _OS_TAG)
    meta.add_row("session",  "● cross-platform")
    meta.add_row("action",   Text(action.lower(), style=f"bold {color}"))
    meta.add_row("clock",    datetime.now().strftime("%H:%M:%S"))
    meta.add_row("date",     datetime.now().strftime("%Y-%m-%d"))

    clock  = Align.center(Text(f"{hh:02d}:{mm:02d}:{ss:02d}",
                                style=f"bold {color}", justify="center"))
    ratio  = (1 - (timer / total)) if total else 1
    filled = round(ratio * 52)
    prog_t = Text()
    prog_t.append("█" * filled,      style=f"bold {color}")
    prog_t.append("░" * (52-filled), style="color(238)")
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

    gap(); body.add_row(Align.center(meta))
    gap(); sep(); gap()
    body.add_row(clock)
    gap()
    body.add_row(Align.center(prog_t))
    gap()
    body.add_row(Align.center(Text(
        f"  remaining: {hh:02d}h {mm:02d}m {ss:02d}s", style=dim
    )))
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
    console.print(Align.center(make_menu_table({k: v[0] for k, v in durations.items()}, "#00ffff")))
    choice = Prompt.ask("\n   [#00ffff]>[/]", choices=list(durations.keys()), show_choices=False)
    total = IntPrompt.ask("   [#00ffff]Minutes[/]") * 60 if choice == "6" else durations[choice][1]
    total = max(60, total)

    section_header("TIMER · action on complete", "#ff00ff")
    console.print(Align.center(make_menu_table(actions, "#ff00ff")))
    a_choice = Prompt.ask("\n   [#ff00ff]>[/]", choices=list(actions.keys()), show_choices=False)
    action   = actions[a_choice]

    timer = total; tick = 0
    _FRAME = 1 / 60
    _stop  = threading.Event()

    def _countdown():
        nonlocal timer
        while timer > 0 and not _stop.is_set():
            _stop.wait(timeout=1.0)
            if not _stop.is_set():
                timer -= 1
        _stop.set()

    _ct = threading.Thread(target=_countdown, daemon=True)
    _ct.start()

    try:
        with Live(build_timer_screen(timer, total, action, tick),
                  console=console, screen=True) as live:
            while not _stop.is_set() and timer > 0:
                t0 = time.perf_counter()
                live.update(build_timer_screen(timer, total, action, tick))
                tick += 1
                spent = time.perf_counter() - t0
                leftover = _FRAME - spent
                if leftover > 0:
                    time.sleep(leftover)
    except KeyboardInterrupt:
        _stop.set(); return
    _stop.set()

    if action == "Just Notify":
        PlatformAPI.notify("REY STATION — Timer complete!")
        pause("Timer finished! Press enter to return.")
    else:
        run_power_action(action)

# ═══════════════════════════════════════════════════════════════
#  MODULE 2: RAM & CACHE CLEANER
# ═══════════════════════════════════════════════════════════════

def module_ram():
    section_header("RAM & CACHE CLEANER", "#ff88ff")

    mem = psutil.virtual_memory()
    stats = Table.grid(padding=(0, 3))
    stats.add_column(style="color(240)", min_width=14)
    stats.add_column(style="bold white", min_width=10)
    stats.add_column()
    stats.add_row("Total RAM",     bytes_to_human(mem.total), "")
    stats.add_row("Used RAM",      bytes_to_human(mem.used),
                  render_bar(mem.used, mem.total, 30, "#ff4444"))
    stats.add_row("Available RAM", bytes_to_human(mem.available),
                  render_bar(mem.available, mem.total, 30, "#00ff88"))
    stats.add_row("Usage",         f"{mem.percent:.1f}%", "")
    console.print(Align.center(Panel(
        stats, border_style="#ff88ff", box=box.ROUNDED,
        title="[bold #ff88ff]memory snapshot[/]"
    )))
    console.print()

    opts = {
        "1": f"Trim / Drop Process Memory   ({'WinAPI' if _IS_WIN else '/proc/vm  · root' if _IS_LINUX else 'purge'})",
        "2": f"Clear Page/Standby Cache      ({'WinAPI' if _IS_WIN else 'sync+drop_caches · root' if _IS_LINUX else 'purge'})",
        "3": f"Flush DNS Cache               ({'WinAPI' if _IS_WIN else 'resolvectl' if _IS_LINUX else 'dscacheutil'})",
        "4": f"Clear File / OS Cache         ({'BranchCache' if _IS_WIN else 'drop_caches · root' if _IS_LINUX else 'purge'})",
        "5": "Run All Optimizations",
        "0": "Back",
    }
    console.print(Align.center(make_menu_table(opts, "#ff88ff")))
    choice = Prompt.ask("\n   [#ff88ff]>[/]", choices=list(opts.keys()), show_choices=False)
    if choice == "0": return

    mem_before = psutil.virtual_memory()
    console.print()

    with Progress(SpinnerColumn(style="#ff88ff"),
                  TextColumn("[progress.description]{task.description}"),
                  transient=True, console=console) as prog:

        if choice in ("1", "5"):
            t = prog.add_task("Trimming process memory...", total=None)
            count = PlatformAPI.trim_working_sets()
            prog.remove_task(t)
            if count:
                result_ok(f"Memory trim applied to {count} processes")
            else:
                result_fail("Memory trim failed — root/admin required")

        if choice in ("2", "5"):
            t = prog.add_task("Clearing page/standby cache...", total=None)
            ok = PlatformAPI.clear_standby_list()
            prog.remove_task(t)
            if ok: result_ok("Page/standby cache cleared")
            else:   result_fail("Cache clear failed — root/admin required")

        if choice in ("3", "5"):
            t = prog.add_task("Flushing DNS cache...", total=None)
            ok = PlatformAPI.flush_dns()
            prog.remove_task(t)
            if ok: result_ok("DNS cache flushed")
            else:   result_fail("DNS flush failed — root may be required")

        if choice in ("4", "5"):
            t = prog.add_task("Clearing file/OS cache...", total=None)
            ok, msg = PlatformAPI.clear_file_cache()
            prog.remove_task(t)
            if ok: result_ok(msg)
            else:   result_fail(msg)

    mem_after = psutil.virtual_memory()
    freed = max(0, mem_after.available - mem_before.available)
    console.print()
    console.print(Rule(style="color(238)", characters="─"))
    console.print(f"   [dim]Memory freed:[/]     [bold #00ff88]{bytes_to_human(freed)}[/]")
    console.print(f"   [dim]Available after:[/]  [bold #00ff88]{bytes_to_human(mem_after.available)}[/]")
    console.print(f"   [dim]Usage after:[/]      "
                  f"[bold {'#00ff88' if mem_after.percent < 70 else '#ff4444'}]"
                  f"{mem_after.percent:.1f}%[/]")
    pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 3: DISK UTILITIES
# ═══════════════════════════════════════════════════════════════

def module_disk():
    section_header("DISK UTILITIES", "#ffff00")

    t = Table(box=box.ROUNDED, border_style="#ffff00",
              header_style="bold #ffff00", show_lines=False)
    t.add_column("Mount/Drive", style="bold white",  min_width=14)
    t.add_column("FS",          style="color(240)",  min_width=6)
    t.add_column("Total",       style="white",       min_width=10)
    t.add_column("Free",        style="#00ff88",     min_width=10)
    t.add_column("Usage",       min_width=36)
    for p in psutil.disk_partitions():
        try:
            u = psutil.disk_usage(p.mountpoint)
            pct_color = ("#ff4444" if u.percent > 85
                         else "#ffcc00" if u.percent > 65 else "#00ff88")
            t.add_row(
                p.device if _IS_WIN else p.mountpoint,
                p.fstype,
                bytes_to_human(u.total),
                bytes_to_human(u.free),
                render_bar(u.used, u.total, 20, pct_color),
            )
        except Exception:
            continue
    console.print(Align.center(t))
    console.print()

    # Build OS-aware options
    opt1_label = ("Optimize / Defrag" if _IS_WIN
                  else "Trim SSDs (fstrim -av)" if _IS_LINUX
                  else "Disk Utility info (macOS)")
    opt2_label = ("Check Disk Health  (WMI)" if _IS_WIN
                  else "Check Disk Health  (smartctl/lsblk)" if _IS_LINUX
                  else "Verify Volume      (diskutil)")
    opt3_label = ("System File Checker  (sfc · Admin)" if _IS_WIN
                  else "Kernel error log     (dmesg grep)" if _IS_LINUX
                  else "Verify Volume        (diskutil)")
    opt4_label = ("Schedule Chkdsk Boot Scan  (Admin)" if _IS_WIN
                  else "Schedule fsck on next boot" if _IS_LINUX
                  else "Repair Volume (diskutil)")

    opts = {
        "1": opt1_label,
        "2": opt2_label,
        "3": opt3_label,
        "4": opt4_label,
        "0": "Back",
    }
    console.print(Align.center(make_menu_table(opts, "#ffff00")))
    choice = Prompt.ask("\n   [#ffff00]>[/]", choices=list(opts.keys()), show_choices=False)

    if choice == "1":
        cmd, shell = PlatformAPI.optimize_drives()
        if cmd:
            console.print("\n   [dim]Running optimization (may take a while)...[/]\n")
            run_cmd(cmd, capture=False, shell=shell)
        else:
            result_warn("macOS manages defragmentation automatically.")

    elif choice == "2":
        cmd, shell = PlatformAPI.disk_health_cmd()
        if cmd:
            out, rc = run_cmd(cmd, shell=shell)
            console.print(f"\n[bold #ffff00]Disk Health:[/]\n[dim]{out or 'No output'}[/]")
        else:
            result_warn("No disk health tool available")

    elif choice == "3":
        cmd, shell = PlatformAPI.file_system_check()
        if not cmd:
            result_fail("Not available on this platform")
        elif _IS_WIN and not PlatformAPI.is_admin():
            result_fail("Administrator required for SFC")
        else:
            console.print("\n   [dim]Running filesystem check...[/]\n")
            run_cmd(cmd, capture=False, shell=shell)

    elif choice == "4":
        cmd, shell = PlatformAPI.schedule_disk_scan()
        if not cmd:
            result_fail("Not available")
        elif not PlatformAPI.is_admin():
            result_fail("Root/Admin required")
        else:
            result_warn("Scheduling disk scan...")
            run_cmd(cmd, capture=False, shell=shell)

    if choice != "0":
        pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 4: PROCESS MANAGER
# ═══════════════════════════════════════════════════════════════

def module_process():
    section_header("PROCESS MANAGER", "#00ff88")

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
        key   = "cpu_percent" if choice == "1" else "memory_percent"
        procs = []
        for p in psutil.process_iter(
            ['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'username']
        ):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs = sorted(procs, key=lambda x: x.get(key) or 0, reverse=True)[:20]

        t = Table(header_style="bold #00ff88", box=box.ROUNDED,
                  border_style="color(238)", show_lines=False)
        t.add_column("PID",    style="color(240)", min_width=7,  justify="right")
        t.add_column("Name",   style="bold white", min_width=28)
        t.add_column("CPU%",   style="#ff8800",    min_width=8,  justify="right")
        t.add_column("MEM%",   style="#ff88ff",    min_width=8,  justify="right")
        t.add_column("Status", style="color(240)", min_width=10)
        if not _IS_WIN:
            t.add_column("User", style="color(240)", min_width=10)
        for p in procs:
            row = [
                str(p.get('pid', '?')),
                (p.get('name') or 'unknown')[:28],
                f"{p.get('cpu_percent') or 0:.1f}",
                f"{p.get('memory_percent') or 0:.1f}",
                p.get('status', ''),
            ]
            if not _IS_WIN:
                row.append(p.get('username', '')[:10])
            t.add_row(*row)
        console.print(Align.center(t))
        pause()

    elif choice == "3":
        pid = IntPrompt.ask("   [#00ff88]PID to terminate[/]")
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            if Confirm.ask(f"   Terminate [bold]{name}[/] (PID {pid})?"):
                proc.terminate()
                result_ok(f"Sent SIGTERM to {name} (PID {pid})")
        except psutil.NoSuchProcess:
            result_fail(f"No process with PID {pid}")
        except psutil.AccessDenied:
            result_fail("Access denied — run as root/admin")
        except Exception as e:
            result_fail(str(e))
        pause()

    elif choice == "4":
        q = Prompt.ask("   [#00ff88]Process name (partial)[/]").lower()
        matches = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if q in (p.info.get('name') or '').lower():
                    matches.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not matches:
            result_warn(f"No processes matching '{q}'")
        else:
            t = Table(header_style="bold #00ff88", box=box.ROUNDED, border_style="color(238)")
            t.add_column("PID"); t.add_column("Name"); t.add_column("CPU%"); t.add_column("MEM%")
            for p in matches[:15]:
                t.add_row(str(p.get('pid','')), p.get('name',''),
                          f"{p.get('cpu_percent',0):.1f}", f"{p.get('memory_percent',0):.1f}")
            console.print(Align.center(t))
        pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 5: LIVE SYSTEM MONITOR
# ═══════════════════════════════════════════════════════════════

def module_monitor():
    def build_monitor(tick):
        color   = DISCO[tick % len(DISCO)]
        cpu_all = psutil.cpu_percent(percpu=True)
        mem     = psutil.virtual_memory()
        try:
            disk_io = psutil.disk_io_counters()
            net_io  = psutil.net_io_counters()
        except Exception:
            disk_io = net_io = None

        cpu_table = Table.grid(padding=(0, 1))
        cpu_table.add_column(style="color(240)", min_width=8)
        cpu_table.add_column()
        for i, p in enumerate(cpu_all[:8]):
            bc = "#ff4444" if p > 85 else "#ffcc00" if p > 60 else "#00ff88"
            cpu_table.add_row(f"Core {i:>2}", render_bar(p, 100, 26, bc))

        cpu_panel = Panel(cpu_table,
                          title=f"[bold {color}]CPU  {psutil.cpu_percent():.1f}%[/]",
                          border_style=color, box=box.ROUNDED)

        mem_table = Table.grid(padding=(0, 1))
        mem_table.add_column(style="color(240)", min_width=12)
        mem_table.add_column()
        mem_table.add_row("Used",  render_bar(mem.used,      mem.total, 26, "#ff88ff"))
        mem_table.add_row("Free",  render_bar(mem.available, mem.total, 26, "#00ff88"))
        mem_table.add_row("",      "")
        mem_table.add_row("Total", Text(bytes_to_human(mem.total),     style="bold white"))
        mem_table.add_row("Used",  Text(bytes_to_human(mem.used),      style="#ff88ff"))
        mem_table.add_row("Avail", Text(bytes_to_human(mem.available), style="#00ff88"))
        mem_panel = Panel(mem_table,
                          title=f"[bold #ff88ff]RAM  {mem.percent:.1f}%[/]",
                          border_style="#ff88ff", box=box.ROUNDED)

        io_table = Table.grid(padding=(0, 2))
        io_table.add_column(style="color(240)", min_width=12)
        io_table.add_column(style="bold white")
        if disk_io:
            io_table.add_row("Disk Read",  bytes_to_human(disk_io.read_bytes))
            io_table.add_row("Disk Write", bytes_to_human(disk_io.write_bytes))
        if net_io:
            io_table.add_row("Net Sent",   bytes_to_human(net_io.bytes_sent))
            io_table.add_row("Net Recv",   bytes_to_human(net_io.bytes_recv))
        io_panel = Panel(io_table, title="[bold #ffcc00]I/O[/]",
                         border_style="#ffcc00", box=box.ROUNDED)

        top_row = Table.grid(padding=(0, 1))
        top_row.add_column(); top_row.add_column()
        top_row.add_row(cpu_panel, mem_panel)

        body = Table.grid()
        body.add_column()
        body.add_row(logo_panel(color, f"LIVE MONITOR  {datetime.now().strftime('%H:%M:%S')}"))
        body.add_row(top_row)
        body.add_row(io_panel)
        body.add_row(Panel(Text("ctrl+c  →  return to menu",
                                style="color(240)", justify="center"),
                           border_style="color(238)", box=box.SIMPLE))
        return body

    _frame = [build_monitor(0)]
    _stop  = threading.Event()

    def _poller():
        t = 0
        while not _stop.is_set():
            _frame[0] = build_monitor(t)
            t += 1
            _stop.wait(timeout=0.5)

    _pt = threading.Thread(target=_poller, daemon=True)
    _pt.start()
    try:
        with Live(_frame[0], console=console, screen=True) as live:
            while True:
                t0 = time.perf_counter()
                live.update(_frame[0])
                spent = time.perf_counter() - t0
                leftover = (1/60) - spent
                if leftover > 0:
                    time.sleep(leftover)
    except KeyboardInterrupt:
        pass
    finally:
        _stop.set()

# ═══════════════════════════════════════════════════════════════
#  MODULE 6: NETWORK TOOLS
# ═══════════════════════════════════════════════════════════════

def module_network():
    section_header("NETWORK TOOLS", "#4488ff")

    reset_label = ("Network Stack Reset  (Admin · Reboot)" if _IS_WIN
                   else "Restart Network      (NetworkManager · root)" if _IS_LINUX
                   else "Flush DNS + mDNS     (macOS)")
    ip_label    = ("IP Configuration     (ipconfig /all)" if _IS_WIN
                   else "IP Configuration     (ip addr / ifconfig)" if _IS_LINUX
                   else "IP Configuration     (ifconfig / ip)")

    opts = {
        "1": "Ping Host",
        "2": "Traceroute",
        "3": reset_label,
        "4": ip_label,
        "5": "Port Scan  (local ports)",
        "0": "Back",
    }
    console.print(Align.center(make_menu_table(opts, "#4488ff")))
    choice = Prompt.ask("\n   [#4488ff]>[/]", choices=list(opts.keys()), show_choices=False)

    if choice == "1":
        host = Prompt.ask("   [#4488ff]Host[/]", default="8.8.8.8")
        console.print()
        run_cmd(PlatformAPI.ping_cmd(host), capture=False)

    elif choice == "2":
        host = Prompt.ask("   [#4488ff]Host[/]", default="8.8.8.8")
        console.print()
        run_cmd(PlatformAPI.traceroute_cmd(host), capture=False)

    elif choice == "3":
        if not PlatformAPI.is_admin():
            result_fail("Root/Admin required for network reset")
        elif Confirm.ask("   [bold #ff4444]Reset/restart networking?[/]"):
            for label, cmd, shell in PlatformAPI.network_reset_cmds():
                out, rc = run_cmd(cmd, shell=shell)
                if rc == 0: result_ok(label)
                else:        result_warn(f"{label} — {out[:60]}")
            if _IS_WIN:
                result_warn("Reboot required to complete network reset")

    elif choice == "4":
        out, _ = run_cmd(PlatformAPI.ipconfig_cmd())
        console.print(f"\n[dim]{out}[/]")

    elif choice == "5":
        console.print("\n   [dim]Scanning common local ports...[/]\n")
        common_ports = [21,22,23,25,53,80,110,143,443,445,3389,8080,8443]
        services = {21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",
                    110:"POP3",143:"IMAP",443:"HTTPS",445:"SMB",3389:"RDP",
                    8080:"HTTP-Alt",8443:"HTTPS-Alt"}
        t = Table(header_style="bold #4488ff", box=box.ROUNDED, border_style="color(238)")
        t.add_column("Port", justify="right", min_width=6)
        t.add_column("Service", min_width=12)
        t.add_column("Status",  min_width=10)
        for port in common_ports:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                    status = Text("OPEN",   style="bold #00ff88")
            except Exception:
                status = Text("closed", style="color(238)")
            t.add_row(str(port), services.get(port, ""), status)
        console.print(Align.center(t))

    if choice != "0":
        pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 7: JUNK FILE CLEANER
# ═══════════════════════════════════════════════════════════════

def module_junk():
    section_header("JUNK FILE CLEANER", "#ff4444")

    targets = PlatformAPI.junk_targets()
    scan_table = Table(header_style="bold #ff4444", box=box.ROUNDED, border_style="color(238)")
    scan_table.add_column("Folder",  style="white",     min_width=20)
    scan_table.add_column("Path",    style="color(240)",min_width=36)
    scan_table.add_column("Size",    style="#ffcc00",   min_width=10)
    scan_table.add_column("Files",   style="color(240)",min_width=8)

    for path, label in targets:
        if not path or not os.path.exists(path):
            scan_table.add_row(label, path[:36] if path else "—", "—", "—")
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
        scan_table.add_row(label, path[:36], bytes_to_human(total_size), str(file_count))

    console.print(Align.center(scan_table))
    console.print()

    cleanup_label = ("Clean pkg cache  (apt/pacman/dnf/brew)" if _IS_LINUX or _IS_MAC
                     else "Run Disk Cleanup  (cleanmgr)")
    trash_label   = ("Empty Trash  (~/.local/share/Trash)" if _IS_LINUX
                     else "Empty Trash  (~/.Trash)" if _IS_MAC
                     else "Empty Recycle Bin  (WinAPI)")

    opts = {
        "1": "Clean All Junk Folders  (listed above)",
        "2": trash_label,
        "3": cleanup_label,
        "0": "Back",
    }
    console.print(Align.center(make_menu_table(opts, "#ff4444")))
    choice = Prompt.ask("\n   [#ff4444]>[/]", choices=list(opts.keys()), show_choices=False)

    if choice == "1":
        total_freed = 0; failed = 0
        for path, label in targets:
            if not path or not os.path.exists(path): continue
            console.print(f"   [dim]Cleaning {label}...[/]")
            for root, dirs, files in os.walk(path):
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        total_freed += os.path.getsize(fp)
                        os.remove(fp)
                    except Exception:
                        failed += 1
        console.print()
        result_ok(f"Freed {bytes_to_human(total_freed)}")
        if failed:
            result_warn(f"{failed} files skipped (locked / permission denied)")

    elif choice == "2":
        if PlatformAPI.empty_trash():
            result_ok("Trash emptied successfully")
        else:
            result_fail("Failed to empty trash (may already be empty or permission denied)")

    elif choice == "3":
        if _IS_LINUX or _IS_MAC:
            if not PlatformAPI.is_admin() and (_IS_LINUX):
                result_warn("Some package caches may need root — attempting anyway")
            ok, msg = PlatformAPI.clean_pkg_cache()
            if ok: result_ok(msg)
            else:   result_fail(msg)
        else:
            ok, msg = PlatformAPI.launch_disk_cleanup()
            if ok: result_ok(msg)
            else:   result_fail(msg)

    if choice != "0":
        pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 8: BATTERY & POWER
# ═══════════════════════════════════════════════════════════════

def module_battery():
    section_header("BATTERY & POWER", "#88ffff")

    bat = PlatformAPI.battery_info()
    if bat.get("available"):
        pct       = bat["percent"]
        plugged   = bat["plugged"]
        secsleft  = bat.get("secsleft")
        bar_color = "#00ff88" if pct > 50 else "#ffcc00" if pct > 20 else "#ff4444"
        status_text = (
            "[bold #00ff88]⚡ PLUGGED IN[/]"
            if plugged else
            "[bold #ffcc00]🔋 ON BATTERY[/]"
        )
        bt = Table.grid(padding=(0, 3))
        bt.add_column(style="color(240)", min_width=14)
        bt.add_column()
        bt.add_row("Status", Text.from_markup(status_text))
        bt.add_row("Level",  render_bar(pct, 100, 30, bar_color))
        bt.add_row("",       Text(f"{pct:.0f}%", style=f"bold {bar_color}"))
        if secsleft and not plugged:
            h, r = divmod(secsleft, 3600); m = r // 60
            bt.add_row("Remaining", Text(f"{h}h {m}m", style="bold white"))
        console.print(Align.center(Panel(
            bt, border_style="#88ffff", box=box.ROUNDED,
            title="[bold #88ffff]battery status[/]"
        )))
    else:
        result_warn("No battery detected (desktop system)")

    console.print()

    # Power plans — labels adapt per OS
    if _IS_WIN:
        plans = {"1": "High Performance", "2": "Balanced", "3": "Power Saver"}
    elif _IS_LINUX:
        plans = {"1": "Performance  (governor: performance)",
                 "2": "Balanced     (governor: schedutil)",
                 "3": "Power Save   (governor: powersave)"}
    else:
        plans = {"1": "Performance  (pmset sleep 0)",
                 "2": "Balanced     (pmset sleep 10)",
                 "3": "Power Save   (pmset sleep 5)"}

    plan_keys = {"1": "performance", "2": "balanced", "3": "powersave"}
    opts = {**plans, "0": "Back"}
    console.print(Align.center(make_menu_table(opts, "#88ffff")))
    choice = Prompt.ask("\n   [#88ffff]>[/]", choices=list(opts.keys()), show_choices=False)

    if choice in plan_keys:
        ok, msg = PlatformAPI.set_power_plan(plan_keys[choice])
        if ok: result_ok(msg)
        else:   result_fail(msg)
        pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE 9: SYSTEM INFO
# ═══════════════════════════════════════════════════════════════

def module_sysinfo():
    section_header("SYSTEM INFORMATION", "#ffffff")

    try:    hostname = socket.gethostname()
    except: hostname = "unknown"
    try:    local_ip = socket.gethostbyname(hostname)
    except: local_ip = "unknown"
    try:    username = os.getlogin()
    except: username = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))

    t = Table.grid(padding=(0, 3))
    t.add_column(style="color(240)", min_width=18)
    t.add_column(style="bold white")
    t.add_row("OS",           platform.platform())
    t.add_row("Architecture", platform.machine())
    t.add_row("Processor",    platform.processor()[:60] or "N/A")
    t.add_row("Python",       platform.python_version())
    t.add_row("Platform Tag", _OS_TAG)
    t.add_row("Hostname",     hostname)
    t.add_row("Local IP",     local_ip)
    t.add_row("User",         username)
    t.add_row("Privileged",
              "[bold #00ff88]Yes[/]" if PlatformAPI.is_admin() else "[bold #ff4444]No[/]")

    # Extra platform-specific fields
    for k, v in PlatformAPI.get_extra_info().items():
        t.add_row(k, str(v))

    if PSUTIL:
        mem  = psutil.virtual_memory()
        freq = None
        try:
            freq = psutil.cpu_freq()
        except Exception:
            pass
        t.add_row("Total RAM",  bytes_to_human(mem.total))
        t.add_row("CPU Cores",
                  f"{psutil.cpu_count(logical=False)} physical / {psutil.cpu_count()} logical")
        if freq:
            t.add_row("CPU Freq",  f"{freq.current:.0f} MHz (max {freq.max:.0f} MHz)")
    t.add_row("Uptime", PlatformAPI.get_uptime())

    console.print(Align.center(Panel(
        t, border_style="#ffffff", box=box.ROUNDED, title="[bold]system info[/]"
    )))
    console.print()

    # Export option
    if _IS_WIN:
        export_label = "Export Report  (msinfo32)"
    elif _IS_LINUX:
        export_label = "Export Report  (inxi / uname / lshw → report.txt)"
    else:
        export_label = "Export Report  (system_profiler → report.txt)"

    opts = {"1": export_label, "0": "Back"}
    console.print(Align.center(make_menu_table(opts, "#ffffff")))
    choice = Prompt.ask("\n   [#ffffff]>[/]", choices=list(opts.keys()), show_choices=False)

    if choice == "1":
        if _IS_WIN:
            try:
                subprocess.Popen(["msinfo32"])
                result_ok("msinfo32 launched")
            except Exception as e:
                result_fail(str(e))
        else:
            report_path = Path.home() / "rey_sysreport.txt"
            try:
                with open(report_path, "w") as fh:
                    fh.write(f"REY STATION — System Report\n")
                    fh.write(f"Generated: {datetime.now()}\n")
                    fh.write(f"{'='*60}\n\n")
                    fh.write(f"Platform: {platform.platform()}\n")
                    fh.write(f"Hostname: {hostname}\n")
                    fh.write(f"User: {username}\n")
                    fh.write(f"Uptime: {PlatformAPI.get_uptime()}\n\n")
                    # Try inxi, lshw, uname fallbacks
                    for tool_cmd, label in [
                        (["inxi", "-Fxz"],         "inxi -Fxz"),
                        (["lshw", "-short"],        "lshw -short"),
                        (["uname", "-a"],           "uname -a"),
                        (["lscpu"],                 "lscpu"),
                        (["free", "-h"],            "free -h"),
                        (["df", "-h"],              "df -h"),
                    ]:
                        if shutil.which(tool_cmd[0]):
                            r = subprocess.run(tool_cmd, capture_output=True, text=True)
                            fh.write(f"--- {label} ---\n{r.stdout}\n\n")
                result_ok(f"Report saved to {report_path}")
            except Exception as e:
                result_fail(str(e))
        pause()

# ═══════════════════════════════════════════════════════════════
#  MODULE A: AFK MODE  (pure visual · zero side-effects)
# ═══════════════════════════════════════════════════════════════

def _afk_scene_matrix(tick: int, w: int = 72) -> Text:
    CHARS = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789"
    random.seed(tick)
    lines = []
    for row in range(14):
        line = Text()
        for col in range(w // 2):
            ch    = random.choice(CHARS)
            depth = (tick // 2 + col * 3 + row * 7) % 20
            if   depth == 0: st = "bold white"
            elif depth <  4: st = "bold #00ff88"
            elif depth <  9: st = "#006622"
            else:             st = "color(234)"
            line.append(ch + " ", style=st)
        lines.append(line)
    combined = Text()
    for l in lines:
        combined.append_text(l)
        combined.append("\n")
    return combined

def _afk_scene_starfield(tick: int, w: int = 72, h: int = 14) -> Text:
    random.seed(42)
    stars = [(random.uniform(-1,1), random.uniform(-1,1), random.random()) for _ in range(80)]
    speed = 0.018
    out_chars  = [[" "]       * w for _ in range(h)]
    out_styles = [["color(234)"] * w for _ in range(h)]
    for sx, sy, sz in stars:
        z = (sz - (tick * speed)) % 1.0
        if z < 0.01: continue
        scale = 1.0 / z
        px = int(w/2 + sx * scale * (w/4))
        py = int(h/2 + sy * scale * (h/2))
        if 0 <= px < w and 0 <= py < h:
            b = 1.0 - z
            if   b > 0.85: ch, st = "★", "bold white"
            elif b > 0.65: ch, st = "·", "bold #aaaaff"
            elif b > 0.40: ch, st = "·", "#555588"
            else:           ch, st = ".", "color(236)"
            out_chars[py][px]  = ch
            out_styles[py][px] = st
    result = Text()
    for r in range(h):
        for c in range(w):
            result.append(out_chars[r][c], style=out_styles[r][c])
        result.append("\n")
    return result

def _afk_scene_plasma(tick: int, w: int = 72, h: int = 14) -> Text:
    PCOLS = ["#ff0055","#ff4400","#ffaa00","#ffff00",
             "#00ff88","#00ffff","#0088ff","#8800ff","#ff00ff","#ff0055"]
    result = Text()
    for row in range(h):
        for col in range(w):
            v = (math.sin(col*0.18+tick*0.07) + math.sin(row*0.35+tick*0.05) +
                 math.sin((col+row)*0.12+tick*0.09) +
                 math.sin(math.sqrt(((col-w/2)**2+(row-h/2)**2))*0.18+tick*0.06))
            idx = max(0, min(int((v+4)/8*(len(PCOLS)-1)), len(PCOLS)-1))
            result.append("█", style=PCOLS[idx])
        result.append("\n")
    return result

def _afk_scene_clock(tick: int) -> Text:
    DIGITS = {
        "0":["███","█ █","█ █","█ █","███"],"1":[" █ "," █ "," █ "," █ "," █ "],
        "2":["███","  █","███","█  ","███"],"3":["███","  █","███","  █","███"],
        "4":["█ █","█ █","███","  █","  █"],"5":["███","█  ","███","  █","███"],
        "6":["███","█  ","███","█ █","███"],"7":["███","  █","  █","  █","  █"],
        "8":["███","█ █","███","█ █","███"],"9":["███","█ █","███","  █","███"],
        ":":[" "," ","●"," ","●"] if tick%2==0 else [" "," "," "," "," "],
    }
    now = datetime.now()
    color = DISCO[tick % len(DISCO)]
    rows = [""] * 5
    for ch in now.strftime("%H:%M:%S"):
        pat = DIGITS.get(ch, ["   "]*5)
        for i in range(5):
            rows[i] += pat[i] + "  "
    result = Text("\n\n")
    for row in rows:
        result.append("  " + row + "\n", style=f"bold {color}")
    result.append("\n")
    result.append(f"  {now.strftime('%A, %d %B %Y')}".center(52)+"\n", style=f"dim {color}")
    if PSUTIL:
        try:
            elapsed = int(time.time() - psutil.boot_time())
            h,r = divmod(elapsed,3600); m=r//60; s=r%60
            result.append(f"  uptime  {h:02d}:{m:02d}:{s:02d}".center(52)+"\n", style="color(240)")
        except Exception: pass
    return result

def _afk_scene_syswatch(tick: int) -> Text:
    color = DISCO[tick % len(DISCO)]
    result = Text()
    result.append(f"  system whisper  ·  {_OS_TAG}  ·  read-only\n\n", style=f"dim {color}")
    if not PSUTIL:
        result.append("  psutil unavailable\n", style="color(240)")
        return result
    cpu_all = psutil.cpu_percent(percpu=True)
    mem     = psutil.virtual_memory()
    result.append("  cpu cores\n", style=f"bold {color}")
    for i, p in enumerate(cpu_all[:8]):
        bc    = "#ff4444" if p > 85 else "#ffcc00" if p > 60 else "#00ff88"
        filled = round(p / 100 * 40)
        result.append(f"    {i:>2}  ", style="color(240)")
        result.append("█"*filled + "░"*(40-filled), style=bc)
        result.append(f"  {p:5.1f}%\n", style="bold white")
    result.append("\n  memory\n", style=f"bold {color}")
    filled = round(mem.percent / 100 * 40)
    bc = "#ff4444" if mem.percent>85 else "#ffcc00" if mem.percent>65 else "#00ff88"
    result.append(f"    used  ", style="color(240)")
    result.append("█"*filled + "░"*(40-filled), style=bc)
    result.append(f"  {mem.percent:5.1f}%\n", style="bold white")
    result.append(f"    {bytes_to_human(mem.used)} / {bytes_to_human(mem.total)}\n", style="color(240)")
    return result

def _afk_scene_quotes(tick: int) -> Text:
    QUOTES = [
        ("The best way to predict the future is to invent it.", "Alan Kay"),
        ("Any sufficiently advanced technology is indistinguishable from magic.", "Arthur C. Clarke"),
        ("Simplicity is the soul of efficiency.", "Austin Freeman"),
        ("First, solve the problem. Then, write the code.", "John Johnson"),
        ("Make it work, make it right, make it fast.", "Kent Beck"),
        ("The computer was born to solve problems that did not exist before.", "Bill Gates"),
        ("Code is like humour. When you have to explain it, it's bad.", "Cory House"),
        ("It's not a bug — it's an undocumented feature.", "Anonymous"),
        ("There are only two hard things in CS: cache invalidation and naming things.", "Phil Karlton"),
        ("Talk is cheap. Show me the code.", "Linus Torvalds"),
        ("Debugging is twice as hard as writing the code in the first place.", "Brian W. Kernighan"),
        ("Any fool can write code that a computer can understand.", "Martin Fowler"),
    ]
    color = DISCO[tick % len(DISCO)]
    q, author = QUOTES[(tick // 6) % len(QUOTES)]
    words = q.split(); lines = []; cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > 58:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    result = Text("\n\n\n")
    result.append("  ❝\n\n", style=f"bold {color}")
    for line in lines:
        result.append(f"    {line}\n", style="bold white")
    result.append(f"\n    — {author}\n", style=f"dim {color}")
    return result

_AFK_SCENES = [
    ("MATRIX RAIN",    _afk_scene_matrix),
    ("STAR WARP",      _afk_scene_starfield),
    ("PLASMA WAVE",    _afk_scene_plasma),
    ("CLOCK",          _afk_scene_clock),
    ("SYSTEM WHISPER", _afk_scene_syswatch),
    ("QUOTES",         _afk_scene_quotes),
]

def module_afk():
    section_header("AFK MODE · choose a scene", "#cc88ff")
    scene_opts = {str(i+1): name for i, (name, _) in enumerate(_AFK_SCENES)}
    scene_opts["r"] = "Random rotation  (auto-switches every 12s)"
    scene_opts["0"] = "Back"
    console.print(Align.center(make_menu_table(scene_opts, "#cc88ff")))
    console.print()
    console.print(Align.center(Text(
        "AFK mode is read-only — it never writes, deletes, or modifies anything.",
        style="dim"
    )))
    console.print()
    choice = Prompt.ask("   [#cc88ff]>[/]", choices=list(scene_opts.keys()), show_choices=False)
    if choice == "0": return

    rotating  = (choice == "r")
    scene_idx = 0 if rotating else int(choice) - 1
    tick = 0; scene_tick = 0
    _FRAME = 1 / 60; _SCENE_TICKS = 12 * 60

    def build_frame(tick, scene_idx, rotating):
        name, fn = _AFK_SCENES[scene_idx % len(_AFK_SCENES)]
        color    = DISCO[tick % len(DISCO)]
        content  = fn(tick)
        info     = Table.grid(padding=(0, 3))
        info.add_column(style=f"bold {color}", min_width=20)
        info.add_column(style="color(240)",    min_width=20)
        info.add_column(style="color(240)")
        nxt = _AFK_SCENES[(scene_idx+1) % len(_AFK_SCENES)][0] if rotating else "—"
        info.add_row(f"◈  {name}", f"tick {tick:>5}",
                     f"next → {nxt}" if rotating else "ctrl+c  exit")
        body = Table.grid()
        body.add_column()
        body.add_row(Panel(content, border_style=color, box=box.ROUNDED, padding=(0,1)))
        body.add_row(Panel(Align.center(info),
                           border_style="color(236)", box=box.SIMPLE, padding=(0,1)))
        body.add_row(Panel(Align.center(Text("ctrl+c  →  return to menu", style="color(238)")),
                           border_style="color(234)", box=box.SIMPLE, padding=(0,0)))
        root = Table.grid()
        root.add_column()
        root.add_row(logo_panel(color, f"AFK MODE · {name}"))
        root.add_row(body)
        return root

    try:
        with Live(build_frame(0, scene_idx, rotating),
                  console=console, screen=True) as live:
            while True:
                t0 = time.perf_counter()
                live.update(build_frame(tick, scene_idx, rotating))
                tick += 1; scene_tick += 1
                if rotating and scene_tick >= _SCENE_TICKS:
                    scene_idx += 1; scene_tick = 0
                spent = time.perf_counter() - t0
                leftover = _FRAME - spent
                if leftover > 0:
                    time.sleep(leftover)
    except KeyboardInterrupt:
        pass

# ═══════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════

def main():
    if not PlatformAPI.is_admin():
        clr()
        priv_word = "root" if not _IS_WIN else "Administrator"
        console.print(Panel(
            f"[bold #ffcc00]Running without {priv_word} privileges.[/]\n\n"
            "Some features will be limited:\n"
            "  [dim]·[/] RAM/cache operations requiring elevated access\n"
            "  [dim]·[/] Disk scan / filesystem check\n"
            "  [dim]·[/] Network stack reset\n"
            "  [dim]·[/] CPU governor changes (Linux)\n\n"
            f"[dim]{'Right-click → Run as administrator' if _IS_WIN else 'Re-run with sudo'} for full access.[/]",
            title=f"[bold #ffcc00]⚠  LIMITED MODE  ·  {_OS_TAG}[/]",
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
                border_style="#00ffff", box=box.DOUBLE, padding=(1, 6),
            ))
            break
        if choice in dispatch:
            try:
                dispatch[choice]()
            except KeyboardInterrupt:
                pass
            except Exception as e:
                result_fail(f"Unexpected error: {e}")
                pause()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
