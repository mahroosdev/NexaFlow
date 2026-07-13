import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  Image,
  KeyboardAvoidingView,
  Linking,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";
import { StatusBar } from "expo-status-bar";
import * as FileSystem from "expo-file-system";
import * as ScreenOrientation from "expo-screen-orientation";
import * as SplashScreen from "expo-splash-screen";
import { useFonts } from "expo-font";
import Ionicons from "@expo/vector-icons/Ionicons";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import {
  GestureHandlerRootView,
  PanGestureHandler,
  PinchGestureHandler,
  State,
  TapGestureHandler
} from "react-native-gesture-handler";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";

const {
  normalizeDesktopBaseUrl,
  connectionFailureMessage,
  fetchWithTimeout
} = require("./connection-utils.cjs");
const {
  QUALITY_PRESETS,
  MIN_STARTUP_MS,
  acceptLoadedFrame,
  createDeviceId,
  migrateSettings,
  playbackPrimary,
  shouldAutoReconnect
} = require("./remote-ui-utils.cjs");

SplashScreen.preventAutoHideAsync().catch(() => {});

const SETTINGS_PATH = FileSystem.documentDirectory
  ? `${FileSystem.documentDirectory}nexaflow-settings.json`
  : "";
const SUPPORT_URL = "https://web-nexaflow.netlify.app/support";
const PRIVACY_URL = "https://web-nexaflow.netlify.app/privacy";
const FALLBACK_DEVICE_NAME = "NexaFlow Phone";

const light = {
  bg: "#F4F8FB",
  panel: "#FFFFFF",
  soft: "#EDF5F7",
  ink: "#101827",
  muted: "#607086",
  faint: "#8A9BAD",
  line: "#D4E0E8",
  accent: "#0797B7",
  accentDark: "#08758C",
  green: "#078C68",
  red: "#CF3B3B",
  amber: "#C87508",
  viewer: "#111827",
  white: "#FFFFFF"
};

const dark = {
  bg: "#0B121D",
  panel: "#121C2A",
  soft: "#1B2A38",
  ink: "#F6F9FC",
  muted: "#B2C0CE",
  faint: "#8091A4",
  line: "#2D4051",
  accent: "#27B8D3",
  accentDark: "#72D6E7",
  green: "#25B889",
  red: "#EF6666",
  amber: "#E9A43B",
  viewer: "#050A12",
  white: "#FFFFFF"
};

const TABS = [
  { id: "connect", label: "Connect", icon: "link-outline" },
  { id: "remote", label: "Remote", icon: "desktop-outline" },
  { id: "settings", label: "Settings", icon: "settings-outline" }
];

const PLAYBACK_MODES = [
  { value: "once", label: "Once" },
  { value: "repeat", label: "Repeat" },
  { value: "loop", label: "Loop" }
];
const SPEEDS = ["0.5", "1.0", "1.5", "2.0"];
const START_DELAYS = ["0", "3", "5", "10"];

function deviceModelName() {
  const model = Platform.constants?.Model || Platform.constants?.model;
  return String(model || "").trim() || FALLBACK_DEVICE_NAME;
}

