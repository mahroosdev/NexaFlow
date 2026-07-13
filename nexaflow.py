#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║     NexaFlow — Professional Desktop Automation Studio      ║
║     Complete Edition · Record · Replay · Events · Schedule       ║
╚══════════════════════════════════════════════════════════════════╝
Self-installs all dependencies. Works on Windows.
"""

import sys, os, subprocess, threading, time, json, shutil, re, glob, struct, webbrowser, queue
from pathlib import Path
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo, available_timezones
except Exception:
    ZoneInfo = None
    def available_timezones():
        return []
try:
    from recorder_core import Recorder as CoreRecorder
except Exception:
    CoreRecorder = None
try:
    from remote_host import RemoteHost
except Exception:
    RemoteHost = None
from remote_access import (
    firewall_repair_script,
    firewall_rule_spec,
    inspect_firewall_rule,
)

SUPPORT_URL = "https://web-nexaflow.netlify.app/support"
PRIVACY_URL = "https://web-nexaflow.netlify.app/privacy"


def _support_url():
    return SUPPORT_URL


def _privacy_url():
    return PRIVACY_URL

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   TKINTER GUARD  — must run before everything else
#   tkinter ships with the official python.org installer but is
#   absent from the Microsoft Store Python and some minimal builds.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _check_tkinter():
    try:
        import tkinter  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    msg = (
        "NexaFlow requires tkinter, which is missing from your Python install.\n\n"
        "This usually means you installed Python from the Microsoft Store\n"
        "or used a minimal installer that omitted the Tk/Tcl component.\n\n"
        "HOW TO FIX:\n"
        "  1. Uninstall the current Python (Settings → Apps → Python).\n"
        "  2. Download the FULL installer from  https://www.python.org/downloads/\n"
        "  3. During install, make sure \"tcl/tk and IDLE\" is checked.\n"
        "  4. Run NexaFlow again.\n\n"
        "The browser will open python.org for you now."
    )

    if sys.platform == 'win32':
        # Show a native Windows message box — requires no dependencies
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0, msg,
                "NexaFlow — Missing tkinter",
                0x10  # MB_ICONERROR
            )
        except Exception:
            print(msg)
        try:
            import webbrowser
            webbrowser.open("https://www.python.org/downloads/")
        except Exception:
            pass
    else:
        # Non-Windows fallback: print to terminal and open the installer page.
        print("\n" + "=" * 60)
        print(msg)
        print("=" * 60 + "\n")
        try:
            import webbrowser
            webbrowser.open("https://www.python.org/downloads/")
        except Exception:
            pass

        # Also try OS-level alerts as a fallback
        if sys.platform == 'darwin':
            subprocess.Popen([
                'osascript', '-e',
                f'display alert "NexaFlow — Missing tkinter" message "{msg[:200]}"'
            ])

    sys.exit(1)

_check_tkinter()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   AUTO-INSTALL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEPS = ['pynput', 'pyperclip', 'Pillow']

def _pip(pkg):
    try:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', pkg,
             '--quiet', '--disable-pip-version-check'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"pip install failed for {pkg}: {exc}") from exc


def _check_deps():
    required = DEPS
    missing  = []
    import_map = {'Pillow': 'PIL'}
    for d in required:
        imp = import_map.get(d, d)
        try:    __import__(imp)
        except ImportError: missing.append(d)
    if not missing:
        return
    try:
        import tkinter as _tk
        splash = _tk.Tk()
        splash.title("NexaFlow — First Run Setup")
        splash.geometry("420x130")
        splash.configure(bg="#050508")
        splash.resizable(False, False)
        splash.attributes('-topmost', True)
        _tk.Label(splash, text="⚡  NexaFlow", bg="#050508",
                  fg="#00f5d4", font=("Segoe UI", 15, "bold")).pack(pady=(16, 3))
        msg = _tk.Label(splash, text="Initializing environment…",
                        bg="#050508", fg="#8892a4", font=("Segoe UI", 9))
        msg.pack()
        pb_frame = _tk.Frame(splash, bg="#050508")
        pb_frame.pack(fill='x', padx=32, pady=8)
        canvas = _tk.Canvas(pb_frame, height=3, bg="#0d0d14", highlightthickness=0)
        canvas.pack(fill='x')
        splash.update()
        for idx, d in enumerate(missing):
            msg.config(text=f"Installing {d}  ({idx+1}/{len(missing)})…")
            pct = idx / len(missing)
            w   = canvas.winfo_width() or 356
            canvas.delete('all')
            canvas.create_rectangle(0, 0, int(w * pct), 3, fill="#00f5d4", outline='')
            splash.update()
            _pip(d)
        splash.destroy()
    except Exception:
        for d in missing:
            print(f"[NexaFlow] Installing {d}...")
            _pip(d)

_check_deps()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   IMPORTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

HAS_PYPERCLIP = False
HAS_PYNPUT   = False
pyperclip    = None
pm           = None
pk           = None
Button       = None
MCtrl        = None
Key          = None
KCtrl        = None

try:
    import pyperclip
    HAS_PYPERCLIP = True
except Exception:
    pyperclip = None

try:
    from pynput import mouse as pm, keyboard as pk
    from pynput.mouse import Button, Controller as MCtrl
    from pynput.keyboard import Key, Controller as KCtrl
    HAS_PYNPUT = True
except Exception:
    pm = None
    pk = None
    Button = None
    MCtrl = None
    Key = None
    KCtrl = None

try:
    from PIL import ImageGrab, Image as PilImage, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Optional system tray
try:
    import pystray
    from PIL import Image as _PILImg, ImageDraw as _PILDraw
    HAS_TRAY = True
except Exception:
    HAS_TRAY = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _copy_to_clipboard(text):
    if not HAS_PYPERCLIP or not text:
        return False
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def _type_text_with_keyboard(keyboard, text):
    if not keyboard or not text:
        return False
    try:
        keyboard.type(text)
        return True
    except Exception:
        for ch in text:
            try:
                keyboard.press(ch)
                keyboard.release(ch)
            except Exception:
                pass
        return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   PLATFORM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   THEMES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THEMES = {
    'light': {
        'bg':      "#fbfdff",
        'panel':   "#ffffff",
        'card':    "#ffffff",
        'card2':   "#f1f5f9",
        'card3':   "#e6eef6",
        'border':  "#e6eef6",
        'border2': "#d1e8ef",
        'accent':  "#06b6d4",
        'accent2': "#0891b2",
        'accent3': "#0ea5a4",
        'amber':   "#f59e0b",
        'amber2':  "#cc9200",
        'red':     "#ef4444",
        'red2':    "#cc2244",
        'green':   "#059669",
        'green2':  "#047857",
        'blue':    "#2563eb",
        'blue2':   "#1e40af",
        'purple':  "#7c3aed",
        'purple2': "#5b21b6",
        'orange':  "#fb923c",
        'text':    "#0f172a",
        'text2':   "#475569",
        'muted':   "#64748b",
        'dim':     "#e2e8f0",
    },
    'dark': {
        'bg':      "#050505",
        'panel':   "#0c0c0c",
        'card':    "#131313",
        'card2':   "#1d1d1d",
        'card3':   "#232323",
        'border':  "#222222",
        'border2': "#2f2f2f",
        'accent':  "#38bdf8",
        'accent2': "#0ea5e9",
        'accent3': "#22d3ee",
        'amber':   "#f59e0b",
        'amber2':  "#d97706",
        'red':     "#f87171",
        'red2':    "#dc2626",
        'green':   "#34d399",
        'green2':  "#10b981",
        'blue':    "#60a5fa",
        'blue2':   "#3b82f6",
        'purple':  "#a78bfa",
        'purple2': "#8b5cf6",
        'orange':  "#fb923c",
        'text':    "#f8fafc",
        'text2':   "#cbd5e1",
        'muted':   "#94a3b8",
        'dim':     "#1f2937",
    },
}

C = THEMES['light'].copy()

def _set_theme(name):
    if name not in THEMES:
        name = 'light'
    vals = THEMES[name]
    C.clear()
    C.update(vals)

_SYS = "Segoe UI"         if IS_WIN else "SF  Display"
_MON = "Consolas"         if IS_WIN else "Menlo"
_HED = "Segoe UI Semibold" if IS_WIN else "SF  Display"

def _f(size=9, bold=False, mono=False):
    fam = _MON if mono else (_HED if bold else _SYS)
    w   = "bold" if bold else "normal"
    return (fam, size, w)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   CONFIG MANAGER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ConfigManager:
    """Persists user preferences, recent files, and window state."""
    def __init__(self):
        self._dir  = Path.home() / ".nexaflow"
        self._dir.mkdir(exist_ok=True)
        self._path = self._dir / "config.json"
        self._data = self._load()

    def _load(self):
        try:
            with open(self._path, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self):
        try:
            with open(self._path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def add_recent(self, path: str):
        recent = self._data.get('recent', [])
        path   = str(Path(path).resolve())
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self._data['recent'] = recent[:12]
        self.save()

    def get_recent(self):
        return [p for p in self._data.get('recent', []) if Path(p).exists()]

    def remove_recent(self, path: str):
        recent = self._data.get('recent', [])
        if path in recent:
            recent.remove(path)
        self._data['recent'] = recent
        self.save()


CFG = ConfigManager()

_set_theme(CFG.get('theme', 'light'))


LOCAL_TIMEZONE = 'local'
LOCAL_TIMEZONE_LABEL = 'Local / System time'


def _get_local_timezone_label():
    try:
        local = datetime.now().astimezone().tzinfo
        if local is not None:
            if getattr(local, 'key', None):
                return local.key
            if getattr(local, 'zone', None):
                return local.zone
            name = getattr(local, 'tzname', None)
            if callable(name):
                name = name(None)
            if isinstance(name, str) and name:
                return name
            return str(local)
    except Exception:
        pass
    return 'Local'


def _get_default_timezone():
    return LOCAL_TIMEZONE


def _get_zone(tz_name):
    if not tz_name or tz_name in (LOCAL_TIMEZONE, LOCAL_TIMEZONE_LABEL):
        return None
    if ZoneInfo is None:
        return None
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return None


def _normalize_timezone_choice(tz_name):
    if not tz_name or tz_name in (LOCAL_TIMEZONE, LOCAL_TIMEZONE_LABEL):
        return LOCAL_TIMEZONE, None
    zone = _get_zone(tz_name)
    if zone:
        return zone.key if getattr(zone, 'key', None) else tz_name, zone
    return LOCAL_TIMEZONE, None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ACTIVITY LOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ActivityLog:
    def __init__(self):
        self._entries   = []
        self._listeners = []
        self._lock      = threading.Lock()

    def add(self, msg, level='info'):
        ts    = datetime.now().strftime("%H:%M:%S")
        entry = (ts, level, msg)
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > 1000:
                self._entries = self._entries[-800:]
            listeners = list(self._listeners)
        for cb in listeners:
            try: cb(entry)
            except: pass

    def subscribe(self, cb):
        with self._lock:
            self._listeners.append(cb)

    def unsubscribe(self, cb):
        with self._lock:
            self._listeners = [l for l in self._listeners if l is not cb]

    def clear(self):
        with self._lock:
            self._entries = []

    def get_all(self):
        with self._lock:
            return list(self._entries)

    def get_filtered(self, level=None):
        with self._lock:
            if not level or level == 'all':
                return list(self._entries)
            return [e for e in self._entries if e[1] == level]


LOG = ActivityLog()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   RECORDER ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class RecorderEngine:
    def __init__(self, on_event=None):
        self.events     = []
        self.recording  = False
        self.playing    = False
        self.paused     = False
        self._stop_flag = False
        self._pause_ev  = threading.Event()
        self._pause_ev.set()
        self._t0        = 0.0
        self._ml = self._kl = None
        self._mc = MCtrl() if HAS_PYNPUT else None
        self._kc = KCtrl() if HAS_PYNPUT else None
        self._pressed_buttons = set()
        self._pressed_keys = set()
        self._pressed_modifiers = set()
        self._synthetic_input_until = 0.0
        self.on_event   = on_event
        self.name       = "untitled"
        self.notes      = ""

    def start(self, smart=True):
        # Prefer shared CoreRecorder if available
        if CoreRecorder is not None:
            try:
                self._recorder = CoreRecorder()
                self._recorder.start()
                self.recording = True
                # point events to shared list
                self.events = self._recorder.events
                LOG.add(f"Recording started (CoreRecorder)", 'record')
                return
            except Exception as exc:
                LOG.add(f"CoreRecorder failed: {exc}", 'error')

        # Fallback to local pynput listeners
        self.events   = []
        self.recording = True
        self._t0      = time.time()
        self._last_mv = 0.0
        self._pressed_modifiers = set()
        smart_mode    = smart

        if not HAS_PYNPUT:
            self.recording = False
            LOG.add("Recording unavailable: pynput is not installed or could not be loaded.", 'error')
            return

        def ts():
            return round(time.time() - self._t0, 4)

        def on_click(x, y, btn, pressed):
            if not self.recording: return False
            self._add(dict(t='click', x=x, y=y, btn=str(btn),
                           pressed=pressed, ts=ts()))

        def on_move(x, y):
            if not self.recording or smart_mode: return
            now = time.time()
            if now - self._last_mv < 0.04: return
            self._last_mv = now
            self._add(dict(t='move', x=x, y=y, ts=ts()))

        def on_scroll(x, y, dx, dy):
            if not self.recording: return
            self._add(dict(t='scroll', x=x, y=y, dx=dx, dy=dy, ts=ts()))

        def on_press(k):
            if not self.recording: return
            self._add(dict(t='kd', k=self._ks(k, pressed=True), ts=ts()))

        def on_release(k):
            if not self.recording: return
            self._add(dict(t='ku', k=self._ks(k, pressed=False), ts=ts()))

        self._ml = pm.Listener(on_click=on_click, on_move=on_move, on_scroll=on_scroll)
        self._kl = pk.Listener(on_press=on_press, on_release=on_release)
        try:
            self._ml.start()
            self._kl.start()
            LOG.add(f"Recording started ({'Smart' if smart else 'Full'} mode)", 'record')
        except Exception as exc:
            self.recording = False
            LOG.add(f"Recording start failed: {exc}", 'error')

    def stop(self):
        # Stop shared recorder if present
        try:
            if getattr(self, '_recorder', None):
                try: self._recorder.stop()
                except: pass
        except Exception:
            pass

        self.recording = False
        if getattr(self, '_ml', None):
            try: self._ml.stop()
            except: pass
        if getattr(self, '_kl', None):
            try: self._kl.stop()
            except: pass
        LOG.add(f"Recording stopped — {len(self.events)} events captured", 'record')

    def _add(self, e):
        self.events.append(e)
        if self.on_event:
            self.on_event(len(self.events))

    def _track_modifier(self, k, pressed=True):
        token = str(k).replace('Key.', '').lower()
        groups = {
            'ctrl': ('ctrl', 'ctrl_l', 'ctrl_r'),
            'shift': ('shift', 'shift_l', 'shift_r'),
            'alt': ('alt', 'alt_l', 'alt_r', 'alt_gr'),
            'cmd': ('cmd', 'cmd_l', 'cmd_r'),
        }
        for name, values in groups.items():
            if token in values:
                if pressed:
                    self._pressed_modifiers.add(name)
                else:
                    self._pressed_modifiers.discard(name)
                return True
        return False

    def _ks(self, k, pressed=True):
        self._track_modifier(k, pressed=pressed)
        try:
            ch = k.char
        except AttributeError:
            ch = None
        if ch:
            code = ord(ch) if len(ch) == 1 else 0
            if 'ctrl' in self._pressed_modifiers and 1 <= code <= 26:
                return chr(code + 96)
            return ch
        return str(k)

    def insert_wait(self, seconds: float, index: int = -1):
        """Insert a synthetic wait event at position."""
        ev = dict(t='wait', secs=round(seconds, 3), ts=0.0)
        if index < 0 or index >= len(self.events):
            self.events.append(ev)
        else:
            self.events.insert(index, ev)
        LOG.add(f"Wait event inserted ({seconds}s)", 'record')

    def insert_type_text(self, text: str, index: int = -1):
        """Insert a type-text macro event."""
        ev = dict(t='type', text=text, ts=0.0)
        if index < 0 or index >= len(self.events):
            self.events.append(ev)
        else:
            self.events.insert(index, ev)
        LOG.add(f"Type-text event inserted: {text[:30]}", 'record')

    def delete_event(self, index: int):
        if 0 <= index < len(self.events):
            self.events.pop(index)

    def play(self, mode='once', count=1, delay=1.0, speed=1.0,
             on_prog=None, on_loop=None, on_done=None):
        if not self.events:
            if on_done:
                try:
                    on_done()
                except Exception:
                    pass
            return
        if self.playing:
            self.halt()
            time.sleep(0.05)
        if self.recording or (getattr(self, '_recorder', None) and getattr(self._recorder, 'recording', False)):
            LOG.add("Playback blocked while recording is active.", 'warn')
            self.stop()
        self._stop_flag = False
        self._pressed_buttons.clear()
        self._pressed_keys.clear()
        self._pause_ev.set()
        self.paused  = False
        self.playing = True

        def run():
            try:
                n = 0
                while not self._stop_flag:
                    n += 1
                    self._play_once(speed, on_prog)
                    if self._stop_flag: break
                    if on_loop: on_loop(n)
                    if   mode == 'once':    break
                    elif mode == 'count':
                        if n >= count: break
                        self._sleep(delay)
                    elif mode == 'infinite': self._sleep(delay)
            finally:
                self.playing = False
                if on_done and not self._stop_flag:
                    try:
                        on_done()
                    except Exception:
                        pass

        threading.Thread(target=run, daemon=True).start()

    def _play_once(self, speed, on_prog):
        total = len(self.events)
        # Detect whether timestamps are absolute (Unix epoch) and normalize to relative
        base = 0.0
        if total and self.events[0].get('ts', 0) > 1e5:
            base = self.events[0]['ts']
        prev = 0.0
        for i, e in enumerate(self.events):
            if self._stop_flag: return
            self._pause_ev.wait()
            if self._stop_flag: return
            ts = e.get('ts', 0) - base
            gap = (ts - prev) / max(speed, 0.1)
            if gap > 0: self._sleep(gap)
            prev = ts
            self._exec(e)
            if on_prog: on_prog(i + 1, total)

    def _sleep(self, sec):
        end = time.time() + sec
        while time.time() < end:
            if self._stop_flag: return
            self._pause_ev.wait()
            time.sleep(0.01)

    def _exec(self, e):
        if not HAS_PYNPUT:
            return
        self._mark_synthetic_input()
        t = e['t']
        if   t == 'move':
            self._mc.position = (e['x'], e['y'])
        elif t == 'scroll':
            self._mc.position = (e['x'], e['y'])
            self._mc.scroll(e['dx'], e['dy'])
        elif t == 'click':
            self._mc.position = (e['x'], e['y'])
            b = Button.left if 'left' in e['btn'] else (
                Button.right if 'right' in e['btn'] else Button.middle)
            btn_name = 'left' if b == Button.left else ('right' if b == Button.right else 'middle')
            if e['pressed']:
                self._pressed_buttons.add(btn_name)
                try: self._mc.press(b)
                except Exception: pass
            else:
                self._pressed_buttons.discard(btn_name)
                try: self._mc.release(b)
                except Exception: pass
        elif t == 'kd':
            k = self._pk(e['k'])
            if k:
                try:
                    self._kc.press(k)
                    self._pressed_keys.add(str(k))
                except: pass
        elif t == 'ku':
            k = self._pk(e['k'])
            if k:
                try:
                    self._kc.release(k)
                    self._pressed_keys.discard(str(k))
                except: pass
        elif t == 'wait':
            self._sleep(e.get('secs', 1.0))
        elif t == 'type':
            text = e.get('text', '')
            if _copy_to_clipboard(text) and self._kc:
                time.sleep(0.05)
                self._mark_synthetic_input(0.8)
                with self._kc.pressed(Key.ctrl):
                    self._kc.press('v')
                    self._kc.release('v')
            elif self._kc:
                self._mark_synthetic_input(max(0.4, min(2.0, len(text) * 0.03)))
                _type_text_with_keyboard(self._kc, text)
            else:
                LOG.add("Type event skipped: no keyboard controller available.", 'error')
        self._mark_synthetic_input()

    def _mark_synthetic_input(self, duration=0.35):
        self._synthetic_input_until = max(self._synthetic_input_until, time.time() + duration)

    def is_synthetic_input_active(self):
        return time.time() < self._synthetic_input_until

    def _pk(self, s):
        if not s: return None
        if len(s) == 1: return s
        try:   return getattr(Key, s.replace('Key.', ''))
        except AttributeError: return None

    def _release_inputs(self):
        try:
            if self._mc:
                for btn_name in list(self._pressed_buttons):
                    try:
                        b = Button.left if btn_name == 'left' else (
                            Button.right if btn_name == 'right' else Button.middle)
                        self._mc.release(b)
                    except Exception:
                        pass
                self._pressed_buttons.clear()
        except Exception:
            pass
        try:
            if self._kc:
                for key in list(self._pressed_keys):
                    try:
                        k = self._pk(key)
                        if k:
                            self._kc.release(k)
                    except Exception:
                        pass
                self._pressed_keys.clear()
        except Exception:
            pass

    def halt(self):
        self._release_inputs()
        self._stop_flag = True
        self.playing = False
        self._pause_ev.set()
        self.paused = False

    def toggle_pause(self):
        if self.paused:
            self.paused = False
            self._pause_ev.set()
            LOG.add("Playback resumed", 'play')
        else:
            self.paused = True
            self._pause_ev.clear()
            LOG.add("Playback paused", 'play')

    def save(self, path):
        meta = {
            'v':        5,
            'name':     self.name,
            'notes':    self.notes,
            'created':  datetime.now().isoformat(),
            'count':    len(self.events),
            'duration': round(self.events[-1]['ts'], 2) if self.events else 0,
            'events':   self.events,
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2)
        except (IOError, OSError) as exc:
            LOG.add(f"Failed to save workflow: {exc}", 'error')
            raise
        CFG.add_recent(path)
        LOG.add(f"Workflow saved: {Path(path).name}", 'file')

    def load(self, path):
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
        self.events = d.get('events', [])
        self.name   = d.get('name', Path(path).stem)
        self.notes  = d.get('notes', '')
        CFG.add_recent(path)
        LOG.add(f"Workflow loaded: {Path(path).name}  ({len(self.events)} events)", 'file')
        return len(self.events)

    def duration(self):
        real = [e['ts'] for e in self.events if e.get('ts', 0) > 0]
        return round(real[-1], 2) if real else 0.0

    def summary(self):
        types = {}
        for e in self.events:
            types[e['t']] = types.get(e['t'], 0) + 1
        return types


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   DATA LOOP ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DataLoopEngine:
    def __init__(self, rec: RecorderEngine):
        self._rec       = rec
        self._stop      = False
        self.last_index = 0

    def run(self, items, pre_delay, post_delay, speed,
            start_from=0, on_item=None, on_done=None):
        self._stop      = False
        self.last_index = start_from

        def loop():
            for i, item in enumerate(items[start_from:], start=start_from):
                if self._stop: break
                if not self._rec.events:
                    LOG.add("Data loop playback aborted: no workflow loaded", 'warn')
                    if on_done: on_done()
                    return
                while self._rec.playing and not self._stop:
                    time.sleep(0.05)
                if self._stop: break
                self.last_index = i
                if not _copy_to_clipboard(item.strip()):
                    LOG.add("Clipboard unavailable — data loop cannot paste text reliably.", 'warn')
                    if on_done: on_done()
                    return
                LOG.add(f"Data loop item {i+1}/{len(items)}: {item.strip()[:40]}", 'data')
                if on_item: on_item(i + 1, len(items), item.strip())
                time.sleep(pre_delay)
                done_ev = threading.Event()
                self._rec.play(mode='once', speed=speed,
                               on_done=lambda ev=done_ev: ev.set())
                if not done_ev.wait(timeout=600) and self._rec.playing:
                    self._rec.halt()
                time.sleep(post_delay)
            if on_done: on_done()

        threading.Thread(target=loop, daemon=True).start()

    def halt(self):
        self._stop = True
        self._rec.halt()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   FILE ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class FileEngine:

    @staticmethod
    def scan(folder, ext='*'):
        p = Path(folder)
        if ext and ext != '*':
            return sorted(p.glob(f"*.{ext.lstrip('.')}"))
        return sorted(f for f in p.iterdir() if f.is_file())

    @staticmethod
    def rename(files, prefix='', suffix='', find='', replace='',
               date_prefix=False, counter=False, counter_start=1):
        done = []
        for idx, f in enumerate(files):
            stem = f.stem
            if find: stem = stem.replace(find, replace or '')
            dp = datetime.now().strftime("%Y%m%d_") if date_prefix else ''
            ct = f"_{str(counter_start + idx).zfill(3)}" if counter else ''
            new = f.parent / f"{dp}{prefix}{stem}{suffix}{ct}{f.suffix}"
            if new != f and not new.exists():
                f.rename(new)
                done.append(f.name)
        return done

    @staticmethod
    def move(files, dest):
        d = Path(dest); d.mkdir(parents=True, exist_ok=True)
        done = []
        for f in files:
            target = d / f.name
            if target.exists():
                stem = f.stem
                for n in range(1, 999):
                    candidate = d / f"{stem}_{n}{f.suffix}"
                    if not candidate.exists():
                        target = candidate; break
            shutil.move(str(f), str(target))
            done.append(f.name)
        return done

    @staticmethod
    def sort_by_type(folder):
        done = []
        for f in Path(folder).iterdir():
            if not f.is_file(): continue
            sub = f.parent / (f.suffix.lstrip('.').upper() or 'OTHER')
            sub.mkdir(exist_ok=True)
            target = sub / f.name
            if not target.exists():
                shutil.move(str(f), str(target))
                done.append(f.name)
        return done

    @staticmethod
    def sort_by_date(folder):
        done = []
        for f in Path(folder).iterdir():
            if not f.is_file(): continue
            dt  = datetime.fromtimestamp(f.stat().st_mtime)
            sub = f.parent / dt.strftime("%Y-%m")
            sub.mkdir(exist_ok=True)
            target = sub / f.name
            if not target.exists():
                shutil.move(str(f), str(target))
                done.append(f.name)
        return done

    @staticmethod
    def copy(files, dest):
        d = Path(dest); d.mkdir(parents=True, exist_ok=True)
        done = []
        for f in files:
            target = d / f.name
            if target.exists():
                stem = f.stem
                for n in range(1, 999):
                    candidate = d / f"{stem}_{n}{f.suffix}"
                    if not candidate.exists():
                        target = candidate; break
            shutil.copy2(str(f), str(target))
            done.append(f.name)
        return done

    @staticmethod
    def delete(files):
        done = []
        for f in files:
            try:
                f.unlink()
                done.append(f.name)
            except: pass
        return done


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   SCHEDULER ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class SchedulerEngine:
    def __init__(self, rec: RecorderEngine):
        self._rec      = rec
        self._jobs     = []
        self._thread   = None
        self._stop     = False
        self._lock     = threading.Lock()
        self._id_seq   = 0
        self._done_ev  = None

    def add_job(self, name, run_at, mode, repeat_sec=0, loop_count=1, speed=1.0):
        self._id_seq += 1
        job = {
            'id':         self._id_seq,
            'name':       name,
            'run_at':     run_at,
            'mode':       mode,
            'repeat_sec': repeat_sec,
            'loop_count': loop_count,
            'speed':      speed,
            'enabled':    True,
            'last_run':   None,
            'run_count':  0,
        }
        with self._lock:
            self._jobs.append(job)
        LOG.add(f"Scheduler job added: {name} at {run_at.strftime('%H:%M:%S')}", 'sched')
        self._ensure_running()
        return job

    def remove_job(self, job_id):
        with self._lock:
            self._jobs = [j for j in self._jobs if j['id'] != job_id]

    def toggle_job(self, job_id):
        with self._lock:
            for j in self._jobs:
                if j['id'] == job_id:
                    j['enabled'] = not j['enabled']
                    return j['enabled']
        return None

    def get_jobs(self):
        with self._lock:
            return sorted(list(self._jobs), key=lambda j: j['run_at'])

    def _ensure_running(self):
        if self._thread and self._thread.is_alive(): return
        self._stop   = False
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while not self._stop:
            with self._lock:
                jobs = list(self._jobs)
            for job in jobs:
                if not job['enabled']: continue
                now = datetime.now(job['run_at'].tzinfo) if job['run_at'].tzinfo else datetime.now()
                if job['run_at'] <= now:
                    job['last_run']   = now
                    job['run_count'] += 1
                    LOG.add(f"Scheduler running: {job['name']}", 'sched')
                    self._done_ev = threading.Event()
                    self._rec.play(
                        mode='count', count=job['loop_count'],
                        speed=job['speed'],
                        on_done=lambda ev=self._done_ev: ev.set())
                    self._done_ev.wait(timeout=3600)
                    self._done_ev = None
                    if job['mode'] == 'repeat' and job['repeat_sec'] > 0:
                        job['run_at'] = now + timedelta(seconds=job['repeat_sec'])
                    else:
                        job['enabled'] = False
            time.sleep(1)

    def stop(self):
        self._stop = True
        self._rec.halt()
        if self._done_ev is not None:
            self._done_ev.set()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   UI HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _entry(parent, var, w=None, **kw):
    opts = dict(
        textvariable=var,
        bg=C['card2'], fg=C['text'],
        insertbackground=C['accent'],
        relief='flat', font=_f(9), bd=0,
        highlightthickness=1,
        highlightbackground=C['border2'],
        highlightcolor=C['accent'],
    )
    opts.update(kw)
    if w: opts['width'] = w
    return tk.Entry(parent, **opts)

def _lbl(parent, text, size=9, bold=False, color=None, **kw):
    return tk.Label(parent, text=text, bg=C['bg'],
                    fg=color or C['text2'], font=_f(size, bold), **kw)

def _clbl(parent, text, size=9, bold=False, color=None, bg=None, **kw):
    return tk.Label(parent, text=text,
                    bg=bg or C['card'],
                    fg=color or C['text'], font=_f(size, bold), **kw)

def _sep(parent, color=None, height=1):
    return tk.Frame(parent, bg=color or C['border'], height=height)

def _card(parent, **kw):
    return tk.Frame(parent, bg=C['card'], **kw)

def _section_header(parent, text, color=None, icon=''):
    row = tk.Frame(parent, bg=C['bg'])
    if icon:
        tk.Label(row, text=icon, bg=C['bg'], fg=color or C['accent'],
                 font=_f(9)).pack(side='left', padx=(0, 4))
    tk.Label(row, text=text.upper(), bg=C['bg'],
             fg=color or C['accent'], font=_f(7, True)).pack(side='left')
    return row

def _scroll_text(parent, height=5, **kw):
    frame = tk.Frame(parent, bg=C['card'], highlightthickness=1,
                     highlightbackground=C['border2'])
    sb = tk.Scrollbar(frame, orient='vertical', bg=C['panel'],
                      troughcolor=C['card'], relief='flat', width=6)
    t  = tk.Text(frame, height=height, bg=C['card'], fg=C['text'],
                 insertbackground=C['accent'], relief='flat',
                 font=_f(8, mono=True), padx=10, pady=8,
                 wrap='none', yscrollcommand=sb.set,
                 selectbackground=C['accent3'], selectforeground=C['text'], **kw)
    sb.config(command=t.yview)
    sb.pack(side='right', fill='y')
    t.pack(side='left', fill='both', expand=True)
    return frame, t


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ICON GENERATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _make_icon_image(size=64):
    """Generate the NexaFlow app icon: cyan lightning on a black background.

    Rendered at 4x and downsampled with LANCZOS so the bolt edges are smooth
    (anti-aliased) instead of jagged/blurry at small taskbar/tray sizes.
    """
    scale = 4
    s = size * scale
    img  = PilImage.new('RGBA', (s, s), (5, 5, 8, 255))
    draw = ImageDraw.Draw(img)
    # Lightning bolt polygon
    pts  = [
        (s*(13/24), s*(2/24)),
        (s*(3/24),  s*(14/24)),
        (s*(12/24), s*(14/24)),
        (s*(11/24), s*(22/24)),
        (s*(21/24), s*(10/24)),
        (s*(12/24), s*(10/24)),
        (s*(13/24), s*(2/24)),
    ]
    draw.polygon(pts, fill=(0, 245, 212, 255))
    if scale != 1:
        img = img.resize((size, size), PilImage.LANCZOS)
    return img

def _make_ico(dest: Path):
    """Write a multi-size .ico file next to the script.

    Frames are built largest-first so the ICO stores each size at its native
    resolution (a smallest-first order makes PIL upscale a tiny frame, producing
    a blurry, few-hundred-byte icon).
    """
    if not HAS_PIL: return None
    try:
        sizes = (256, 128, 64, 48, 32, 16)
        imgs = [_make_icon_image(sz) for sz in sizes]
        imgs[0].save(str(dest), format='ICO',
                     sizes=[(sz, sz) for sz in sizes],
                     append_images=imgs[1:])
        return dest
    except Exception as e:
        LOG.add(f"Icon creation failed: {e}", 'error')
        return None


def _app_icon_path():
    """Return the shared multi-resolution NexaFlow lightning icon."""
    base_dir = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
    candidates = [
        base_dir / "nexaflow.ico",
        Path(sys.executable).with_name("nexaflow.ico"),
        Path(__file__).with_name("nexaflow.ico"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    target = Path(__file__).with_name("nexaflow.ico")
    if HAS_PIL:
        _make_ico(target)
    return target


def _apply_tk_titlebar_icon(win, ico_path: Path = None):
    """Apply the NexaFlow lightning icon to Tk and child windows."""
    try:
        app_icon = Path(ico_path) if ico_path else _app_icon_path()
        if IS_WIN and app_icon.exists():
            try:
                win.iconbitmap(default=str(app_icon))
            except Exception:
                try:
                    win.iconbitmap(str(app_icon))
                except Exception:
                    pass
        try:
            from PIL import ImageTk
            icon_photo = ImageTk.PhotoImage(PilImage.open(str(app_icon)).resize((32, 32)))
            win._nexaflow_icon_photo = icon_photo
            win.iconphoto(True, icon_photo)
        except Exception:
            pass
    except Exception:
        pass


def _set_windows_app_identity():
    """Give Windows a stable identity so the taskbar uses NexaFlow's icon."""
    if not IS_WIN:
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "NexaFlow.v1.0.Desktop"
        )
    except Exception:
        pass


