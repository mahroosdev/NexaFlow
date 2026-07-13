const test = require("node:test");
const assert = require("node:assert/strict");
const {
  normalizeDesktopBaseUrl,
  connectionFailureMessage,
  fetchWithTimeout
} = require("../connection-utils.cjs");


test("normalizes a desktop address and supplies the default port", () => {
  assert.equal(normalizeDesktopBaseUrl("10.83.172.243"), "http://10.83.172.243:8765");
  assert.equal(normalizeDesktopBaseUrl("https://192.168.1.20:9000/"), "http://192.168.1.20:9000");
});

test("rejects phone-unreachable or path-bearing addresses", () => {
  assert.throws(() => normalizeDesktopBaseUrl("127.0.0.1:8765"), /not localhost/i);
  assert.throws(() => normalizeDesktopBaseUrl("192.168.1.20:8765/pair"), /without a path/i);
});

test("bounded fetch reports a timeout", async () => {
  const neverCompletes = (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener("abort", () => {
      const error = new Error("aborted");
      error.name = "AbortError";
      reject(error);
    });
  });
  await assert.rejects(
    fetchWithTimeout(neverCompletes, "http://desktop/health", {}, { timeoutMs: 10 }),
    (error) => error.code === "timeout"
  );
});

test("bounded fetch distinguishes user cancellation", async () => {
  let cancelled = false;
  const waitsForAbort = (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener("abort", () => {
      const error = new Error("aborted");
      error.name = "AbortError";
      reject(error);
    });
  });
  await assert.rejects(
    fetchWithTimeout(waitsForAbort, "http://desktop/health", {}, {
      timeoutMs: 1000,
      isCancelled: () => cancelled,
      onController: (controller) => {
        if (controller) {
          setImmediate(() => {
            cancelled = true;
            controller.abort();
          });
        }
      }
    }),
    (error) => error.code === "cancelled"
  );
});

test("connection failures are stage-specific", () => {
  const timeout = Object.assign(new Error("timeout"), { code: "timeout" });
  assert.match(connectionFailureMessage(timeout, "checking"), /Remote Access is ON/i);
  assert.match(connectionFailureMessage(new Error("offline"), "waiting"), /approval was pending/i);
});
