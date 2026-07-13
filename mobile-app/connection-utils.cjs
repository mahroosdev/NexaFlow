const DEFAULT_DESKTOP_PORT = "8765";

class DesktopAddressError extends Error {
  constructor(message) {
    super(message);
    this.name = "DesktopAddressError";
    this.code = "invalid-address";
  }
}

function normalizeDesktopBaseUrl(value) {
  const input = String(value || "").trim();
  if (!input) return "";
  const withScheme = /^[a-z][a-z0-9+.-]*:\/\//i.test(input) ? input : `http://${input}`;
  let parsed;
  try {
    parsed = new URL(withScheme);
  } catch (_error) {
    throw new DesktopAddressError("Enter the desktop address shown by NexaFlow, including port 8765.");
  }
  if (!/^https?:$/.test(parsed.protocol)) {
    throw new DesktopAddressError("The desktop address must use a local HTTP connection.");
  }
  if (parsed.username || parsed.password || (parsed.pathname && parsed.pathname !== "/") || parsed.search || parsed.hash) {
    throw new DesktopAddressError("Enter only the desktop IP address and port, without a path or sign-in details.");
  }
  const hostname = parsed.hostname.toLowerCase();
  if (!hostname || hostname === "localhost" || hostname === "0.0.0.0" || hostname.startsWith("127.")) {
    throw new DesktopAddressError("Use the Wi-Fi or hotspot address shown by NexaFlow Desktop, not localhost.");
  }
  const host = parsed.hostname.includes(":") && !parsed.hostname.startsWith("[")
    ? `[${parsed.hostname}]`
    : parsed.hostname;
  return `http://${host}:${parsed.port || DEFAULT_DESKTOP_PORT}`;
}

function connectionFailureMessage(error, stage = "checking") {
  if (error && error.code === "invalid-address") return error.message;
  if (error && error.code === "wrong-service") {
    return "That address answered, but it is not NexaFlow Desktop. Check the IP and port.";
  }
  if (error && error.code === "cancelled") return "Pairing cancelled";
  if (error && error.code === "timeout") {
    return "The desktop did not respond. Confirm Remote Access is ON and Windows Firewall allows NexaFlow.";
  }
  if (stage === "waiting") {
    return "The desktop stopped responding while approval was pending. Confirm Remote Access is still ON.";
  }
  return "Could not reach NexaFlow Desktop. Check the shown IP, port 8765, Remote Access, and firewall permission.";
}

async function fetchWithTimeout(fetchImpl, url, options = {}, controls = {}) {
  const controller = new AbortController();
  const timeoutMs = Number(controls.timeoutMs || 7000);
  if (controls.onController) controls.onController(controller, null);
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetchImpl(url, { ...options, signal: controller.signal });
  } catch (error) {
    if (error && error.name === "AbortError") {
      const aborted = new Error(controls.isCancelled?.() ? "Pairing cancelled" : "Request timed out");
      aborted.code = controls.isCancelled?.() ? "cancelled" : "timeout";
      throw aborted;
    }
    throw error;
  } finally {
    clearTimeout(timer);
    if (controls.onController) controls.onController(null, controller);
  }
}

module.exports = {
  DEFAULT_DESKTOP_PORT,
  DesktopAddressError,
  normalizeDesktopBaseUrl,
  connectionFailureMessage,
  fetchWithTimeout
};