def _apply_windows_window_icon(win, ico_path: Path = None):
    """Apply the same NexaFlow identity to the native title bar and taskbar."""
    if not IS_WIN:
        return
    try:
        import ctypes
        app_icon = Path(ico_path) if ico_path else _app_icon_path()
        _apply_tk_titlebar_icon(win, app_icon)

        def apply_titlebar_icon():
            try:
                child_hwnd = win.winfo_id()
                hwnd = ctypes.windll.user32.GetParent(child_hwnd) or child_hwnd
                SWP_NOSIZE = 0x0001
                SWP_NOMOVE = 0x0002
                SWP_NOZORDER = 0x0004
                SWP_FRAMECHANGED = 0x0020
                icon_small = 0
                icon_big = 0
                if app_icon.exists():
                    load_image = ctypes.windll.user32.LoadImageW
                    load_image.restype = ctypes.c_void_p
                    icon_small = load_image(
                        0, str(app_icon), 1, 16, 16, 0x00000010
                    )
                    icon_big = load_image(
                        0, str(app_icon), 1, 32, 32, 0x00000010
                    )
                if icon_small or icon_big:
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, icon_small or icon_big)
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, icon_big or icon_small)
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 2, icon_small or icon_big)
                    win._nexaflow_icon_handles = (icon_small, icon_big)
                else:
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, 0)
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, 0)
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 2, 0)
                ctypes.windll.user32.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
                )
                ctypes.windll.user32.DrawMenuBar(hwnd)
            except Exception:
                pass

        apply_titlebar_icon()
        try:
            win.after(0, apply_titlebar_icon)
            win.after(100, apply_titlebar_icon)
            win.after(800, apply_titlebar_icon)
            win.after(2000, apply_titlebar_icon)
        except Exception:
            pass
    except Exception:
        pass


