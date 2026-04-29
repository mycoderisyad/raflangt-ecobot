/**
 * EcoBot Docs — Shared Navigation & Utilities
 * Dynamically renders nav, footer, and language toggle on every page.
 */

const NAV_ITEMS = [
  { href: "index.html", label: "Home" },
  { href: "getting-started.html", label: "Getting Started" },
  { href: "architecture.html", label: "Architecture" },
  { href: "configuration.html", label: "Configuration" },
  { href: "api.html", label: "API Reference" },
  { href: "admin-panel.html", label: "Admin Panel" },
  { href: "security.html", label: "Security" },
];

const GITHUB_URL = "https://github.com/mycoderisyad/raflangt-ecobot";
const WA_URL = "https://wa.me/6287875366731";

/* ------------------------------------------------------------------ */
/*  Render shared navigation                                          */
/* ------------------------------------------------------------------ */
function renderNav() {
  const nav = document.getElementById("main-nav");
  if (!nav) return;

  const current = location.pathname.split("/").pop() || "index.html";

  nav.innerHTML = `
    <div class="nav-inner">
      <a href="index.html" class="nav-brand">
        <span class="brand-icon">&#9851;</span> EcoBot <span class="brand-tag">Docs</span>
      </a>
      <button class="nav-toggle" id="nav-toggle" aria-label="Toggle menu">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav-links" id="nav-links">
        ${NAV_ITEMS.map(
          (item) =>
            `<li><a href="${item.href}" class="${current === item.href ? "active" : ""}">${item.label}</a></li>`
        ).join("")}
        <li class="nav-sep"></li>
        <li><a href="${GITHUB_URL}" target="_blank" rel="noopener">GitHub</a></li>
      </ul>
    </div>`;

  // Hamburger toggle
  const toggle = document.getElementById("nav-toggle");
  const links = document.getElementById("nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", () => {
      links.classList.toggle("open");
      toggle.classList.toggle("open");
    });
    links.querySelectorAll("a").forEach((a) =>
      a.addEventListener("click", () => {
        links.classList.remove("open");
        toggle.classList.remove("open");
      })
    );
  }
}

/* ------------------------------------------------------------------ */
/*  Render shared footer                                              */
/* ------------------------------------------------------------------ */
function renderFooter() {
  const footer = document.getElementById("main-footer");
  if (!footer) return;

  footer.innerHTML = `
    <div class="footer-inner">
      <p>&copy; ${new Date().getFullYear()} EcoBot &mdash; Intelligent Waste Management System. Licensed under Apache 2.0.</p>
      <div class="footer-links">
        <a href="${GITHUB_URL}" target="_blank" rel="noopener">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
          GitHub
        </a>
        <a href="${WA_URL}" target="_blank" rel="noopener">WhatsApp Bot</a>
        <a href="api.html">API Docs</a>
      </div>
    </div>`;
}

/* ------------------------------------------------------------------ */
/*  Smooth scroll for anchor links                                    */
/* ------------------------------------------------------------------ */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener("click", (e) => {
      const id = a.getAttribute("href").slice(1);
      const target = document.getElementById(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        history.pushState(null, "", `#${id}`);
      }
    });
  });
}

/* ------------------------------------------------------------------ */
/*  Copy-to-clipboard on code blocks                                  */
/* ------------------------------------------------------------------ */
function initCodeCopy() {
  document.querySelectorAll("pre > code").forEach((block) => {
    const btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.textContent = "Copy";
    btn.addEventListener("click", () => {
      navigator.clipboard.writeText(block.textContent).then(() => {
        btn.textContent = "Copied!";
        setTimeout(() => (btn.textContent = "Copy"), 2000);
      });
    });
    block.parentElement.style.position = "relative";
    block.parentElement.appendChild(btn);
  });
}

/* ------------------------------------------------------------------ */
/*  Init                                                              */
/* ------------------------------------------------------------------ */
document.addEventListener("DOMContentLoaded", () => {
  renderNav();
  renderFooter();
  initSmoothScroll();
  initCodeCopy();
});
