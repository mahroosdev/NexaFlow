import queue
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import nexaflow
import remote_access
import remote_host


class RemoteAddressTests(unittest.TestCase):
    def test_pairable_addresses_reject_local_and_virtual_ranges(self):
        self.assertTrue(remote_access.is_pairable_ipv4("10.83.172.243"))
        self.assertTrue(remote_access.is_pairable_ipv4("192.168.1.20"))
        for address in ("127.0.0.1", "169.254.1.2", "192.168.56.1", "8.8.8.8", "bad"):
            self.assertFalse(remote_access.is_pairable_ipv4(address), address)

    def test_active_route_is_first_and_virtual_candidate_is_removed(self):
        class FakeSocket:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def connect(self, _target):
                return None

            def getsockname(self):
                return ("10.0.0.5", 12345)

        addresses = [
            (None, None, None, None, ("192.168.56.1", 0)),
            (None, None, None, None, ("192.168.1.20", 0)),
        ]
        with mock.patch("remote_access.socket.socket", return_value=FakeSocket()), mock.patch(
            "remote_access.socket.getaddrinfo", return_value=addresses
        ):
            self.assertEqual(remote_access.local_ipv4_candidates(), ["10.0.0.5", "192.168.1.20"])


class FirewallRuleTests(unittest.TestCase):
    def setUp(self):
        self.spec = remote_access.firewall_rule_spec(8765, r"C:\Apps\NexaFlow.exe", packaged=True)
        self.rule = {
            "Enabled": "True",
            "Direction": "Inbound",
            "Action": "Allow",
            "Profile": "Any",
            "Protocol": ["TCP"],
            "LocalPort": ["8765"],
            "RemoteAddress": ["LocalSubnet"],
            "Program": r"C:\Apps\NexaFlow.exe",
        }

    def test_exact_rule_matches(self):
        self.assertTrue(remote_access.firewall_rule_matches(self.rule, self.spec))

    def test_stale_executable_is_rejected(self):
        stale = dict(self.rule, Program=r"C:\Program Files\Python314\python.exe")
        self.assertFalse(remote_access.firewall_rule_matches(stale, self.spec))

    def test_partial_profile_is_rejected(self):
        private_only = dict(self.rule, Profile="Private")
        self.assertFalse(remote_access.firewall_rule_matches(private_only, self.spec))

    def test_development_rule_has_separate_name(self):
        dev = remote_access.firewall_rule_spec(8765, r"C:\Python\python.exe", packaged=False)
        self.assertEqual(self.spec.name, "NexaFlow Remote 8765")
        self.assertEqual(dev.name, "NexaFlow Remote 8765 (Development)")


class UiDispatchTests(unittest.TestCase):
    def test_child_window_is_centered_inside_the_visible_screen(self):
        class Window:
            def __init__(self):
                self.position = ""
                self.visible = False

            def update_idletasks(self):
                return None

            def winfo_reqwidth(self):
                return 250

            def winfo_reqheight(self):
                return 180

            def winfo_screenwidth(self):
                return 1920

            def winfo_screenheight(self):
                return 1080

            def geometry(self, value):
                self.position = value

            def deiconify(self):
                self.visible = True

            def lift(self):
                return None

        parent = SimpleNamespace(
            update_idletasks=lambda: None,
            winfo_width=lambda: 900,
            winfo_height=lambda: 700,
            winfo_rootx=lambda: 500,
            winfo_rooty=lambda: 200,
        )
        window = Window()
        nexaflow._show_centered_child(window, parent)
        self.assertEqual(window.position, "250x180+825+460")
        self.assertTrue(window.visible)

    def test_remote_toggle_uses_one_start_stop_control(self):
        app = object.__new__(nexaflow.NexaFlow)
        app._remote_host = SimpleNamespace(running=False)
        app._remote_start = mock.Mock()
        app._remote_stop = mock.Mock()
        nexaflow.NexaFlow._remote_toggle(app)
        app._remote_start.assert_called_once_with()
        app._remote_host.running = True
        nexaflow.NexaFlow._remote_toggle(app)
        app._remote_stop.assert_called_once_with()

    def test_worker_callbacks_only_enqueue(self):
        app = object.__new__(nexaflow.NexaFlow)
        app._ui_events = queue.SimpleQueue()
        nexaflow.NexaFlow._on_pair_request(app, {"requestId": "pair-1"})
        nexaflow.NexaFlow._handle_remote_command(app, "stop", {})
        self.assertEqual(app._ui_events.get_nowait()[0], "pair_request")
        self.assertEqual(app._ui_events.get_nowait()[0], "remote_command")

    def test_pairing_request_from_worker_reaches_ui_queue(self):
        app = object.__new__(nexaflow.NexaFlow)
        app._ui_events = queue.SimpleQueue()
        host = remote_host.RemoteHost(approval_handler=app._on_pair_request)
        worker = threading.Thread(
            target=host.create_request,
            args=("Phone", "phone-1", "10.0.0.2"),
        )
        worker.start()
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        event_type, record = app._ui_events.get_nowait()
        self.assertEqual(event_type, "pair_request")
        self.assertEqual(record["deviceId"], "phone-1")

    def test_cancelled_request_is_ignored_before_dialog_creation(self):
        class Host:
            @staticmethod
            def poll_request(_request_id):
                return {"status": "cancelled"}

        app = object.__new__(nexaflow.NexaFlow)
        app._remote_host = Host()
        self.assertIsNone(nexaflow.NexaFlow._show_pair_dialog(app, {"requestId": "pair-1"}))

    def test_auto_start_preference_persists(self):
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch(
            "nexaflow.Path.home", return_value=Path(temp_dir)
        ):
            first = nexaflow.ConfigManager()
            self.assertFalse(first.get("remote_start_on_launch", False))
            first.set("remote_start_on_launch", True)
            second = nexaflow.ConfigManager()
            self.assertTrue(second.get("remote_start_on_launch"))


