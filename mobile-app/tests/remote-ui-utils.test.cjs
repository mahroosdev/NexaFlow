const assert = require("node:assert/strict");
const test = require("node:test");

const {
  QUALITY_PRESETS,
  MIN_STARTUP_MS,
  acceptLoadedFrame,
  createDeviceId,
  migrateSettings,
  playbackPrimary,
  shouldAutoReconnect
} = require("../remote-ui-utils.cjs");

test("settings migration keeps address and removes obsolete choices", () => {
  const settings = migrateSettings({
    hostInput: "10.0.0.2:8765",
    deviceId: "phone-1",
    themeMode: "dark",
    screenQuality: "sharp",
    refreshRate: "fast",
    reconnectOnLaunch: "off"
  });
  assert.deepEqual(settings, {
    hostInput: "10.0.0.2:8765",
    deviceId: "phone-1",
    themeMode: "dark",
    screenQuality: "sharp"
  });
});

test("system appearance migrates to light and startup remains visible long enough", () => {
  assert.equal(migrateSettings({ themeMode: "system" }).themeMode, "light");
  assert.equal(MIN_STARTUP_MS, 2500);
});

test("trusted reconnect is attempted once only when address and identity exist", () => {
  assert.equal(shouldAutoReconnect({ hostInput: "10.0.0.2:8765", deviceId: "phone-1" }), true);
  assert.equal(shouldAutoReconnect({ hostInput: "", deviceId: "phone-1" }), false);
  assert.equal(shouldAutoReconnect({ hostInput: "10.0.0.2:8765", deviceId: "" }), false);
});

test("primary playback control maps start pause and resume", () => {
  assert.equal(playbackPrimary("idle").command, "play");
  assert.deepEqual(playbackPrimary("playing"), { label: "Pause", command: "pause", icon: "pause" });
  assert.deepEqual(playbackPrimary("paused"), { label: "Resume", command: "pause", icon: "play" });
  assert.equal(playbackPrimary("countdown").command, null);
});

test("quality presets control both width and refresh interval", () => {
  assert.deepEqual(QUALITY_PRESETS.sharp, { maxWidth: 1600, intervalMs: 800 });
  assert.ok(QUALITY_PRESETS.balanced.intervalMs > QUALITY_PRESETS.sharp.intervalMs);
  assert.ok(QUALITY_PRESETS.battery.maxWidth < QUALITY_PRESETS.balanced.maxWidth);
  assert.ok(QUALITY_PRESETS.battery.intervalMs > QUALITY_PRESETS.balanced.intervalMs);
});

test("failed frame keeps the visible frame and loaded frame swaps it", () => {
  assert.equal(acceptLoadedFrame("frame-a", "frame-b", false), "frame-a");
  assert.equal(acceptLoadedFrame("frame-a", "frame-b", true), "frame-b");
});

test("device identity is stable in format and does not contain the model name", () => {
  assert.equal(createDeviceId(123, 0.5), "pair_123_i");
});
