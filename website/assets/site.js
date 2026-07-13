(function () {
  const releases = window.NEXAFLOW_RELEASES || { products: [], published: false };

  function releaseUrl(product) {
    return releases.published ? `${releases.releaseBase}${product.file}` : "";
  }

  function downloadControl(product, className = "button primary") {
    const url = releaseUrl(product);
    if (!url) {
      return `<span class="${className} disabled" aria-disabled="true">Release upload pending</span>`;
    }
    return `<a class="${className}" href="${url}" download>${product.label}${iconDownload()}</a>`;
  }

  function iconDownload() {
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></svg>`;
  }

  function productCard(product) {
    return `
      <article class="product-card">
        <div class="product-card-head">
          <span class="platform-icon" aria-hidden="true">${product.symbol}</span>
          <div>
            <span class="eyebrow">${product.eyebrow}</span>
            <h3>${product.name}</h3>
          </div>
        </div>
        <p>${product.summary}</p>
        <div class="product-meta">
          <span>${product.format}</span>
          <span>${product.size}</span>
          <span>v${releases.version}</span>
        </div>
        ${downloadControl(product)}
      </article>
    `;
  }

  function downloadPanel(product) {
    const steps = product.install.map((step, index) => `
      <li><span>${index + 1}</span><p>${step}</p></li>
    `).join("");
    return `
      <section class="download-panel" id="${product.id}">
        <div class="download-summary">
          <span class="platform-icon large" aria-hidden="true">${product.symbol}</span>
          <span class="eyebrow">${product.eyebrow}</span>
          <h2>${product.name}</h2>
          <p>${product.summary}</p>
          <div class="download-file">
            <strong>${product.file}</strong>
            <span>${product.format} / ${product.size}</span>
          </div>
          ${downloadControl(product)}
        </div>
        <div class="install-guide">
          <span class="eyebrow">Installation</span>
          <ol>${steps}</ol>
          <details>
            <summary>SHA-256 checksum</summary>
            <code>${product.checksum}</code>
          </details>
        </div>
      </section>
    `;
  }

  document.querySelectorAll("[data-release-version]").forEach((node) => {
    node.textContent = releases.version || "1.0.0";
  });

  const productGrid = document.querySelector("[data-product-grid]");
  if (productGrid) productGrid.innerHTML = releases.products.map(productCard).join("");

  const downloadList = document.querySelector("[data-download-list]");
  if (downloadList) downloadList.innerHTML = releases.products.map(downloadPanel).join("");

  const integrityTable = document.querySelector("[data-integrity-table]");
  if (integrityTable) {
    integrityTable.innerHTML = releases.products.map((product) => `
      <tr>
        <td>${product.name}</td>
        <td>${product.file.split(".").pop().toUpperCase()}</td>
        <td><code>${product.checksum}</code></td>
      </tr>
    `).join("");
  }

  const releaseNotice = document.querySelector("[data-release-notice]");
  if (releaseNotice) {
    releaseNotice.classList.toggle("is-live", !!releases.published);
    releaseNotice.innerHTML = releases.published
      ? `<span class="dot" aria-hidden="true"></span>NexaFlow v${releases.version} downloads are available.`
      : `<span class="dot" aria-hidden="true"></span>NexaFlow v${releases.version} packages are verified locally. Direct links activate after the release files are uploaded.`;
  }

  document.querySelectorAll("[data-status-label]").forEach((node) => {
    node.classList.toggle("is-live", !!releases.published);
    node.textContent = releases.published ? "Available now" : node.textContent;
  });

  const menuButton = document.querySelector("[data-menu-button]");
  const menu = document.querySelector("[data-menu]");
  if (menuButton && menu) {
    menuButton.addEventListener("click", () => {
      const open = menuButton.getAttribute("aria-expanded") === "true";
      menuButton.setAttribute("aria-expanded", String(!open));
      menu.classList.toggle("open", !open);
      document.body.classList.toggle("menu-open", !open);
    });
  }

  const form = document.querySelector("[data-support-form]");
  const formStatus = document.querySelector("[data-form-status]");
  if (form && formStatus) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const fields = new FormData(form);
      const title = encodeURIComponent(`[Support] ${fields.get("product")}: ${fields.get("subject")}`);
      const body = encodeURIComponent(
        `Product: ${fields.get("product")}\n` +
        `Issue: ${fields.get("subject")}\n\n` +
        `${fields.get("message")}\n\n` +
        "Do not include passwords, pairing tokens, private screenshots, or workflow data."
      );
      formStatus.textContent = "Opening the issue tracker. Review the public report before submitting.";
      window.location.href = `${releases.supportUrl}?title=${title}&body=${body}`;
    });
  }
}());
