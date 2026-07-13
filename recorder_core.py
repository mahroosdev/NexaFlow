"""recorder_core.py

Lightweight shared recorder used by both the launcher and main app.
Provides start/stop/play/save/load and stores events in a simple JSON format.
"""
import time
import json
from pathlib import Path
try:
    from pynput import keyboard as pk, mouse as pm
    from pynput.keyboard import Key, Controller as KCtrl
    from pynput.mouse import Button, Controller as MCtrl
except Exception:
    pk = pm = Key = KCtrl = Button = MCtrl = None


class Recorder:
    def __init__(self):
        self.events = []
        self.recording = False
        self._ml = None
        self._kl = None
        self._t0 = None
        self._last_move_ts = 0.0
        self._stop_play = False
        self._pressed_modifiers = set()

    def _ts(self):
        if not self._t0:
            return 0.0
        return round(time.time() - self._t0, 4)

    def _on_click(self, x, y, btn, pressed):
        if not self.recording: return
        self.events.append({'t':'click','x':x,'y':y,'btn':str(btn),'pressed':pressed,'ts':self._ts()})

    def _on_move(self, x, y):
        if not self.recording: return
        # throttled sampling: avoid flooding with many move events
        now = time.time()
        if now - (self._last_move_ts or 0.0) < 0.03:
            return
        self._last_move_ts = now
        self.events.append({'t':'move','x':x,'y':y,'ts':self._ts()})

    def _on_press(self, k):
        if not self.recording: return
        key = self._key_to_record_value(k)
        self.events.append({'t':'kd','k':key,'ts':self._ts()})

    def _on_release(self, k):
        if not self.recording: return
        key = self._key_to_record_value(k)
        self.events.append({'t':'ku','k':key,'ts':self._ts()})
        self._track_modifier(k, pressed=False)

    def _on_scroll(self, x, y, dx, dy):
        if not self.recording: return
        self.events.append({'t':'scroll','x':x,'y':y,'dx':dx,'dy':dy,'ts':self._ts()})

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

    def _key_to_record_value(self, k):
        self._track_modifier(k, pressed=True)
        try:
            ch = k.char
        except Exception:
            ch = None
        if ch:
            code = ord(ch) if len(ch) == 1 else 0
            if 'ctrl' in self._pressed_modifiers and 1 <= code <= 26:
                return chr(code + 96)
            return ch
        return str(k)

    def start(self):
        if not (pk and pm):
            raise RuntimeError('pynput not available')
        self.events = []
        self.recording = True
        self._t0 = time.time()
        self._last_move_ts = 0.0
        self._pressed_modifiers = set()
        # register scroll handler as well
        self._ml = pm.Listener(on_click=self._on_click, on_move=self._on_move, on_scroll=self._on_scroll)
        self._kl = pk.Listener(on_press=self._on_press, on_release=self._on_release)
        self._ml.start(); self._kl.start()

    def stop(self):
        self._stop_play = True
        self.recording = False
        try:
            if self._ml: self._ml.stop()
            if self._kl: self._kl.stop()
        except: pass

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'v':5,'events':self.events}, f, indent=2)

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            d = json.load(f)
        self.events = d.get('events', [])

    def _translate_key(self, k):
        if not k or not isinstance(k, str):
            return None
        if k.startswith('Key.'):
            name = k.split('.', 1)[1]
            return getattr(Key, name, None)
        if len(k) == 1:
            return k
        return getattr(Key, k, None)

    def play(self):
        if not self.events:
            return
        self._stop_play = False
        kc = KCtrl() if KCtrl else None
        mc = MCtrl() if MCtrl else None

        def _wait(secs):
            end = time.time() + secs
            while time.time() < end:
                if self._stop_play:
                    return
                time.sleep(0.01)

        for e in self.events:
            if self._stop_play:
                break
            t = e.get('t')
            if t == 'move' and mc:
                mc.position = (e['x'], e['y'])
            elif t == 'scroll' and mc:
                mc.position = (e['x'], e['y'])
                mc.scroll(e.get('dx', 0), e.get('dy', 0))
            elif t == 'click' and mc:
                mc.position = (e['x'], e['y'])
                btn = Button.left if 'left' in e['btn'] else (
                    Button.right if 'right' in e['btn'] else Button.middle)
                if e.get('pressed'):
                    mc.press(btn)
                else:
                    mc.release(btn)
            elif t == 'wait':
                _wait(e.get('secs', 1.0))
            elif t == 'type' and kc:
                text = e.get('text', '')
                if text:
                    try:
                        kc.type(text)
                    except Exception:
                        pass
            elif t in ('kd', 'ku') and kc:
                k = self._translate_key(e.get('k'))
                if not k:
                    continue
                try:
                    if t == 'kd': kc.press(k)
                    else: kc.release(k)
                except Exception:
                    pass
            if self._stop_play:
                break