class FirewallLifecycleTests(unittest.TestCase):
    class Value:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    def make_app(self):
        app = object.__new__(nexaflow.NexaFlow)
        app._firewall_rule_ready = False
        app._firewall_spec = None
        app._firewall_check_inflight = None
        app._firewall_repair_inflight = None
        app._firewall_prompted_signatures = set()
        app._remote_firewall_var = self.Value()
        return app

    def test_duplicate_firewall_check_is_suppressed(self):
        app = self.make_app()
        with mock.patch("nexaflow.IS_WIN", True), mock.patch("nexaflow.threading.Thread") as thread:
            nexaflow.NexaFlow._ensure_firewall_rule(app, 8765)
            nexaflow.NexaFlow._ensure_firewall_rule(app, 8765)
        self.assertEqual(thread.call_count, 1)

    def test_valid_rule_is_reused_without_prompt(self):
        app = self.make_app()
        spec = remote_access.firewall_rule_spec(8765, r"C:\Apps\NexaFlow.exe", True)
        app._firewall_spec = spec
        app._firewall_check_inflight = f"{spec.name}|{spec.port}|{spec.executable}"
        with mock.patch("nexaflow.messagebox.askyesno") as prompt, mock.patch.object(nexaflow.CFG, "set"):
            nexaflow.NexaFlow._handle_firewall_check(app, {"spec": spec, "result": {"status": "valid"}})
        prompt.assert_not_called()
        self.assertTrue(app._firewall_rule_ready)

    def test_missing_rule_prompts_only_once_per_run(self):
        app = self.make_app()
        spec = remote_access.firewall_rule_spec(8765, r"C:\Apps\NexaFlow.exe", True)
        app._firewall_spec = spec
        with mock.patch("nexaflow.messagebox.askyesno", return_value=False) as prompt:
            payload = {"spec": spec, "result": {"status": "missing"}}
            nexaflow.NexaFlow._handle_firewall_check(app, payload)
            nexaflow.NexaFlow._handle_firewall_check(app, payload)
        self.assertEqual(prompt.call_count, 1)


class PlaybackStatusTests(unittest.TestCase):
    def make_app(self):
        app = object.__new__(nexaflow.NexaFlow)
        app._rec = SimpleNamespace(recording=False, playing=False, paused=False, events=[{}, {}], name="demo")
        app._ui_playing = False
        app._play_countdown_active = False
        app._play_countdown_remaining = 0
        app._play_t0 = 0.0
        app._play_paused_total = 0.0
        app._play_pause_started = 0.0
        app._play_current_event = 0
        app._play_total_events = 0
        app._play_current_loop = 0
        app._play_total_loops = None
        return app

    def test_playback_phases_and_progress_are_reported(self):
        app = self.make_app()
        app._rec.playing = True
        app._play_t0 = time.time() - 2
        app._play_current_event = 1
        app._play_total_events = 2
        app._play_current_loop = 1
        app._play_total_loops = 3
        with mock.patch.object(nexaflow.CFG, "get_recent", return_value=[]):
            status = nexaflow.NexaFlow._remote_status_snapshot(app)
        self.assertEqual(status["playback"]["phase"], "playing")
        self.assertEqual(status["playback"]["progressPercent"], 50.0)
        self.assertEqual(status["playback"]["totalLoops"], 3)
        app._rec.paused = True
        with mock.patch.object(nexaflow.CFG, "get_recent", return_value=[]):
            self.assertEqual(nexaflow.NexaFlow._remote_status_snapshot(app)["playback"]["phase"], "paused")

    def test_pause_time_is_excluded_from_elapsed_time(self):
        app = self.make_app()
        app._play_t0 = 100.0
        app._play_paused_total = 10.0
        app._play_pause_started = 150.0
        with mock.patch("nexaflow.time.time", return_value=200.0):
            self.assertEqual(nexaflow.NexaFlow._play_elapsed_seconds(app), 40.0)

    def test_countdown_callback_is_cancelled(self):
        app = self.make_app()
        app._play_countdown_active = True
        app._play_countdown_remaining = 3
        app._play_countdown_after_id = "after-1"
        app.after_cancel = mock.Mock()
        nexaflow.NexaFlow._cancel_play_countdown(app)
        app.after_cancel.assert_called_once_with("after-1")
        self.assertFalse(app._play_countdown_active)
        self.assertEqual(app._play_countdown_remaining, 0)


if __name__ == "__main__":
    unittest.main()
