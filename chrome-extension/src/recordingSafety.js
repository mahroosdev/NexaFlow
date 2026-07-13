(function exposeRecordingSafety(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.NexaFlowRecordingSafety = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function createRecordingSafety() {
  function attribute(element, name) {
    return String(element?.getAttribute?.(name) || "").trim();
  }

  function isSensitive(element) {
    return attribute(element, "type").toLowerCase() === "password";
  }

  function labelFor(element) {
    if (!element) return "";
    if (isSensitive(element)) return "Password field";

    const tag = String(element.tagName || "").toLowerCase();
    const editable = ["input", "textarea", "select"].includes(tag)
      || attribute(element, "contenteditable").toLowerCase() === "true";
    const accessible = attribute(element, "aria-label")
      || attribute(element, "title")
      || attribute(element, "placeholder")
      || attribute(element, "name");
    const text = editable ? accessible : (element.innerText || accessible || "");
    return String(text).trim().replace(/\s+/g, " ").slice(0, 80);
  }

  return { isSensitive, labelFor };
});