def _show_centered_child(win, parent, width=None, height=None):
    """Position a child window over its parent before making it visible."""
    try:
        win.update_idletasks()
        parent.update_idletasks()
        child_w = int(width or win.winfo_reqwidth())
        child_h = int(height or win.winfo_reqheight())
        parent_w = max(1, parent.winfo_width())
        parent_h = max(1, parent.winfo_height())
        x = parent.winfo_rootx() + ((parent_w - child_w) // 2)
        y = parent.winfo_rooty() + ((parent_h - child_h) // 2)
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        x = max(0, min(x, max(0, screen_w - child_w)))
        y = max(0, min(y, max(0, screen_h - child_h)))
        win.geometry(f"{child_w}x{child_h}+{x}+{y}")
    except Exception:
        pass
    try:
        win.deiconify()
        win.lift()
    except Exception:
        pass


_CLICK_THROUGH_STYLES = {}


def _set_window_click_through(win, enabled=True):
    """Let playback clicks pass through NexaFlow windows on Windows."""
    if not IS_WIN:
        return
    try:
        import ctypes
        hwnd = win.winfo_id()
        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_LAYERED = 0x00080000
        get_style = ctypes.windll.user32.GetWindowLongPtrW
        set_style = ctypes.windll.user32.SetWindowLongPtrW
        cur = get_style(hwnd, GWL_EXSTYLE)
        if enabled:
            _CLICK_THROUGH_STYLES.setdefault(hwnd, cur)
            set_style(hwnd, GWL_EXSTYLE, cur | WS_EX_TRANSPARENT | WS_EX_LAYERED)
        else:
            original = _CLICK_THROUGH_STYLES.pop(hwnd, None)
            if original is not None:
                set_style(hwnd, GWL_EXSTYLE, original)
            else:
                set_style(hwnd, GWL_EXSTYLE, cur & ~WS_EX_TRANSPARENT)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x27)
    except Exception:
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   FOCUS MODE WINDOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class FocusModeWindow(tk.Toplevel):
    """Compact always-on-top command center for daily recording/playback."""
    def __init__(self, parent, rec, on_rec, on_play, on_pause, on_stop):
        super().__init__(parent)
        _apply_windows_window_icon(self)
        self.withdraw()
        self.overrideredirect(True)
        self.title("Focus Mode")
        self.geometry("370x330")
        self.minsize(350, 315)
        self._rec = rec
        self._on_rec = on_rec
        self._on_play = on_play
        self._on_pause = on_pause
        self._on_stop = on_stop
        self._parent = parent
        self._drag_x = 0
        self._drag_y = 0
        self._pulse_on = False
        self._message_override_until = 0
        self._message_override = ""
        self._countdown_override_until = 0
        
        # Transparency
        self._opacity = max(0.05, min(1.0, CFG.get('focus_mode_opacity', 0.95)))
        CFG.set('focus_mode_opacity', self._opacity)
        self.attributes('-topmost', True)
        try:
            self.attributes('-alpha', self._opacity)
        except Exception:
            pass
        
        # Background
        self.configure(bg=C['card'])
        
        # Custom title bar: removes the duplicated native title/maximize controls.
        titlebar = tk.Frame(self, bg=C['card2'], height=34)
        titlebar.pack(fill='x')
        titlebar.pack_propagate(False)

        tk.Label(titlebar, text="⚡", bg=C['card2'], fg=C['accent'],
                 font=_f(12, True)).pack(side='left', padx=(10, 4), pady=5)
        tk.Label(titlebar, text="Focus Mode", bg=C['card2'], fg=C['text'],
                 font=_f(10, True)).pack(side='left', padx=(0, 10), pady=6)
        self._close_btn = tk.Button(titlebar, text="✕", bg=C['card2'], fg=C['text2'],
                                    font=_f(10, True), relief='flat', bd=0, padx=8,
                                    command=self._exit_focus_mode)
        self._close_btn.pack(side='right', padx=(0, 6), pady=3)
        self._mini_btn = tk.Button(titlebar, text="—", bg=C['card2'], fg=C['text2'],
                                   font=_f(10, True), relief='flat', bd=0, padx=8,
                                   command=self._minimize)
        self._mini_btn.pack(side='right', padx=(0, 2), pady=3)
        self._settings_btn = tk.Button(titlebar, text="⚙", bg=C['card2'], fg=C['text2'],
                                       font=_f(10, True), relief='flat', bd=0, padx=8,
                                       command=self._open_focus_settings)
        self._settings_btn.pack(side='right', padx=(0, 2), pady=3)
        
        # Make title bar draggable
        titlebar.bind('<Button-1>', self._drag_start)
        titlebar.bind('<B1-Motion>', self._drag_motion)
        
        body = tk.Frame(self, bg=C['card'])
        body.pack(fill='both', expand=True, padx=10, pady=8)

        status_row = tk.Frame(body, bg=C['card'])
        status_row.pack(fill='x')
        self._status_dot = tk.Label(status_row, text="●", bg=C['card'], fg=C['green'], font=_f(12, True))
        self._status_dot.pack(side='left')
        self._status_lbl = tk.Label(status_row, text="Ready", bg=C['card'], fg=C['text'],
                                    font=_f(11, True))
        self._status_lbl.pack(side='left', padx=(6, 0))
        self._hint_lbl = tk.Label(status_row, text="F9 Rec/Stop  ·  F10 Play  ·  F11 Stop", bg=C['card'],
                                  fg=C['muted'], font=_f(7))
        self._hint_lbl.pack(side='right')

        countdown_row = tk.Frame(body, bg=C['card'], height=24)
        countdown_row.pack(fill='x', pady=(5, 0))
        countdown_row.pack_propagate(False)
        countdown_row.columnconfigure(0, weight=1)
        countdown_row.columnconfigure(1, weight=0)
        self._countdown_lbl = tk.Label(countdown_row, text="", bg=C['card'])
        self._countdown_lbl.grid(row=0, column=0, sticky='ew')
        self._countdown_num_lbl = tk.Label(countdown_row, text="", bg=C['card2'], fg=C['accent'],
                                           font=_f(12, True), anchor='center',
                                           highlightbackground=C['border'], highlightthickness=1,
                                           width=5)
        self._countdown_num_lbl.grid(row=0, column=1, sticky='e', padx=(8, 0))

        self._workflow_lbl = tk.Label(body, text="No workflow loaded", bg=C['card'], fg=C['muted'],
                                      font=_f(8), anchor='w')
        self._workflow_lbl.pack(fill='x', pady=(5, 6))

        stats = tk.Frame(body, bg=C['card'])
        stats.pack(fill='x', pady=(0, 8))
        self._events_value = self._make_stat(stats, "Events", "0", C['red'])
        self._duration_value = self._make_stat(stats, "Duration", "0.0 s", C['accent'])
        self._size_value = self._make_stat(stats, "Size", "0 KB", C['blue'])

        btn_frame = tk.Frame(body, bg=C['card'])
        btn_frame.pack(fill='x')
        self._rec_btn = self._make_compact_btn(btn_frame, 'REC', C['red'], self._run_rec)
        self._rec_btn.grid(row=0, column=0, sticky='ew', padx=(0, 5), pady=(0, 6))
        self._play_btn = self._make_compact_btn(btn_frame, 'PLAY', C['green'], self._run_play)
        self._play_btn.grid(row=0, column=1, sticky='ew', padx=(5, 0), pady=(0, 6))
        self._pause_btn = self._make_compact_btn(btn_frame, 'PAUSE', C['amber'], self._run_pause)
        self._pause_btn.grid(row=1, column=0, sticky='ew', padx=(0, 5))
        self._stop_btn = self._make_compact_btn(btn_frame, 'STOP', C['text2'], self._run_stop)
        self._stop_btn.grid(row=1, column=1, sticky='ew', padx=(5, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        message_box = tk.Frame(body, bg=C['card2'], height=30)
        message_box.pack(fill='x', pady=(8, 0))
        message_box.pack_propagate(False)
        self._message_lbl = tk.Label(message_box, text="Ready to record or play.",
                                     bg=C['card2'], fg=C['muted'], font=_f(7), anchor='w')
        self._message_lbl.pack(fill='both', expand=True, padx=8)
        
        # Save position
        self.protocol('WM_DELETE_WINDOW', self._exit_focus_mode)
        self.bind('<Map>', lambda e: self.after(80, self._restore_override))
        self.after(100, self._load_position)
        self.after(150, self._refresh)
        self.deiconify()
        self.lift()
        self.focus_force()
        self.after(200, lambda: self.attributes('-topmost', True))
    
    def _make_compact_btn(self, parent, text, color, cmd):
        btn = tk.Button(parent, text=text, bg=color, fg='white', font=_f(9, True),
                       relief='flat', bd=0, padx=10, pady=10, cursor='hand2',
                       command=cmd, activebackground=color, activeforeground='white')
        return btn

    def _make_stat(self, parent, label, value, color):
        box = tk.Frame(parent, bg=C['card2'], highlightbackground=C['border'], highlightthickness=1)
        box.pack(side='left', expand=True, fill='x', padx=3)
        tk.Label(box, text=value, bg=C['card2'], fg=color, font=_f(12, True)).pack(pady=(6, 0))
        value_lbl = box.winfo_children()[0]
        tk.Label(box, text=label.upper(), bg=C['card2'], fg=C['muted'], font=_f(6)).pack(pady=(0, 6))
        return value_lbl

    def _open_focus_settings(self):
        if getattr(self, '_settings_win', None) and self._settings_win.winfo_exists():
            self._settings_win.lift()
            return

        win = tk.Toplevel(self)
        win.withdraw()
        self._settings_win = win
        win.title("Focus Mode Settings")
        win.configure(bg=C['card'])
        win.resizable(False, False)
        win.transient(self)
        win.attributes('-topmost', True)
        _apply_windows_window_icon(win)

        frm = tk.Frame(win, bg=C['card'])
        frm.pack(fill='both', expand=True, padx=14, pady=12)

        tk.Label(frm, text="Focus Mode", bg=C['card'], fg=C['text'],
                 font=_f(11, True)).pack(anchor='w')

        opacity_row = tk.Frame(frm, bg=C['card'])
        opacity_row.pack(fill='x', pady=(12, 4))
        tk.Label(opacity_row, text="Transparency", bg=C['card'], fg=C['text2'],
                 font=_f(8)).pack(side='left')
        self._focus_settings_opacity_pct = tk.IntVar(value=int(self._opacity * 100))
        spin = tk.Spinbox(opacity_row, from_=5, to=100, width=4,
                          textvariable=self._focus_settings_opacity_pct,
                          command=self._apply_focus_settings_opacity,
                          bg=C['card2'], fg=C['text'], insertbackground=C['text'],
                          buttonbackground=C['card2'], relief='flat', font=_f(8))
        spin.pack(side='right')
        tk.Label(opacity_row, text="%", bg=C['card'], fg=C['accent'],
                 font=_f(8, True)).pack(side='right', padx=(0, 4))

        self._focus_settings_opacity_var = tk.DoubleVar(value=self._opacity)
        scale = ttk.Scale(frm, from_=0.05, to=1.0, orient='horizontal',
                          variable=self._focus_settings_opacity_var,
                          command=lambda v: self._set_focus_settings_opacity(float(v)))
        scale.pack(fill='x', pady=(0, 12))
        spin.bind('<Return>', lambda e: self._apply_focus_settings_opacity())
        spin.bind('<FocusOut>', lambda e: self._apply_focus_settings_opacity())

        self._focus_hide_play_var = tk.BooleanVar(
            value=CFG.get('hide_windows_during_playback', False)
        )
        tk.Checkbutton(
            frm,
            text="  Hide windows during play",
            variable=self._focus_hide_play_var,
            command=self._set_focus_hide_playback,
            bg=C['card'], fg=C['text2'], selectcolor=C['card2'],
            activebackground=C['card'], activeforeground=C['accent'],
            font=_f(8), relief='flat', cursor='hand2'
        ).pack(anchor='w', pady=(0, 10))

        tk.Button(frm, text="Close", bg=C['card2'], fg=C['text2'],
                  font=_f(8), relief='flat', padx=16, pady=6,
                  command=win.destroy).pack(anchor='e')

        _show_centered_child(win, self, 250, 180)

    def _set_focus_settings_opacity(self, value):
        value = max(0.05, min(1.0, float(value)))
        self._focus_settings_opacity_pct.set(int(round(value * 100)))
        CFG.set('focus_mode_opacity', value)
        self.set_opacity(value)
        if self._parent and hasattr(self._parent, '_focus_opacity_var'):
            self._parent._focus_opacity_var.set(value)
        if self._parent and hasattr(self._parent, '_focus_opacity_pct'):
            self._parent._focus_opacity_pct.set(int(round(value * 100)))

    def _apply_focus_settings_opacity(self):
        try:
            pct = int(self._focus_settings_opacity_pct.get())
        except Exception:
            pct = 95
        pct = max(5, min(100, pct))
        value = pct / 100
        self._focus_settings_opacity_pct.set(pct)
        self._focus_settings_opacity_var.set(value)
        self._set_focus_settings_opacity(value)

    def _set_focus_hide_playback(self):
        CFG.set('hide_windows_during_playback', self._focus_hide_play_var.get())
        if self._parent and hasattr(self._parent, '_hide_windows_playback_var'):
            self._parent._hide_windows_playback_var.set(self._focus_hide_play_var.get())

    def _run_rec(self):
        self._on_rec()
        self.after(120, self._refresh)

    def _run_play(self):
        self._on_play()
        self.after(120, self._refresh)

    def _run_pause(self):
        self._on_pause()
        self.after(120, self._refresh)

    def _run_stop(self):
        self._on_stop()
        self.after(120, self._refresh)
    
    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()
    
    def _drag_motion(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _minimize(self):
        self._save_position()
        self.overrideredirect(False)
        self.iconify()
        self.after(200, self._restore_override)

    def _restore_override(self):
        try:
            if self.state() == 'normal':
                self.overrideredirect(True)
        except Exception:
            pass

    def _refresh(self):
        try:
            events = len(self._rec.events)
            duration = self._rec.duration()
            size_kb = max(0, int(len(json.dumps(self._rec.events)) / 1024)) if self._rec.events else 0
            name = getattr(self._rec, 'name', '') or 'No workflow loaded'

            parent_playing = bool(getattr(self._parent, '_ui_playing', False))
            is_playing = self._rec.playing or parent_playing

            if self._rec.recording:
                status, color, msg = "Recording", C['red'], "Capturing your actions now."
                rec_text, play_state, pause_state = "STOP REC", 'disabled', 'disabled'
            elif is_playing and self._rec.paused:
                status, color, msg = "Paused", C['orange'], "Playback is paused."
                rec_text, play_state, pause_state = "REC", 'disabled', 'normal'
            elif is_playing:
                status, color, msg = "Playing", C['amber'], "Workflow playback is running."
                rec_text, play_state, pause_state = "REC", 'disabled', 'normal'
            else:
                status, color, msg = "Ready", C['green'], "Ready to record or play."
                rec_text, play_state, pause_state = "REC", 'normal', 'disabled'

            self._status_lbl.config(text=status, fg=color)
            self._status_dot.config(fg=color)
            self._workflow_lbl.config(text=name)
            self._events_value.config(text=str(events))
            self._duration_value.config(text=f"{duration:.1f} s")
            self._size_value.config(text=f"{size_kb} KB")
            if time.time() < self._message_override_until:
                self._message_lbl.config(text=self._message_override)
            else:
                self._message_lbl.config(text=msg)
            if time.time() >= self._countdown_override_until:
                self._countdown_lbl.config(text="")
                self._countdown_num_lbl.config(text="", bg=C['card'])
            self._rec_btn.config(text=rec_text, state='normal')
            self._play_btn.config(state=('normal' if self._rec.events and play_state == 'normal' else 'disabled'))
            self._pause_btn.config(state=pause_state)
            self._stop_btn.config(state='normal')
        except Exception:
            pass
        if self.winfo_exists():
            self.after(500, self._refresh)
    
    def _exit_focus_mode(self):
        self._save_position()
        self.destroy()
        if self._parent and hasattr(self._parent, '_focus_mode_window'):
            self._parent._focus_mode_window = None
    
    def _save_position(self):
        try:
            CFG.set('focus_mode_x', self.winfo_x())
            CFG.set('focus_mode_y', self.winfo_y())
        except Exception:
            pass
    
    def _load_position(self):
        try:
            x = CFG.get('focus_mode_x', 100)
            y = CFG.get('focus_mode_y', 100)
            self.update_idletasks()
            w = max(self.winfo_width(), 360)
            h = max(self.winfo_height(), 330)
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = max(8, min(int(x), max(8, sw - w - 8)))
            y = max(8, min(int(y), max(8, sh - h - 48)))
            self.geometry(f"+{x}+{y}")
            CFG.set('focus_mode_x', x)
            CFG.set('focus_mode_y', y)
        except Exception:
            pass
    
    def set_opacity(self, value):
        value = max(0.05, min(1.0, float(value)))
        self._opacity = value
        try:
            self.attributes('-alpha', value)
        except Exception:
            pass

    def show_countdown(self, label, seconds):
        try:
            self.deiconify()
            self.lift()
            self._countdown_override_until = time.time() + 1.25
            self._countdown_lbl.config(text="")
            self._countdown_num_lbl.config(text=str(seconds), bg=C['card2'], fg=C['accent'])
            self._message_override = "Countdown running."
            self._message_override_until = time.time() + 1.25
            self._message_lbl.config(text=self._message_override)
        except Exception:
            pass

    def clear_countdown(self):
        try:
            self._countdown_override_until = 0
            self._countdown_lbl.config(text="")
            self._countdown_num_lbl.config(text="", bg=C['card'])
        except Exception:
            pass

    def show_message(self, text, color=None):
        try:
            self.clear_countdown()
            if color:
                self._status_lbl.config(fg=color)
                self._status_dot.config(fg=color)
            self._message_override = text
            self._message_override_until = time.time() + 2.0
            self._message_lbl.config(text=text)
        except Exception:
            pass

    def set_status(self, text, color):
        try:
            self._status_lbl.config(text=text, fg=color)
            self._status_dot.config(fg=color)
        except Exception:
            pass

    def protect_for_playback(self):
        try:
            self.deiconify()
            self.lift()
            self._save_position()
            _set_window_click_through(self, True)
            self.set_status("Playing", C['amber'])
            self.show_message("Playback running. Focus Mode is protected from clicks.", C['amber'])
        except Exception:
            pass

    def restore_after_click_protection(self):
        try:
            _set_window_click_through(self, False)
            self.attributes('-topmost', True)
            self.show_message("Playback finished. Ready for the next action.", C['green'])
        except Exception:
            pass

    def hide_for_playback(self):
        try:
            self._save_position()
            self.withdraw()
        except Exception:
            pass

    def restore_after_playback(self):
        try:
            self._load_position()
            self.deiconify()
            self.lift()
            self.attributes('-topmost', True)
            self.show_message("Playback finished. Ready for the next action.", C['green'])
        except Exception:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   MAIN APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class NexaFlow(tk.Tk):

    def __init__(self):
        _set_windows_app_identity()
        super().__init__()
        self.withdraw()
        self._rec       = RecorderEngine(on_event=self._on_evt)
        self._dl        = DataLoopEngine(self._rec)
        self._sched     = SchedulerEngine(self._rec)
        self._fe        = FileEngine()
        self._files     = []
        self._rec_t0    = 0.0
        self._play_t0   = 0.0
        self._play_paused_total = 0.0
        self._play_pause_started = 0.0
        self._play_current_event = 0
        self._play_total_events = 0
        self._play_current_loop = 0
        self._play_total_loops = None
        self._timer_mode = None
        self._timer_after_id = None
        self._ui_playing = False
        self._play_countdown_active = False
        self._play_countdown_remaining = 0
        self._play_countdown_after_id = None
        self._playback_safety_listener_keyboard = None
        self._playback_safety_listener_mouse = None
        self._playback_safety_triggered = False
        self._playback_safety_armed_at = 0.0
        self._timezone, self._tz = _normalize_timezone_choice(
            CFG.get('timezone', _get_default_timezone())
        )
        CFG.set('timezone', self._timezone)
        self._timezone_options = [LOCAL_TIMEZONE_LABEL] + (sorted(available_timezones()) if available_timezones else [])
        self._dl_items  = []
        self._tray_icon = None
        self._sched_after_id = None   # fix duplicate scheduler refresh
        self._focus_mode_window = None
        self._ui_events = queue.SimpleQueue()
        self._ui_events_after_id = None
        self._remote_host = RemoteHost(
            command_handler=self._handle_remote_command,
            status_provider=self._remote_status_snapshot,
            approval_handler=self._on_pair_request,
            trusted_check=self._is_trusted_device,
            trusted_add=self._add_trusted_device,
            trusted_remove=self._remove_trusted_device,
            log=lambda msg: LOG.add(msg, 'remote')
        ) if RemoteHost else None
        self._remote_refresh_after_id = None
        self._firewall_rule_ready = False
        self._firewall_spec = None
        self._firewall_check_inflight = None
        self._firewall_repair_inflight = None
        self._firewall_prompted_signatures = set()
        self._pair_dialog = None
        self._pair_dialog_request_id = ""

        self._init_window()
        self._init_styles()
        self._build()
        self._start_hotkeys()
        self._setup_tray()
        self.update_idletasks()
        self.deiconify()
        self.lift()
        self._ui_events_after_id = self.after(75, self._drain_ui_events)
        LOG.add("NexaFlow v1.0 initialized", 'system')
        self.after(700, self._show_first_run_welcome)
        if CFG.get('remote_start_on_launch', False):
            self.after(1200, self._remote_start)

    # ── Window ────────────────────────────────────────────────
    def _init_window(self):
        self.title(" ")
        self.configure(bg=C['bg'])
        self.resizable(True, True)
        self.minsize(520, 680)

        W = CFG.get('win_w', 540)
        H = CFG.get('win_h', 760)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        cx = CFG.get('win_x', (sw - W) // 2)
        cy = CFG.get('win_y', (sh - H) // 2)
        self.geometry(f"{W}x{H}+{cx}+{cy}")

        aot = CFG.get('always_on_top', True)
        self.attributes('-topmost', aot)
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self.bind('<Configure>', self._on_resize)

        ico_path = _app_icon_path()
        if IS_WIN:
            _apply_windows_window_icon(self, ico_path)
        else:
            _apply_tk_titlebar_icon(self, ico_path)

    def _on_resize(self, event):
        if event.widget is self:
            try:
                CFG._data['win_w'] = self.winfo_width()
                CFG._data['win_h'] = self.winfo_height()
                CFG._data['win_x'] = self.winfo_x()
                CFG._data['win_y'] = self.winfo_y()
                if getattr(self, '_resize_save_id', None):
                    self.after_cancel(self._resize_save_id)
                self._resize_save_id = self.after(300, CFG.save)
            except Exception:
                pass

    def _on_close(self):
        if getattr(self, '_ui_events_after_id', None):
            try: self.after_cancel(self._ui_events_after_id)
            except: pass
            self._ui_events_after_id = None
        if getattr(self, '_remote_refresh_after_id', None):
            try: self.after_cancel(self._remote_refresh_after_id)
            except: pass
            self._remote_refresh_after_id = None
        if getattr(self, '_remote_host', None):
            try: self._remote_host.stop()
            except: pass
        self._rec.halt()
        self._dl.halt()
        self._sched.stop()
        if getattr(self, '_hk_listener', None):
            try: self._hk_listener.stop()
            except: pass
        self._stop_playback_safety_listener()
        if hasattr(self, '_aot'):
            CFG.set('always_on_top', bool(self._aot.get()))
        else:
            CFG.set('always_on_top', bool(CFG.get('always_on_top', True)))
        CFG.save()
        if self._tray_icon:
            try: self._tray_icon.stop()
            except: pass
        self.destroy()

    def _queue_ui_event(self, event_type, payload=None):
        """Accept worker-thread events without calling any Tk method."""
        self._ui_events.put((event_type, payload))

    def _drain_ui_events(self):
        """Process worker results exclusively on the Tk main thread."""
        try:
            for _ in range(100):
                try:
                    event_type, payload = self._ui_events.get_nowait()
                except queue.Empty:
                    break
                if event_type == 'pair_request':
                    self._show_pair_dialog(payload or {})
                elif event_type == 'log' and hasattr(self, '_log_text'):
                    self._append_log(payload)
                elif event_type == 'firewall_check':
                    self._handle_firewall_check(payload or {})
                elif event_type == 'firewall_repair':
                    self._handle_firewall_repair(payload or {})
                elif event_type == 'remote_command':
                    cmd, body = payload
                    self._execute_remote_command(cmd, body)
        finally:
            try:
                self._ui_events_after_id = self.after(75, self._drain_ui_events)
            except Exception:
                self._ui_events_after_id = None

    def _show_first_run_welcome(self):
        if CFG.get('welcome_shown_v1', False):
            return
        CFG.set('welcome_shown_v1', True)
        messagebox.showinfo(
            "Welcome to NexaFlow",
            "Welcome to NexaFlow.\n\n"
            "Your desktop automation workspace is ready. For the best first experience, "
            "we recommend reading the NexaFlow User Guide included with your download. "
            "It explains recording, playback, Focus Mode, hotkeys, safety options, and "
            "workflow management in a simple step-by-step way."
        )

    # ── Styles ────────────────────────────────────────────────
    def _init_styles(self):
        s = ttk.Style(self)
        s.theme_use('clam')

        s.configure('NF.TNotebook',
                    background=C['bg'], borderwidth=0, tabmargins=[0, 0, 0, 0])
        s.configure('NF.TNotebook.Tab',
                    background=C['panel'], foreground=C['muted'],
                    font=_f(8, True), padding=[12, 7], borderwidth=0)
        s.map('NF.TNotebook.Tab',
              background=[('selected', C['card']), ('active', C['card3'])],
              foreground=[('selected', C['accent']), ('active', C['text2'])])

        s.configure('NF.TFrame', background=C['bg'])

        s.configure('NF.Horizontal.TProgressbar',
                    troughcolor=C['card2'], background=C['red'],
                    borderwidth=0, thickness=3)
        s.configure('Green.Horizontal.TProgressbar',
                    troughcolor=C['card2'], background=C['green'],
                    borderwidth=0, thickness=3)
        s.configure('Cyan.Horizontal.TProgressbar',
                    troughcolor=C['card2'], background=C['accent'],
                    borderwidth=0, thickness=3)
        s.configure('TScale',
                    background=C['bg'], troughcolor=C['card2'],
                    borderwidth=0, sliderlength=14, sliderrelief='flat')
        s.map('TScale', background=[('active', C['bg'])])

        # Treeview style
        s.configure('NF.Treeview',
                    background=C['card'], foreground=C['text2'],
                    fieldbackground=C['card'],
                    borderwidth=0, rowheight=22, font=_f(8, mono=True))
        s.configure('NF.Treeview.Heading',
                    background=C['card2'], foreground=C['accent'],
                    font=_f(7, True), relief='flat', borderwidth=0)
        s.map('NF.Treeview',
              background=[('selected', C['accent3'])],
              foreground=[('selected', C['accent'])])

    # ── Full UI ───────────────────────────────────────────────
    def _build(self):
        # Top bar
        topbar = tk.Frame(self, bg=C['panel'], height=52)
        topbar.pack(fill='x')
        topbar.pack_propagate(False)

        left = tk.Frame(topbar, bg=C['panel'])
        left.pack(side='left', padx=16, fill='y')

        logo_row = tk.Frame(left, bg=C['panel'])
        logo_row.pack(side='left', fill='y')
        tk.Label(logo_row, text="⚡", bg=C['panel'], fg=C['accent'],
                 font=_f(14)).pack(side='left', pady=14)
        tk.Label(logo_row, text="NEXA FLOW", bg=C['panel'], fg=C['text'],
                 font=_f(12, True)).pack(side='left', pady=14)
        
        self._focus_mode_btn = tk.Button(left, text="⊟ Focus", bg=C['accent'], fg='white',
                                         font=_f(8, True), relief='flat', bd=0, padx=10,
                                         highlightthickness=1, highlightbackground=C['accent3'],
                                         activebackground=C['accent'], activeforeground='white',
                                         cursor='hand2', command=self._toggle_focus_mode)
        self._focus_mode_btn.pack(side='left', padx=8, pady=12)
        self._focus_mode_btn.bind(
            '<Enter>',
            lambda e: self._focus_mode_btn.config(highlightbackground=C['blue'])
        )
        self._focus_mode_btn.bind(
            '<Leave>',
            lambda e: self._focus_mode_btn.config(highlightbackground=C['accent3'])
        )

        right = tk.Frame(topbar, bg=C['panel'])
        right.pack(side='right', padx=16, fill='y')

        self._remote_badge_var = tk.StringVar(value="REMOTE OFF")
        self._remote_badge = tk.Label(right, textvariable=self._remote_badge_var,
                                      bg=C['card2'], fg=C['muted'],
                                      font=_f(7, True), padx=8, pady=3,
                                      highlightthickness=1, highlightbackground=C['border'])
        self._remote_badge.pack(side='right', padx=(10, 0), pady=14)

        self._status_dot = tk.Label(right, text="●", bg=C['panel'],
                                    fg=C['green'], font=_f(10))
        self._status_dot.pack(side='right', pady=14)
        self._status_var = tk.StringVar(value="READY")
        self._status_lbl = tk.Label(right, textvariable=self._status_var,
                                    bg=C['panel'], fg=C['green'],
                                    font=_f(8, True))
        self._status_lbl.pack(side='right', padx=(0, 4), pady=14)

        self._clock_lbl = tk.Label(right, text="", bg=C['panel'],
                                   fg=C['muted'], font=_f(8, mono=True))
        self._clock_lbl.pack(side='right', padx=(10, 0), pady=14)
        self._clock_zone_lbl = tk.Label(right, text="", bg=C['panel'],
                                       fg=C['muted'], font=_f(7, mono=True))
        self._clock_zone_lbl.pack(side='right', padx=(10, 0), pady=14)
        self._tick_clock()

        tk.Frame(self, bg=C['accent'], height=1).pack(fill='x')
        tk.Frame(self, bg=C['border'], height=1).pack(fill='x')

        # Main content area
        content_frame = tk.Frame(self, bg=C['bg'])
        content_frame.pack(fill='both', expand=True)

        # Simple UI mode (sidebar + editor) — fallback only
        if CFG.get('simple_ui', False):
            self._build_simple(content_frame)
        else:
            # Notebook (advanced)
            nb_frame = tk.Frame(content_frame, bg=C['bg'])
            nb_frame.pack(fill='both', expand=True)
            self._nb = ttk.Notebook(nb_frame, style='NF.TNotebook')
            self._nb.pack(fill='both', expand=True)

            self._tab_record()
            self._tab_play()
            self._tab_data()
            self._tab_files()
            self._tab_scheduler()
            self._tab_events()
            self._tab_log()
            self._tab_settings()

        # Footer
        tk.Frame(self, bg=C['border'], height=1).pack(fill='x')
        footer = tk.Frame(self, bg=C['panel'], height=28)
        footer.pack(fill='x')
        footer.pack_propagate(False)

        hotkeys = "  F9 REC  ·  F10 PLAY  ·  F12 PAUSE  ·  F11 STOP  ·  ESC STOP ALL"
        tk.Label(footer, text=hotkeys, bg=C['panel'], fg=C['muted'],
                 font=_f(7, mono=True)).pack(side='left', pady=5)

        self._wf_badge = tk.Label(footer, text="No workflow", bg=C['panel'],
                                  fg=C['amber'], font=_f(7, True))
        self._wf_badge.pack(side='right', padx=10, pady=5)

    def _tick_clock(self):
        now = datetime.now(tz=self._tz) if self._tz else datetime.now().astimezone()
        self._clock_lbl.config(text=now.strftime("%H:%M:%S"))
        if self._timezone == LOCAL_TIMEZONE:
            self._clock_zone_lbl.config(text="Local Time")
        else:
            self._clock_zone_lbl.config(text=self._timezone)
        self.after(1000, self._tick_clock)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   SIMPLE UI (sidebar + editor)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_simple(self, parent):
        # Left sidebar
        left = tk.Frame(parent, bg=C['card2'], width=300)
        left.pack(side='left', fill='y')
        left.pack_propagate(False)

        tk.Label(left, text='Workflows', bg=C['card2'], fg=C['text'], font=_f(12, True)).pack(anchor='nw', padx=18, pady=(18, 8))
        self._listbox = tk.Listbox(left, bg=C['card'], fg=C['text'], selectbackground=C['accent3'],
                                   selectforeground=C['text'], bd=0, highlightthickness=0,
                                   relief='flat', font=_f(9))
        self._listbox.pack(fill='both', expand=True, padx=16, pady=(0, 12))
        for r in CFG.get_recent():
            try:
                self._listbox.insert('end', Path(r).name)
            except:
                pass

        lb_btns = tk.Frame(left, bg=C['card2'])
        lb_btns.pack(fill='x', padx=16, pady=(0, 16))
        self._ghost_btn(lb_btns, '+ New', self._new_workflow).pack(side='left', expand=True, fill='x', padx=(0, 8))
        self._ghost_btn(lb_btns, 'Delete', self._delete_selected).pack(side='left', expand=True, fill='x')

        # Right area (toolbar + editor)
        right = tk.Frame(parent, bg=C['bg'])
        right.pack(side='left', fill='both', expand=True)

        toolbar = tk.Frame(right, bg=C['card'], height=72)
        toolbar.pack(fill='x', padx=18, pady=(18, 0))
        toolbar.pack_propagate(False)
        self._big_btn(toolbar, '⏺ Record', C['red'], self._toggle_rec).pack(side='left', padx=12, pady=14)
        self._big_btn(toolbar, '▶ Play', C['green'], self._play_start).pack(side='left', padx=6, pady=14)
        self._big_btn(toolbar, '⏸ Pause', C['amber'], self._toggle_pause).pack(side='left', padx=6, pady=14)
        self._big_btn(toolbar, '■ Stop', C['text2'], self._play_stop).pack(side='left', padx=6, pady=14)
        self._ghost_btn(toolbar, '💾 Save', self._save_workflow_dialog).pack(side='right', padx=12, pady=14)

        editor_frame = tk.Frame(right, bg=C['card2'])
        editor_frame.pack(fill='both', expand=True, padx=18, pady=18)
        self._editor = tk.Text(editor_frame, bg=C['card'], fg=C['text'], wrap='word', font=_f(11), bd=0,
                               insertbackground=C['accent'], selectbackground=C['accent3'], selectforeground=C['text'])
        self._editor.pack(fill='both', expand=True, padx=16, pady=16)

        footer = tk.Frame(right, bg=C['panel'], height=28)
        footer.pack(fill='x', padx=18, pady=(0, 18))
        footer.pack_propagate(False)
        tk.Label(footer, text='Hotkeys: ' + '  '.join([f"{k.upper()}" for k in (CFG.get('hotkeys', {}) or {}).values()]),
                 bg=C['panel'], fg=C['muted'], font=_f(7, mono=True)).pack(side='left', padx=8)

    def _new_workflow(self):
        self._editor.delete('1.0', 'end')
        self._wf_badge.config(text='New workflow')

    def _delete_selected(self):
        sel = self._listbox.curselection()
        if not sel: return
        idx = sel[0]
        name = self._listbox.get(idx)
        # locate path
        for p in CFG.get_recent():
            if Path(p).name == name:
                try: Path(p).unlink()
                except: pass
        self._listbox.delete(idx)

    def _save_workflow_dialog(self):
        path = filedialog.asksaveasfilename(defaultextension='.nxf', filetypes=[('NexaFlow', '*.nxf'), ('JSON', '*.json')])
        if not path: return
        # create a simple save structure: use saved events if any
        try:
            # prefer recorder events
            if hasattr(self._rec, 'events') and self._rec.events:
                self._rec.save(path)
            else:
                # fallback: save editor content as a note
                data = {'v':5, 'name': Path(path).stem, 'notes': self._editor.get('1.0','end'), 'events': []}
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                CFG.add_recent(path)
                self._wf_badge.config(text=Path(path).name)
                LOG.add(f"Workflow saved: {path}", 'file')
        except Exception as e:
            messagebox.showerror('Save failed', str(e))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   TAB 1 — RECORD
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _tab_record(self):
        tab = ttk.Frame(self._nb, style='NF.TFrame')
        self._nb.add(tab, text="  ⏺  REC  ")
        p = tk.Frame(tab, bg=C['bg'])
        p.pack(fill='both', expand=True, padx=18, pady=12)

        # Workflow name & notes
        _section_header(p, "Workflow", icon="◆").pack(anchor='w', pady=(0, 4))
        nrow = tk.Frame(p, bg=C['bg'])
        nrow.pack(fill='x', pady=(0, 4))
        self._rec_name = tk.StringVar(value="workflow_1")
        e = _entry(nrow, self._rec_name)
        e.pack(fill='x')

        nrow2 = tk.Frame(p, bg=C['bg'])
        nrow2.pack(fill='x', pady=(0, 10))
        self._rec_notes = tk.StringVar(value="")
        ne = _entry(nrow2, self._rec_notes)
        ne.configure(fg=C['muted'])
        ne.pack(fill='x')
        # Placeholder
        def _notes_focus_in(e):
            if ne.get() == "Add notes…":
                ne.delete(0, 'end')
                ne.config(fg=C['text'])
        def _notes_focus_out(e):
            if not ne.get():
                ne.insert(0, "Add notes…")
                ne.config(fg=C['muted'])
        ne.insert(0, "Add notes…")
        ne.bind('<FocusIn>',  _notes_focus_in)
        ne.bind('<FocusOut>', _notes_focus_out)

        # Recent workflows
        recent = CFG.get_recent()
        rf = tk.Frame(p, bg=C['bg'])
        rf.pack(fill='x', pady=(0, 6))
        tk.Label(rf, text="Recent:", bg=C['bg'], fg=C['muted'],
                 font=_f(7)).pack(side='left')
        self._recent_var = tk.StringVar()
        self._recent_cb = ttk.Combobox(rf, textvariable=self._recent_var,
                                      values=[Path(r).name for r in recent],
                                      width=28, state='readonly', font=_f(7))
        self._recent_cb.pack(side='left', padx=6)
        self._recent_paths = recent
        def _load_recent(ev=None):
            idx = self._recent_cb.current()
            if idx >= 0 and idx < len(self._recent_paths):
                self._do_load(self._recent_paths[idx])
        self._recent_cb.bind('<<ComboboxSelected>>', _load_recent)

        # Capture mode
        _section_header(p, "Capture Mode", icon="◆").pack(anchor='w', pady=(0, 4))
        mc = _card(p)
        mc.pack(fill='x', pady=(0, 8))
        self._rec_mode = tk.StringVar(value=CFG.get('capture_mode', 'smart'))
        for v, icon, lbl, tip in [
            ('smart', '⚡', 'Smart Mode', 'Clicks + keyboard · Recommended'),
            ('full',  '⊙', 'Full Mode',  'All mouse movement · High precision'),
        ]:
            row = tk.Frame(mc, bg=C['card'])
            row.pack(fill='x', padx=10, pady=3)
            tk.Radiobutton(row, text=f" {icon}  {lbl}", variable=self._rec_mode,
                           value=v, bg=C['card'], fg=C['text'],
                           selectcolor=C['card2'], activebackground=C['card'],
                           font=_f(9), indicatoron=True, relief='flat',
                           cursor='hand2').pack(side='left')
            tk.Label(row, text=tip, bg=C['card'], fg=C['muted'],
                     font=_f(7)).pack(side='left', padx=10)
        tk.Frame(mc, bg=C['card'], height=4).pack()

        # Stats row
        _section_header(p, "Session Stats", icon="◆").pack(anchor='w', pady=(0, 4))
        sc = tk.Frame(p, bg=C['bg'])
        sc.pack(fill='x', pady=(0, 8))
        sc.columnconfigure(0, weight=1)
        sc.columnconfigure(1, weight=1)
        sc.columnconfigure(2, weight=1)

        for col, label, attr, val, color in [
            (0, "EVENTS",    '_evt_lbl',  "0",     C['red']),
            (1, "DURATION",  '_dur_lbl',  "0.0 s", C['accent']),
            (2, "EST. SIZE", '_size_lbl', "0 KB",  C['blue']),
        ]:
            tile = tk.Frame(sc, bg=C['card2'],
                            highlightthickness=1, highlightbackground=C['border2'])
            tile.grid(row=0, column=col, padx=(0 if col == 0 else 3, 0), sticky='ew')
            lv = tk.Label(tile, text=val, bg=C['card2'], fg=color, font=_f(18, True))
            lv.pack(pady=(8, 0))
            setattr(self, attr, lv)
            tk.Label(tile, text=label, bg=C['card2'], fg=C['muted'],
                     font=_f(6, True)).pack(pady=(0, 6))

        # Record button
        self._rec_btn = self._big_btn(p, "⏺   START RECORDING", C['red'], self._toggle_rec)
        self._rec_btn.pack(fill='x', pady=(2, 4))

        # Options row
        opts_row = tk.Frame(p, bg=C['bg'])
        opts_row.pack(fill='x', pady=2)
        _lbl(opts_row, "Countdown:", 8).pack(side='left')
        self._rec_countdown = tk.StringVar(value=str(CFG.get('countdown', '3')))
        cb2 = ttk.Combobox(opts_row, textvariable=self._rec_countdown,
                           values=["0","1","2","3","5","10"], width=3, state='readonly')
        cb2.pack(side='left', padx=6)
        _lbl(opts_row, "sec", 8).pack(side='left')

        sv_row = tk.Frame(p, bg=C['bg'])
        sv_row.pack(fill='x', pady=3)
        self._ghost_btn(sv_row, "💾  Save .nxf", self._save_rec).pack(side='left', expand=True, fill='x', padx=(0,3))
        self._ghost_btn(sv_row, "📂  Load .nxf", self._load_rec).pack(side='left', expand=True, fill='x')

        ss_row = tk.Frame(p, bg=C['bg'])
        ss_row.pack(fill='x', pady=3)
        self._auto_save_on_stop = tk.BooleanVar(value=True)
        self._check(ss_row, "Auto-save on stop", self._auto_save_on_stop).pack(side='left', padx=(0, 12))
        self._ss_on_stop = tk.BooleanVar(value=False)
        self._check(ss_row, "Screenshot on stop", self._ss_on_stop).pack(side='left')

        self._rec_info = tk.Label(p, text="No workflow recorded or loaded",
                                  bg=C['bg'], fg=C['muted'], font=_f(8))
        self._rec_info.pack(pady=(4, 0))
        self._refresh_recent_workflows()

    def _toggle_rec(self):
        if getattr(self, '_countdown_active', False):
            return
        if not self._rec.recording:
            cd = int(self._rec_countdown.get() or 0)
            if cd > 0:
                self._countdown_active = True
                self._rec_btn.config(state='disabled')
                self._countdown_rec(cd)
            else:
                self._start_recording()
        else:
            self._stop_recording()

    def _countdown_rec(self, n):
        if n <= 0:
            self._countdown_active = False
            if self._focus_mode_window:
                self._focus_mode_window.show_message("Recording starts now.", C['red'])
            self._start_recording()
            return
        self._rec_btn.config(text=f"⏳  Starting in {n}…", bg=C['orange'], state='normal')
        if self._focus_mode_window:
            self._focus_mode_window.show_countdown("Recording", n)
        self.after(1000, lambda: self._countdown_rec(n - 1))

    def _sanitize_filename(self, name: str):
        safe = ''.join(c for c in name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        return safe or 'workflow'

    def _ensure_workflow_save_path(self, name: str):
        wf_dir = CFG._dir / 'workflows'
        wf_dir.mkdir(parents=True, exist_ok=True)
        stem = self._sanitize_filename(name)
        path = wf_dir / f"{stem}.nxf"
        if path.exists():
            for idx in range(1, 1000):
                candidate = wf_dir / f"{stem}_{idx}.nxf"
                if not candidate.exists():
                    path = candidate
                    break
        return path

    def _refresh_recent_workflows(self):
        recent = CFG.get_recent()
        names = [Path(r).name for r in recent]
        try:
            self._recent_paths = recent
            self._recent_cb.config(values=names)
            current = self._recent_var.get() if hasattr(self, '_recent_var') else ''
            if current in names:
                self._recent_var.set(current)
            elif names:
                self._recent_var.set(names[0])
            else:
                self._recent_var.set('')
        except Exception:
            pass
        try:
            self._play_recent_paths = recent
            self._play_recent_cb.config(values=names)
            current = self._play_recent_var.get() if hasattr(self, '_play_recent_var') else ''
            if current in names:
                self._play_recent_var.set(current)
            elif names:
                self._play_recent_var.set(names[0])
            else:
                self._play_recent_var.set('')
        except Exception:
            pass
        try:
            self._listbox.delete(0, 'end')
            for r in recent:
                self._listbox.insert('end', Path(r).name)
        except Exception:
            pass

    def _start_recording(self):
        self._stop_timer()
        self._rec_t0  = time.time()
        self._timer_mode = 'record'
        self._rec.name  = self._rec_name.get().strip() or "workflow"
        notes_val = self._rec_notes.get()
        self._rec.notes = "" if notes_val == "Add notes…" else notes_val
        self._rec.start(smart=(self._rec_mode.get() == 'smart'))
        self._rec_btn.config(text="⏹   STOP RECORDING", bg=C['red2'], state='normal')
        self._status("RECORDING", C['red'])
        if hasattr(self, '_evt_lbl'):
            self._evt_lbl.config(text="0")
        # Disable always-on-top so other windows can be clicked
        self.attributes('-topmost', False)
        self._start_timer()

    def _stop_recording(self):
        self._stop_timer()
        self._rec.stop()
        self._rec_btn.config(text="⏺   START RECORDING", bg=C['red'])
        n   = len(self._rec.events)
        dur = time.time() - getattr(self, '_rec_t0', time.time())
        kb  = round(n * 0.05, 1)
        if hasattr(self, '_dur_lbl'):
            self._dur_lbl.config(text=f"{dur:.1f} s")
        if hasattr(self, '_size_lbl'):
            self._size_lbl.config(text=f"~{kb} KB")
        self._size_lbl.config(text=f"~{kb} KB")
        save_note = ''
        if self._auto_save_on_stop.get() and self._rec.events:
            try:
                saved_path = self._ensure_workflow_save_path(self._rec.name)
                self._rec.save(saved_path)
                save_note = f" · Saved: {Path(saved_path).name}"
                self._refresh_recent_workflows()
            except Exception as ex:
                LOG.add(f"Auto-save failed: {ex}", 'error')
        self._rec_info.config(
            text=f"✓  {self._rec.name}  ·  {n} events  ·  {dur:.1f}s  · ready{save_note}",
            fg=C['green'])
        self._wf_badge.config(text=f"⚡ {self._rec.name}")
        # Restore always-on-top
        aot = CFG.get('always_on_top', True)
        self.attributes('-topmost', aot)
        self._status("READY", C['green'])
        self._refresh_events_tab()
        if self._ss_on_stop.get():
            self._take_screenshot(f"rec_stop_{datetime.now().strftime('%H%M%S')}")

    def _start_timer(self):
        self._stop_timer()
        self._timer_after_id = self.after(200, self._tick_timer)

    def _play_elapsed_seconds(self):
        if not self._play_t0:
            return 0.0
        end = self._play_pause_started if self._play_pause_started else time.time()
        return max(0.0, end - self._play_t0 - self._play_paused_total)

    def _stop_timer(self):
        if self._timer_after_id is not None:
            try:
                self.after_cancel(self._timer_after_id)
            except Exception:
                pass
            self._timer_after_id = None
        self._timer_mode = None

    def _tick_timer(self):
        self._timer_after_id = None
        if self._timer_mode == 'record' and self._rec.recording:
            d = time.time() - self._rec_t0
            self._dur_lbl.config(text=f"{d:.1f} s")
            n = len(self._rec.events)
            self._size_lbl.config(text=f"~{round(n*0.05,1)} KB")
            self._timer_after_id = self.after(200, self._tick_timer)
            return
        if self._timer_mode == 'play' and self._rec.playing:
            d = self._play_elapsed_seconds()
            self._dur_lbl.config(text=f"{d:.1f} s")
            self._timer_after_id = self.after(200, self._tick_timer)
            return
        self._dur_lbl.config(text="0.0 s")

    def _on_evt(self, count):
        self.after(0, lambda: self._evt_lbl.config(text=str(count)))

    def _save_rec(self):
        if not self._rec.events:
            messagebox.showwarning("NexaFlow", "Nothing recorded yet."); return
        name = self._rec_name.get().strip() or "recording"
        path = filedialog.asksaveasfilename(
            defaultextension=".nxf", initialfile=name,
            filetypes=[("NexaFlow Workflow", "*.nxf"), ("All", "*.*")])
        if path:
            self._rec.save(path)
            self._rec_info.config(text=f"✓  Saved: {Path(path).name}", fg=C['green'])
            self._refresh_recent_workflows()

    def _load_rec(self):
        path = filedialog.askopenfilename(
            filetypes=[("NexaFlow Workflow", "*.nxf"), ("All", "*.*")])
        if path:
            self._do_load(path)

    def _do_load(self, path):
        try:
            n   = self._rec.load(path)
            dur = self._rec.duration()
            self._evt_lbl.config(text=str(n))
            self._dur_lbl.config(text=f"{dur} s")
            self._rec_info.config(
                text=f"✓  {Path(path).name}  ({n} events, {dur}s)",
                fg=C['green'])
            self._rec_name.set(self._rec.name)
            self._wf_badge.config(text=f"⚡ {self._rec.name}")
            self._status("READY", C['green'])
            self._refresh_events_tab()
            try:
                self._play_wf_label.config(text=f"Workflow: {self._rec.name}")
            except Exception:
                pass
            try:
                self._recent_var.set(Path(path).name)
            except Exception:
                pass
            try:
                self._play_recent_var.set(Path(path).name)
            except Exception:
                pass
            self._refresh_recent_workflows()
        except Exception as ex:
            messagebox.showerror("NexaFlow", f"Load error:\n{ex}")

    def _take_screenshot(self, label='screenshot'):
        if not HAS_PIL: return
        try:
            img  = ImageGrab.grab()
            home = Path.home() / "NexaFlow_Screenshots"
            home.mkdir(exist_ok=True)
            fname = home / f"{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img.save(str(fname))
            LOG.add(f"Screenshot saved: {fname.name}", 'file')
        except Exception as e:
            LOG.add(f"Screenshot failed: {e}", 'error')

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   TAB 2 — PLAY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _tab_play(self):
        tab = ttk.Frame(self._nb, style='NF.TFrame')
        self._nb.add(tab, text="  ▶  PLAY  ")
        p = tk.Frame(tab, bg=C['bg'])
        p.pack(fill='both', expand=True, padx=18, pady=12)

        wf_row = tk.Frame(p, bg=C['bg'])
        wf_row.pack(fill='x', pady=(0, 8))
        tk.Label(wf_row, text="Workflow:", bg=C['bg'], fg=C['muted'], font=_f(7)).pack(side='left')
        self._play_recent_var = tk.StringVar()
        self._play_recent_cb = ttk.Combobox(wf_row, textvariable=self._play_recent_var,
                                           values=[Path(r).name for r in CFG.get_recent()],
                                           width=28, state='readonly', font=_f(7))
        self._play_recent_cb.pack(side='left', padx=6)
        self._play_recent_paths = CFG.get_recent()
        self._play_recent_cb.bind('<<ComboboxSelected>>', self._load_play_recent)
        self._ghost_btn(wf_row, "Load", self._load_play_recent).pack(side='left', padx=(6, 0))
        self._ghost_btn(wf_row, "🗑 Delete", self._delete_play_workflow).pack(side='left', padx=(6, 0))
        self._play_wf_label = tk.Label(p, text="No workflow loaded", bg=C['bg'], fg=C['muted'], font=_f(8))
        self._play_wf_label.pack(anchor='w', pady=(0, 8))

        _section_header(p, "Playback Speed", icon="◆").pack(anchor='w', pady=(0, 4))
        sc = _card(p)
        sc.pack(fill='x', pady=(0, 10))
        sf = tk.Frame(sc, bg=C['card'])
        sf.pack(fill='x', padx=12, pady=(10, 4))
        self._speed = tk.DoubleVar(value=CFG.get('speed', 1.0))
        ttk.Scale(sf, variable=self._speed, from_=0.1, to=5.0,
                  orient='horizontal').pack(side='left', fill='x', expand=True)
        self._spd_lbl = tk.Label(sf, text="1.0×", bg=C['card'], fg=C['amber'],
                                 font=_f(13, True), width=5)
        self._spd_lbl.pack(side='right')
        self._speed.trace_add('write', lambda *_: self._spd_lbl.config(
            text=f"{self._speed.get():.1f}×"))

        pf = tk.Frame(sc, bg=C['card'])
        pf.pack(fill='x', padx=12, pady=(0, 10))
        for label, val in [("0.5×", 0.5), ("1×", 1.0), ("1.5×", 1.5),
                            ("2×", 2.0), ("3×", 3.0), ("5×", 5.0)]:
            tk.Button(pf, text=label, command=lambda v=val: self._speed.set(v),
                      bg=C['card2'], fg=C['text2'], font=_f(7, True),
                      relief='flat', cursor='hand2', padx=7, pady=3,
                      activebackground=C['card3'],
                      activeforeground=C['accent']).pack(side='left', padx=(0, 2))

        _section_header(p, "Loop Mode", icon="◆").pack(anchor='w', pady=(0, 4))
        lc = _card(p)
        lc.pack(fill='x', pady=(0, 10))
        self._lmode = tk.StringVar(value='once')
        lf = tk.Frame(lc, bg=C['card'])
        lf.pack(fill='x', padx=12, pady=8)
        for v, label in [('once', '  Once  '), ('count', '  N Times  '), ('infinite', '  ∞ Infinite  ')]:
            tk.Radiobutton(lf, text=label, variable=self._lmode, value=v,
                           bg=C['card2'], fg=C['text2'], selectcolor=C['card3'],
                           activebackground=C['card2'], font=_f(8, True), relief='flat',
                           command=self._on_lmode, cursor='hand2').pack(side='left', padx=3)

        tc = tk.Frame(p, bg=C['bg'])
        tc.pack(fill='x', pady=(0, 10))
        tc.columnconfigure(0, weight=1); tc.columnconfigure(1, weight=1); tc.columnconfigure(2, weight=1)
        self._lcount = tk.StringVar(value="10")
        self._ldelay = tk.StringVar(value="1.0")
        self._sdelay = tk.StringVar(value="3")
        for col, label, var, unit in [
            (0, "Repeat Count", self._lcount, "times"),
            (1, "Loop Delay",   self._ldelay, "sec"),
            (2, "Start After",  self._sdelay, "sec"),
        ]:
            tile = tk.Frame(tc, bg=C['card2'],
                            highlightthickness=1, highlightbackground=C['border'])
            tile.grid(row=0, column=col, padx=(0 if col == 0 else 3, 0), sticky='ew')
            tk.Label(tile, text=label, bg=C['card2'], fg=C['muted'], font=_f(7)).pack(pady=(8, 2))
            e = _entry(tile, var, w=6)
            e.pack(pady=2)
            if col == 0: self._count_e = e
            tk.Label(tile, text=unit, bg=C['card2'], fg=C['muted'], font=_f(7)).pack(pady=(2, 8))

        self._play_info = tk.Label(p, text="", bg=C['bg'], fg=C['amber'], font=_f(8))
        self._play_info.pack(pady=(4, 2))
        self._pvar = tk.DoubleVar(value=0)
        ttk.Progressbar(p, variable=self._pvar, maximum=100,
                        style='Cyan.Horizontal.TProgressbar').pack(fill='x')

        self._loop_ctr = tk.Label(p, text="", bg=C['bg'], fg=C['muted'], font=_f(7))
        self._loop_ctr.pack(anchor='e')

        ss2 = tk.Frame(p, bg=C['bg'])
        ss2.pack(fill='x', pady=2)
        self._ss_on_done = tk.BooleanVar(value=False)
        self._check(ss2, "Screenshot on completion", self._ss_on_done).pack(side='left')

        bf = tk.Frame(p, bg=C['bg'])
        bf.pack(fill='x', pady=(8, 2))
        self._play_btn = self._big_btn(bf, "▶   PLAY", C['green'], self._play_start)
        self._play_btn.pack(side='left', expand=True, fill='x', padx=(0, 3))
        self._pause_btn = tk.Button(bf, text="Ⅱ", command=self._toggle_pause,
                                    bg=C['amber'], fg=C['bg'], font=_f(11, True),
                                    relief='flat', cursor='hand2', padx=10, pady=10,
                                    activebackground=C['amber2'], state='disabled')
        self._pause_btn.pack(side='left', padx=(0, 3))
        self._stop_btn_play = tk.Button(bf, text="■  STOP", command=self._play_stop,
                                        bg=C['card2'], fg=C['text2'], font=_f(8, True),
                                        relief='flat', cursor='hand2', padx=12, pady=10,
                                        activebackground=C['card3'],
                                        activeforeground=C['accent'],
                                        highlightthickness=1,
                                        highlightbackground=C['border2'],
                                        highlightcolor=C['accent'])
        self._stop_btn_play.pack(side='left', padx=(0, 0))

        self._on_lmode()

    def _on_lmode(self):
        st = 'normal' if self._lmode.get() == 'count' else 'disabled'
        try: self._count_e.config(state=st)
        except: pass

    def _play_start(self):
        if self._ui_playing or self._rec.playing or getattr(self, '_play_countdown_active', False):
            return
        if not self._rec.events and getattr(self, '_play_recent_paths', None):
            self._load_play_recent()
        if not self._rec.events:
            messagebox.showwarning("NexaFlow", "Record or load a workflow first."); return
        try:
            sd = max(0.0, float(self._sdelay.get() or 0))
        except ValueError:
            messagebox.showerror("NexaFlow", "Enter a valid start delay.")
            return
        if sd > 0:
            self._play_countdown_active = True
            self._countdown_play(int(sd))
        else:
            self._do_play()

    def _load_play_recent(self, ev=None):
        if not getattr(self, '_play_recent_paths', None):
            return
        idx = self._play_recent_cb.current()
        if idx >= 0 and idx < len(self._play_recent_paths):
            self._do_load(self._play_recent_paths[idx])
            try:
                self._play_wf_label.config(text=f"Workflow: {self._rec.name}")
            except Exception:
                pass

    def _delete_play_workflow(self):
        if not getattr(self, '_play_recent_paths', None):
            messagebox.showinfo("NexaFlow", "No saved workflows to delete.")
            return
        idx = self._play_recent_cb.current()
        if idx < 0 or idx >= len(self._play_recent_paths):
            messagebox.showwarning("NexaFlow", "Select a workflow first.")
            return
        path = Path(self._play_recent_paths[idx])
        if not path.exists():
            CFG.remove_recent(str(path))
            self._refresh_recent_workflows()
            return
        if not messagebox.askyesno("Delete Workflow",
                                   f"Delete this saved workflow?\n\n{path.name}"):
            return
        try:
            path.unlink()
        except Exception as exc:
            messagebox.showerror("NexaFlow", f"Failed to delete workflow:\n{exc}")
            return
        CFG.remove_recent(str(path))
        self._refresh_recent_workflows()
        self._play_wf_label.config(text="No workflow loaded")
        messagebox.showinfo("NexaFlow", f"Deleted: {path.name}")

    def _countdown_play(self, n):
        self._play_countdown_remaining = max(0, int(n))
        if n <= 0:
            self._play_info.config(text="▶  Starting…")
            if self._focus_mode_window:
                self._focus_mode_window.show_message("Playback starts now.", C['amber'])
            self._play_countdown_after_id = self.after(100, self._do_play)
            return
        self._play_btn.config(state='disabled')
        self._play_info.config(text=f"⏳  Starting in {n}…")
        if self._focus_mode_window:
            self._focus_mode_window.show_countdown("Playing", n)
        self._play_countdown_after_id = self.after(1000, lambda: self._countdown_play(n - 1))

    def _do_play(self):
        self._play_countdown_after_id = None
        self._play_countdown_active = False
        self._play_countdown_remaining = 0
        mode  = self._lmode.get()
        try:
            count = int(self._lcount.get() or 1)
            delay = float(self._ldelay.get() or 1.0)
            speed = float(self._speed.get())
        except ValueError:
            messagebox.showerror("NexaFlow", "Enter valid numbers for playback settings.")
            return
        if mode == 'count' and count <= 0:
            messagebox.showerror("NexaFlow", "Repeat count must be greater than 0.")
            return
        if delay < 0:
            messagebox.showerror("NexaFlow", "Loop delay cannot be negative.")
            return
        speed = max(0.1, min(5.0, speed))
        CFG.set('speed', speed)

        self._ui_playing = True
        self._rec.halt()
        self._rec._stop_flag = False
        self._stop_timer()
        self._play_t0 = time.time()
        self._play_paused_total = 0.0
        self._play_pause_started = 0.0
        self._play_current_event = 0
        self._play_total_events = len(self._rec.events)
        self._play_current_loop = 1
        self._play_total_loops = 1 if mode == 'once' else (count if mode == 'count' else None)
        self._timer_mode = 'play'
        self._play_btn.config(state='disabled', text="▶  PLAYING…", bg=C['green2'])
        self._pause_btn.config(state='normal')
        self._status("PLAYING", C['amber'])
        self._start_timer()
        self._pvar.set(0)
        LOG.add(f"Playback started — mode:{mode}  speed:{speed:.1f}×", 'play')
        if self._focus_mode_window:
            self._focus_mode_window.set_status("Playing", C['amber'])
            self._focus_mode_window._refresh()
        if CFG.get('hide_windows_during_playback', False):
            if self._focus_mode_window:
                self._focus_mode_window.hide_for_playback()
            try:
                self.iconify()
            except Exception:
                pass
        else:
            try:
                _set_window_click_through(self, True)
            except Exception:
                pass
            if self._focus_mode_window:
                self._focus_mode_window.protect_for_playback()
        self._start_playback_safety_listener()

        def prog(i, t):
            pct = i / t * 100
            def update():
                try:
                    self._play_current_event = i
                    self._play_total_events = t
                    self._pvar.set(pct)
                    self._play_info.config(text=f"Event {i} / {t}")
                except Exception:
                    pass
            self.after(0, update)

        def on_loop(n):
            if mode == 'once':
                self._play_current_loop = 1
            elif mode == 'count':
                self._play_current_loop = min(n + 1, count)
            else:
                self._play_current_loop = n + 1
            txt = f"Loop {n}/{count}" if mode == 'count' else f"Loop {n}"
            self.after(0, lambda: self._loop_ctr.config(text=txt))

        def done():
            self.after(0, self._play_done)

        self._rec.play(mode=mode, count=count, delay=delay, speed=speed,
                       on_prog=prog, on_loop=on_loop, on_done=done)
        if self._focus_mode_window:
            self._focus_mode_window.set_status("Playing", C['amber'])
            self._focus_mode_window.after(120, self._focus_mode_window._refresh)

    def _toggle_pause(self):
        if not (self._ui_playing or self._rec.playing):
            return
        self._rec.toggle_pause()
        if self._rec.paused:
            self._play_pause_started = time.time()
            self._pause_btn.config(text="▶", bg=C['green'])
            self._status("PAUSED", C['orange'])
        else:
            if self._play_pause_started:
                self._play_paused_total += max(0.0, time.time() - self._play_pause_started)
                self._play_pause_started = 0.0
            self._pause_btn.config(text="Ⅱ", bg=C['amber'])
            self._status("PLAYING", C['amber'])

    def _play_stop(self):
        self._cancel_play_countdown()
        self._ui_playing = False
        self._stop_playback_safety_listener()
        self._rec.halt()
        self._dl.halt()
        self._play_done()

    def _cancel_play_countdown(self):
        if self._play_countdown_after_id is not None:
            try:
                self.after_cancel(self._play_countdown_after_id)
            except Exception:
                pass
            self._play_countdown_after_id = None
        self._play_countdown_active = False
        self._play_countdown_remaining = 0

    def _play_done(self):
        self._stop_playback_safety_listener()
        self._play_countdown_active = False
        self._play_countdown_remaining = 0
        self._play_countdown_after_id = None
        self._ui_playing = False
        self._stop_timer()
        self._dur_lbl.config(text="0.0 s")
        self._play_btn.config(state='normal', text="▶   PLAY", bg=C['green'])
        self._pause_btn.config(state='disabled', text="Ⅱ", bg=C['amber'])
        self._status("READY", C['green'])
        self._play_info.config(text="✓  Complete")
        self._pvar.set(100)
        self._play_t0 = 0.0
        self._play_paused_total = 0.0
        self._play_pause_started = 0.0
        self._play_current_event = 0
        self._play_total_events = 0
        self._play_current_loop = 0
        self._play_total_loops = None
        LOG.add("Playback complete", 'play')
        if self._ss_on_done.get():
            self._take_screenshot("play_done")
        if CFG.get('hide_windows_during_playback', False):
            if self._focus_mode_window:
                self._focus_mode_window.restore_after_playback()
            try:
                self.deiconify()
                self.lift()
                self.attributes('-topmost', CFG.get('always_on_top', True))
                self.after(250, lambda: self.attributes('-topmost', CFG.get('always_on_top', True)))
            except Exception:
                pass
        else:
            try:
                _set_window_click_through(self, False)
            except Exception:
                pass
            if self._focus_mode_window:
                self._focus_mode_window.restore_after_click_protection()

    def _start_playback_safety_listener(self):
        self._stop_playback_safety_listener()
        self._playback_safety_triggered = False
        self._playback_safety_armed_at = time.time() + 0.8
        if not CFG.get('stop_on_user_input_during_playback', False):
            return
        if not HAS_PYNPUT or not pk or not pm:
            LOG.add("Playback safety unavailable: input listener is not available.", 'error')
            return

        def should_stop():
            if not self._ui_playing or self._playback_safety_triggered:
                return None
            if time.time() < getattr(self, '_playback_safety_armed_at', 0.0):
                return None
            if getattr(self._rec, 'is_synthetic_input_active', lambda: False)():
                return None
            self._playback_safety_triggered = True
            LOG.add("Playback stopped by user input safety.", 'play')
            self.after(0, self._play_stop)
            return False

        try:
            self._playback_safety_listener_keyboard = pk.Listener(
                on_press=lambda key: should_stop(),
                on_release=lambda key: should_stop()
            )
            self._playback_safety_listener_mouse = pm.Listener(
                on_move=lambda x, y: should_stop(),
                on_click=lambda x, y, button, pressed: should_stop(),
                on_scroll=lambda x, y, dx, dy: should_stop()
            )
            self._playback_safety_listener_keyboard.start()
            self._playback_safety_listener_mouse.start()
        except Exception as exc:
            LOG.add(f"Playback safety failed: {exc}", 'error')
            self._stop_playback_safety_listener()

    def _stop_playback_safety_listener(self):
        for attr in ('_playback_safety_listener_keyboard', '_playback_safety_listener_mouse'):
            listener = getattr(self, attr, None)
            if listener:
                try:
                    listener.stop()
                except Exception:
                    pass
                setattr(self, attr, None)

    def _toggle_focus_mode(self):
        if self._focus_mode_window:
            self._focus_mode_window._exit_focus_mode()
        else:
            self._focus_mode_window = FocusModeWindow(
                self, self._rec,
                on_rec=self._toggle_rec,
                on_play=self._play_start,
                on_pause=self._toggle_pause,
                on_stop=self._play_stop
            )

    def _update_focus_opacity(self, value):
        value = max(0.05, min(1.0, float(value)))
        try:
            self._focus_opacity_pct.set(int(round(value * 100)))
        except Exception:
            pass
        CFG.set('focus_mode_opacity', value)
        if self._focus_mode_window:
            self._focus_mode_window.set_opacity(value)

    def _apply_focus_opacity_percent(self):
        try:
            pct = max(5, min(100, int(self._focus_opacity_pct.get())))
        except Exception:
            pct = 95
        self._focus_opacity_pct.set(pct)
        value = pct / 100
        self._focus_opacity_var.set(value)
        self._update_focus_opacity(value)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   TAB 3 — DATA LOOP
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _tab_data(self):
        tab = ttk.Frame(self._nb, style='NF.TFrame')
        self._nb.add(tab, text="  ⟳  DATA  ")
        p = tk.Frame(tab, bg=C['bg'])
        p.pack(fill='both', expand=True, padx=18, pady=12)

        info = tk.Frame(p, bg=C['card2'], highlightthickness=1,
                        highlightbackground=C['border2'])
        info.pack(fill='x', pady=(0, 10))
        tk.Label(info,
                 text="Feed a list → clipboard → workflow → repeat for each item",
                 bg=C['card2'], fg=C['text2'], font=_f(8), pady=10).pack()

        fr = tk.Frame(p, bg=C['bg'])
        fr.pack(fill='x', pady=2)
        self._dlfile_lbl = tk.Label(fr, text="No file loaded",
                                    bg=C['bg'], fg=C['muted'], font=_f(8))
        self._dlfile_lbl.pack(side='left')
        self._ghost_btn(fr, "Load .txt / .csv", self._load_dl_file).pack(side='right')

        _lbl(p, "Items  (one per line):", 8).pack(anchor='w', pady=(6, 3))
        sf, self._dl_text = _scroll_text(p, height=6)
        sf.pack(fill='x')

        sr = tk.Frame(p, bg=C['bg'])
        sr.pack(fill='x', pady=2)
        self._dl_count_lbl = tk.Label(sr, text="0 items", bg=C['bg'],
                                       fg=C['muted'], font=_f(8))
        self._dl_count_lbl.pack(side='left')
        self._dl_text.bind('<KeyRelease>', lambda _: self._count_items())

        rf = tk.Frame(p, bg=C['card2'], highlightthickness=1,
                      highlightbackground=C['border'])
        rf.pack(fill='x', pady=(6, 0))
        rr = tk.Frame(rf, bg=C['card2'])
        rr.pack(fill='x', padx=10, pady=8)
        tk.Label(rr, text="Start from item #:", bg=C['card2'], fg=C['text2'],
                 font=_f(8)).pack(side='left')
        self._dl_resume = tk.StringVar(value="1")
        _entry(rr, self._dl_resume, w=5).pack(side='left', padx=8)
        tk.Label(rr, text="(1 = beginning)", bg=C['card2'], fg=C['muted'],
                 font=_f(7)).pack(side='left')

        tc = tk.Frame(p, bg=C['bg'])
        tc.pack(fill='x', pady=6)
        tc.columnconfigure(0, weight=1); tc.columnconfigure(1, weight=1)
        self._dl_pre  = tk.StringVar(value="0.5")
        self._dl_post = tk.StringVar(value="1.0")
        for col, label, var, unit in [
            (0, "Delay Before", self._dl_pre,  "sec"),
            (1, "Delay After",  self._dl_post, "sec"),
        ]:
            tile = tk.Frame(tc, bg=C['card2'],
                            highlightthickness=1, highlightbackground=C['border'])
            tile.grid(row=0, column=col, padx=(0 if col == 0 else 3, 0), sticky='ew')
            tk.Label(tile, text=label, bg=C['card2'], fg=C['muted'], font=_f(7)).pack(pady=(8, 2))
            _entry(tile, var, w=6).pack(pady=2)
            tk.Label(tile, text=unit, bg=C['card2'], fg=C['muted'], font=_f(7)).pack(pady=(2, 8))

        self._dl_info = tk.Label(p, text="", bg=C['bg'], fg=C['amber'], font=_f(8))
        self._dl_info.pack(pady=(6, 2))
        self._dl_pvar = tk.DoubleVar(value=0)
        ttk.Progressbar(p, variable=self._dl_pvar, maximum=100,
                        style='Green.Horizontal.TProgressbar').pack(fill='x')

        bf = tk.Frame(p, bg=C['bg'])
        bf.pack(fill='x', pady=8)
        self._dl_btn = self._big_btn(bf, "▶   START DATA LOOP", C['green'], self._dl_start)
        self._dl_btn.pack(side='left', expand=True, fill='x', padx=(0, 3))
        self._ghost_btn(bf, "⏹ Stop", self._dl_stop).pack(side='right')

    def _load_dl_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text", "*.txt"), ("CSV", "*.csv"), ("All", "*.*")])
        if not path: return
        with open(path, encoding='utf-8', errors='ignore') as f:
            text = f.read()
        self._dl_text.delete('1.0', 'end')
        self._dl_text.insert('1.0', text)
        self._dlfile_lbl.config(text=Path(path).name, fg=C['green'])
        self._count_items()
        LOG.add(f"Data file loaded: {Path(path).name}", 'data')

    def _count_items(self):
        items = [l for l in self._dl_text.get('1.0', 'end').splitlines() if l.strip()]
        self._dl_count_lbl.config(text=f"{len(items)} items")
        self._dl_items = items

    def _dl_start(self):
        if not self._rec.events:
            messagebox.showwarning("NexaFlow", "Record or load a workflow first."); return
        self._count_items()
        items = self._dl_items
        if not items:
            messagebox.showwarning("NexaFlow", "No items in the list."); return

        try:
            start_from = max(0, int(self._dl_resume.get() or 1) - 1)
            pre_delay = max(0.0, float(self._dl_pre.get() or 0.5))
            post_delay = max(0.0, float(self._dl_post.get() or 1.0))
        except ValueError:
            messagebox.showerror("NexaFlow", "Enter valid numbers for start item and delays.")
            return
        if start_from >= len(items):
            messagebox.showwarning("NexaFlow", "Start item is beyond the end of the list.")
            return
        if not getattr(self._rec, 'playing', False):
            self._dl.last_index = start_from
        self._dl_pvar.set(0)
        self._dl_btn.config(state='disabled', bg=C['muted'])
        self._status("DATA LOOP", C['amber'])

        def on_item(i, total, item):
            pct     = i / total * 100
            preview = item[:32] + ('…' if len(item) > 32 else '')
            def update():
                try:
                    self._dl_pvar.set(pct)
                    self._dl_info.config(text=f"Item {i}/{total}: {preview}")
                except Exception:
                    pass
            self.after(0, update)

        def done():
            def update_done():
                try:
                    self._dl_btn.config(state='normal', bg=C['green'])
                    self._status("READY", C['green'])
                    self._dl_info.config(text=f"✓  All {len(items)} items complete")
                except Exception:
                    pass
            self.after(0, update_done)

        self._dl.run(
            items=items,
            pre_delay=pre_delay,
            post_delay=post_delay,
            speed=self._speed.get(),
            start_from=start_from,
            on_item=on_item,
            on_done=done)

    def _dl_stop(self):
        self._dl.halt()
        last = self._dl.last_index + 1
        self._dl_btn.config(state='normal', bg=C['green'])
        self._status("READY", C['green'])
        self._dl_resume.set(str(max(1, last + 1)))
        self._dl_info.config(text=f"⏹  Stopped at item {last}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   TAB 4 — FILES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _tab_files(self):
        tab = ttk.Frame(self._nb, style='NF.TFrame')
        self._nb.add(tab, text="  ◫  FILES  ")
        p = tk.Frame(tab, bg=C['bg'])
        p.pack(fill='both', expand=True, padx=18, pady=12)

        self._ft_folder = ''
        fr = tk.Frame(p, bg=C['bg'])
        fr.pack(fill='x')
        self._ft_fol_lbl = tk.Label(fr, text="No folder selected",
                                    bg=C['bg'], fg=C['muted'], font=_f(8), anchor='w')
        self._ft_fol_lbl.pack(side='left', expand=True, fill='x')
        self._ghost_btn(fr, "◫  Choose Folder", self._ft_pick).pack(side='right')

        ef = tk.Frame(p, bg=C['bg'])
        ef.pack(fill='x', pady=6)
        tk.Label(ef, text="Extension:", bg=C['bg'], fg=C['text2'], font=_f(8)).pack(side='left')
        self._ft_ext = tk.StringVar(value='*')
        _entry(ef, self._ft_ext, w=6).pack(side='left', padx=8)
        tk.Label(ef, text="* = all", bg=C['bg'], fg=C['muted'], font=_f(7)).pack(side='left')
        self._ghost_btn(ef, "⌕ Scan", self._ft_scan).pack(side='right')

        lf = tk.Frame(p, bg=C['card'],
                      highlightthickness=1, highlightbackground=C['border2'])
        lf.pack(fill='x', pady=3)
        sb = tk.Scrollbar(lf, orient='vertical', bg=C['panel'],
                          troughcolor=C['card'], relief='flat', width=6)
        self._ft_list = tk.Listbox(lf, bg=C['card'], fg=C['text2'],
                                   font=_f(8, mono=True),
                                   selectbackground=C['accent3'],
                                   selectforeground=C['accent'],
                                   activestyle='none', relief='flat', height=5,
                                   selectmode='extended', yscrollcommand=sb.set)
        sb.config(command=self._ft_list.yview)
        self._ft_list.pack(side='left', fill='both', expand=True, padx=2, pady=2)
        sb.pack(side='right', fill='y')

        stats_row = tk.Frame(p, bg=C['bg'])
        stats_row.pack(fill='x', pady=2)
        self._ft_cnt = tk.Label(stats_row, text="0 files", bg=C['bg'],
                                fg=C['muted'], font=_f(7))
        self._ft_cnt.pack(side='left')
        self._ft_size_lbl = tk.Label(stats_row, text="", bg=C['bg'],
                                     fg=C['muted'], font=_f(7))
        self._ft_size_lbl.pack(side='right')

        tk.Frame(p, bg=C['border'], height=1).pack(fill='x', pady=6)

        _section_header(p, "Rename", icon="✏").pack(anchor='w', pady=(0, 4))
        rc = _card(p)
        rc.pack(fill='x', pady=(0, 6))

        row1 = tk.Frame(rc, bg=C['card'])
        row1.pack(fill='x', padx=10, pady=(8, 3))
        for label, attr, w in [("Prefix:", '_rn_pre', 10), ("Suffix:", '_rn_suf', 10)]:
            tk.Label(row1, text=label, bg=C['card'], fg=C['text2'],
                     font=_f(8), width=7, anchor='w').pack(side='left')
            v = tk.StringVar()
            setattr(self, attr, v)
            _entry(row1, v, w=w).pack(side='left', padx=(0, 10))

        row2 = tk.Frame(rc, bg=C['card'])
        row2.pack(fill='x', padx=10, pady=3)
        self._rn_find = tk.StringVar()
        self._rn_rep  = tk.StringVar()
        for label, attr, w in [("Find:", '_rn_find', 10), ("Replace:", '_rn_rep', 10)]:
            tk.Label(row2, text=label, bg=C['card'], fg=C['text2'],
                     font=_f(8), width=7, anchor='w').pack(side='left')
            _entry(row2, getattr(self, attr), w=w).pack(side='left', padx=(0, 10))

        row3 = tk.Frame(rc, bg=C['card'])
        row3.pack(fill='x', padx=10, pady=3)
        self._rn_date = tk.BooleanVar(value=False)
        self._rn_ctr  = tk.BooleanVar(value=False)
        for var, label in [(self._rn_date, "Add date"), (self._rn_ctr, "Add counter")]:
            self._check(row3, label, var, bg=C['card']).pack(side='left', padx=(0, 10))
        tk.Frame(rc, bg=C['card'], height=4).pack()
        self._ghost_btn(rc, "▶  Rename Files",
                        lambda: self._ft_op('rename')).pack(anchor='e', padx=10, pady=(0, 8))

        _section_header(p, "Organize", icon="◈").pack(anchor='w', pady=(4, 4))
        oc = _card(p)
        oc.pack(fill='x')
        bf = tk.Frame(oc, bg=C['card'])
        bf.pack(fill='x', padx=10, pady=8)
        for label, op, color in [
            ("Move →",   'move',      C['blue']),
            ("Copy →",   'copy',      C['accent2']),
            ("By Type",  'sort_type', C['purple2']),
            ("By Date",  'sort_date', C['amber2']),
            ("🗑 Delete", 'delete',   C['red2']),
        ]:
            tk.Button(bf, text=label, command=lambda o=op: self._ft_op(o),
                      bg=color, fg=C['text'], font=_f(8),
                      relief='flat', cursor='hand2', padx=8, pady=5,
                      activebackground=color).pack(side='left', padx=(0, 3))

        self._ft_res = tk.Label(p, text="", bg=C['bg'], fg=C['green'], font=_f(8))
        self._ft_res.pack(pady=4)

    def _ft_pick(self):
        folder = filedialog.askdirectory()
        if folder:
            self._ft_folder = folder
            name = Path(folder).name
            self._ft_fol_lbl.config(text=f"  {name}  —  {folder}", fg=C['text2'])
            self._ft_scan()

    def _ft_scan(self):
        if not self._ft_folder:
            messagebox.showwarning("NexaFlow", "Choose a folder first.")
            return
        self._files = self._fe.scan(self._ft_folder, self._ft_ext.get())
        self._ft_list.delete(0, 'end')
        for f in self._files[:200]:
            self._ft_list.insert('end', f"  {f.name}")
        n = len(self._files)
        self._ft_cnt.config(text=f"{n} file{'s' if n != 1 else ''}"
                            + (" (showing first 200)" if n > 200 else ""))
        try:
            total = sum(f.stat().st_size for f in self._files)
            mb    = round(total / 1024 / 1024, 1)
            self._ft_size_lbl.config(text=f"{mb} MB total")
        except: pass

    def _ft_op(self, op):
        if not self._files:
            messagebox.showwarning("NexaFlow", "Scan a folder first."); return
        sel_idx = list(self._ft_list.curselection())
        files   = [self._files[i] for i in sel_idx] if sel_idx else self._files
        try:
            if op == 'rename':
                r = self._fe.rename(files,
                                    prefix=self._rn_pre.get(), suffix=self._rn_suf.get(),
                                    find=self._rn_find.get(), replace=self._rn_rep.get(),
                                    date_prefix=self._rn_date.get(), counter=self._rn_ctr.get())
                self._ft_res.config(text=f"✓  Renamed {len(r)} files", fg=C['green'])
                LOG.add(f"Renamed {len(r)} files", 'file')
            elif op in ('move', 'copy'):
                dest = filedialog.askdirectory(title=f"{'Move' if op=='move' else 'Copy'} to…")
                if not dest: return
                fn = self._fe.move if op == 'move' else self._fe.copy
                r  = fn(files, dest)
                self._ft_res.config(text=f"✓  {op.title()}d {len(r)} files", fg=C['green'])
                LOG.add(f"{op.title()}d {len(r)} files → {dest}", 'file')
            elif op == 'sort_type':
                if not messagebox.askyesno("Sort by Type", "Move files into subfolders by extension?"): return
                r = self._fe.sort_by_type(self._ft_folder)
                self._ft_res.config(text=f"✓  Sorted {len(r)} files by type", fg=C['green'])
            elif op == 'sort_date':
                if not messagebox.askyesno("Sort by Date", "Move files into YYYY-MM subfolders?"): return
                r = self._fe.sort_by_date(self._ft_folder)
                self._ft_res.config(text=f"✓  Sorted {len(r)} files by date", fg=C['green'])
            elif op == 'delete':
                if not messagebox.askyesno("Delete Files",
                    f"Permanently delete {len(files)} file(s)?\nThis cannot be undone!"): return
                r = self._fe.delete(files)
                self._ft_res.config(text=f"✓  Deleted {len(r)} files", fg=C['red'])
                LOG.add(f"Deleted {len(r)} files", 'file')
            self._ft_scan()
        except Exception as e:
            messagebox.showerror("NexaFlow Error", str(e))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   TAB 5 — SCHEDULER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _tab_scheduler(self):
        tab = ttk.Frame(self._nb, style='NF.TFrame')
        self._nb.add(tab, text="  ◷  SCHED  ")
        p = tk.Frame(tab, bg=C['bg'])
        p.pack(fill='both', expand=True, padx=18, pady=12)

        _section_header(p, "New Job", icon="◆").pack(anchor='w', pady=(0, 6))
        ac = _card(p)
        ac.pack(fill='x', pady=(0, 10))

        nr = tk.Frame(ac, bg=C['card'])
        nr.pack(fill='x', padx=10, pady=(10, 4))
        tk.Label(nr, text="Name:", bg=C['card'], fg=C['text2'],
                 font=_f(8), width=10, anchor='w').pack(side='left')
        self._sched_name = tk.StringVar(value="My Schedule")
        _entry(nr, self._sched_name).pack(side='left', fill='x', expand=True)

        tr = tk.Frame(ac, bg=C['card'])
        tr.pack(fill='x', padx=10, pady=4)
        tk.Label(tr, text="Run at:", bg=C['card'], fg=C['text2'],
                 font=_f(8), width=10, anchor='w').pack(side='left')
        self._sched_h = tk.StringVar(value=datetime.now().strftime("%H"))
        self._sched_m = tk.StringVar(value=datetime.now().strftime("%M"))
        _entry(tr, self._sched_h, w=3).pack(side='left')
        tk.Label(tr, text=":", bg=C['card'], fg=C['text'], font=_f(12, True)).pack(side='left', padx=2)
        _entry(tr, self._sched_m, w=3).pack(side='left')
        tk.Label(tr, text="  HH:MM", bg=C['card'], fg=C['muted'], font=_f(7)).pack(side='left', padx=8)

        mr = tk.Frame(ac, bg=C['card'])
        mr.pack(fill='x', padx=10, pady=4)
        tk.Label(mr, text="Mode:", bg=C['card'], fg=C['text2'],
                 font=_f(8), width=10, anchor='w').pack(side='left')
        self._sched_mode = tk.StringVar(value='once')
        for v, label in [('once', 'Once'), ('repeat', 'Repeat every')]:
            tk.Radiobutton(mr, text=f" {label}", variable=self._sched_mode, value=v,
                           bg=C['card'], fg=C['text2'], selectcolor=C['card2'],
                           activebackground=C['card'], font=_f(8), relief='flat',
                           cursor='hand2').pack(side='left', padx=4)
        self._sched_repeat = tk.StringVar(value="60")
        _entry(mr, self._sched_repeat, w=5).pack(side='left', padx=4)
        tk.Label(mr, text="sec", bg=C['card'], fg=C['muted'], font=_f(7)).pack(side='left')

        lr = tk.Frame(ac, bg=C['card'])
        lr.pack(fill='x', padx=10, pady=(4, 10))
        tk.Label(lr, text="Loops:", bg=C['card'], fg=C['text2'],
                 font=_f(8), width=10, anchor='w').pack(side='left')
        self._sched_loops = tk.StringVar(value="1")
        _entry(lr, self._sched_loops, w=5).pack(side='left')
        tk.Label(lr, text="times per run", bg=C['card'], fg=C['muted'], font=_f(7)).pack(side='left', padx=8)

        self._ghost_btn(ac, "＋  Add Job", self._sched_add).pack(anchor='e', padx=10, pady=(0, 8))

        _section_header(p, "Scheduled Jobs", icon="◆").pack(anchor='w', pady=(4, 4))
        jf = tk.Frame(p, bg=C['card'],
                      highlightthickness=1, highlightbackground=C['border2'])
        jf.pack(fill='both', expand=True, pady=(0, 4))
        jsb = tk.Scrollbar(jf, orient='vertical', bg=C['panel'],
                           troughcolor=C['card'], relief='flat', width=6)
        self._sched_list = tk.Listbox(jf, bg=C['card'], fg=C['text2'],
                                      font=_f(8, mono=True),
                                      selectbackground=C['accent3'],
                                      selectforeground=C['accent'],
                                      activestyle='none', relief='flat', height=5,
                                      yscrollcommand=jsb.set)
        jsb.config(command=self._sched_list.yview)
        self._sched_list.pack(side='left', fill='both', expand=True, padx=2, pady=2)
        jsb.pack(side='right', fill='y')

        bf = tk.Frame(p, bg=C['bg'])
        bf.pack(fill='x', pady=4)
        self._ghost_btn(bf, "⏸  Pause/Resume", self._sched_toggle).pack(side='left', padx=(0, 4))
        self._ghost_btn(bf, "✕  Remove",        self._sched_remove).pack(side='left')

        self._sched_status = tk.Label(p, text="No jobs scheduled",
                                      bg=C['bg'], fg=C['muted'], font=_f(8))
        self._sched_status.pack(pady=2)
        # Start a single refresh loop
        self._sched_refresh_loop()

    def _sched_refresh_loop(self):
        """Single recurring refresh — never spawns duplicates."""
        if self._sched_after_id:
            self.after_cancel(self._sched_after_id)
        self._sched_list.delete(0, 'end')
        jobs = self._sched.get_jobs()
        for j in jobs:
            state = "ON " if j['enabled'] else "OFF"
            ran   = f"  ×{j['run_count']}" if j['run_count'] else ""
            line  = f"  [{state}]  {j['name']:<18}  {j['run_at'].strftime('%H:%M')}  {j['mode']}{ran}"
            self._sched_list.insert('end', line)
        n = len(jobs)
        if n:
            self._sched_status.config(
                text=f"{n} job{'s' if n > 1 else ''}  ·  next: {jobs[0]['run_at'].strftime('%H:%M:%S')}",
                fg=C['text2'])
        else:
            self._sched_status.config(text="No jobs scheduled", fg=C['muted'])
        self._sched_after_id = self.after(2000, self._sched_refresh_loop)

    def _sched_add(self):
        if not self._rec.events:
            messagebox.showwarning("NexaFlow", "Record or load a workflow first."); return
        try:
            h = int(self._sched_h.get())
            m = int(self._sched_m.get())
            repeat_sec = int(self._sched_repeat.get() or 60)
            loop_count = int(self._sched_loops.get() or 1)
        except ValueError:
            messagebox.showerror("NexaFlow", "Enter valid numbers for time, repeat seconds, and loops."); return
        if not (0 <= h <= 23 and 0 <= m <= 59):
            messagebox.showerror("NexaFlow", "Enter a valid 24-hour time from 00:00 to 23:59."); return
        if self._sched_mode.get() == 'repeat' and repeat_sec <= 0:
            messagebox.showerror("NexaFlow", "Repeat seconds must be greater than 0."); return
        if loop_count <= 0:
            messagebox.showerror("NexaFlow", "Loops must be greater than 0."); return
        now = datetime.now(self._tz) if self._tz else datetime.now().astimezone()
        run_at = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if run_at < now:
            run_at += timedelta(days=1)
        self._sched.add_job(
            name       = self._sched_name.get().strip() or "Scheduled workflow",
            run_at     = run_at,
            mode       = self._sched_mode.get(),
            repeat_sec = repeat_sec,
            loop_count = loop_count,
            speed      = self._speed.get() if hasattr(self, '_speed') else 1.0)
        self._sched_refresh_loop()

    def _sched_toggle(self):
        sel  = self._sched_list.curselection()
        if not sel:
            messagebox.showinfo("NexaFlow", "Select a scheduled job first."); return
        jobs = self._sched.get_jobs()
        if sel[0] < len(jobs):
            enabled = self._sched.toggle_job(jobs[sel[0]]['id'])
            state   = "enabled" if enabled else "paused"
            LOG.add(f"Job {jobs[sel[0]]['name']} {state}", 'sched')
            self._sched_refresh_loop()

    def _sched_remove(self):
        sel  = self._sched_list.curselection()
        if not sel:
            messagebox.showinfo("NexaFlow", "Select a scheduled job first."); return
        jobs = self._sched.get_jobs()
        if sel[0] < len(jobs):
            self._sched.remove_job(jobs[sel[0]]['id'])
            LOG.add(f"Job removed: {jobs[sel[0]]['name']}", 'sched')
            self._sched_refresh_loop()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   TAB 6 — EVENTS VIEWER / EDITOR  (NEW)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _tab_events(self):
        tab = ttk.Frame(self._nb, style='NF.TFrame')
        self._nb.add(tab, text="  ◈  EVENTS  ")
        p = tk.Frame(tab, bg=C['bg'])
        p.pack(fill='both', expand=True, padx=18, pady=12)

        # Header row
        hdr = tk.Frame(p, bg=C['bg'])
        hdr.pack(fill='x', pady=(0, 6))
        tk.Label(hdr, text="EVENT EDITOR", bg=C['bg'],
                 fg=C['accent'], font=_f(8, True)).pack(side='left')
        self._ev_count_lbl = tk.Label(hdr, text="0 events", bg=C['bg'],
                                      fg=C['muted'], font=_f(7))
        self._ev_count_lbl.pack(side='right')

        # Filter row
        fr = tk.Frame(p, bg=C['bg'])
        fr.pack(fill='x', pady=(0, 4))
        tk.Label(fr, text="Filter:", bg=C['bg'], fg=C['text2'], font=_f(8)).pack(side='left')
        self._ev_filter = tk.StringVar(value="all")
        for v, lbl in [("all","All"), ("click","Clicks"), ("kd","Keys"),
                        ("scroll","Scroll"), ("move","Move"), ("wait","Wait"), ("type","Type")]:
            tk.Radiobutton(fr, text=lbl, variable=self._ev_filter, value=v,
                           bg=C['bg'], fg=C['text2'], selectcolor=C['card2'],
                           activebackground=C['bg'], font=_f(7), relief='flat',
                           cursor='hand2',
                           command=self._refresh_events_tab).pack(side='left', padx=2)

        # Treeview
        tree_frame = tk.Frame(p, bg=C['card'],
                              highlightthickness=1, highlightbackground=C['border2'])
        tree_frame.pack(fill='both', expand=True, pady=(0, 4))

        cols = ('#', 'type', 'time', 'details')
        self._ev_tree = ttk.Treeview(tree_frame, columns=cols, show='headings',
                                      style='NF.Treeview', selectmode='browse')
        self._ev_tree.heading('#',       text='#',       anchor='center')
        self._ev_tree.heading('type',    text='TYPE',    anchor='w')
        self._ev_tree.heading('time',    text='TIME(s)', anchor='center')
        self._ev_tree.heading('details', text='DETAILS', anchor='w')
        self._ev_tree.column('#',       width=40,  minwidth=35,  anchor='center', stretch=False)
        self._ev_tree.column('type',    width=70,  minwidth=60,  anchor='w',      stretch=False)
        self._ev_tree.column('time',    width=65,  minwidth=55,  anchor='center', stretch=False)
        self._ev_tree.column('details', width=300, minwidth=120, anchor='w',      stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self._ev_tree.yview)
        self._ev_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self._ev_tree.pack(side='left', fill='both', expand=True, padx=2, pady=2)

        # Tag colors per type
        for tag, color in [
            ('click',  C['green']),  ('kd',    C['amber']),
            ('ku',     C['amber2']), ('scroll', C['blue']),
            ('move',   C['muted']),  ('wait',   C['purple']),
            ('type',   C['accent']),
        ]:
            self._ev_tree.tag_configure(tag, foreground=color)

        # Action buttons
        bf = tk.Frame(p, bg=C['bg'])
        bf.pack(fill='x', pady=(0, 4))

        self._ghost_btn(bf, "🗑  Delete Selected",
                        self._ev_delete_selected).pack(side='left', padx=(0, 3))
        self._ghost_btn(bf, "＋ Wait",
                        self._ev_insert_wait).pack(side='left', padx=(0, 3))
        self._ghost_btn(bf, "＋ Type Text",
                        self._ev_insert_type).pack(side='left', padx=(0, 3))
        self._ghost_btn(bf, "🗑 Clear ALL",
                        self._ev_clear_all).pack(side='right')
        self._ghost_btn(bf, "📋 Export",
                        self._ev_export).pack(side='right', padx=(0, 3))

        # Stats summary
        self._ev_stats_lbl = tk.Label(p, text="", bg=C['bg'],
                                       fg=C['muted'], font=_f(7))
        self._ev_stats_lbl.pack(anchor='w')

    def _refresh_events_tab(self):
        """Repopulate the events treeview."""
        tree    = self._ev_tree
        filt    = self._ev_filter.get() if hasattr(self, '_ev_filter') else 'all'
        events  = self._rec.events

        for item in tree.get_children():
            tree.delete(item)

        shown = 0
        for i, e in enumerate(events):
            t = e['t']
            if filt != 'all' and t != filt:
                continue
            ts = f"{e.get('ts', 0):.3f}"
            if t == 'click':
                btn_name = 'L' if 'left' in e.get('btn','') else ('R' if 'right' in e.get('btn','') else 'M')
                action   = '↓' if e.get('pressed') else '↑'
                details  = f"({e['x']}, {e['y']})  {btn_name}{action}"
            elif t == 'move':
                details = f"({e['x']}, {e['y']})"
            elif t == 'scroll':
                details = f"({e['x']}, {e['y']})  Δ({e.get('dx',0)}, {e.get('dy',0)})"
            elif t in ('kd', 'ku'):
                action  = '↓' if t == 'kd' else '↑'
                details = f"key={e.get('k','?')}  {action}"
            elif t == 'wait':
                details = f"{e.get('secs', 0)}s"
            elif t == 'type':
                txt     = e.get('text', '')
                details = txt[:60] + ('…' if len(txt) > 60 else '')
            else:
                details = str(e)

            tree.insert('', 'end', iid=f'evt-{i}',
                        values=(i+1, t, ts, details), tags=(t,))
            shown += 1

        total = len(events)
        self._ev_count_lbl.config(
            text=f"{shown} / {total} events" if filt != 'all' else f"{total} events")

        # Summary stats
        summary = self._rec.summary()
        parts   = [f"{k}: {v}" for k, v in sorted(summary.items())]
        self._ev_stats_lbl.config(text="  ·  ".join(parts) if parts else "")

    def _ev_delete_selected(self):
        sel = self._ev_tree.selection()
        if not sel:
            messagebox.showinfo("NexaFlow", "Select an event to delete."); return
        idx = self._ev_selected_index()
        if idx is None:
            messagebox.showerror("NexaFlow", "Unable to determine selected event."); return
        self._rec.delete_event(idx)
        LOG.add(f"Event #{idx+1} deleted", 'record')
        if hasattr(self, '_evt_lbl'):
            self._evt_lbl.config(text=str(len(self._rec.events)))
        self._refresh_events_tab()

    def _ev_selected_index(self):
        sel = self._ev_tree.selection()
        if not sel:
            return None
        item = sel[0]
        try:
            return int(str(item).split('-', 1)[1])
        except Exception:
            return None

    def _ev_insert_wait(self):
        if not self._rec.events:
            messagebox.showwarning("NexaFlow", "No workflow loaded."); return
        win = tk.Toplevel(self)
        win.withdraw()
        _apply_windows_window_icon(win)
        win.title("Insert Wait")
        win.configure(bg=C['bg'])
        win.resizable(False, False)
        win.transient(self)
        win.attributes('-topmost', True)
        tk.Label(win, text="Wait duration (seconds):", bg=C['bg'],
                 fg=C['text2'], font=_f(9)).pack(pady=(20, 8))
        var = tk.StringVar(value="1.0")
        e   = _entry(win, var, w=10)
        e.pack(pady=4)
        e.focus()
        def _ok():
            try:
                secs = float(var.get())
                if secs < 0:
                    raise ValueError
                idx  = self._ev_selected_index()
                if idx is None:
                    idx = -1
                self._rec.insert_wait(secs, idx)
                if hasattr(self, '_evt_lbl'):
                    self._evt_lbl.config(text=str(len(self._rec.events)))
                self._refresh_events_tab()
                win.destroy()
            except ValueError:
                messagebox.showerror("NexaFlow", "Enter a valid non-negative number.", parent=win)
        tk.Button(win, text="Insert", command=_ok,
                  bg=C['purple'], fg=C['text'], font=_f(9, True),
                  relief='flat', padx=16, pady=6, cursor='hand2').pack(pady=8)
        win.bind('<Return>', lambda _: _ok())
        _show_centered_child(win, self, 300, 130)
        e.focus_force()

    def _ev_insert_type(self):
        if not self._rec.events:
            messagebox.showwarning("NexaFlow", "No workflow loaded."); return
        win = tk.Toplevel(self)
        win.withdraw()
        _apply_windows_window_icon(win)
        win.title("Insert Type-Text")
        win.configure(bg=C['bg'])
        win.resizable(False, False)
        win.transient(self)
        win.attributes('-topmost', True)
        tk.Label(win, text="Text to type (via clipboard paste):", bg=C['bg'],
                 fg=C['text2'], font=_f(9)).pack(pady=(18, 6))
        var = tk.StringVar()
        e   = _entry(win, var)
        e.pack(fill='x', padx=20, pady=4)
        e.focus()
        def _ok():
            text = var.get()
            if not text:
                messagebox.showerror("NexaFlow", "Enter text.", parent=win); return
            idx = self._ev_selected_index()
            if idx is None:
                idx = -1
            self._rec.insert_type_text(text, idx)
            if hasattr(self, '_evt_lbl'):
                self._evt_lbl.config(text=str(len(self._rec.events)))
            self._refresh_events_tab()
            win.destroy()
        tk.Button(win, text="Insert", command=_ok,
                  bg=C['accent3'], fg=C['text'], font=_f(9, True),
                  relief='flat', padx=16, pady=6, cursor='hand2').pack(pady=8)
        win.bind('<Return>', lambda _: _ok())
        _show_centered_child(win, self, 360, 150)
        e.focus_force()

    def _ev_clear_all(self):
        if not self._rec.events: return
        if messagebox.askyesno("Clear All Events",
            "Delete all recorded events?\nThis cannot be undone."):
            self._rec.events = []
            self._refresh_events_tab()
            self._evt_lbl.config(text="0")
            LOG.add("All events cleared", 'record')

    def _ev_export(self):
        if not self._rec.events:
            messagebox.showwarning("NexaFlow", "No events to export."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"{self._rec.name}_events.txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if not path: return
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"NexaFlow — Event Export\n")
            f.write(f"Workflow : {self._rec.name}\n")
            f.write(f"Events   : {len(self._rec.events)}\n")
            f.write(f"Duration : {self._rec.duration()}s\n")
            f.write(f"Exported : {datetime.now().isoformat()}\n")
            f.write("─" * 60 + "\n\n")
            for i, e in enumerate(self._rec.events):
                f.write(f"{i+1:4d}  [{e['t']:8s}]  ts={e.get('ts',0):.3f}  {json.dumps({k:v for k,v in e.items() if k not in ('t','ts')})}\n")
        LOG.add(f"Events exported: {Path(path).name}", 'file')
        messagebox.showinfo("NexaFlow", f"Events exported to:\n{path}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   TAB 7 — LOG
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _tab_log(self):
        tab = ttk.Frame(self._nb, style='NF.TFrame')
        self._nb.add(tab, text="  ≡  LOG  ")
        p = tk.Frame(tab, bg=C['bg'])
        p.pack(fill='both', expand=True, padx=18, pady=12)

        self._log_colors = {
            'system': C['blue'],   'record': C['red'],
            'play':   C['green'],  'data':   C['purple'],
            'file':   C['amber'],  'sched':  C['orange'],
            'error':  C['red'],    'info':   C['text2'],
        }

        hdr = tk.Frame(p, bg=C['bg'])
        hdr.pack(fill='x', pady=(0, 4))
        tk.Label(hdr, text="ACTIVITY LOG", bg=C['bg'],
                 fg=C['accent'], font=_f(8, True)).pack(side='left')
        self._ghost_btn(hdr, "Export", self._export_log).pack(side='right', padx=4)
        self._ghost_btn(hdr, "Clear",  self._clear_log).pack(side='right')

        # Filter row
        fr = tk.Frame(p, bg=C['bg'])
        fr.pack(fill='x', pady=(0, 4))
        tk.Label(fr, text="Filter:", bg=C['bg'], fg=C['text2'], font=_f(7)).pack(side='left')
        self._log_filter = tk.StringVar(value='all')
        for lv in ['all', 'system', 'record', 'play', 'data', 'file', 'sched', 'error']:
            col = self._log_colors.get(lv, C['text2']) if lv != 'all' else C['muted']
            tk.Radiobutton(fr, text=lv, variable=self._log_filter, value=lv,
                           bg=C['bg'], fg=col, selectcolor=C['card2'],
                           activebackground=C['bg'], font=_f(7), relief='flat',
                           cursor='hand2',
                           command=self._apply_log_filter).pack(side='left', padx=2)

        lf = tk.Frame(p, bg=C['card'],
                      highlightthickness=1, highlightbackground=C['border2'])
        lf.pack(fill='both', expand=True)
        sb = tk.Scrollbar(lf, orient='vertical', bg=C['panel'],
                          troughcolor=C['card'], relief='flat', width=6)
        self._log_text = tk.Text(lf, bg=C['card'], fg=C['text2'],
                                 insertbackground=C['accent'], relief='flat',
                                 font=_f(8, mono=True), padx=10, pady=8,
                                 wrap='word', state='disabled',
                                 selectbackground=C['accent3'],
                                 yscrollcommand=sb.set)
        sb.config(command=self._log_text.yview)
        self._log_text.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        for level, color in self._log_colors.items():
            self._log_text.tag_config(level, foreground=color)
        self._log_text.tag_config('ts', foreground=C['muted'])

        old_listener = getattr(self, '_log_listener', None)
        if old_listener:
            LOG.unsubscribe(old_listener)
        self._log_listener = lambda entry: self._queue_ui_event('log', entry)
        LOG.subscribe(self._log_listener)
        for entry in LOG.get_all():
            self._append_log(entry)

    def _append_log(self, entry):
        ts, level, msg = entry
        filt = self._log_filter.get() if hasattr(self, '_log_filter') else 'all'
        if filt != 'all' and level != filt:
            return
        self._log_text.config(state='normal')
        self._log_text.insert('end', f"[{ts}] ", 'ts')
        self._log_text.insert('end', f"{msg}\n", level)
        self._log_text.see('end')
        self._log_text.config(state='disabled')

    def _apply_log_filter(self):
        self._log_text.config(state='normal')
        self._log_text.delete('1.0', 'end')
        self._log_text.config(state='disabled')
        filt = self._log_filter.get()
        for entry in LOG.get_filtered(filt):
            self._append_log(entry)

    def _clear_log(self):
        LOG.clear()
        self._log_text.config(state='normal')
        self._log_text.delete('1.0', 'end')
        self._log_text.config(state='disabled')

    def _export_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"nexaflow_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if not path: return
        entries = LOG.get_all()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                for ts, level, msg in entries:
                    f.write(f"[{ts}] [{level.upper():8}] {msg}\n")
        except OSError as exc:
            messagebox.showerror("NexaFlow", f"Failed to export log: {exc}")
            return
        messagebox.showinfo("NexaFlow", f"Log exported: {Path(path).name}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   TAB 8 — SETTINGS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _tab_settings(self):
        tab = ttk.Frame(self._nb, style='NF.TFrame')
        self._nb.add(tab, text="  ⚙  ")

        canvas = tk.Canvas(tab, bg=C['bg'], highlightthickness=0)
        vsb    = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        p = tk.Frame(canvas, bg=C['bg'])
        win_id = canvas.create_window((0, 0), window=p, anchor='nw')

        def _on_frame_cfg(evt):
            canvas.configure(scrollregion=canvas.bbox('all'))
        def _on_canvas_cfg(evt):
            canvas.itemconfig(win_id, width=evt.width)
        self._settings_tab_id = str(tab)
        def _scroll_settings(delta):
            try:
                canvas.yview_scroll(delta, 'units')
            except Exception:
                pass
        def _is_settings_pointer(evt):
            try:
                w = self.winfo_containing(
                    getattr(evt, 'x_root', 0),
                    getattr(evt, 'y_root', 0)
                )
            except Exception:
                w = None
            while w is not None:
                if w is tab or w is canvas or w is p:
                    return True
                try:
                    w = w.master
                except Exception:
                    break
            return False
        def _mark_combo_scroll_lock(_evt=None):
            self._settings_combo_scroll_lock_until = time.monotonic() + 2.5
        def _clear_combo_scroll_lock(_evt=None):
            self._settings_combo_scroll_lock_until = 0
        def _protect_combo_scroll(widget):
            def _combo_page_mousewheel(evt):
                if time.monotonic() < getattr(self, '_settings_combo_scroll_lock_until', 0):
                    return 'break'
                delta = getattr(evt, 'delta', 0)
                if delta:
                    steps = int(delta / 120)
                    if steps == 0:
                        steps = 1 if delta > 0 else -1
                    _scroll_settings(-steps)
                return 'break'
            def _combo_page_up(_evt):
                if time.monotonic() < getattr(self, '_settings_combo_scroll_lock_until', 0):
                    return 'break'
                _scroll_settings(-3)
                return 'break'
            def _combo_page_down(_evt):
                if time.monotonic() < getattr(self, '_settings_combo_scroll_lock_until', 0):
                    return 'break'
                _scroll_settings(3)
                return 'break'
            try:
                widget.bind('<Button-1>', _mark_combo_scroll_lock, add='+')
                widget.bind('<<ComboboxSelected>>',
                            lambda e: self.after(150, _clear_combo_scroll_lock),
                            add='+')
                widget.bind('<Escape>', _clear_combo_scroll_lock, add='+')
                widget.bind('<FocusOut>',
                            lambda e: self.after(300, _clear_combo_scroll_lock),
                            add='+')
                widget.bind('<MouseWheel>', _combo_page_mousewheel)
                widget.bind('<Button-4>', _combo_page_up)
                widget.bind('<Button-5>', _combo_page_down)
            except Exception:
                pass
        def _is_combo_scroll(evt):
            if time.monotonic() < getattr(self, '_settings_combo_scroll_lock_until', 0):
                return True
            widgets = []
            for getter in (
                lambda: getattr(evt, 'widget', None),
                self.focus_get,
                lambda: self.winfo_containing(
                    getattr(evt, 'x_root', 0),
                    getattr(evt, 'y_root', 0)
                ),
            ):
                try:
                    w = getter()
                    if w is not None:
                        widgets.append(w)
                except Exception:
                    pass
            for w in widgets:
                try:
                    cls = str(w.winfo_class()).lower()
                    name = str(w).lower()
                    if 'listbox' in cls or 'popdown' in name:
                        return True
                except Exception:
                    pass
            return False
        def _on_mousewheel(evt):
            try:
                if str(self._nb.select()) != self._settings_tab_id:
                    return
            except Exception:
                return
            if not _is_settings_pointer(evt):
                return
            if _is_combo_scroll(evt):
                return 'break'
            delta = getattr(evt, 'delta', 0)
            if delta:
                steps = int(delta / 120)
                if steps == 0:
                    steps = 1 if delta > 0 else -1
                _scroll_settings(-steps)
                return 'break'
        def _on_button4(evt):
            try:
                if str(self._nb.select()) != self._settings_tab_id:
                    return
            except Exception:
                return
            if not _is_settings_pointer(evt):
                return
            if _is_combo_scroll(evt):
                return 'break'
            _scroll_settings(-3)
            return 'break'
        def _on_button5(evt):
            try:
                if str(self._nb.select()) != self._settings_tab_id:
                    return
            except Exception:
                return
            if not _is_settings_pointer(evt):
                return
            if _is_combo_scroll(evt):
                return 'break'
            _scroll_settings(3)
            return 'break'
        p.bind('<Configure>', _on_frame_cfg)
        canvas.bind('<Configure>', _on_canvas_cfg)
        canvas.bind_all('<MouseWheel>', _on_mousewheel)
        canvas.bind_all('<Button-4>', _on_button4)
        canvas.bind_all('<Button-5>', _on_button5)

        pp = tk.Frame(p, bg=C['bg'])
        pp.pack(fill='both', expand=True, padx=18, pady=12)

        # Hotkeys (editable)
        _section_header(pp, "Global Hotkeys", icon="⌨").pack(anchor='w', pady=(0, 6))
        hk_frame = tk.Frame(pp, bg=C['card'],
                            highlightthickness=1, highlightbackground=C['border2'])
        hk_frame.pack(fill='x', pady=(0, 12))

        # Load current hotkeys or defaults
        defaults = {
            'rec_toggle': 'F9',
            'play': 'F10',
            'pause': 'F12',
            'stop': 'F11',
            'stop_all': 'ESC',
        }
        hk_cfg = CFG.get('hotkeys', defaults)
        self._hk_vars = {}
        rows = [
            ('rec_toggle', 'Start / Stop recording'),
            ('play', 'Play workflow'),
            ('pause', 'Pause / Resume playback'),
            ('stop', 'Stop playback'),
            ('stop_all', 'Stop everything'),
        ]
        for i, (k, desc) in enumerate(rows):
            if i > 0:
                tk.Frame(hk_frame, bg=C['border'], height=1).pack(fill='x')
            row = tk.Frame(hk_frame, bg=C['card'])
            row.pack(fill='x', padx=10, pady=6)
            tk.Label(row, text=f" {k.upper()} ", bg=C['card2'],
                     fg=C['amber'], font=_f(8, True, mono=True), padx=6, pady=2).pack(side='left')
            tk.Label(row, text=f"  {desc}", bg=C['card'], fg=C['text2'], font=_f(9)).pack(side='left')
            var = tk.StringVar(value=hk_cfg.get(k, defaults.get(k)))
            ent = tk.Entry(row, textvariable=var, width=18, font=_f(9))
            ent.pack(side='right', padx=10)
            self._hk_vars[k] = var

        btn_row = tk.Frame(hk_frame, bg=C['card'])
        btn_row.pack(fill='x', padx=10, pady=(8, 4))
        self._ghost_btn(btn_row, 'Save Hotkeys', self._save_hotkeys).pack(side='right')
        tk.Label(hk_frame, text='Format examples: F9  |  ESC  |  ctrl+alt+r  |  shift+F8',
                 bg=C['card'], fg=C['muted'], font=_f(7)).pack(anchor='w', padx=10, pady=(6, 4))

        # Remote access
        _section_header(pp, "Remote Access", icon="▣").pack(anchor='w', pady=(0, 6))
        remote_card = _card(pp)
        remote_card.pack(fill='x', pady=(0, 12))
        rf = tk.Frame(remote_card, bg=C['card'])
        rf.pack(fill='x', padx=10, pady=10)
        self._remote_port_var = tk.StringVar(value=str(CFG.get('remote_port', 8765)))
        self._remote_status_var = tk.StringVar(value="Remote access is off")
        self._remote_host_var = tk.StringVar(value="Local address: --")
        self._remote_client_var = tk.StringVar(value="Phone: --")
        self._remote_firewall_var = tk.StringVar(value="")
        tk.Label(rf, textvariable=self._remote_status_var, bg=C['card'],
                 fg=C['text2'], font=_f(9, True)).pack(anchor='w')
        tk.Label(rf, textvariable=self._remote_host_var, bg=C['card'],
                 fg=C['accent'], font=_f(10, True, mono=True)).pack(anchor='w', pady=(4, 0))
        tk.Label(rf, textvariable=self._remote_firewall_var, bg=C['card'],
                 fg=C['muted'], font=_f(8)).pack(anchor='w', pady=(2, 0))
        tk.Label(rf, textvariable=self._remote_client_var, bg=C['card'],
                 fg=C['muted'], font=_f(8)).pack(anchor='w', pady=(4, 8))
        port_row = tk.Frame(rf, bg=C['card'])
        port_row.pack(fill='x', pady=(0, 8))
        tk.Label(port_row, text="Local port", bg=C['card'], fg=C['text2'],
                 font=_f(8)).pack(side='left')
        tk.Entry(port_row, textvariable=self._remote_port_var, width=10,
                 font=_f(8)).pack(side='left', padx=(8, 16))
        tk.Label(port_row, text="Same Wi-Fi or hotspot as your phone",
                 bg=C['card'], fg=C['muted'], font=_f(8)).pack(side='left')
        btns = tk.Frame(rf, bg=C['card'])
        btns.pack(fill='x')
        self._remote_toggle_btn = self._ghost_btn(btns, "Start Remote", self._remote_toggle)
        self._remote_toggle_btn.pack(side='left')
        self._ghost_btn(btns, "Trusted Devices", self._remote_manage_trusted).pack(side='left', padx=6)
        self._ghost_btn(btns, "Copy Address", self._remote_copy_details).pack(side='right')
        tk.Label(rf,
                 text="On your phone: enter this PC's address, tap Pair, then approve the request here. "
                      "Remote control is visible and consent-based.",
                 bg=C['card'], fg=C['muted'], font=_f(7), wraplength=460,
                 justify='left').pack(anchor='w', pady=(8, 0))
        self._remote_refresh_labels()

        # Preferences
        _section_header(pp, "Preferences", icon="◈").pack(anchor='w', pady=(0, 6))
        pref_card = _card(pp)
        pref_card.pack(fill='x', pady=(0, 12))
        pf = tk.Frame(pref_card, bg=C['card'])
        pf.pack(fill='x', padx=10, pady=(10, 4))
        pf2 = tk.Frame(pref_card, bg=C['card'])
        pf2.pack(fill='x', padx=10, pady=(0, 10))
        self._aot = tk.BooleanVar(value=CFG.get('always_on_top', True))
        self._check(pf, "Always on top", self._aot, bg=C['card'],
                    command=self._toggle_aot).pack(side='left')
        self._minimize_to_tray_var = tk.BooleanVar(value=CFG.get('minimize_to_tray', HAS_TRAY))
        self._check(pf, "Minimize to tray" + (" (pystray required)" if not HAS_TRAY else ""),
                    self._minimize_to_tray_var, bg=C['card'],
                    command=lambda: CFG.set('minimize_to_tray', self._minimize_to_tray_var.get())
                    ).pack(side='left', padx=16)
        self._hide_windows_playback_var = tk.BooleanVar(
            value=CFG.get('hide_windows_during_playback', False)
        )
        self._check(
            pf,
            "Hide windows during play",
            self._hide_windows_playback_var,
            bg=C['card'],
            command=lambda: CFG.set(
                'hide_windows_during_playback',
                self._hide_windows_playback_var.get()
            )
        ).pack(side='left')
        self._stop_on_input_var = tk.BooleanVar(
            value=CFG.get('stop_on_user_input_during_playback', False)
        )
        self._check(
            pf2,
            "Stop play on user input",
            self._stop_on_input_var,
            bg=C['card'],
            command=lambda: CFG.set(
                'stop_on_user_input_during_playback',
                self._stop_on_input_var.get()
            )
        ).pack(side='left')
        self._remote_start_on_launch_var = tk.BooleanVar(
            value=bool(CFG.get('remote_start_on_launch', False))
        )
        self._check(
            pf2,
            "Start Remote when NexaFlow opens",
            self._remote_start_on_launch_var,
            bg=C['card'],
            command=lambda: CFG.set(
                'remote_start_on_launch', bool(self._remote_start_on_launch_var.get())
            ),
        ).pack(side='left', padx=16)

        # Theme
        _section_header(pp, "Theme", icon="🌓").pack(anchor='w', pady=(0, 6))
        theme_card = _card(pp)
        theme_card.pack(fill='x', pady=(0, 12))
        tf = tk.Frame(theme_card, bg=C['card'])
        tf.pack(fill='x', padx=10, pady=10)
        tk.Label(tf, text="Color mode:", bg=C['card'], fg=C['text2'], font=_f(8)).pack(side='left')
        self._theme_var = tk.StringVar(value=CFG.get('theme', 'light'))
        for val, label in [('light', 'Light'), ('dark', 'Dark')]:
            tk.Radiobutton(tf, text=label, variable=self._theme_var, value=val,
                           bg=C['card'], fg=C['text2'], selectcolor=C['card2'],
                           activebackground=C['card'], font=_f(8), relief='flat',
                           cursor='hand2').pack(side='left', padx=8)
        self._ghost_btn(tf, 'Apply', self._apply_theme).pack(side='right')

        # Time zone
        _section_header(pp, "Time Zone", icon="🕒").pack(anchor='w', pady=(0, 6))
        tz_card = _card(pp)
        tz_card.pack(fill='x', pady=(0, 12))
        tzf = tk.Frame(tz_card, bg=C['card'])
        tzf.pack(fill='x', padx=10, pady=10)
        tk.Label(tzf, text="Live timezone:", bg=C['card'], fg=C['text2'], font=_f(8)).pack(side='left')
        self._timezone_var = tk.StringVar(
            value=LOCAL_TIMEZONE_LABEL if self._timezone == LOCAL_TIMEZONE else self._timezone
        )
        self._timezone_cb = ttk.Combobox(tzf, textvariable=self._timezone_var,
                                        values=self._timezone_options,
                                        width=34, state='normal', font=_f(8))
        self._timezone_cb.pack(side='left', fill='x', expand=True, padx=(8, 0))
        self._timezone_cb.bind('<Return>', lambda e: self._apply_timezone(silent=True))
        _protect_combo_scroll(self._timezone_cb)
        self._ghost_btn(tzf, 'Apply',
                        lambda: (self._apply_timezone(silent=True),
                                 _clear_combo_scroll_lock(),
                                 self.focus_set())).pack(side='left', padx=(8, 0))

        # Screenshots
        _section_header(pp, "Screenshots", icon="◎").pack(anchor='w', pady=(0, 6))
        ss_card = _card(pp)
        ss_card.pack(fill='x', pady=(0, 12))
        ss_folder = Path.home() / "NexaFlow_Screenshots"
        sf2 = tk.Frame(ss_card, bg=C['card'])
        sf2.pack(fill='x', padx=10, pady=10)
        tk.Label(sf2, text=f"Saved to: {ss_folder}", bg=C['card'],
                 fg=C['muted'], font=_f(8)).pack(anchor='w')
        self._ghost_btn(sf2, "◫  Open Folder",
                        lambda: self._open_folder(ss_folder)).pack(anchor='w', pady=4)

        # Config location
        _section_header(pp, "Config & Data", icon="◆").pack(anchor='w', pady=(0, 6))
        cfg_card = _card(pp)
        cfg_card.pack(fill='x', pady=(0, 12))
        cf2 = tk.Frame(cfg_card, bg=C['card'])
        cf2.pack(fill='x', padx=10, pady=10)
        cfg_dir = Path.home() / ".nexaflow"
        tk.Label(cf2, text=f"Config: {cfg_dir}", bg=C['card'],
                 fg=C['muted'], font=_f(8)).pack(anchor='w')
        self._ghost_btn(cf2, "◫  Open Config Folder",
                        lambda: self._open_folder(cfg_dir)).pack(anchor='w', pady=4)
        self._ghost_btn(cf2, "✕  Clear Recent Files",
                        self._clear_recent).pack(anchor='w')

        # About
        _section_header(pp, "About", icon="◆").pack(anchor='w', pady=(0, 6))
        about_card = _card(pp)
        about_card.pack(fill='x')
        ac = tk.Frame(about_card, bg=C['card'])
        ac.pack(fill='x', padx=10, pady=10)
        tk.Label(ac,
                 text="Windows  ·  100% Offline  ·  No Cloud  ·  No Limits\n"
                      "Events Editor  ·  Type-Text  ·  Scheduler  ·  File Engine\n"
                      "NexaFlow  —  Professional Desktop Automation\n"
                      "Version 1.0.0",
                 bg=C['card'], fg=C['muted'], font=_f(8), justify='left').pack(anchor='w')
        about_links = tk.Frame(ac, bg=C['card'])
        about_links.pack(anchor='w', pady=(8, 0))
        self._ghost_btn(about_links, "Support",
                        lambda: self._open_url(_support_url())).pack(side='left', padx=(0, 8))
        self._ghost_btn(about_links, "Privacy",
                        lambda: self._open_url(_privacy_url())).pack(side='left')

    def _remote_status_snapshot(self):
        recent = CFG.get_recent()
        if self._play_countdown_active:
            phase = 'countdown'
        elif self._rec.paused:
            phase = 'paused'
        elif self._rec.playing or self._ui_playing:
            phase = 'playing'
        else:
            phase = 'idle'
        total_events = self._play_total_events or len(getattr(self._rec, 'events', []) or [])
        current_event = min(self._play_current_event, total_events) if total_events else 0
        progress = (current_event / total_events * 100.0) if total_events else 0.0
        return {
            'state': 'Recording' if self._rec.recording else phase.title() if phase != 'idle' else 'Ready',
            'recording': bool(self._rec.recording),
            'playing': bool(self._rec.playing),
            'paused': bool(self._rec.paused),
            'events': len(getattr(self._rec, 'events', []) or []),
            'workflow': getattr(self._rec, 'name', None) or CFG.get('workflow_name', 'workflow_1'),
            'recent': [Path(str(p)).name for p in recent[:8]],
            'recentWorkflows': [
                {'index': index, 'name': Path(str(path)).name}
                for index, path in enumerate(recent[:8])
            ],
            'playback': {
                'phase': phase,
                'countdownRemaining': self._play_countdown_remaining if phase == 'countdown' else 0,
                'elapsedSeconds': round(self._play_elapsed_seconds(), 2) if phase in {'playing', 'paused'} else 0.0,
                'currentEvent': current_event,
                'totalEvents': total_events,
                'progressPercent': round(progress, 1),
                'currentLoop': self._play_current_loop,
                'totalLoops': self._play_total_loops,
            },
            'theme': CFG.get('theme', 'light'),
            'appVersion': '1.0.0',
        }

    def _remote_start(self):
        if not self._remote_host:
            messagebox.showerror("NexaFlow", "Remote access is unavailable in this build.")
            return
        try:
            port = int(self._remote_port_var.get().strip() or 8765)
            if port < 1024 or port > 65535:
                raise ValueError
        except Exception:
            messagebox.showerror("NexaFlow", "Enter a local port between 1024 and 65535.")
            return
        CFG.set('remote_port', port)
        try:
            self._remote_host.start(port=port, bind_host="0.0.0.0")
        except OSError as exc:
            messagebox.showerror(
                "NexaFlow",
                f"Could not start remote access on port {port}.\n\n"
                f"{exc}\n\nTry another port or allow NexaFlow through Windows Firewall."
            )
            return
        self._ensure_firewall_rule(port)
        self._status("REMOTE READY", C['accent'])
        self._remote_refresh_labels()

    def _remote_toggle(self):
        remote = getattr(self, '_remote_host', None)
        if remote and remote.running:
            self._remote_stop()
        else:
            self._remote_start()

    def _remote_stop(self):
        if self._remote_host:
            self._remote_host.stop()
        self._status("REMOTE OFF", C['muted'])
        self._remote_refresh_labels()

    # ── Windows Firewall rule (so the phone can reach this PC on the LAN) ──
    def _ensure_firewall_rule(self, port):
        """Verify the exact runtime rule before claiming the firewall is ready."""
        if not IS_WIN:
            return
        spec = firewall_rule_spec(
            port,
            sys.executable or "",
            packaged=bool(getattr(sys, 'frozen', False)),
        )
        signature = f"{spec.name}|{spec.port}|{spec.executable}"
        if signature in {self._firewall_check_inflight, self._firewall_repair_inflight}:
            return
        self._firewall_spec = spec
        self._firewall_rule_ready = False
        self._firewall_check_inflight = signature
        self._remote_firewall_var.set("Firewall: checking…")

        def worker():
            result = inspect_firewall_rule(spec)
            self._queue_ui_event('firewall_check', {'spec': spec, 'result': result})

        threading.Thread(target=worker, daemon=True).start()

    def _handle_firewall_check(self, payload):
        spec = payload.get('spec')
        result = payload.get('result') or {}
        if spec != self._firewall_spec:
            return
        signature = f"{spec.name}|{spec.port}|{spec.executable}"
        if self._firewall_check_inflight == signature:
            self._firewall_check_inflight = None
        if result.get('status') == 'valid':
            self._firewall_rule_ready = True
            self._remote_firewall_var.set("Firewall: allowed ✓")
            if CFG.get('firewall_verified_signature') != signature:
                CFG.set('firewall_verified_signature', signature)
            return
        if result.get('status') == 'error':
            self._remote_firewall_var.set("Firewall: could not verify rule")
            LOG.add(f"Firewall inspection failed: {result.get('error')}", 'error')
            return
        self._remote_firewall_var.set("Firewall: permission required")
        if signature in self._firewall_prompted_signatures:
            return
        self._firewall_prompted_signatures.add(signature)
        allow = messagebox.askyesno(
            "Allow local connection?",
            "NexaFlow needs a verified Windows Firewall rule so your phone can reach "
            f"this app on the local network (TCP port {spec.port}, local subnet only).\n\n"
            "Windows will show a permission prompt. Allow it?"
        )
        if not allow:
            self._remote_firewall_var.set("Firewall: not allowed — phone may not connect")
            return
        self._firewall_repair_inflight = signature
        self._remote_firewall_var.set("Firewall: requesting permission…")

        def worker():
            import base64
            try:
                repair_encoded = base64.b64encode(
                    firewall_repair_script(spec).encode('utf-16-le')
                ).decode('ascii')
                elevated = (
                    "$p=Start-Process -FilePath 'powershell.exe' -ArgumentList "
                    f"@('-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand','{repair_encoded}') "
                    "-Verb RunAs -WindowStyle Hidden -Wait -PassThru; exit $p.ExitCode"
                )
                process = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", elevated],
                    capture_output=True,
                    text=True,
                    timeout=75,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                )
                if process.returncode != 0:
                    detail = (process.stderr or process.stdout or "Permission was cancelled").strip()
                    result = {'status': 'error', 'error': detail}
                else:
                    result = inspect_firewall_rule(spec)
            except Exception as exc:
                result = {'status': 'error', 'error': f'{type(exc).__name__}: {exc}'}
            self._queue_ui_event('firewall_repair', {'spec': spec, 'result': result})

        threading.Thread(target=worker, daemon=True).start()

    def _handle_firewall_repair(self, payload):
        spec = payload.get('spec')
        result = payload.get('result') or {}
        if spec != self._firewall_spec:
            return
        signature = f"{spec.name}|{spec.port}|{spec.executable}"
        if self._firewall_repair_inflight == signature:
            self._firewall_repair_inflight = None
        if result.get('status') == 'valid':
            self._firewall_rule_ready = True
            self._remote_firewall_var.set("Firewall: allowed ✓")
            CFG.set('firewall_verified_signature', signature)
            LOG.add(f"Verified firewall rule for port {spec.port}", 'remote')
            return
        self._firewall_rule_ready = False
        self._remote_firewall_var.set("Firewall: repair failed — allow NexaFlow manually")
        LOG.add(f"Firewall rule failed verification: {result.get('error') or result.get('status')}", 'error')

    # ── Approve-based pairing (phone taps Pair -> we prompt here) ─────────
    def _on_pair_request(self, record):
        """Called from an HTTP worker; enqueue without touching Tk."""
        self._queue_ui_event('pair_request', record)

    def _show_pair_dialog(self, record):
        rid = record.get('requestId', '')
        if (
            not rid
            or not self._remote_host
            or self._remote_host.poll_request(rid).get('status') != 'pending'
        ):
            return
        try:
            if self._pair_dialog and self._pair_dialog.winfo_exists():
                if self._remote_host and self._pair_dialog_request_id:
                    self._remote_host.deny_request(self._pair_dialog_request_id)
                self._pair_dialog.destroy()
        except Exception:
            pass
        name = record.get('deviceName', 'A device')
        ip = record.get('ip', '')
        dlg = tk.Toplevel(self)
        dlg.withdraw()
        _apply_windows_window_icon(dlg)
        self._pair_dialog = dlg
        self._pair_dialog_request_id = rid
        dlg.title("Pairing request")
        dlg.configure(bg=C['card'])
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.attributes('-topmost', True)
        try:
            dlg.grab_set()
        except Exception:
            pass
        tk.Label(dlg, text="\U0001F4F1  Pairing request", bg=C['card'], fg=C['text'],
                 font=_f(11, True)).pack(anchor='w', padx=16, pady=(14, 4))
        tk.Label(dlg, text=f"{name}\n{ip} wants to connect and control this desktop.",
                 bg=C['card'], fg=C['text2'], font=_f(9), justify='left').pack(
                 anchor='w', padx=16, pady=(0, 8))
        trust_var = tk.BooleanVar(value=True)
        self._check(dlg, "Trust this device (connect automatically next time)",
                    trust_var, bg=C['card']).pack(anchor='w', padx=16, pady=(0, 10))
        row = tk.Frame(dlg, bg=C['card'])
        row.pack(fill='x', padx=16, pady=(0, 14))

        def close_dialog():
            if self._pair_dialog is dlg:
                self._pair_dialog = None
                self._pair_dialog_request_id = ""
            try:
                if dlg.winfo_exists():
                    dlg.destroy()
            except Exception:
                pass

        def approve():
            approved = bool(
                self._remote_host
                and self._remote_host.approve_request(rid, trust=trust_var.get())
            )
            if approved:
                self._status("PHONE PAIRED", C['accent'])
            close_dialog()

        def deny():
            if self._remote_host:
                self._remote_host.deny_request(rid)
            close_dialog()

        def sync_request_status():
            try:
                if not dlg.winfo_exists() or not self._remote_host:
                    return
                status = self._remote_host.poll_request(rid).get('status')
                if status != 'pending':
                    close_dialog()
                    return
                dlg.after(500, sync_request_status)
            except Exception:
                close_dialog()

        self._ghost_btn(row, "Approve", approve).pack(side='left')
        self._ghost_btn(row, "Deny", deny).pack(side='left', padx=8)
        dlg.protocol("WM_DELETE_WINDOW", deny)
        dlg.after(500, sync_request_status)
        _show_centered_child(dlg, self)

    def _is_trusted_device(self, device_id):
        return device_id in (CFG.get('trusted_devices', {}) or {})

    def _add_trusted_device(self, device_id, device_name):
        trusted = dict(CFG.get('trusted_devices', {}) or {})
        trusted[device_id] = device_name
        CFG.set('trusted_devices', trusted)

    def _remove_trusted_device(self, device_id):
        trusted = dict(CFG.get('trusted_devices', {}) or {})
        if device_id in trusted:
            trusted.pop(device_id, None)
            CFG.set('trusted_devices', trusted)

    def _remote_manage_trusted(self):
        trusted = dict(CFG.get('trusted_devices', {}) or {})
        if not trusted:
            messagebox.showinfo("NexaFlow", "No trusted devices yet.\n\nApprove a phone with "
                                            "“Trust this device” checked to add one.")
            return
        names = "\n".join(f"• {n}" for n in trusted.values())
        if messagebox.askyesno("Trusted devices",
                               f"These devices connect without asking:\n\n{names}\n\n"
                               "Remove all trusted devices?"):
            CFG.set('trusted_devices', {})
            messagebox.showinfo("NexaFlow", "Trusted devices cleared.")

    def _remote_pairing_text(self):
        if not self._remote_host or not self._remote_host.running:
            return "Remote access is off."
        host = self._remote_host.local_ip()
        port = self._remote_host.port
        if not host:
            return (
                "NexaFlow Desktop\n"
                "No phone-reachable Wi-Fi or hotspot address was detected.\n"
                "Connect this PC to the phone's network, then try again."
            )
        return (
            "NexaFlow Desktop\n"
            f"Address for your phone: {host}:{port}\n"
            "On the phone: enter this address, tap Pair, then approve here."
        )

    def _remote_copy_details(self):
        text = self._remote_pairing_text()
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update_idletasks()
        except Exception:
            pass
        messagebox.showinfo("NexaFlow", "Address copied.")

    def _remote_refresh_labels(self):
        remote = getattr(self, '_remote_host', None)
        running = bool(remote and remote.running)
        if hasattr(self, '_remote_badge_var'):
            self._remote_badge_var.set("REMOTE ON" if running else "REMOTE OFF")
            try:
                self._remote_badge.config(
                    fg=C['accent'] if running else C['muted'],
                    highlightbackground=C['accent3'] if running else C['border']
                )
            except Exception:
                pass
        if hasattr(self, '_remote_status_var'):
            if running:
                self._remote_status_var.set("Remote access is running")
                host = remote.local_ip()
                if host:
                    self._remote_host_var.set(f"Local address: {host}:{remote.port}")
                else:
                    self._remote_host_var.set("Local address: no phone-reachable network detected")
                self._remote_client_var.set(f"Phone: {remote.last_client or '--'}")
            else:
                self._remote_status_var.set("Remote access is off")
                self._remote_host_var.set("Local address: --")
                self._remote_firewall_var.set("")
                self._remote_client_var.set("Phone: --")
        if hasattr(self, '_remote_toggle_btn'):
            try:
                self._remote_toggle_btn.config(text="Stop Remote" if running else "Start Remote")
            except Exception:
                pass
        if self._remote_refresh_after_id:
            try: self.after_cancel(self._remote_refresh_after_id)
            except Exception: pass
        self._remote_refresh_after_id = self.after(1000, self._remote_refresh_labels)

    def _handle_remote_command(self, cmd, body=None):
        self._queue_ui_event('remote_command', (cmd, body or {}))

    def _execute_remote_command(self, cmd, body=None):
        body = body or {}

        def apply_value(attr, value):
            target = getattr(self, attr, None)
            if target is not None and value is not None:
                try:
                    target.set(str(value))
                except Exception:
                    pass

        def run():
            try:
                if cmd == 'record':
                    if self._rec.recording:
                        self._stop_recording()
                        return
                    apply_value('_rec_name', body.get('name'))
                    apply_value('_rec_mode', body.get('mode'))
                    apply_value('_rec_countdown', body.get('delay'))
                    self._start_recording()
                    return
                if cmd == 'stop':
                    if self._rec.recording:
                        self._stop_recording()
                    if (
                        self._rec.playing
                        or getattr(self, '_ui_playing', False)
                        or getattr(self, '_play_countdown_active', False)
                    ):
                        self._play_stop()
                    return
                if cmd == 'play':
                    requested_mode = str(body.get('mode') or 'once').lower()
                    mode = {'repeat': 'count', 'loop': 'infinite'}.get(requested_mode, requested_mode)
                    if mode not in {'once', 'count', 'infinite'}:
                        mode = 'once'
                    apply_value('_lmode', mode)
                    apply_value('_lcount', body.get('count'))
                    apply_value('_ldelay', body.get('delay'))
                    if hasattr(self, '_speed') and body.get('speed') is not None:
                        try: self._speed.set(float(body.get('speed')))
                        except Exception: pass
                    if hasattr(self, '_sdelay'):
                        try: self._sdelay.set(str(body.get('startDelay', 0)))
                        except Exception: pass
                    try: self._on_lmode()
                    except Exception: pass
                    self._play_start()
                    return
                if cmd == 'pause':
                    self._toggle_pause()
                    return
                if cmd == 'save':
                    self._save_rec()
                    return
                if cmd == 'load':
                    recent = CFG.get_recent()
                    try:
                        workflow_index = int(body.get('workflowIndex', 0))
                    except (TypeError, ValueError):
                        workflow_index = -1
                    if 0 <= workflow_index < len(recent):
                        self._do_load(recent[workflow_index])
                    return
            except Exception as exc:
                LOG.add(f"Remote command failed: {cmd}: {exc}", 'error')

        run()

    def _apply_timezone(self, silent=False):
        tz_name = self._timezone_var.get().strip()
        if not tz_name:
            messagebox.showerror("NexaFlow", "Enter a timezone name.")
            return
        if tz_name in (LOCAL_TIMEZONE, LOCAL_TIMEZONE_LABEL):
            self._timezone = LOCAL_TIMEZONE
            self._tz = None
            CFG.set('timezone', self._timezone)
            self._timezone_var.set(LOCAL_TIMEZONE_LABEL)
            self._clock_zone_lbl.config(text="Local Time")
            if not silent:
                messagebox.showinfo("NexaFlow", "Timezone set to Local / System time.")
            return
        if ZoneInfo is None:
            messagebox.showerror("NexaFlow", "Timezone support is unavailable in this Python build.")
            return
        zone = _get_zone(tz_name)
        if not zone:
            messagebox.showerror("NexaFlow", "Invalid timezone selected. Use Local / System time or a name like Asia/Riyadh.")
            return
        self._timezone = zone.key if getattr(zone, 'key', None) else tz_name
        self._tz = zone
        CFG.set('timezone', self._timezone)
        self._timezone_var.set(self._timezone)
        self._clock_zone_lbl.config(text=self._timezone)
        if not silent:
            messagebox.showinfo("NexaFlow", f"Timezone updated to: {self._timezone}")

    def _apply_theme(self):
        theme = self._theme_var.get()
        if theme not in THEMES:
            messagebox.showerror("NexaFlow", "Invalid theme selection.")
            return
        CFG.set('theme', theme)
        _set_theme(theme)
        self.configure(bg=C['bg'])
        self._init_styles()
        for child in self.winfo_children():
            child.destroy()
        self._build()
        messagebox.showinfo("NexaFlow", "Theme applied.")

    def _toggle_aot(self):
        val = self._aot.get()
        self.attributes('-topmost', val)
        CFG.set('always_on_top', val)

    def _clear_recent(self):
        CFG.set('recent', [])
        self._refresh_recent_workflows()
        messagebox.showinfo("NexaFlow", "Recent files cleared.")

    def _save_hotkeys(self):
        try:
            hk = {}
            for k, var in getattr(self, '_hk_vars', {}).items():
                v = var.get().strip()
                if v:
                    hk[k] = v
            normalized = [v.lower() for v in hk.values()]
            if len(normalized) != len(set(normalized)):
                messagebox.showwarning('NexaFlow', 'Each hotkey must be different.')
                return
            if hk:
                CFG.set('hotkeys', hk)
                # restart listener only if not actively recording
                try:
                    if not getattr(self, '_rec', None) or not getattr(self._rec, 'recording', False):
                        self._start_hotkeys()
                except Exception:
                    pass
                messagebox.showinfo('NexaFlow', 'Hotkeys saved')
            else:
                messagebox.showwarning('NexaFlow', 'No hotkeys to save')
        except Exception as e:
            messagebox.showerror('NexaFlow', f'Failed to save hotkeys: {e}')

    def _open_folder(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        if IS_WIN:   os.startfile(str(path))
        elif IS_MAC: subprocess.Popen(['open', str(path)])
        else:        subprocess.Popen(['xdg-open', str(path)])

    def _open_url(self, url):
        try:
            webbrowser.open(url)
        except Exception:
            messagebox.showinfo("NexaFlow", f"Open this link in your browser:\n{url}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   BUILD EXE  (Enhanced)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_exe(self):
        script_dir = Path(sys.argv[0]).parent.resolve()
        script     = Path(sys.argv[0]).resolve()

        # Progress window
        win = tk.Toplevel(self)
        win.withdraw()
        _apply_windows_window_icon(win)
        win.title("Building NexaFlow.exe")
        win.configure(bg=C['bg'])
        win.resizable(False, False)
        win.transient(self)
        win.attributes('-topmost', True)

        tk.Label(win, text="🔨  Building NexaFlow.exe", bg=C['bg'],
                 fg=C['accent'], font=_f(12, True)).pack(pady=(20, 6))
        status_lbl = tk.Label(win, text="Preparing build…", bg=C['bg'],
                              fg=C['text2'], font=_f(8))
        status_lbl.pack(pady=2)
        pvar = tk.DoubleVar(value=0)
        pb   = ttk.Progressbar(win, variable=pvar, maximum=100,
                               style='Cyan.Horizontal.TProgressbar')
        pb.pack(fill='x', padx=30, pady=10)
        log_frame, log_text = _scroll_text(win, height=6)
        log_frame.pack(fill='both', expand=True, padx=20, pady=4)
        _show_centered_child(win, self, 480, 260)

        def log(msg, pct=None):
            def ui_update():
                try:
                    log_text.config(state='normal')
                    log_text.insert('end', msg + '\n')
                    log_text.see('end')
                    log_text.config(state='disabled')
                    if pct is not None:
                        pvar.set(pct)
                    status_lbl.config(text=msg[:60])
                except Exception:
                    pass
            win.after(0, ui_update)

        def do_build():
            try:
                log("Step 1/4 — Installing PyInstaller…", 5)
                _pip('pyinstaller')

                log("Step 2/4 — Generating icon…", 20)
                ico = None
                if HAS_PIL:
                    ico = script_dir / "nexaflow.ico"
                    _make_ico(ico)

                log("Step 3/4 — Writing build spec…", 35)
                hidden = [
                    'pynput', 'pynput.keyboard', 'pynput.mouse',
                    'pynput.keyboard._win32', 'pynput.mouse._win32',
                    'pyperclip', 'PIL', 'PIL.ImageGrab',
                    'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
                    'pystray', 'tkinter', 'tkinter.ttk',
                    'json', 'threading', 'pathlib',
                ]
                icon_line = f"icon=r'{ico}'," if ico and ico.exists() else ''
                spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    [r'{script}'],
    pathex=[r'{script_dir}'],
    binaries=[],
    datas=[],
    hiddenimports={hidden!r},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name='NexaFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    windowed=True,
{icon_line}
)
"""
                spec_path = script_dir / "nexaflow.spec"
                spec_path.write_text(spec_content, encoding='utf-8')

                log("Step 4/4 — Running PyInstaller (may take 1-3 min)…", 50)

                proc_kwargs = dict(
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    cwd=str(script_dir), text=True)
                if IS_WIN:
                    proc_kwargs['creationflags'] = 0x08000000
                proc  = subprocess.Popen(
                    [sys.executable, '-m', 'PyInstaller', str(spec_path),
                     '--distpath', str(script_dir / 'dist'),
                     '--workpath', str(script_dir / 'build'),
                     '--clean', '--noconfirm'],
                    **proc_kwargs)

                for line in proc.stdout:
                    line = line.strip()
                    if line:
                        log(line[:80], min(95, pvar.get() + 0.5))

                proc.wait()
                pvar.set(100)

                dist = script_dir / 'dist' / ('NexaFlow.exe' if IS_WIN else 'NexaFlow')
                if not dist.exists():
                    alt = script_dir / 'dist' / 'NexaFlow.exe'
                    if alt.exists():
                        dist = alt
                if dist.exists():
                    log(f"\n✓  SUCCESS!  NexaFlow ready at:\n   {dist}")
                    status_lbl.config(text="✓ Build complete!", fg=C['green'])
                    LOG.add(f"EXE built: {dist}", 'system')
                    if IS_WIN:
                        self.after(1000, lambda: os.startfile(str(script_dir / 'dist')))
                else:
                    log("\n[!] Build finished but EXE not found. Check output above.")
                    status_lbl.config(text="Build may have failed — check log.", fg=C['red'])

            except Exception as ex:
                log(f"\n[ERROR] {ex}")
                status_lbl.config(text="Build failed!", fg=C['red'])

        threading.Thread(target=do_build, daemon=True).start()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   SYSTEM TRAY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _setup_tray(self):
        if not HAS_TRAY: return
        try:
            img = _make_icon_image(64)
            menu = pystray.Menu(
                pystray.MenuItem("Show Nexa Flow", self._tray_show, default=True),
                pystray.MenuItem("Start Recording", lambda *_: self.after(0, self._toggle_rec)),
                pystray.MenuItem("Play Workflow",   lambda *_: self.after(0, self._play_start)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit",            lambda *_: self.after(0, self._on_close)),
            )
            self._tray_icon = pystray.Icon("Nexa Flow", img, "NexaFlow v1.0", menu)
            threading.Thread(target=self._tray_icon.run, daemon=True).start()
            LOG.add("System tray icon active", 'system')
        except Exception as e:
            LOG.add(f"Tray icon failed: {e}", 'error')

    def _tray_show(self, *_):
        self.after(0, lambda: (self.deiconify(), self.lift(), self.focus_force()))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   HOTKEYS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _start_hotkeys(self):
        # Do nothing if pynput is not available
        if not HAS_PYNPUT or not pk:
            LOG.add("Hotkeys disabled: pynput not available", 'system')
            self._hk_listener = None
            return

        # Stop existing listener if present
        try:
            if getattr(self, '_hk_listener', None):
                try: self._hk_listener.stop()
                except: pass
        except Exception:
            pass

        # Load hotkeys from config
        defaults = {
            'rec_toggle': 'F9',
            'play': 'F10',
            'pause': 'F12',
            'stop': 'F11',
            'stop_all': 'ESC',
        }
        hk_cfg = CFG.get('hotkeys', defaults)

        # Normalize mapping: build set of normalized strings -> callback
        def norm_hotkey(s: str):
            return '+'.join([t.strip().lower() for t in s.replace(' ', '').split('+') if t.strip()])

        mapping = {}
        try:
            mapping[norm_hotkey(hk_cfg.get('rec_toggle', defaults['rec_toggle']))] = lambda: self.after(0, self._toggle_rec)
            mapping[norm_hotkey(hk_cfg.get('play', defaults['play']))] = lambda: self.after(0, self._play_start)
            mapping[norm_hotkey(hk_cfg.get('pause', defaults['pause']))] = lambda: self.after(0, self._toggle_pause)
            mapping[norm_hotkey(hk_cfg.get('stop', defaults['stop']))] = lambda: self.after(0, self._play_stop)
            mapping[norm_hotkey(hk_cfg.get('stop_all', defaults['stop_all']))] = lambda: self.after(0, self._play_stop)
        except Exception:
            mapping = {}

        pressed_mods = set()

        def key_to_token(key):
            # Return a simple token for the key (e.g., 'f9', 'a', 'esc')
            try:
                if hasattr(key, 'char') and key.char is not None:
                    return str(key.char).lower()
            except Exception:
                pass
            try:
                name = str(key).split('.')[-1]
                return name.lower()
            except Exception:
                return str(key).lower()

        def on_press(k):
            try:
                tok = key_to_token(k)
                if tok in ('ctrl', 'ctrl_l', 'ctrl_r', 'control'):
                    pressed_mods.add('ctrl'); return
                if tok in ('alt', 'alt_l', 'alt_r'):
                    pressed_mods.add('alt'); return
                if tok in ('shift', 'shift_l', 'shift_r'):
                    pressed_mods.add('shift'); return

                # Build event token
                parts = []
                for m in ('ctrl', 'alt', 'shift'):
                    if m in pressed_mods:
                        parts.append(m)
                parts.append(tok)
                evt = '+'.join(parts)
                # match mapping (prefer full event token)
                if evt in mapping:
                    try: mapping[evt]()
                    except Exception: pass
                elif tok in mapping:
                    try: mapping[tok]()
                    except Exception: pass
            except Exception:
                pass

        def on_release(k):
            try:
                tok = key_to_token(k)
                if tok in ('ctrl', 'ctrl_l', 'ctrl_r', 'control'):
                    pressed_mods.discard('ctrl'); return
                if tok in ('alt', 'alt_l', 'alt_r'):
                    pressed_mods.discard('alt'); return
                if tok in ('shift', 'shift_l', 'shift_r'):
                    pressed_mods.discard('shift'); return
            except Exception:
                pass

        listener = pk.Listener(on_press=on_press, on_release=on_release)
        listener.daemon = True
        listener.start()
        self._hk_listener = listener

        LOG.add(f"Hotkeys active: {', '.join(mapping.keys())}", 'system')

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #   WIDGET HELPERS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _big_btn(self, parent, text, color, cmd):
        dark_fg = color in (C['accent'], C['green'], C['amber'])
        return tk.Button(
            parent, text=text, command=cmd,
            bg=color,
            fg=C['bg'] if dark_fg else '#ffffff',
            font=_f(10, True), relief='flat', cursor='hand2',
            padx=14, pady=11,
            activebackground=color, activeforeground='#ffffff')

    def _ghost_btn(self, parent, text, cmd):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=C['card2'], fg=C['text2'], font=_f(8),
            relief='flat', cursor='hand2', padx=10, pady=6,
            activebackground=C['card3'], activeforeground=C['accent'],
            highlightthickness=1, highlightbackground=C['border2'],
            highlightcolor=C['accent'])

    def _check(self, parent, text, var, command=None, bg=None):
        opts = dict(
            text=f"  {text}", variable=var,
            bg=bg or C['bg'], fg=C['text2'],
            selectcolor=C['card2'],
            activebackground=bg or C['bg'],
            activeforeground=C['accent'],
            font=_f(8), relief='flat', cursor='hand2')
        if command: opts['command'] = command
        return tk.Checkbutton(parent, **opts)

    def _status(self, text, color):
        def update_status():
            try:
                self._status_var.set(text)
                self._status_lbl.config(fg=color)
                self._status_dot.config(fg=color)
            except Exception:
                pass
        self.after(0, update_status)

    def run(self):
        self.mainloop()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == '__main__':
    NexaFlow().run()