function formatElapsed(value) {
  const seconds = Math.max(0, Number(value) || 0);
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${mins}:${secs}`;
}

function openUrl(url) {
  Linking.openURL(url).catch(() => Alert.alert("Open link", url));
}

function useFrameBuffer({ active, baseUrl, token, quality }) {
  const [currentFrame, setCurrentFrame] = useState("");
  const [pendingFrame, setPendingFrame] = useState("");
  const loadingRef = useRef(false);
  const preset = QUALITY_PRESETS[quality] || QUALITY_PRESETS.balanced;

  const requestFrame = useCallback(() => {
    if (!active || !baseUrl || !token || loadingRef.current) return;
    loadingRef.current = true;
    setPendingFrame(
      `${baseUrl}/screen.jpg?token=${encodeURIComponent(token)}`
      + `&maxWidth=${preset.maxWidth}&t=${Date.now()}`
    );
  }, [active, baseUrl, token, preset.maxWidth]);

  useEffect(() => {
    if (!active || !baseUrl || !token) {
      loadingRef.current = false;
      setPendingFrame("");
      if (!token) setCurrentFrame("");
      return undefined;
    }
    requestFrame();
    const timer = setInterval(requestFrame, preset.intervalMs);
    return () => clearInterval(timer);
  }, [active, baseUrl, token, preset.intervalMs, requestFrame]);

  const frameLoader = pendingFrame ? (
    <Image
      key={pendingFrame}
      source={{ uri: pendingFrame }}
      style={styles.hiddenFrame}
      onLoad={() => {
        setCurrentFrame((current) => acceptLoadedFrame(current, pendingFrame, true));
        setPendingFrame("");
        loadingRef.current = false;
      }}
      onError={() => {
        setCurrentFrame((current) => acceptLoadedFrame(current, pendingFrame, false));
        setPendingFrame("");
        loadingRef.current = false;
      }}
    />
  ) : null;

  return { currentFrame, frameLoader };
}

export default function App() {
  const [fontsLoaded] = useFonts({
    ...Ionicons.font,
    ...MaterialCommunityIcons.font
  });
  const [settingsLoaded, setSettingsLoaded] = useState(false);
  const [showStartup, setShowStartup] = useState(true);
  const startupProgress = useRef(new Animated.Value(0.08)).current;
  const startupBeganAt = useRef(Date.now());

  const [activeTab, setActiveTab] = useState("connect");
  const [hostInput, setHostInput] = useState("");
  const [deviceId, setDeviceId] = useState("");
  const [token, setToken] = useState("");
  const [pairing, setPairing] = useState(false);
  const [pairingStage, setPairingStage] = useState("idle");
  const [message, setMessage] = useState("Enter the desktop address");
  const [status, setStatus] = useState(null);
  const [themeMode, setThemeMode] = useState("light");
  const [screenQuality, setScreenQuality] = useState("balanced");
  const [fullscreen, setFullscreen] = useState(false);
  const [workflowIndex, setWorkflowIndex] = useState(null);
  const [workflowMenuOpen, setWorkflowMenuOpen] = useState(false);
  const [playMode, setPlayMode] = useState("once");
  const [repeatCount, setRepeatCount] = useState("3");
  const [loopDelay, setLoopDelay] = useState("1.0");
  const [speed, setSpeed] = useState("1.0");
  const [startDelay, setStartDelay] = useState("0");
  const pairCancelledRef = useRef(false);
  const pairAbortRef = useRef(null);
  const pairRequestRef = useRef("");
  const autoReconnectRef = useRef(false);

  const resolvedTheme = themeMode;
  const colors = resolvedTheme === "dark" ? dark : light;
  styles = useMemo(() => createStyles(colors), [colors]);

  const desktopAddress = useMemo(() => {
    try {
      return { baseUrl: normalizeDesktopBaseUrl(hostInput), error: "" };
    } catch (error) {
      return { baseUrl: "", error: error.message };
    }
  }, [hostInput]);
  const baseUrl = desktopAddress.baseUrl;
  const paired = Boolean(baseUrl && token);
  const playback = status?.playback || {
    phase: status?.paused ? "paused" : status?.playing ? "playing" : "idle",
    countdownRemaining: 0,
    elapsedSeconds: 0,
    currentEvent: 0,
    totalEvents: Number(status?.events || 0),
    progressPercent: 0,
    currentLoop: 0,
    totalLoops: null
  };
  const workflows = Array.isArray(status?.recentWorkflows) ? status.recentWorkflows : [];
  const selectedWorkflow = workflows.find((item) => item.index === workflowIndex) || workflows[0] || null;
  const primary = playbackPrimary(playback.phase);
  const framesActive = paired && (activeTab === "remote" || fullscreen);
  const { currentFrame, frameLoader } = useFrameBuffer({
    active: framesActive,
    baseUrl,
    token,
    quality: screenQuality
  });

  const apiRequest = useCallback(async (path, options = {}) => {
    if (!baseUrl) throw new Error("Desktop address is missing");
    const { timeoutMs = 7000, trackPairing = false, ...fetchOptions } = options;
    const response = await fetchWithTimeout(
      fetch,
      `${baseUrl}${path}`,
      {
        ...fetchOptions,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(fetchOptions.headers || {})
        }
      },
      {
        timeoutMs,
        isCancelled: () => trackPairing && pairCancelledRef.current,
        onController: trackPairing
          ? (next, current) => {
              if (next) pairAbortRef.current = next;
              else if (pairAbortRef.current === current) pairAbortRef.current = null;
            }
          : null
      }
    );
    const text = await response.text();
    let body = {};
    try {
      body = text ? JSON.parse(text) : {};
    } catch (_error) {
      const error = new Error("Unexpected desktop response");
      error.code = "wrong-service";
      throw error;
    }
    if (!response.ok || body.ok === false) throw new Error(body.error || `Request failed (${response.status})`);
    return body;
  }, [baseUrl, token]);

  const command = useCallback(async (name, values = {}) => {
    if (!paired) return false;
    try {
      await apiRequest("/command", {
        method: "POST",
        timeoutMs: 3500,
        body: JSON.stringify({ command: name, ...values })
      });
      return true;
    } catch (error) {
      setMessage(error.message || "Desktop command failed");
      return false;
    }
  }, [apiRequest, paired]);

  function updateHost(value) {
    if (value !== hostInput && token) {
      setToken("");
      setStatus(null);
      setPairingStage("idle");
      setMessage("Pair again with this address");
    }
    setHostInput(value);
  }

  function cancelPairing() {
    const requestId = pairRequestRef.current;
    pairCancelledRef.current = true;
    pairAbortRef.current?.abort();
    pairAbortRef.current = null;
    pairRequestRef.current = "";
    if (requestId) {
      apiRequest("/pair/cancel", {
        method: "POST",
        timeoutMs: 2500,
        body: JSON.stringify({ requestId })
      }).catch(() => {});
    }
    setPairing(false);
    setPairingStage("cancelled");
    setMessage("Pairing cancelled");
  }

  async function pair({ silent = false, auto = false } = {}) {
    if (!baseUrl) {
      setMessage(desktopAddress.error || "Enter the desktop address");
      return false;
    }
    let stage = "checking";
    setPairing(true);
    setPairingStage(stage);
    pairCancelledRef.current = false;
    setMessage(auto ? "Reconnecting" : "Checking desktop");
    try {
      const health = await apiRequest("/health", { timeoutMs: 5000, trackPairing: true });
      if (health.app !== "NexaFlow") {
        const error = new Error("Wrong service");
        error.code = "wrong-service";
        throw error;
      }
      if (pairCancelledRef.current) return false;
      stage = "requesting";
      setPairingStage(stage);
      setMessage("Sending request");
      const nextDeviceId = deviceId || createDeviceId();
      if (!deviceId) setDeviceId(nextDeviceId);
      const result = await apiRequest("/pair/request", {
        method: "POST",
        timeoutMs: 6000,
        trackPairing: true,
        body: JSON.stringify({ deviceName: deviceModelName(), deviceId: nextDeviceId })
      });
      if (result.status === "approved" && result.token) {
        setToken(result.token);
        setPairingStage("connected");
        setMessage("Connected");
        setActiveTab("remote");
        return true;
      }
      if (!result.requestId) throw new Error("Desktop rejected the request");
      pairRequestRef.current = result.requestId;
      stage = "waiting";
      setPairingStage(stage);
      setMessage("Approve on desktop");
      const deadline = Date.now() + 60000;
      let failures = 0;
      while (Date.now() < deadline) {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        if (pairCancelledRef.current) return false;
        let poll;
        try {
          poll = await apiRequest(`/pair/poll?requestId=${encodeURIComponent(result.requestId)}`, {
            timeoutMs: 4500,
            trackPairing: true
          });
          failures = 0;
        } catch (error) {
          if (error.code === "cancelled") return false;
          failures += 1;
          if (failures >= 3) throw error;
          continue;
        }
        if (poll.status === "approved" && poll.token) {
          setToken(poll.token);
          setPairingStage("connected");
          setMessage("Connected");
          setActiveTab("remote");
          return true;
        }
        if (["denied", "cancelled", "expired", "unknown"].includes(poll.status)) {
          const labels = {
            denied: "Request denied",
            cancelled: "Pairing cancelled",
            expired: "Request expired",
            unknown: "Request expired"
          };
          setPairingStage(poll.status === "cancelled" ? "cancelled" : "failed");
          setMessage(labels[poll.status]);
          return false;
        }
      }
      apiRequest("/pair/cancel", {
        method: "POST",
        timeoutMs: 2500,
        body: JSON.stringify({ requestId: result.requestId })
      }).catch(() => {});
      setPairingStage("failed");
      setMessage("Approval timed out");
      return false;
    } catch (error) {
      if (error.code !== "cancelled") {
        setPairingStage("failed");
        setMessage(connectionFailureMessage(error, stage));
      }
      if (!silent && error.code === "invalid-address") Alert.alert("Desktop address", error.message);
      return false;
    } finally {
      pairAbortRef.current = null;
      pairRequestRef.current = "";
      setPairing(false);
    }
  }

  async function clearPairing() {
    pairCancelledRef.current = true;
    pairAbortRef.current?.abort();
    if (paired && deviceId) {
      try {
        await apiRequest("/pair/revoke", {
          method: "POST",
          timeoutMs: 3500,
          body: JSON.stringify({ deviceId })
        });
      } catch (_error) {
        // A new local identity still prevents this phone from reusing old trust.
      }
    }
    setToken("");
    setStatus(null);
    setDeviceId(createDeviceId());
    setPairingStage("idle");
    setMessage("Pairing cleared");
    setActiveTab("connect");
  }

  async function runPrimary() {
    if (!primary.command) return;
    if (primary.command === "pause") {
      await command("pause");
      return;
    }
    if (selectedWorkflow) await command("load", { workflowIndex: selectedWorkflow.index });
    await command("play", {
      mode: playMode,
      count: Math.max(1, Number.parseInt(repeatCount, 10) || 1),
      delay: Math.max(0, Number.parseFloat(loopDelay) || 0),
      speed: Math.max(0.1, Number.parseFloat(speed) || 1),
      startDelay: Math.max(0, Number.parseFloat(startDelay) || 0)
    });
  }

  async function chooseWorkflow(item) {
    setWorkflowIndex(item.index);
    setWorkflowMenuOpen(false);
    await command("load", { workflowIndex: item.index });
  }

  useEffect(() => {
    Animated.timing(startupProgress, {
      toValue: 0.82,
      duration: 2100,
      useNativeDriver: false
    }).start();
  }, [startupProgress]);

  useEffect(() => {
    let mounted = true;
    async function loadSettings() {
      let next = migrateSettings();
      if (SETTINGS_PATH) {
        try {
          next = migrateSettings(JSON.parse(await FileSystem.readAsStringAsync(SETTINGS_PATH)));
        } catch (_error) {
          // The settings file does not exist on first launch.
        }
      }
      if (!mounted) return;
      setHostInput(next.hostInput);
      setDeviceId(next.deviceId || createDeviceId());
      setThemeMode(next.themeMode);
      setScreenQuality(next.screenQuality);
      setSettingsLoaded(true);
    }
    loadSettings();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!settingsLoaded || !SETTINGS_PATH) return;
    FileSystem.writeAsStringAsync(SETTINGS_PATH, JSON.stringify({
      hostInput,
      deviceId,
      themeMode,
      screenQuality
    })).catch(() => {});
  }, [settingsLoaded, hostInput, deviceId, themeMode, screenQuality]);

  useEffect(() => {
    if (!fontsLoaded || !settingsLoaded) return;
    Animated.timing(startupProgress, {
      toValue: 1,
      duration: 250,
      useNativeDriver: false
    }).start(() => {
      const remaining = Math.max(0, MIN_STARTUP_MS - (Date.now() - startupBeganAt.current));
      setTimeout(() => setShowStartup(false), remaining);
    });
  }, [fontsLoaded, settingsLoaded, startupProgress]);

  useEffect(() => {
    if (!settingsLoaded || autoReconnectRef.current) return;
    autoReconnectRef.current = true;
    if (shouldAutoReconnect({ hostInput, deviceId })) pair({ silent: true, auto: true });
  }, [settingsLoaded, hostInput, deviceId, baseUrl]);

  useEffect(() => {
    if (!paired) return undefined;
    let alive = true;
    async function refreshStatus() {
      try {
        const result = await apiRequest("/status", { timeoutMs: 3500 });
        if (!alive) return;
        setStatus(result.status || null);
        setMessage("Connected");
      } catch (error) {
        if (alive) setMessage(error.message || "Desktop unavailable");
      }
    }
    refreshStatus();
    const timer = setInterval(refreshStatus, 700);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [paired, apiRequest]);

  useEffect(() => {
    if (workflowIndex === null && workflows.length) setWorkflowIndex(workflows[0].index);
  }, [workflows, workflowIndex]);

  const rootReady = () => SplashScreen.hideAsync().catch(() => {});

  return (
    <GestureHandlerRootView style={styles.root} onLayout={rootReady}>
      <SafeAreaProvider>
        <StatusBar style={resolvedTheme === "dark" ? "light" : "dark"} />
        {showStartup ? (
          <StartupScreen colors={colors} progress={startupProgress} fontsLoaded={fontsLoaded} />
        ) : (
          <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
            <Header paired={paired} colors={colors} />
            <View style={styles.content}>
              {activeTab === "connect" && (
                <ConnectScreen
                  hostInput={hostInput}
                  updateHost={updateHost}
                  pairing={pairing}
                  paired={paired}
                  stage={pairingStage}
                  message={message}
                  pair={pair}
                  cancelPairing={cancelPairing}
                  colors={colors}
                />
              )}
              {activeTab === "remote" && (
                <RemoteScreen
                  paired={paired}
                  message={message}
                  currentFrame={currentFrame}
                  openFullscreen={() => setFullscreen(true)}
                  workflows={workflows}
                  selectedWorkflow={selectedWorkflow}
                  openWorkflowMenu={() => setWorkflowMenuOpen(true)}
                  playback={playback}
                  primary={primary}
                  runPrimary={runPrimary}
                  stop={() => command("stop")}
                  playMode={playMode}
                  setPlayMode={setPlayMode}
                  repeatCount={repeatCount}
                  setRepeatCount={setRepeatCount}
                  loopDelay={loopDelay}
                  setLoopDelay={setLoopDelay}
                  speed={speed}
                  setSpeed={setSpeed}
                  startDelay={startDelay}
                  setStartDelay={setStartDelay}
                  colors={colors}
                  goConnect={() => setActiveTab("connect")}
                />
              )}
              {activeTab === "settings" && (
                <SettingsScreen
                  colors={colors}
                  themeMode={themeMode}
                  setThemeMode={setThemeMode}
                  screenQuality={screenQuality}
                  setScreenQuality={setScreenQuality}
                  paired={paired}
                  hostInput={hostInput}
                  clearPairing={clearPairing}
                />
              )}
            </View>
            <TabBar active={activeTab} setActive={setActiveTab} paired={paired} colors={colors} />
          </SafeAreaView>
        )}
        {frameLoader}
        <WorkflowModal
          visible={workflowMenuOpen}
          close={() => setWorkflowMenuOpen(false)}
          workflows={workflows}
          selected={selectedWorkflow}
          choose={chooseWorkflow}
          colors={colors}
        />
        <FullscreenViewer
          visible={fullscreen}
          frame={currentFrame}
          close={() => setFullscreen(false)}
          colors={colors}
        />
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

function StartupScreen({ colors, progress, fontsLoaded }) {
  return (
    <View style={styles.startup}>
      <View style={styles.startupLogo}>
        {fontsLoaded ? <Ionicons name="flash" size={52} color={colors.accent} /> : <ActivityIndicator color={colors.accent} />}
      </View>
      <Text style={styles.startupName}>NexaFlow</Text>
      <Text style={styles.startupSub}>REMOTE COMPANION</Text>
      <View style={styles.startupTrack}>
        <Animated.View
          style={[
            styles.startupFill,
            { width: progress.interpolate({ inputRange: [0, 1], outputRange: ["0%", "100%"] }) }
          ]}
        />
      </View>
    </View>
  );
}

function Header({ paired, colors }) {
  return (
    <View style={styles.header}>
      <View style={styles.brandIcon}><Ionicons name="flash" size={25} color={colors.accent} /></View>
      <View style={styles.brandText}>
        <Text style={styles.brandName}>NexaFlow</Text>
        <Text style={styles.brandSub}>Mobile</Text>
      </View>
      <View style={[styles.connectionPill, paired && styles.connectionPillOn]}>
        <View style={[styles.statusDot, paired && styles.statusDotOn]} />
        <Text style={[styles.connectionText, paired && styles.connectionTextOn]}>{paired ? "Connected" : "Offline"}</Text>
      </View>
    </View>
  );
}

function ConnectScreen({ hostInput, updateHost, pairing, paired, stage, message, pair, cancelPairing, colors }) {
  const stageIcon = paired || stage === "connected" ? "checkmark-circle" : stage === "failed" ? "alert-circle" : "radio-button-on";
  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={styles.page} keyboardShouldPersistTaps="handled">
        <Text style={styles.pageTitle}>Connect</Text>
        <Text style={styles.shortHint}>Same Wi-Fi or hotspot</Text>
        <View style={styles.section}>
          <Text style={styles.fieldLabel}>Desktop address</Text>
          <TextInput
            value={hostInput}
            onChangeText={updateHost}
            placeholder="192.168.1.20:8765"
            placeholderTextColor={colors.faint}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            editable={!pairing}
            style={styles.input}
          />
          <Pressable
            style={({ pressed }) => [styles.primaryButton, (pressed || paired) && styles.buttonPressed, paired && styles.buttonDisabled]}
            onPress={pairing ? cancelPairing : () => pair()}
            disabled={paired}
          >
            {pairing ? <ActivityIndicator color={colors.white} /> : <Ionicons name={paired ? "checkmark" : "link"} size={20} color={colors.white} />}
            <Text style={styles.primaryButtonText}>{pairing ? "Cancel" : paired ? "Paired" : "Pair"}</Text>
          </Pressable>
        </View>
        <View style={styles.compactStatus}>
          <Ionicons name={stageIcon} size={19} color={paired ? colors.green : stage === "failed" ? colors.red : colors.accent} />
          <Text style={styles.compactStatusText}>{message}</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function RemoteScreen(props) {
  const {
    paired, message, currentFrame, openFullscreen, workflows, selectedWorkflow, openWorkflowMenu,
    playback, primary, runPrimary, stop, playMode, setPlayMode, repeatCount, setRepeatCount,
    loopDelay, setLoopDelay, speed, setSpeed, startDelay, setStartDelay, colors, goConnect
  } = props;
  const hasPlayback = playback.phase !== "idle";
  const progress = Math.max(0, Math.min(100, Number(playback.progressPercent) || 0));
  if (!paired) {
    return (
      <View style={styles.emptyState}>
        <Ionicons name="desktop-outline" size={46} color={colors.faint} />
        <Text style={styles.emptyTitle}>Desktop not connected</Text>
        <Text style={styles.emptyText}>{message}</Text>
        <Pressable style={styles.outlineButton} onPress={goConnect}>
          <Text style={styles.outlineButtonText}>Open Connect</Text>
        </Pressable>
      </View>
    );
  }
  return (
    <ScrollView contentContainerStyle={styles.remotePage}>
      <View style={styles.viewer}>
        {currentFrame ? (
          <Image source={{ uri: currentFrame }} resizeMode="contain" style={styles.viewerImage} />
        ) : (
          <View style={styles.viewerLoading}><ActivityIndicator color={colors.accent} /><Text style={styles.viewerLoadingText}>Loading desktop</Text></View>
        )}
        <Pressable style={styles.fullscreenButton} onPress={openFullscreen} accessibilityLabel="Open full screen">
          <Ionicons name="expand" size={21} color={colors.white} />
        </Pressable>
      </View>

      <View style={styles.remoteSection}>
        <Text style={styles.sectionTitle}>Workflow</Text>
        <Pressable style={styles.selectButton} onPress={openWorkflowMenu} disabled={!workflows.length}>
          <MaterialCommunityIcons name="file-play-outline" size={21} color={colors.accent} />
          <Text style={styles.selectText} numberOfLines={1}>{selectedWorkflow?.name || "No saved workflow"}</Text>
          <Ionicons name="chevron-down" size={19} color={colors.muted} />
        </Pressable>
      </View>

      <View style={styles.remoteSection}>
        <Text style={styles.sectionTitle}>Playback</Text>
        <Segmented options={PLAYBACK_MODES} value={playMode} setValue={setPlayMode} />
        {playMode !== "once" && (
          <View style={styles.twoColumns}>
            {playMode === "repeat" && (
              <LabeledNumber label="Repeats" value={repeatCount} setValue={setRepeatCount} colors={colors} />
            )}
            <LabeledNumber label="Loop delay" value={loopDelay} setValue={setLoopDelay} suffix="s" colors={colors} />
          </View>
        )}
        <Text style={styles.controlLabel}>Speed</Text>
        <ChoiceRow values={SPEEDS} value={speed} setValue={setSpeed} suffix="×" />
        <Text style={styles.controlLabel}>Start delay</Text>
        <ChoiceRow values={START_DELAYS} value={startDelay} setValue={setStartDelay} suffix="s" />
      </View>

      <View style={styles.progressSection}>
        <View style={styles.progressTop}>
          <Text style={styles.progressPhase}>
            {playback.phase === "countdown" ? `Starting in ${playback.countdownRemaining}s` : playback.phase.charAt(0).toUpperCase() + playback.phase.slice(1)}
          </Text>
          <Text style={styles.progressTime}>{formatElapsed(playback.elapsedSeconds)}</Text>
        </View>
        <View style={styles.progressTrack}><View style={[styles.progressFill, { width: `${progress}%` }]} /></View>
        <View style={styles.progressDetails}>
          <Text style={styles.progressDetail}>Event {playback.currentEvent || 0}/{playback.totalEvents || 0}</Text>
          <Text style={styles.progressDetail}>
            {playback.totalLoops ? `Loop ${playback.currentLoop || 0}/${playback.totalLoops}` : playback.currentLoop ? `Loop ${playback.currentLoop}` : ""}
          </Text>
        </View>
      </View>

      <View style={styles.commandRow}>
        <Pressable
          style={({ pressed }) => [styles.playButton, pressed && styles.buttonPressed, (!selectedWorkflow || !primary.command) && styles.buttonDisabled]}
          onPress={runPrimary}
          disabled={!selectedWorkflow || !primary.command}
        >
          <Ionicons name={primary.icon} size={23} color={colors.white} />
          <Text style={styles.primaryButtonText}>{primary.label}</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [styles.stopButton, pressed && styles.buttonPressed, !hasPlayback && styles.buttonDisabled]}
          onPress={stop}
          disabled={!hasPlayback}
        >
          <Ionicons name="stop" size={22} color={colors.white} />
          <Text style={styles.primaryButtonText}>Stop</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

function SettingsScreen({ colors, themeMode, setThemeMode, screenQuality, setScreenQuality, paired, hostInput, clearPairing }) {
  return (
    <ScrollView contentContainerStyle={styles.page}>
      <Text style={styles.pageTitle}>Settings</Text>
      <View style={styles.settingsSection}>
        <Text style={styles.sectionTitle}>Appearance</Text>
        <Segmented
          options={[{ value: "light", label: "Light" }, { value: "dark", label: "Dark" }]}
          value={themeMode}
          setValue={setThemeMode}
        />
      </View>
      <View style={styles.settingsSection}>
        <Text style={styles.sectionTitle}>Screen Quality</Text>
        <Segmented
          options={[{ value: "sharp", label: "Sharp" }, { value: "balanced", label: "Balanced" }, { value: "battery", label: "Battery" }]}
          value={screenQuality}
          setValue={setScreenQuality}
        />
      </View>
      <View style={styles.settingsSection}>
        <Text style={styles.sectionTitle}>Pairing</Text>
        <View style={styles.summaryRow}>
          <Ionicons name={paired ? "checkmark-circle" : "desktop-outline"} size={22} color={paired ? colors.green : colors.faint} />
          <View style={styles.summaryText}>
            <Text style={styles.summaryTitle}>{paired ? "Paired desktop" : "No paired desktop"}</Text>
            <Text style={styles.summarySub} numberOfLines={1}>{hostInput || "Not set"}</Text>
          </View>
        </View>
        <Pressable style={styles.outlineButton} onPress={clearPairing}>
          <Ionicons name="unlink-outline" size={19} color={colors.red} />
          <Text style={[styles.outlineButtonText, { color: colors.red }]}>Clear Pairing</Text>
        </Pressable>
      </View>
      <View style={styles.linkSection}>
        <Pressable style={styles.linkButton} onPress={() => openUrl(SUPPORT_URL)}>
          <Ionicons name="help-circle-outline" size={21} color={colors.accent} /><Text style={styles.linkText}>Support</Text>
        </Pressable>
        <Pressable style={styles.linkButton} onPress={() => openUrl(PRIVACY_URL)}>
          <Ionicons name="shield-checkmark-outline" size={21} color={colors.accent} /><Text style={styles.linkText}>Privacy</Text>
        </Pressable>
        <View style={styles.versionRow}><Text style={styles.versionText}>NexaFlow 1.0.0</Text></View>
      </View>
    </ScrollView>
  );
}

function Segmented({ options, value, setValue }) {
  return (
    <View style={styles.segmented}>
      {options.map((item) => (
        <Pressable key={item.value} style={[styles.segment, value === item.value && styles.segmentActive]} onPress={() => setValue(item.value)}>
          <Text style={[styles.segmentText, value === item.value && styles.segmentTextActive]}>{item.label}</Text>
        </Pressable>
      ))}
    </View>
  );
}

function ChoiceRow({ values, value, setValue, suffix }) {
  return (
    <View style={styles.choiceRow}>
      {values.map((item) => (
        <Pressable key={item} style={[styles.choice, value === item && styles.choiceActive]} onPress={() => setValue(item)}>
          <Text style={[styles.choiceText, value === item && styles.choiceTextActive]}>{item}{suffix}</Text>
        </Pressable>
      ))}
    </View>
  );
}

function LabeledNumber({ label, value, setValue, suffix = "", colors }) {
  return (
    <View style={styles.numberField}>
      <Text style={styles.controlLabel}>{label}</Text>
      <View style={styles.numberInputWrap}>
        <TextInput value={value} onChangeText={setValue} keyboardType="decimal-pad" style={styles.numberInput} placeholderTextColor={colors.faint} />
        {suffix ? <Text style={styles.numberSuffix}>{suffix}</Text> : null}
      </View>
    </View>
  );
}

function TabBar({ active, setActive, paired, colors }) {
  return (
    <View style={styles.tabBar}>
      {TABS.map((tab) => {
        const selected = active === tab.id;
        return (
          <Pressable key={tab.id} style={styles.tab} onPress={() => setActive(tab.id)}>
            <View style={[styles.tabIcon, selected && styles.tabIconActive]}>
              <Ionicons name={tab.icon} size={22} color={selected ? colors.accent : colors.faint} />
              {tab.id === "remote" && paired ? <View style={styles.tabOnlineDot} /> : null}
            </View>
            <Text style={[styles.tabText, selected && styles.tabTextActive]}>{tab.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

function WorkflowModal({ visible, close, workflows, selected, choose, colors }) {
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={close}>
      <Pressable style={styles.modalBackdrop} onPress={close}>
        <Pressable style={styles.modalPanel} onPress={() => {}}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Choose Workflow</Text>
            <Pressable style={styles.iconButton} onPress={close}><Ionicons name="close" size={23} color={colors.ink} /></Pressable>
          </View>
          <ScrollView style={styles.workflowList}>
            {workflows.map((item) => (
              <Pressable key={item.index} style={styles.workflowRow} onPress={() => choose(item)}>
                <MaterialCommunityIcons name="file-play-outline" size={22} color={colors.accent} />
                <Text style={styles.workflowName} numberOfLines={1}>{item.name}</Text>
                {selected?.index === item.index ? <Ionicons name="checkmark" size={21} color={colors.green} /> : null}
              </Pressable>
            ))}
          </ScrollView>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

function FullscreenViewer({ visible, frame, close, colors }) {
  const baseScale = useRef(new Animated.Value(1)).current;
  const pinchScale = useRef(new Animated.Value(1)).current;
  const panX = useRef(new Animated.Value(0)).current;
  const panY = useRef(new Animated.Value(0)).current;
  const lastScale = useRef(1);
  const lastPan = useRef({ x: 0, y: 0 });

  const reset = useCallback(() => {
    lastScale.current = 1;
    lastPan.current = { x: 0, y: 0 };
    baseScale.setValue(1);
    pinchScale.setValue(1);
    panX.setValue(0);
    panY.setValue(0);
  }, [baseScale, pinchScale, panX, panY]);

  useEffect(() => {
    if (!visible) return undefined;
    reset();
    ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.LANDSCAPE).catch(() => {});
    return () => {
      ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.PORTRAIT_UP).catch(() => {});
    };
  }, [visible, reset]);

  const pinchEvent = Animated.event([{ nativeEvent: { scale: pinchScale } }], { useNativeDriver: true });
  const panEvent = Animated.event([{ nativeEvent: { translationX: panX, translationY: panY } }], { useNativeDriver: true });
  const scale = Animated.multiply(baseScale, pinchScale);

  function pinchState(event) {
    if (event.nativeEvent.oldState === State.ACTIVE) {
      const next = Math.max(1, Math.min(5, lastScale.current * event.nativeEvent.scale));
      lastScale.current = next;
      baseScale.setValue(next);
      pinchScale.setValue(1);
      if (next === 1) {
        lastPan.current = { x: 0, y: 0 };
        panX.setValue(0);
        panY.setValue(0);
      }
    }
  }

  function panState(event) {
    if (event.nativeEvent.state === State.BEGAN) {
      panX.setOffset(lastPan.current.x);
      panY.setOffset(lastPan.current.y);
      panX.setValue(0);
      panY.setValue(0);
    }
    if (event.nativeEvent.oldState === State.ACTIVE) {
      lastPan.current = {
        x: lastPan.current.x + event.nativeEvent.translationX,
        y: lastPan.current.y + event.nativeEvent.translationY
      };
      panX.flattenOffset();
      panY.flattenOffset();
    }
  }

  function doubleTap(event) {
    if (event.nativeEvent.state === State.ACTIVE) reset();
  }

  return (
    <Modal visible={visible} animationType="fade" onRequestClose={close} supportedOrientations={["landscape", "portrait"]}>
      <View style={styles.fullscreenRoot}>
        <TapGestureHandler numberOfTaps={2} onHandlerStateChange={doubleTap}>
          <Animated.View style={styles.fullscreenGestureArea}>
            <PanGestureHandler onGestureEvent={panEvent} onHandlerStateChange={panState} minPointers={1} maxPointers={2}>
              <Animated.View style={styles.fullscreenGestureArea}>
                <PinchGestureHandler onGestureEvent={pinchEvent} onHandlerStateChange={pinchState}>
                  <Animated.View style={[styles.fullscreenImageWrap, { transform: [{ translateX: panX }, { translateY: panY }, { scale }] }]}>
                    {frame ? <Image source={{ uri: frame }} resizeMode="contain" style={styles.fullscreenImage} /> : <ActivityIndicator color={colors.accent} />}
                  </Animated.View>
                </PinchGestureHandler>
              </Animated.View>
            </PanGestureHandler>
          </Animated.View>
        </TapGestureHandler>
        <View style={styles.fullscreenTools}>
          <Pressable style={styles.fullscreenTool} onPress={reset} accessibilityLabel="Reset zoom">
            <MaterialCommunityIcons name="fit-to-screen-outline" size={24} color={colors.white} />
          </Pressable>
          <Pressable style={styles.fullscreenTool} onPress={close} accessibilityLabel="Close full screen">
            <Ionicons name="close" size={27} color={colors.white} />
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

let styles = StyleSheet.create({});

function createStyles(c) {
  return StyleSheet.create({
    root: { flex: 1, backgroundColor: c.bg },
    flex: { flex: 1 },
    safe: { flex: 1, backgroundColor: c.bg },
    content: { flex: 1 },
    hiddenFrame: { position: "absolute", width: 2, height: 2, opacity: 0, left: -10, top: -10 },
    startup: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: c.bg, padding: 32 },
    startupLogo: { width: 82, height: 82, borderRadius: 8, alignItems: "center", justifyContent: "center", backgroundColor: c.panel, borderWidth: 1, borderColor: c.line },
    startupName: { marginTop: 24, color: c.ink, fontSize: 35, fontWeight: "700", letterSpacing: 0 },
    startupSub: { marginTop: 6, color: c.muted, fontSize: 13, fontWeight: "600", letterSpacing: 0 },
    startupTrack: { width: 220, height: 4, marginTop: 32, overflow: "hidden", backgroundColor: c.line, borderRadius: 2 },
    startupFill: { height: 4, backgroundColor: c.accent, borderRadius: 2 },
    header: { height: 78, flexDirection: "row", alignItems: "center", paddingHorizontal: 18, backgroundColor: c.panel, borderBottomWidth: 1, borderBottomColor: c.line },
    brandIcon: { width: 42, height: 42, borderRadius: 8, alignItems: "center", justifyContent: "center", backgroundColor: c.soft },
    brandText: { marginLeft: 11, flex: 1 },
    brandName: { color: c.ink, fontSize: 21, fontWeight: "700", letterSpacing: 0 },
    brandSub: { color: c.muted, fontSize: 12, marginTop: 1 },
    connectionPill: { height: 34, flexDirection: "row", alignItems: "center", paddingHorizontal: 11, borderWidth: 1, borderColor: c.line, borderRadius: 17 },
    connectionPillOn: { borderColor: c.green },
    statusDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: c.faint, marginRight: 7 },
    statusDotOn: { backgroundColor: c.green },
    connectionText: { color: c.muted, fontSize: 12, fontWeight: "600" },
    connectionTextOn: { color: c.green },
    page: { padding: 20, paddingBottom: 34 },
    remotePage: { padding: 14, paddingBottom: 30 },
    pageTitle: { color: c.ink, fontSize: 28, fontWeight: "700", letterSpacing: 0 },
    shortHint: { color: c.muted, fontSize: 14, marginTop: 5, marginBottom: 22 },
    section: { paddingVertical: 18, borderTopWidth: 1, borderBottomWidth: 1, borderColor: c.line },
    fieldLabel: { color: c.muted, fontSize: 12, fontWeight: "600", marginBottom: 7 },
    input: { height: 54, paddingHorizontal: 15, color: c.ink, backgroundColor: c.panel, borderWidth: 1, borderColor: c.line, borderRadius: 7, fontSize: 17 },
    primaryButton: { height: 52, marginTop: 14, flexDirection: "row", gap: 9, alignItems: "center", justifyContent: "center", backgroundColor: c.accent, borderRadius: 7 },
    primaryButtonText: { color: c.white, fontSize: 16, fontWeight: "700" },
    buttonPressed: { opacity: 0.78 },
    buttonDisabled: { opacity: 0.46 },
    compactStatus: { flexDirection: "row", alignItems: "flex-start", gap: 9, paddingVertical: 16 },
    compactStatusText: { flex: 1, color: c.muted, fontSize: 13, lineHeight: 19 },
    viewer: { aspectRatio: 16 / 9, overflow: "hidden", backgroundColor: c.viewer, borderRadius: 7, borderWidth: 1, borderColor: c.line },
    viewerImage: { width: "100%", height: "100%" },
    viewerLoading: { flex: 1, alignItems: "center", justifyContent: "center", gap: 8 },
    viewerLoadingText: { color: c.faint, fontSize: 12 },
    fullscreenButton: { position: "absolute", right: 8, top: 8, width: 38, height: 38, borderRadius: 6, alignItems: "center", justifyContent: "center", backgroundColor: "rgba(0,0,0,0.62)" },
    remoteSection: { paddingVertical: 16, borderBottomWidth: 1, borderBottomColor: c.line },
    sectionTitle: { color: c.ink, fontSize: 17, fontWeight: "700", marginBottom: 11 },
    selectButton: { height: 48, flexDirection: "row", alignItems: "center", gap: 10, paddingHorizontal: 13, borderWidth: 1, borderColor: c.line, backgroundColor: c.panel, borderRadius: 7 },
    selectText: { flex: 1, color: c.ink, fontSize: 14, fontWeight: "600" },
    segmented: { height: 44, flexDirection: "row", padding: 3, backgroundColor: c.soft, borderRadius: 7 },
    segment: { flex: 1, alignItems: "center", justifyContent: "center", borderRadius: 5 },
    segmentActive: { backgroundColor: c.panel, borderWidth: 1, borderColor: c.line },
    segmentText: { color: c.muted, fontSize: 13, fontWeight: "600" },
    segmentTextActive: { color: c.accentDark },
    twoColumns: { flexDirection: "row", gap: 12, marginTop: 13 },
    numberField: { flex: 1 },
    controlLabel: { color: c.muted, fontSize: 12, fontWeight: "600", marginTop: 13, marginBottom: 7 },
    numberInputWrap: { height: 44, flexDirection: "row", alignItems: "center", borderWidth: 1, borderColor: c.line, borderRadius: 7, backgroundColor: c.panel },
    numberInput: { flex: 1, height: 42, paddingHorizontal: 12, color: c.ink, fontSize: 14 },
    numberSuffix: { color: c.muted, paddingRight: 12 },
    choiceRow: { flexDirection: "row", gap: 7 },
    choice: { flex: 1, height: 39, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: c.line, backgroundColor: c.panel, borderRadius: 6 },
    choiceActive: { backgroundColor: c.soft, borderColor: c.accent },
    choiceText: { color: c.muted, fontSize: 12, fontWeight: "600" },
    choiceTextActive: { color: c.accentDark },
    progressSection: { paddingVertical: 15 },
    progressTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
    progressPhase: { color: c.ink, fontSize: 14, fontWeight: "700" },
    progressTime: { color: c.muted, fontSize: 14, fontVariant: ["tabular-nums"] },
    progressTrack: { height: 6, backgroundColor: c.line, overflow: "hidden", borderRadius: 3, marginTop: 10 },
    progressFill: { height: 6, backgroundColor: c.green, borderRadius: 3 },
    progressDetails: { flexDirection: "row", justifyContent: "space-between", marginTop: 7 },
    progressDetail: { minHeight: 16, color: c.faint, fontSize: 11 },
    commandRow: { flexDirection: "row", gap: 10, paddingTop: 2 },
    playButton: { flex: 1.35, height: 54, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 9, borderRadius: 7, backgroundColor: c.green },
    stopButton: { flex: 1, height: 54, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 9, borderRadius: 7, backgroundColor: c.red },
    emptyState: { flex: 1, alignItems: "center", justifyContent: "center", padding: 28 },
    emptyTitle: { color: c.ink, fontSize: 19, fontWeight: "700", marginTop: 14 },
    emptyText: { color: c.muted, fontSize: 13, lineHeight: 19, textAlign: "center", marginTop: 7, marginBottom: 18 },
    outlineButton: { minHeight: 45, flexDirection: "row", gap: 8, alignItems: "center", justifyContent: "center", paddingHorizontal: 16, borderWidth: 1, borderColor: c.line, borderRadius: 7, backgroundColor: c.panel },
    outlineButtonText: { color: c.accentDark, fontSize: 14, fontWeight: "700" },
    settingsSection: { paddingVertical: 18, borderBottomWidth: 1, borderBottomColor: c.line },
    summaryRow: { flexDirection: "row", alignItems: "center", marginBottom: 13 },
    summaryText: { flex: 1, marginLeft: 10 },
    summaryTitle: { color: c.ink, fontSize: 14, fontWeight: "700" },
    summarySub: { color: c.muted, fontSize: 12, marginTop: 2 },
    linkSection: { paddingTop: 16 },
    linkButton: { height: 46, flexDirection: "row", alignItems: "center", gap: 10, borderBottomWidth: 1, borderBottomColor: c.line },
    linkText: { color: c.ink, fontSize: 14, fontWeight: "600" },
    versionRow: { paddingVertical: 16 },
    versionText: { color: c.faint, fontSize: 12 },
    tabBar: { height: 68, flexDirection: "row", backgroundColor: c.panel, borderTopWidth: 1, borderTopColor: c.line, paddingHorizontal: 12 },
    tab: { flex: 1, alignItems: "center", justifyContent: "center" },
    tabIcon: { width: 38, height: 28, alignItems: "center", justifyContent: "center", borderRadius: 6 },
    tabIconActive: { backgroundColor: c.soft },
    tabOnlineDot: { position: "absolute", right: 4, top: 2, width: 6, height: 6, borderRadius: 3, backgroundColor: c.green },
    tabText: { color: c.faint, fontSize: 11, fontWeight: "600", marginTop: 2 },
    tabTextActive: { color: c.accentDark },
    modalBackdrop: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, backgroundColor: "rgba(0,0,0,0.52)" },
    modalPanel: { width: "100%", maxHeight: "70%", backgroundColor: c.panel, borderRadius: 8, overflow: "hidden" },
    modalHeader: { height: 58, flexDirection: "row", alignItems: "center", paddingLeft: 17, paddingRight: 8, borderBottomWidth: 1, borderBottomColor: c.line },
    modalTitle: { flex: 1, color: c.ink, fontSize: 18, fontWeight: "700" },
    iconButton: { width: 42, height: 42, alignItems: "center", justifyContent: "center" },
    workflowList: { paddingHorizontal: 10, paddingBottom: 10 },
    workflowRow: { minHeight: 52, flexDirection: "row", alignItems: "center", gap: 10, paddingHorizontal: 8, borderBottomWidth: 1, borderBottomColor: c.line },
    workflowName: { flex: 1, color: c.ink, fontSize: 14 },
    fullscreenRoot: { flex: 1, backgroundColor: "#000000" },
    fullscreenGestureArea: { flex: 1 },
    fullscreenImageWrap: { flex: 1, alignItems: "center", justifyContent: "center" },
    fullscreenImage: { width: "100%", height: "100%" },
    fullscreenTools: { position: "absolute", right: 16, top: 16, flexDirection: "row", gap: 9 },
    fullscreenTool: { width: 46, height: 46, alignItems: "center", justifyContent: "center", borderRadius: 7, backgroundColor: "rgba(0,0,0,0.66)" }
  });
}
