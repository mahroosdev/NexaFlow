const assert = require("node:assert/strict");
const { isSensitive, labelFor } = require("../src/recordingSafety.js");

function element(tagName, attributes = {}, values = {}) {
  return {
    tagName,
    innerText: values.innerText || "",
    value: values.value || "",
    getAttribute(name) {
      return attributes[name] || "";
    }
  };
}

const password = element("INPUT", { type: "password", "aria-label": "Account password" }, {
  value: "must-never-be-recorded"
});
assert.equal(isSensitive(password), true);
assert.equal(labelFor(password), "Password field");
assert.equal(labelFor(password).includes(password.value), false);

const textInput = element("INPUT", { placeholder: "Search workflows" }, {
  value: "private typed value"
});
assert.equal(labelFor(textInput), "Search workflows");
assert.equal(labelFor(textInput).includes(textInput.value), false);

const button = element("BUTTON", {}, { innerText: "Save workflow" });
assert.equal(labelFor(button), "Save workflow");

console.log("recording safety tests passed");
