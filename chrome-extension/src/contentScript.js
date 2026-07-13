let recording = false;
let replaying = false;
const { isSensitive, labelFor } = globalThis.NexaFlowRecordingSafety;

function cssEscape(value) {
  if (window.CSS?.escape) {
    return window.CSS.escape(value);
  }
  return String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
}

function selectorFor(element) {
  if (!element || element === document.body) {
    return "body";
  }

  const id = element.getAttribute("id");
  if (id) {
    return `#${cssEscape(id)}`;
  }

  const testId = element.getAttribute("data-testid") || element.getAttribute("data-test");
  if (testId) {
    return `[data-testid="${cssEscape(testId)}"]`;
  }

  const aria = element.getAttribute("aria-label");
  if (aria) {
    return `${element.tagName.toLowerCase()}[aria-label="${cssEscape(aria)}"]`;
  }

  const name = element.getAttribute("name");
  if (name) {
    return `${element.tagName.toLowerCase()}[name="${cssEscape(name)}"]`;
  }

  const parts = [];
  let node = element;
  while (node && node.nodeType === Node.ELEMENT_NODE && parts.length < 5) {
    const tag = node.tagName.toLowerCase();
    const parent = node.parentElement;
    if (!parent) {
      parts.unshift(tag);
      break;
    }
    const sameTag = [...parent.children].filter((child) => child.tagName === node.tagName);
    const index = sameTag.indexOf(node) + 1;
    parts.unshift(sameTag.length > 1 ? `${tag}:nth-of-type(${index})` : tag);
    node = parent;
  }
  return parts.join(" > ");
}

function postEvent(event) {
  if (!recording || replaying) {
    return;
  }

  chrome.runtime.sendMessage({
    type: "nexaflow:record-event",
    event: {
      ...event,
      url: location.href,
      title: document.title
    }
  });
}

function onClick(event) {
  const target = event.target?.closest?.("button,a,input,textarea,select,[role='button'],[contenteditable='true']") || event.target;
  postEvent({
    kind: "click",
    selector: selectorFor(target),
    label: labelFor(target)
  });
}

function onInput(event) {
  const target = event.target;
  if (!target || isSensitive(target)) {
    postEvent({
      kind: "input",
      selector: selectorFor(target),
      label: labelFor(target),
      value: "",
      inputType: target?.getAttribute?.("type") || "",
      sensitive: true
    });
    return;
  }

  postEvent({
    kind: "input",
    selector: selectorFor(target),
    label: labelFor(target),
    value: target.value ?? target.innerText ?? "",
    inputType: target?.getAttribute?.("type") || ""
  });
}

function onKeydown(event) {
  if (!["Enter", "Tab", "Escape", "Backspace"].includes(event.key)) {
    return;
  }
  postEvent({
    kind: "key",
    selector: selectorFor(event.target),
    label: labelFor(event.target),
    key: event.key
  });
}

function setRecording(next) {
  recording = next;
  if (recording) {
    document.addEventListener("click", onClick, true);
    document.addEventListener("change", onInput, true);
    document.addEventListener("keydown", onKeydown, true);
  } else {
    document.removeEventListener("click", onClick, true);
    document.removeEventListener("change", onInput, true);
    document.removeEventListener("keydown", onKeydown, true);
  }
}

async function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function playEvent(event) {
  if (event.kind === "navigate" && event.url && location.href !== event.url) {
    location.href = event.url;
    return;
  }

  const element = event.selector ? document.querySelector(event.selector) : null;
  if (!element) {
    return;
  }

  element.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" });
  await wait(250);

  if (event.kind === "click") {
    element.click();
  }

  if (event.kind === "input") {
    element.focus();
    element.value = event.value || "";
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }

  if (event.kind === "key") {
    element.focus();
    element.dispatchEvent(new KeyboardEvent("keydown", { key: event.key, bubbles: true }));
  }
}

async function playWorkflow(workflow) {
  replaying = true;
  try {
    for (const event of workflow.events || []) {
      await playEvent(event);
      await wait(450);
    }
  } finally {
    replaying = false;
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  (async () => {
    if (message?.type === "nexaflow:ping") {
      return { ok: true };
    }
    if (message?.type === "nexaflow:start-recording") {
      setRecording(true);
      return { ok: true };
    }
    if (message?.type === "nexaflow:stop-recording") {
      setRecording(false);
      return { ok: true };
    }
    if (message?.type === "nexaflow:play-workflow") {
      await playWorkflow(message.workflow || {});
      return { ok: true };
    }
    return { ok: false };
  })()
    .then((payload) => sendResponse(payload))
    .catch((error) => sendResponse({ ok: false, error: error.message || "Unknown error" }));

  return true;
});
