const QUALITY_PRESETS = Object.freeze({
  sharp: Object.freeze({ maxWidth: 1600, intervalMs: 800 }),
  balanced: Object.freeze({ maxWidth: 1200, intervalMs: 1100 }),
  battery: Object.freeze({ maxWidth: 800, intervalMs: 1900 })
});
const MIN_STARTUP_MS = 2500;

function createDeviceId(now = Date.now(), random = Math.random()) {
  return `pair_${now}_${random.toString(36).slice(2, 10)}`;
}

function migrateSettings(value = {}) {
  const quality = Object.hasOwn(QUALITY_PRESETS, value.screenQuality)
    ? value.screenQuality
    : "balanced";
  const theme = ["light", "dark"].includes(value.themeMode)
    ? value.themeMode
    : "light";
  return {
    hostInput: String(value.hostInput || ""),
    deviceId: String(value.deviceId || ""),
    themeMode: theme,
    screenQuality: quality
  };
}

function shouldAutoReconnect(settings) {
  return Boolean(String(settings?.hostInput || "").trim() && String(settings?.deviceId || "").trim());
}

function playbackPrimary(phase) {
  if (phase === "playing") return { label: "Pause", command: "pause", icon: "pause" };
  if (phase === "paused") return { label: "Resume", command: "pause", icon: "play" };
  if (phase === "countdown") return { label: "Starting", command: null, icon: "timer-outline" };
  return { label: "Start", command: "play", icon: "play" };
}

function acceptLoadedFrame(currentFrame, candidateFrame, loaded) {
  return loaded && candidateFrame ? candidateFrame : currentFrame;
}

module.exports = {
  QUALITY_PRESETS,
  MIN_STARTUP_MS,
  acceptLoadedFrame,
  createDeviceId,
  migrateSettings,
  playbackPrimary,
  shouldAutoReconnect
};
