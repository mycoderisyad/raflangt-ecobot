/**
 * EcoBot API Playground — Interactive live-test widget
 * Sends real HTTP requests from the browser using fetch().
 */

(function () {
  "use strict";

  const DEFAULT_BASE = "http://localhost:8000";
  const DEFAULT_ADMIN_BASE = "http://localhost:3001";

  /* ---------------------------------------------------------------- */
  /*  Endpoint catalogue                                              */
  /* ---------------------------------------------------------------- */
  const ENDPOINTS = [
    {
      id: "health-root",
      group: "Health",
      method: "GET",
      path: "/",
      desc: "Root status check — returns app name and running status.",
      auth: false,
      server: "api",
    },
    {
      id: "health-check",
      group: "Health",
      method: "GET",
      path: "/health",
      desc: "Lightweight health-check endpoint.",
      auth: false,
      server: "api",
    },
    {
      id: "users-list",
      group: "Users",
      method: "GET",
      path: "/api/users",
      desc: "List all registered users with pagination.",
      auth: true,
      params: [
        { name: "limit", type: "number", default: "100", desc: "Max rows to return" },
        { name: "offset", type: "number", default: "0", desc: "Row offset for pagination" },
      ],
      server: "api",
    },
    {
      id: "users-get",
      group: "Users",
      method: "GET",
      path: "/api/users/{phone}",
      desc: "Get a single user by phone number (e.g. 628xxx@c.us).",
      auth: true,
      pathParams: [{ name: "phone", desc: "Phone number identifier" }],
      server: "api",
    },
    {
      id: "webhook-wa",
      group: "Webhooks",
      method: "POST",
      path: "/webhook/whatsapp",
      desc: "WhatsApp (WAHA) webhook receiver. Requires X-Waha-Webhook-Secret header.",
      auth: "webhook",
      headers: [{ name: "X-Waha-Webhook-Secret", desc: "WAHA webhook secret" }],
      body: JSON.stringify(
        {
          event: "message",
          payload: {
            from: "628xxx@c.us",
            hasMedia: false,
            type: "chat",
            body: "Hello EcoBot!",
          },
        },
        null,
        2
      ),
      server: "api",
    },
    {
      id: "webhook-tg",
      group: "Webhooks",
      method: "POST",
      path: "/webhook/telegram",
      desc: "Telegram Bot webhook receiver. Requires X-Telegram-Bot-Api-Secret-Token header.",
      auth: "webhook",
      headers: [
        {
          name: "X-Telegram-Bot-Api-Secret-Token",
          desc: "Telegram webhook secret",
        },
      ],
      body: JSON.stringify(
        {
          update_id: 1,
          message: {
            message_id: 1,
            chat: { id: 12345, type: "private" },
            from: { id: 12345, first_name: "Test" },
            text: "Hello",
            date: Math.floor(Date.now() / 1000),
          },
        },
        null,
        2
      ),
      server: "api",
    },
    {
      id: "admin-health",
      group: "Admin Panel",
      method: "GET",
      path: "/health",
      desc: "Admin panel health check.",
      auth: false,
      server: "admin",
    },
  ];

  /* ---------------------------------------------------------------- */
  /*  Render playground into #api-playground                          */
  /* ---------------------------------------------------------------- */
  function init() {
    const container = document.getElementById("api-playground");
    if (!container) return;

    // Base URL selector
    container.innerHTML = `
      <div class="playground-header">
        <div class="base-url-group">
          <label for="pg-base-url">API Base URL</label>
          <input type="text" id="pg-base-url" value="${DEFAULT_BASE}" spellcheck="false" />
        </div>
        <div class="base-url-group">
          <label for="pg-admin-url">Admin Panel URL</label>
          <input type="text" id="pg-admin-url" value="${DEFAULT_ADMIN_BASE}" spellcheck="false" />
        </div>
      </div>
      <div class="endpoint-list" id="endpoint-list"></div>
    `;

    renderEndpoints();
  }

  function renderEndpoints() {
    const list = document.getElementById("endpoint-list");
    if (!list) return;

    const groups = {};
    ENDPOINTS.forEach((ep) => {
      if (!groups[ep.group]) groups[ep.group] = [];
      groups[ep.group].push(ep);
    });

    let html = "";
    for (const [group, eps] of Object.entries(groups)) {
      html += `<h3 class="ep-group-title">${group}</h3>`;
      eps.forEach((ep) => {
        const methodClass = ep.method.toLowerCase();
        const authBadge = ep.auth === true
          ? '<span class="badge badge-auth">API Key</span>'
          : ep.auth === "webhook"
          ? '<span class="badge badge-webhook">Webhook Secret</span>'
          : '<span class="badge badge-public">Public</span>';

        html += `
          <div class="endpoint-card" id="ep-${ep.id}">
            <div class="ep-header" onclick="window.__pgToggle('${ep.id}')">
              <span class="method-badge ${methodClass}">${ep.method}</span>
              <code class="ep-path">${ep.path}</code>
              ${authBadge}
              <span class="ep-desc">${ep.desc}</span>
              <span class="ep-chevron">&#9662;</span>
            </div>
            <div class="ep-body" id="ep-body-${ep.id}" style="display:none;">
              ${renderEndpointForm(ep)}
            </div>
          </div>`;
      });
    }
    list.innerHTML = html;
  }

  function renderEndpointForm(ep) {
    let html = '<div class="ep-form">';

    // Path params
    if (ep.pathParams) {
      html += '<div class="form-section"><label class="section-label">Path Parameters</label>';
      ep.pathParams.forEach((p) => {
        html += `<div class="form-row">
          <label>${p.name}</label>
          <input type="text" class="pg-input" data-ep="${ep.id}" data-pathparam="${p.name}" placeholder="${p.desc}" />
        </div>`;
      });
      html += "</div>";
    }

    // Query params
    if (ep.params) {
      html += '<div class="form-section"><label class="section-label">Query Parameters</label>';
      ep.params.forEach((p) => {
        html += `<div class="form-row">
          <label>${p.name} <span class="param-type">${p.type}</span></label>
          <input type="text" class="pg-input" data-ep="${ep.id}" data-param="${p.name}" placeholder="${p.default}" value="${p.default}" />
        </div>`;
      });
      html += "</div>";
    }

    // Headers
    if (ep.auth === true) {
      html += `<div class="form-section"><label class="section-label">Headers</label>
        <div class="form-row">
          <label>X-API-Key</label>
          <input type="text" class="pg-input" data-ep="${ep.id}" data-header="X-API-Key" placeholder="Your API secret key" />
        </div></div>`;
    }
    if (ep.headers) {
      html += '<div class="form-section"><label class="section-label">Headers</label>';
      ep.headers.forEach((h) => {
        html += `<div class="form-row">
          <label>${h.name}</label>
          <input type="text" class="pg-input" data-ep="${ep.id}" data-header="${h.name}" placeholder="${h.desc}" />
        </div>`;
      });
      html += "</div>";
    }

    // Body
    if (ep.body) {
      html += `<div class="form-section"><label class="section-label">Request Body (JSON)</label>
        <textarea class="pg-body" id="pg-body-${ep.id}" rows="8" spellcheck="false">${ep.body}</textarea>
      </div>`;
    }

    // Send button + response area
    html += `
      <button class="btn-send" onclick="window.__pgSend('${ep.id}')">
        <span class="send-icon">&#9654;</span> Send Request
      </button>
      <div class="response-area" id="pg-resp-${ep.id}" style="display:none;">
        <div class="resp-header">
          <span class="resp-status" id="pg-status-${ep.id}"></span>
          <span class="resp-time" id="pg-time-${ep.id}"></span>
        </div>
        <pre class="resp-body"><code id="pg-resp-body-${ep.id}"></code></pre>
      </div>
    </div>`;

    return html;
  }

  /* ---------------------------------------------------------------- */
  /*  Toggle endpoint card                                            */
  /* ---------------------------------------------------------------- */
  window.__pgToggle = function (id) {
    const body = document.getElementById(`ep-body-${id}`);
    const card = document.getElementById(`ep-${id}`);
    if (!body) return;
    const open = body.style.display === "none";
    body.style.display = open ? "block" : "none";
    card.classList.toggle("open", open);
  };

  /* ---------------------------------------------------------------- */
  /*  Send request                                                    */
  /* ---------------------------------------------------------------- */
  window.__pgSend = async function (id) {
    const ep = ENDPOINTS.find((e) => e.id === id);
    if (!ep) return;

    const baseUrl =
      ep.server === "admin"
        ? document.getElementById("pg-admin-url").value.replace(/\/$/, "")
        : document.getElementById("pg-base-url").value.replace(/\/$/, "");

    // Build path with path params
    let path = ep.path;
    if (ep.pathParams) {
      ep.pathParams.forEach((p) => {
        const input = document.querySelector(`[data-ep="${id}"][data-pathparam="${p.name}"]`);
        const val = input ? input.value : "";
        path = path.replace(`{${p.name}}`, encodeURIComponent(val));
      });
    }

    // Build query string
    const queryParts = [];
    if (ep.params) {
      ep.params.forEach((p) => {
        const input = document.querySelector(`[data-ep="${id}"][data-param="${p.name}"]`);
        const val = input ? input.value.trim() : "";
        if (val) queryParts.push(`${p.name}=${encodeURIComponent(val)}`);
      });
    }

    const url = baseUrl + path + (queryParts.length ? "?" + queryParts.join("&") : "");

    // Build headers
    const headers = { Accept: "application/json" };
    document.querySelectorAll(`[data-ep="${id}"][data-header]`).forEach((input) => {
      const val = input.value.trim();
      if (val) headers[input.dataset.header] = val;
    });

    // Body
    const bodyEl = document.getElementById(`pg-body-${id}`);
    let body = undefined;
    if (ep.method === "POST" && bodyEl) {
      headers["Content-Type"] = "application/json";
      body = bodyEl.value;
    }

    // Show response area
    const respArea = document.getElementById(`pg-resp-${id}`);
    const statusEl = document.getElementById(`pg-status-${id}`);
    const timeEl = document.getElementById(`pg-time-${id}`);
    const bodyOut = document.getElementById(`pg-resp-body-${id}`);

    respArea.style.display = "block";
    statusEl.textContent = "Loading...";
    statusEl.className = "resp-status";
    timeEl.textContent = "";
    bodyOut.textContent = "";

    const t0 = performance.now();
    try {
      const resp = await fetch(url, {
        method: ep.method,
        headers,
        body,
        mode: "cors",
      });
      const elapsed = Math.round(performance.now() - t0);
      const text = await resp.text();

      statusEl.textContent = `${resp.status} ${resp.statusText}`;
      statusEl.className = `resp-status status-${resp.status < 300 ? "ok" : resp.status < 500 ? "warn" : "err"}`;
      timeEl.textContent = `${elapsed}ms`;

      try {
        bodyOut.textContent = JSON.stringify(JSON.parse(text), null, 2);
      } catch {
        bodyOut.textContent = text;
      }
    } catch (err) {
      const elapsed = Math.round(performance.now() - t0);
      statusEl.textContent = "Network Error";
      statusEl.className = "resp-status status-err";
      timeEl.textContent = `${elapsed}ms`;
      bodyOut.textContent = err.message + "\n\nMake sure the server is running and CORS is enabled.";
    }
  };

  /* ---------------------------------------------------------------- */
  document.addEventListener("DOMContentLoaded", init);
})();
