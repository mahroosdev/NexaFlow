const DEFAULT_SETTINGS = {
  desktopHost: "127.0.0.1",
  desktopPort: "8765",
  authToken: "",
  deviceId: "",
  pairedAt: 0,
  workflows: [],
  activeWorkflowId: "",
  recording: false
};

const SENSITIVE_TYPES = new Set(["password", "email", "tel", "number"]);

async function readState() {
  return chrome.storage.local.get(DEFAULT_SETTINGS);
}

async function writeState(patch) {
  await chrome.storage.local.set(patch);
  return readState();
}

function baseUrl(state) {
  const host = String(state.desktopHost || DEFAULT_SETTINGS.desktopHost).trim();
  const port = String(state.desktopPort || DEFAULT_SETTINGS.desktopPort).trim();
  return `http://${host}:${port}`;
}

async function callDesktop(path, options = {}) {
  const state = await readState();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  if (state.authToken) {
    headers.Authorization = `Bearer ${state.authToken}`;
  }

  const response = await fetch(`${baseUrl(state)}${path}`, {
    ...options,
    headers
  });

  let body = {};
  try {
    body = await response.json();
  } catch {
    body = {};
  }

  if (!response.ok) {
    const message = body.error || body.message || `Desktop returned ${response.status}`;
    throw new Error(message);
  }

  return body;
}

async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    throw new Error("No active Chrome tab is available.");
  }
  return tab;
}

async function ensureContentScript(tabId) {
  try {
    await chrome.tabs.sendMessage(tabId, { type: "nexaflow:ping" });
  } catch {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["src/recordingSafety.js", "src/contentScript.js"]
    });
  }
}

function normalizeEvent(event) {
  const clean = {
    kind: event.kind,
    selector: event.selector,
    label: event.label || "",
    url: event.url || "",
    title: event.title || "",
    ts: Date.now()
  };

  if (event.kind === "input") {
    clean.value = event.sensitive ? "" : String(event.value || "").slice(0, 500);
    clean.sensitive = Boolean(event.sensitive);
  }

  if (event.kind === "key") {
    clean.key = event.key;
  }

  return clean;
}

async function appendRecordedEvent(event) {
  const state = await readState();
  if (!state.recording || !state.activeWorkflowId) {
    return;
  }

  const workflows = Array.isArray(state.workflows) ? state.workflows : [];
  const index = workflows.findIndex((item) => item.id === state.activeWorkflowId);
  if (index < 0) {
    return;
  }

  const next = workflows.slice();
  const workflow = { ...next[index] };
  workflow.events = [...(workflow.events || []), normalizeEvent(event)];
  workflow.updatedAt = Date.now();
  next[index] = workflow;
  await writeState({ workflows: next });
}

async function startRecording() {
  const tab = await activeTab();
  await ensureContentScript(tab.id);
  const id = `browser_${new Date().toISOString().replace(/[:.]/g, "-")}`;
  const workflow = {
    id,
    name: "Browser workflow",
    createdAt: Date.now(),
    updatedAt: Date.now(),
    startUrl: tab.url || "",
    events: [
      {
        kind: "navigate",
        url: tab.url || "",
        title: tab.title || "",
        ts: Date.now()
      }
    ]
  };

  const state = await readState();
  await writeState({
    recording: true,
    activeWorkflowId: id,
    workflows: [workflow, ...(state.workflows || [])].slice(0, 20)
  });

  await chrome.tabs.sendMessage(tab.id, { type: "nexaflow:start-recording" });
  return readState();
}

async function stopRecording() {
  const tab = await activeTab().catch(() => null);
  if (tab?.id) {
    await ensureContentScript(tab.id).catch(() => undefined);
    await chrome.tabs.sendMessage(tab.id, { type: "nexaflow:stop-recording" }).catch(() => undefined);
  }
  return writeState({ recording: false });
}

async function playWorkflow(workflowId) {
  const state = await readState();
  const workflow = (state.workflows || []).find((item) => item.id === workflowId) || state.workflows?.[0];
  if (!workflow) {
    throw new Error("No browser workflow has been recorded yet.");
  }

  const tab = await activeTab();
  await ensureContentScript(tab.id);
  await chrome.tabs.sendMessage(tab.id, {
    type: "nexaflow:play-workflow",
    workflow
  });
  return workflow;
}

// Approve-based pairing: ask the desktop to connect, then wait for the user to
// approve the request in NexaFlow Desktop (or auto-approve if this browser is trusted).
async function pairDesktop() {
  const state = await readState();
  let deviceId = state.deviceId;
  if (!deviceId) {
    deviceId = `chrome_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
    await writeState({ deviceId });
  }

  const res = await callDesktop("/pair/request", {
    method: "POST",
    body: JSON.stringify({ deviceName: "Chrome Companion", deviceId })
  });

  // Trusted browser: approved instantly, no desktop prompt.
  if (res.status === "approved" && res.token) {
    await writeState({ authToken: res.token, pairedAt: Date.now() });
    return readState();
  }

  const requestId = res.requestId;
  if (!requestId) {
    throw new Error("NexaFlow Desktop did not accept the request.");
  }

  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, 1500));
    let poll;
    try {
      poll = await callDesktop(`/pair/poll?requestId=${encodeURIComponent(requestId)}`, { method: "GET" });
    } catch (e) {
      continue; // transient hiccup — keep polling
    }
    if (poll.status === "approved" && poll.token) {
      await writeState({ authToken: poll.token, pairedAt: Date.now() });
      return readState();
    }
    if (poll.status === "denied") {
      throw new Error("NexaFlow Desktop denied the pairing request.");
    }
    if (poll.status === "expired" || poll.status === "unknown") {
      throw new Error("The pairing request expired. Try again.");
    }
  }
  throw new Error("No approval within a minute. Try again from NexaFlow Desktop.");
}

async function desktopCommand(command) {
  return callDesktop("/command", {
    method: "POST",
    body: JSON.stringify({ command })
  });
}

async function getDesktopStatus() {
  return callDesktop("/status", { method: "GET" });
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    switch (message?.type) {
      case "nexaflow:get-state":
        return { state: await readState() };
      case "nexaflow:save-settings":
        return { state: await writeState(message.patch || {}) };
      case "nexaflow:pair":
        return { state: await pairDesktop() };
      case "nexaflow:disconnect":
        return { state: await writeState({ authToken: "", pairedAt: 0 }) };
      case "nexaflow:desktop-status":
        return { status: await getDesktopStatus() };
      case "nexaflow:desktop-command":
        return { result: await desktopCommand(message.command) };
      case "nexaflow:start-recording":
        return { state: await startRecording() };
      case "nexaflow:stop-recording":
        return { state: await stopRecording() };
      case "nexaflow:play-workflow":
        return { workflow: await playWorkflow(message.workflowId) };
      case "nexaflow:record-event":
        if (message.event?.kind === "input" && SENSITIVE_TYPES.has(String(message.event.inputType || "").toLowerCase())) {
          message.event.sensitive = true;
        }
        await appendRecordedEvent(message.event || {});
        return { ok: true };
      case "nexaflow:clear-workflows":
        return { state: await writeState({ workflows: [], activeWorkflowId: "", recording: false }) };
      case "nexaflow:import-workflows":
        return { state: await writeState({ workflows: Array.isArray(message.workflows) ? message.workflows.slice(0, 20) : [] }) };
      default:
        return { ok: false };
    }
  })()
    .then((payload) => sendResponse({ ok: true, ...payload }))
    .catch((error) => sendResponse({ ok: false, error: error.message || "Unknown error" }));

  return true;
});
