"""Secure visible remote-control host for NexaFlow.

This module intentionally does not expose hidden or silent access. A remote
session must be started from the desktop app, approved by the desktop user, and
can be stopped from the desktop at any time.
"""

from __future__ import annotations

import io
import json
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Optional
from urllib.parse import parse_qs, urlparse

from remote_access import recommended_local_ipv4

try:
    from PIL import ImageGrab
except Exception:  # pragma: no cover - depends on desktop environment
    ImageGrab = None

try:
    from pynput.mouse import Button, Controller as MouseController
    from pynput.keyboard import Controller as KeyboardController, Key
except Exception:  # pragma: no cover - optional at import time
    Button = MouseController = KeyboardController = Key = None


# How long a pending pairing request waits for desktop approval before it expires.
PAIR_REQUEST_TTL = 60.0
PAIR_RATE_WINDOW = 60.0
PAIR_RATE_LIMIT = 6
MAX_JSON_BODY_BYTES = 64 * 1024
MAX_DEVICE_NAME_LENGTH = 80
MAX_DEVICE_ID_LENGTH = 200
MAX_PAIR_RECORDS = 200


class PairingRateLimitError(RuntimeError):
    pass


class RequestBodyTooLargeError(ValueError):
    pass


class RemoteHost:
    def __init__(
        self,
        *,
        command_handler: Optional[Callable[..., None]] = None,
        status_provider: Optional[Callable[[], dict]] = None,
        approval_handler: Optional[Callable[[dict], None]] = None,
        trusted_check: Optional[Callable[[str], bool]] = None,
        trusted_add: Optional[Callable[[str, str], None]] = None,
        trusted_remove: Optional[Callable[[str], None]] = None,
        log: Optional[Callable[[str], None]] = None,
    ):
        self.command_handler = command_handler
        self.status_provider = status_provider
        # Called (on the server thread) when a new pairing request needs desktop approval.
        self.approval_handler = approval_handler
        # Returns True if a deviceId was previously approved ("trusted") -> auto-approve.
        self.trusted_check = trusted_check
        # Persist a newly approved device as trusted (deviceId, deviceName).
        self.trusted_add = trusted_add
        # Remove a device from the persistent trusted-device list.
        self.trusted_remove = trusted_remove
        self.log = log or (lambda msg: None)
        self.port = 8765
        self.bind_host = "0.0.0.0"
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._token = ""
        # Pending/decided pairing requests keyed by requestId.
        # value: {requestId, deviceName, deviceId, ip, status, token, created}
        self._pending: dict[str, dict] = {}
        self._pair_attempts: dict[str, list[float]] = {}
        self._mouse = MouseController() if MouseController else None
        self._keyboard = KeyboardController() if KeyboardController else None
        self._last_client = ""
        self._lock = threading.Lock()

    @property
    def running(self) -> bool:
        return self._server is not None

    @property
    def last_client(self) -> str:
        return self._last_client

    def start(self, port: int = 8765, bind_host: str = "0.0.0.0") -> None:
        if self.running:
            return
        self.port = int(port)
        self.bind_host = bind_host
        self._token = ""
        with self._lock:
            self._pending.clear()
            self._pair_attempts.clear()
        handler = self._make_handler()
        self._server = ThreadingHTTPServer((self.bind_host, self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self.log(f"Remote access started on {self.local_ip()}:{self.port}")

    def stop(self) -> None:
        server = self._server
        self._server = None
        self._token = ""
        with self._lock:
            self._pending.clear()
            self._pair_attempts.clear()
        if server:
            server.shutdown()
            server.server_close()
        self.log("Remote access stopped")

    # ── Approve-based pairing ────────────────────────────────────────────
    def _prune_pending(self) -> None:
        """Drop pending requests that were never decided within the TTL."""
        now = time.time()
        for rid in list(self._pending.keys()):
            rec = self._pending[rid]
            if rec["status"] == "pending" and now - rec["created"] > PAIR_REQUEST_TTL:
                rec["status"] = "expired"
        if len(self._pending) > MAX_PAIR_RECORDS:
            removable = sorted(
                (
                    (rid, rec)
                    for rid, rec in self._pending.items()
                    if rec["status"] != "pending"
                ),
                key=lambda item: item[1]["created"],
            )
            for rid, _ in removable[: len(self._pending) - MAX_PAIR_RECORDS]:
                self._pending.pop(rid, None)

    def _record_pair_attempt(self, ip: str) -> None:
        now = time.time()
        attempts = [
            created
            for created in self._pair_attempts.get(ip, [])
            if now - created < PAIR_RATE_WINDOW
        ]
        if len(attempts) >= PAIR_RATE_LIMIT:
            self._pair_attempts[ip] = attempts
            raise PairingRateLimitError("Too many pairing requests. Wait and try again.")
        attempts.append(now)
        self._pair_attempts[ip] = attempts

    def create_request(self, device_name: str, device_id: str, ip: str) -> dict:
        """Register a pairing request. Auto-approves trusted devices."""
        device_name = device_name or "Unknown device"
        device_id = device_id or ""
        with self._lock:
            self._prune_pending()
            for existing in self._pending.values():
                same_device = (
                    existing["deviceId"] == device_id
                    if device_id
                    else existing["deviceName"] == device_name
                )
                if existing["status"] == "pending" and existing["ip"] == ip and same_device:
                    return dict(existing)
            self._record_pair_attempt(ip)

        request_id = secrets.token_urlsafe(12)
        record = {
            "requestId": request_id,
            "deviceName": device_name,
            "deviceId": device_id,
            "ip": ip,
            "status": "pending",
            "token": "",
            "created": time.time(),
        }
        with self._lock:
            self._prune_pending()
            self._pending[request_id] = record
        # Trusted device -> approve immediately, no desktop prompt.
        if device_id and self.trusted_check and self.trusted_check(device_id):
            self.approve_request(request_id, trust=False)
            self.log(f"Auto-approved trusted device {record['deviceName']} ({ip})")
        elif self.approval_handler:
            try:
                self.approval_handler(dict(record))
            except Exception as exc:  # pragma: no cover - UI thread issues
                self.log(f"Approval handler error: {exc}")
        return dict(self._pending[request_id])

    def approve_request(self, request_id: str, trust: bool = False) -> bool:
        with self._lock:
            rec = self._pending.get(request_id)
            if not rec or rec["status"] != "pending":
                return False
            token = secrets.token_urlsafe(32)
            self._token = token
            rec["status"] = "approved"
            rec["token"] = token
        if trust and self.trusted_add and rec["deviceId"]:
            try:
                self.trusted_add(rec["deviceId"], rec["deviceName"])
            except Exception as exc:  # pragma: no cover
                self.log(f"Trusted-add error: {exc}")
        self.log(f"Approved {rec['deviceName']} ({rec['ip']})")
        return True

    def deny_request(self, request_id: str) -> bool:
        with self._lock:
            rec = self._pending.get(request_id)
            if not rec or rec["status"] != "pending":
                return False
            rec["status"] = "denied"
            rec["token"] = ""
        self.log(f"Denied {rec['deviceName']} ({rec['ip']})")
        return True

    def cancel_request(self, request_id: str) -> bool:
        with self._lock:
            rec = self._pending.get(request_id)
            if not rec or rec["status"] != "pending":
                return False
            rec["status"] = "cancelled"
            rec["token"] = ""
        self.log(f"Cancelled pairing for {rec['deviceName']} ({rec['ip']})")
        return True

    def revoke_device(self, device_id: str) -> bool:
        device_id = str(device_id or "").strip()
        if not device_id:
            return False
        if self.trusted_remove:
            try:
                self.trusted_remove(device_id)
            except Exception as exc:  # pragma: no cover
                self.log(f"Trusted-remove error: {exc}")
                return False
        self._token = ""
        self.log("Revoked a trusted companion device")
        return True

    def poll_request(self, request_id: str) -> dict:
        with self._lock:
            self._prune_pending()
            rec = self._pending.get(request_id)
            if not rec:
                return {"status": "unknown"}
            out = {"status": rec["status"]}
            if rec["status"] == "approved":
                out["token"] = rec["token"]
            return out

    def pending_requests(self) -> list:
        with self._lock:
            self._prune_pending()
            return [dict(r) for r in self._pending.values() if r["status"] == "pending"]

    def local_ip(self) -> str:
        return recommended_local_ipv4()

    def public_state(self) -> dict:
        base = self.status_provider() if self.status_provider else {}
        base.update({
            "remoteRunning": self.running,
            "host": self.local_ip(),
            "port": self.port,
            "lastClient": self.last_client,
        })
        return base

    def _authorized(self, request: BaseHTTPRequestHandler, query: dict) -> bool:
        if not self._token:
            return False
        header = request.headers.get("Authorization", "")
        if header == f"Bearer {self._token}":
            return True
        return query.get("token", [""])[0] == self._token

    def _make_handler(self):
        host = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "NexaFlowRemote/1.0"

            def log_message(self, fmt, *args):  # keep console quiet
                return

            def _origin_allowed(self) -> bool:
                origin = self.headers.get("Origin", "").strip()
                return not origin or origin.startswith("chrome-extension://")

            def _send_cors_headers(self) -> None:
                origin = self.headers.get("Origin", "").strip()
                if origin.startswith("chrome-extension://"):
                    self.send_header("Access-Control-Allow-Origin", origin)
                    self.send_header("Vary", "Origin")
                    self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
                    self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

            def _send_json(self, status: int, payload: dict):
                data = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _read_json(self) -> dict:
                try:
                    size = int(self.headers.get("Content-Length", "0") or 0)
                except ValueError as exc:
                    raise ValueError("Invalid Content-Length") from exc
                if size > MAX_JSON_BODY_BYTES:
                    raise RequestBodyTooLargeError("Request body is too large")
                if size <= 0:
                    return {}
                return json.loads(self.rfile.read(size).decode("utf-8"))

            def _reject_disallowed_origin(self) -> bool:
                if self._origin_allowed():
                    return False
                self._send_json(403, {"ok": False, "error": "Web origins are not allowed"})
                return True

            def do_OPTIONS(self):
                if self._reject_disallowed_origin():
                    return
                self._send_json(200, {"ok": True})

            def do_GET(self):
                if self._reject_disallowed_origin():
                    return
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                if parsed.path == "/health":
                    self._send_json(200, {"ok": True, "app": "NexaFlow"})
                    return
                if parsed.path == "/pair/poll":
                    request_id = query.get("requestId", [""])[0]
                    self._send_json(200, host.poll_request(request_id))
                    return
                if not host._authorized(self, query):
                    self._send_json(401, {"ok": False, "error": "Not paired"})
                    return
                host._last_client = self.client_address[0]
                if parsed.path == "/status":
                    self._send_json(200, {"ok": True, "status": host.public_state()})
                    return
                if parsed.path == "/screen.jpg":
                    host._send_screen(self, query)
                    return
                self._send_json(404, {"ok": False, "error": "Not found"})

            def do_POST(self):
                if self._reject_disallowed_origin():
                    return
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                try:
                    body = self._read_json()
                except RequestBodyTooLargeError as exc:
                    self._send_json(413, {"ok": False, "error": str(exc)})
                    return
                except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                    self._send_json(400, {"ok": False, "error": "Invalid JSON request"})
                    return
                if not isinstance(body, dict):
                    self._send_json(400, {"ok": False, "error": "JSON request must be an object"})
                    return
                if parsed.path == "/pair/request":
                    device_name = str(body.get("deviceName", "")).strip()
                    device_id = str(body.get("deviceId", "")).strip()
                    if len(device_name) > MAX_DEVICE_NAME_LENGTH or len(device_id) > MAX_DEVICE_ID_LENGTH:
                        self._send_json(400, {"ok": False, "error": "Device identity is too long"})
                        return
                    host._last_client = self.client_address[0]
                    try:
                        record = host.create_request(device_name, device_id, self.client_address[0])
                    except PairingRateLimitError as exc:
                        self._send_json(429, {"ok": False, "error": str(exc)})
                        return
                    self._send_json(200, {
                        "ok": True,
                        "requestId": record["requestId"],
                        "status": record["status"],
                        "token": record.get("token", ""),
                    })
                    return
                if parsed.path == "/pair/cancel":
                    request_id = str(body.get("requestId", "")).strip()
                    cancelled = host.cancel_request(request_id)
                    self._send_json(200, {"ok": True, "cancelled": cancelled})
                    return
                if not host._authorized(self, query):
                    self._send_json(401, {"ok": False, "error": "Not paired"})
                    return
                host._last_client = self.client_address[0]
                if parsed.path == "/pair/revoke":
                    device_id = str(body.get("deviceId", "")).strip()
                    if host.revoke_device(device_id):
                        self._send_json(200, {"ok": True})
                    else:
                        self._send_json(400, {"ok": False, "error": "Could not revoke device"})
                    return
                if parsed.path == "/input":
                    self._send_json(200, host._handle_input(body))
                    return
                if parsed.path == "/command":
                    cmd = str(body.get("command", "")).strip().lower()
                    if host.command_handler and cmd:
                        try:
                            host.command_handler(cmd, body)
                        except TypeError:
                            host.command_handler(cmd)
                        self._send_json(200, {"ok": True})
                    else:
                        self._send_json(400, {"ok": False, "error": "Unknown command"})
                    return
                self._send_json(404, {"ok": False, "error": "Not found"})

        return Handler

    def _send_screen(self, request: BaseHTTPRequestHandler, query: dict) -> None:
        if ImageGrab is None:
            request.send_error(503, "Screen capture is unavailable")
            return
        image = ImageGrab.grab()
        max_width = int(query.get("maxWidth", ["1200"])[0] or 1200)
        if max_width and image.width > max_width:
            height = int(image.height * (max_width / image.width))
            image = image.resize((max_width, height))
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=55, optimize=True)
        data = buf.getvalue()
        request.send_response(200)
        request._send_cors_headers()
        request.send_header("Content-Type", "image/jpeg")
        request.send_header("Cache-Control", "no-store")
        request.send_header("Content-Length", str(len(data)))
        request.end_headers()
        request.wfile.write(data)

    def _screen_size(self):
        if ImageGrab is None:
            return None
        image = ImageGrab.grab()
        return image.size

    def _handle_input(self, body: dict) -> dict:
        action = str(body.get("action", "")).lower()
        if action in ("tap", "move"):
            if not self._mouse:
                return {"ok": False, "error": "Mouse control unavailable"}
            coords = self._coords(body)
            if not coords:
                return {"ok": False, "error": "Invalid coordinates"}
            self._mouse.position = coords
            if action == "tap":
                self._mouse.click(Button.left, 1)
            return {"ok": True}
        if action == "scroll":
            if not self._mouse:
                return {"ok": False, "error": "Mouse control unavailable"}
            self._mouse.scroll(int(body.get("dx", 0)), int(body.get("dy", 0)))
            return {"ok": True}
        if action == "text":
            if not self._keyboard:
                return {"ok": False, "error": "Keyboard control unavailable"}
            self._keyboard.type(str(body.get("text", "")))
            return {"ok": True}
        if action == "key":
            return self._send_key(str(body.get("key", "")))
        return {"ok": False, "error": "Unknown input action"}

    def _coords(self, body: dict):
        if "x" in body and "y" in body:
            return int(body["x"]), int(body["y"])
        size = self._screen_size()
        if not size:
            return None
        nx = max(0.0, min(1.0, float(body.get("nx", 0))))
        ny = max(0.0, min(1.0, float(body.get("ny", 0))))
        return int(size[0] * nx), int(size[1] * ny)

    def _send_key(self, key_name: str) -> dict:
        if not self._keyboard:
            return {"ok": False, "error": "Keyboard control unavailable"}
        key_name = key_name.lower().strip()
        special = {
            "enter": Key.enter if Key else None,
            "backspace": Key.backspace if Key else None,
            "esc": Key.esc if Key else None,
            "tab": Key.tab if Key else None,
            "space": Key.space if Key else None,
        }
        key = special.get(key_name) or (key_name if len(key_name) == 1 else None)
        if not key:
            return {"ok": False, "error": "Unsupported key"}
        self._keyboard.press(key)
        self._keyboard.release(key)
        return {"ok": True}
