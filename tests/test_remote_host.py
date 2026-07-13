import json
import http.client
import time
import unittest
import urllib.error
import urllib.request

import remote_host


remote_host.MouseController = None
remote_host.KeyboardController = None


class RemoteHostPairingTests(unittest.TestCase):
    def make_host(self, **overrides):
        trusted = overrides.pop("trusted", {})
        removed = overrides.pop("removed", [])
        approvals = overrides.pop("approvals", [])
        host = remote_host.RemoteHost(
            approval_handler=approvals.append,
            trusted_check=lambda device_id: device_id in trusted,
            trusted_add=lambda device_id, name: trusted.__setitem__(device_id, name),
            trusted_remove=lambda device_id: (removed.append(device_id), trusted.pop(device_id, None)),
            **overrides,
        )
        return host, trusted, removed, approvals

    def test_approve_poll_and_trusted_reconnect(self):
        host, trusted, _, approvals = self.make_host()
        request = host.create_request("Phone", "phone-1", "192.168.1.20")
        self.assertEqual(request["status"], "pending")
        self.assertEqual(len(approvals), 1)
        self.assertTrue(host.approve_request(request["requestId"], trust=True))
        result = host.poll_request(request["requestId"])
        self.assertEqual(result["status"], "approved")
        self.assertTrue(result["token"])
        self.assertEqual(trusted["phone-1"], "Phone")

        reconnect = host.create_request("Phone", "phone-1", "192.168.1.20")
        self.assertEqual(reconnect["status"], "approved")
        self.assertTrue(reconnect["token"])
        self.assertEqual(len(approvals), 1)

    def test_duplicate_pending_request_is_reused(self):
        host, _, _, approvals = self.make_host()
        first = host.create_request("Phone", "phone-1", "192.168.1.20")
        second = host.create_request("Phone", "phone-1", "192.168.1.20")
        self.assertEqual(first["requestId"], second["requestId"])
        self.assertEqual(len(approvals), 1)

    def test_pairing_rate_limit_reuses_duplicates_and_rejects_new_requests(self):
        host, _, _, approvals = self.make_host()
        first = host.create_request("Phone", "phone-0", "192.168.1.20")
        duplicate = host.create_request("Phone", "phone-0", "192.168.1.20")
        self.assertEqual(first["requestId"], duplicate["requestId"])

        for index in range(1, remote_host.PAIR_RATE_LIMIT):
            host.create_request("Phone", f"phone-{index}", "192.168.1.20")

        self.assertEqual(len(approvals), remote_host.PAIR_RATE_LIMIT)
        with self.assertRaises(remote_host.PairingRateLimitError):
            host.create_request("Phone", "phone-over-limit", "192.168.1.20")

    def test_deny_cancel_and_expiry(self):
        host, _, _, _ = self.make_host()
        denied = host.create_request("Denied", "phone-1", "192.168.1.20")
        self.assertTrue(host.deny_request(denied["requestId"]))
        self.assertEqual(host.poll_request(denied["requestId"]), {"status": "denied"})

        cancelled = host.create_request("Cancelled", "phone-2", "192.168.1.21")
        self.assertTrue(host.cancel_request(cancelled["requestId"]))
        self.assertEqual(host.poll_request(cancelled["requestId"]), {"status": "cancelled"})

        expired = host.create_request("Expired", "phone-3", "192.168.1.22")
        with host._lock:
            host._pending[expired["requestId"]]["created"] = time.time() - remote_host.PAIR_REQUEST_TTL - 1
        self.assertEqual(host.poll_request(expired["requestId"]), {"status": "expired"})

    def test_revoke_removes_trust_and_invalidates_token(self):
        host, trusted, removed, _ = self.make_host(trusted={"phone-1": "Phone"})
        request = host.create_request("Phone", "phone-1", "192.168.1.20")
        self.assertEqual(request["status"], "approved")
        self.assertTrue(host._token)
        self.assertTrue(host.revoke_device("phone-1"))
        self.assertEqual(removed, ["phone-1"])
        self.assertNotIn("phone-1", trusted)
        self.assertEqual(host._token, "")

    def test_http_cancel_and_revoke_endpoints(self):
        host, trusted, removed, _ = self.make_host(trusted={"phone-1": "Phone"})
        host.start(port=0, bind_host="127.0.0.1")
        port = host._server.server_address[1]

        def post(path, payload, token=""):
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}{path}",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    **({"Authorization": f"Bearer {token}"} if token else {}),
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))

        try:
            pending = post("/pair/request", {"deviceName": "Other", "deviceId": "phone-2"})
            cancelled = post("/pair/cancel", {"requestId": pending["requestId"]})
            self.assertTrue(cancelled["cancelled"])

            approved = post("/pair/request", {"deviceName": "Phone", "deviceId": "phone-1"})
            revoked = post("/pair/revoke", {"deviceId": "phone-1"}, approved["token"])
            self.assertTrue(revoked["ok"])
            self.assertEqual(removed, ["phone-1"])
            self.assertNotIn("phone-1", trusted)
        finally:
            host.stop()

    def test_http_blocks_web_origins_and_allows_extension_origin(self):
        host, _, _, _ = self.make_host()
        host.start(port=0, bind_host="127.0.0.1")
        port = host._server.server_address[1]
        extension_origin = "chrome-extension://abcdefghijklmnop"

        try:
            blocked = urllib.request.Request(
                f"http://127.0.0.1:{port}/health",
                headers={"Origin": "https://attacker.example"},
            )
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(blocked, timeout=5)
            self.assertEqual(error.exception.code, 403)
            self.assertIsNone(error.exception.headers.get("Access-Control-Allow-Origin"))
            error.exception.close()

            allowed = urllib.request.Request(
                f"http://127.0.0.1:{port}/health",
                headers={"Origin": extension_origin},
            )
            with urllib.request.urlopen(allowed, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Access-Control-Allow-Origin"], extension_origin)

            native = urllib.request.Request(f"http://127.0.0.1:{port}/health")
            with urllib.request.urlopen(native, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
        finally:
            host.stop()

    def test_http_rejects_oversized_and_non_object_json(self):
        host, _, _, _ = self.make_host()
        host.start(port=0, bind_host="127.0.0.1")
        port = host._server.server_address[1]

        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.putrequest("POST", "/pair/request")
            connection.putheader("Content-Type", "application/json")
            connection.putheader("Content-Length", str(remote_host.MAX_JSON_BODY_BYTES + 1))
            connection.endheaders()
            response = connection.getresponse()
            self.assertEqual(response.status, 413)
            response.read()
            connection.close()

            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/pair/request",
                data=b"[]",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(request, timeout=5)
            self.assertEqual(error.exception.code, 400)
            error.exception.close()
        finally:
            host.stop()


if __name__ == "__main__":
    unittest.main()
