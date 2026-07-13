const els = {
  host: document.getElementById("desktopHost"),
  port: document.getElementById("desktopPort"),
  status: document.getElementById("statusPill"),
  message: document.getElementById("message"),
  workflowName: document.getElementById("workflowName"),
  workflowCount: document.getElementById("workflowCount"),
  pair: document.getElementById("pairBtn"),
  disconnect: document.getElementById("disconnectBtn"),
  refresh: document.getElementById("refreshBtn"),
  record: document.getElementById("recordBtn"),
  stop: document.getElementById("stopBtn"),
  playWorkflow: document.getElementById("playWorkflowBtn"),
  exportBtn: document.getElementById("exportBtn"),
  importBtn: document.getElementById("importBtn"),
  importFile: document.getElementById("importFile"),
  clear: document.getElementById("clearBtn")
};

function send(type, payload = {}) {
  return chrome.runtime.sendMessage({ type, ...payload });
}

function setMessage(text, danger = false) {
  els.message.textContent = text || "";
  els.message.style.color = danger ? "#b42318" : "#0b8096";
}

function renderState(state) {
  els.host.value = state.desktopHost || "127.0.0.1";
  els.port.value = state.desktopPort || "8765";

  const connected = Boolean(state.authToken);
  els.status.textContent = connected ? "Paired" : "Offline";
  els.status.classList.toggle("online", connected);
  els.disconnect.disabled = !connected;

  const workflows = Array.isArray(state.workflows) ? state.workflows : [];
  const workflow = workflows[0];
  els.workflowName.textContent = workflow ? workflow.name : "No workflow yet";
  els.workflowCount.textContent = workflow ? `${workflow.events?.length || 0} events` : "0 events";
  els.record.textContent = state.recording ? "Recording..." : "Start Recording";
  els.record.disabled = Boolean(state.recording);
  els.stop.disabled = !state.recording;
  els.playWorkflow.disabled = !workflow;
  els.exportBtn.disabled = workflows.length === 0;
  els.clear.disabled = workflows.length === 0;
}

async function refreshState() {
  const response = await send("nexaflow:get-state");
  if (!response.ok) {
    throw new Error(response.error);
  }
  renderState(response.state);
  return response.state;
}

async function saveSettings() {
  const response = await send("nexaflow:save-settings", {
    patch: {
      desktopHost: els.host.value.trim() || "127.0.0.1",
      desktopPort: els.port.value.trim() || "8765"
    }
  });
  if (!response.ok) {
    throw new Error(response.error);
  }
  renderState(response.state);
}

async function run(action, success) {
  try {
    setMessage("");
    await action();
    await refreshState();
    if (success) {
      setMessage(success);
    }
  } catch (error) {
    setMessage(error.message || "Something went wrong.", true);
  }
}

els.pair.addEventListener("click", () => run(async () => {
  await saveSettings();
  setMessage("Waiting for approval in NexaFlow Desktop…");
  els.pair.disabled = true;
  try {
    const response = await send("nexaflow:pair");
    if (!response.ok) {
      throw new Error(response.error);
    }
    renderState(response.state);
  } finally {
    els.pair.disabled = false;
  }
}, "Desktop paired."));

els.disconnect.addEventListener("click", () => run(async () => {
  const response = await send("nexaflow:disconnect");
  if (!response.ok) {
    throw new Error(response.error);
  }
  renderState(response.state);
}, "Disconnected."));

els.refresh.addEventListener("click", () => run(async () => {
  await saveSettings();
  const response = await send("nexaflow:desktop-status");
  if (!response.ok) {
    throw new Error(response.error);
  }
  els.status.textContent = response.status?.remoteAccessOn === false ? "Remote Off" : "Online";
  els.status.classList.add("online");
}, "Desktop is reachable."));

els.record.addEventListener("click", () => run(async () => {
  const response = await send("nexaflow:start-recording");
  if (!response.ok) {
    throw new Error(response.error);
  }
  renderState(response.state);
}, "Browser recording started."));

els.stop.addEventListener("click", () => run(async () => {
  const response = await send("nexaflow:stop-recording");
  if (!response.ok) {
    throw new Error(response.error);
  }
  renderState(response.state);
}, "Browser recording stopped."));

els.playWorkflow.addEventListener("click", () => run(async () => {
  const response = await send("nexaflow:play-workflow");
  if (!response.ok) {
    throw new Error(response.error);
  }
}, "Playing browser workflow."));

document.querySelectorAll("[data-command]").forEach((button) => {
  button.addEventListener("click", () => run(async () => {
    const response = await send("nexaflow:desktop-command", { command: button.dataset.command });
    if (!response.ok) {
      throw new Error(response.error);
    }
  }, `${button.textContent} sent to desktop.`));
});

els.exportBtn.addEventListener("click", () => run(async () => {
  const state = await refreshState();
  const blob = new Blob([JSON.stringify(state.workflows || [], null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "nexaflow-browser-workflows.json";
  link.click();
  URL.revokeObjectURL(url);
}, "Browser workflows exported."));

els.importBtn.addEventListener("click", () => els.importFile.click());

els.importFile.addEventListener("change", () => run(async () => {
  const file = els.importFile.files?.[0];
  if (!file) {
    return;
  }
  const workflows = JSON.parse(await file.text());
  const response = await send("nexaflow:import-workflows", { workflows });
  if (!response.ok) {
    throw new Error(response.error);
  }
  renderState(response.state);
}, "Browser workflows imported."));

els.clear.addEventListener("click", () => run(async () => {
  const response = await send("nexaflow:clear-workflows");
  if (!response.ok) {
    throw new Error(response.error);
  }
  renderState(response.state);
}, "Browser workflows cleared."));

[els.host, els.port].forEach((input) => {
  input.addEventListener("change", () => run(saveSettings, "Connection settings saved."));
});

refreshState().catch((error) => setMessage(error.message, true));
