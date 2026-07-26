/* ============================================================
 * push-aio · app.js
 * Apple-inspired UI logic
 * ============================================================ */

const API_KEY_STORAGE = "push_aio_api_key";

const state = {
  metas: [],
  channels: [],
  status: null,
  logs: [],
  apiKey: localStorage.getItem(API_KEY_STORAGE) || "",
  route: "dashboard",
  editingChannelId: null,
};

let dragData = { id: null, type: null };

const ROUTE_TITLES = {
  dashboard: "概览",
  channels: "渠道管理",
  "send-test": "发送测试",
  settings: "设置",
};

/* ===== SVG Icons ===== */
const ICONS = {
  online: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>',
  enabled: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="6" width="22" height="12" rx="6"/><circle cx="17" cy="12" r="3"/></svg>',
  emergency: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
  types: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
  grip: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/><circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/></svg>',
  pen: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>',
  send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>',
  power: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>',
  chevronDown: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
  arrowUp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>',
  arrowDown: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>',
  checkCircle: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  alertTriangle: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  zap: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
};

/* 生成带尺寸的图标 HTML */
function icon(name, size) {
  const svg = ICONS[name] || "";
  const s = size || 16;
  return svg.replace('<svg', `<svg width="${s}" height="${s}"`);
}

/* ============ Key 管理 ============ */
function getApiKey() {
  return state.apiKey || localStorage.getItem(API_KEY_STORAGE) || "";
}
function setApiKey(key) {
  state.apiKey = key;
  if (key) localStorage.setItem(API_KEY_STORAGE, key);
  else localStorage.removeItem(API_KEY_STORAGE);
}

/* ============ API 调用 ============ */
async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const key = getApiKey();
  if (key) headers["X-API-Key"] = key;
  const res = await fetch(path, { ...options, headers });
  if (res.status === 401) {
    setApiKey("");
    showLogin();
    throw new Error("API Key 无效");
  }
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ============ Toast ============ */
function toast(message, type = "ok") {
  const root = document.getElementById("toast-root");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

/* ============ 登录 / 登出 ============ */
function showLogin() {
  document.getElementById("login-view").hidden = false;
  document.getElementById("app-view").hidden = true;
}
function showApp() {
  document.getElementById("login-view").hidden = true;
  document.getElementById("app-view").hidden = false;
}

function renderLoginView(setupMode) {
  const title = document.getElementById("login-title");
  const lead = document.getElementById("login-lead");
  const keyLabel = document.getElementById("login-key-label");
  const submitBtn = document.getElementById("login-submit");
  const errorEl = document.getElementById("login-error");
  const hintEl = document.getElementById("login-hint");

  if (setupMode) {
    title.textContent = "首次设置";
    lead.textContent = "检测到数据库中尚未设置 API Key，请先设置一个密钥用于登录与外部调用。";
    keyLabel.textContent = "设置 API Key（至少 12 位）";
    submitBtn.textContent = "设置并登录";
    errorEl.textContent = "设置失败，请检查 Key 长度后重试";
    hintEl.textContent = "设置后密钥保存在数据库中，后续可在此页面登录。";
  } else {
    title.textContent = "push-aio";
    lead.textContent = "按渠道类型调度：主通道组（同类型）逐个尝试，全失败升级全局紧急通道组（并发发送）。";
    keyLabel.textContent = "API Key";
    submitBtn.textContent = "登录";
    errorEl.textContent = "Key 无效，请检查后重试";
    hintEl.textContent = "Key 会存到浏览器 localStorage，后续请求自动携带。";
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const input = event.currentTarget.key;
  const key = input.value.trim();
  if (!key) return;

  const setupMode = await checkSetupMode();
  if (setupMode) {
    try {
      await api("/admin/api/auth/setup", {
        method: "POST",
        body: JSON.stringify({ new_key: key }),
      });
      setApiKey(key);
      input.value = "";
      document.getElementById("login-error").style.display = "none";
      showApp();
      await bootstrap();
      toast("API Key 已设置并登录");
    } catch (e) {
      setApiKey("");
      document.getElementById("login-error").style.display = "flex";
    }
    return;
  }

  setApiKey(key);
  try {
    await api("/admin/api/auth/verify");
    input.value = "";
    document.getElementById("login-error").style.display = "none";
    showApp();
    await bootstrap();
    toast("登录成功");
  } catch (e) {
    setApiKey("");
    document.getElementById("login-error").style.display = "flex";
  }
}

async function checkSetupMode() {
  try {
    const data = await fetch("/admin/api/auth/status").then((r) => r.json());
    return !!data.setup_mode;
  } catch (e) {
    return false;
  }
}

function handleLogout() {
  setApiKey("");
  showLogin();
}

/* ============ 路由 ============ */
function navigate(route) {
  if (!ROUTE_TITLES[route]) route = "dashboard";
  state.route = route;
  document.querySelectorAll(".page-content").forEach((el) => {
    el.classList.toggle("active", el.id === `page-${route}`);
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.route === route);
  });
  document.getElementById("page-title").textContent = ROUTE_TITLES[route];
  if (route === "dashboard") renderDashboard();
  if (route === "channels") renderChannelsPage();
  if (route === "send-test") renderNotifyChannelPicker();
  if (window.innerWidth <= 768) closeSidebar();
}

/* ============ 工具 ============ */
function escapeHtml(input) {
  return String(input ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function tagClassForRole(role) {
  if (role === "backup") return "tag tag-backup";
  if (role === "emergency") return "tag tag-emergency";
  return "tag tag-primary";
}
function roleLabel(role) {
  if (role === "backup") return "备用";
  if (role === "emergency") return "紧急";
  return "主";
}

function errorKindLabel(kind) {
  switch (kind) {
    case "rate_limit": return "限流";
    case "auth": return "认证失败";
    case "config": return "配置错误";
    case "network": return "网络异常";
    case "channel_error": return "渠道错误";
    case "none": return "";
    default: return "";
  }
}
function errorKindTag(kind) {
  const label = errorKindLabel(kind);
  if (!label) return "";
  const cls = kind === "rate_limit" || kind === "network" ? "tag tag-backup" : "tag tag-error";
  return `<span class="${cls}">${escapeHtml(label)}</span>`;
}

/* ============ 概览页 ============ */
function renderDashboard() {
  if (!state.status) return;

  const stats = [
    { num: state.status.online_count, lbl: "在线渠道", icon: ICONS.online },
    { num: state.status.enabled_count, lbl: "启用中", icon: ICONS.enabled },
    { num: state.status.emergency_count, lbl: "紧急通道", icon: ICONS.emergency },
    { num: state.status.supported_count, lbl: "支持类型", icon: ICONS.types },
  ];
  document.getElementById("stat-grid").innerHTML = stats.map((s) => `
    <div class="stat-card">
      <div class="icon">${s.icon}</div>
      <div class="num">${s.num}</div>
      <div class="lbl">${s.lbl}</div>
    </div>
  `).join("");

  // 渠道状态概览
  const channelsBox = document.getElementById("dashboard-channels");
  if (!state.channels.length) {
    channelsBox.innerHTML = `<div class="list-item"><span class="meta">还没有渠道，前往「渠道管理」新增一个。</span></div>`;
  } else {
    channelsBox.innerHTML = state.channels.map((item) => {
      const meta = state.metas.find((m) => m.type === item.type);
      const label = meta ? meta.label : item.type;
      const statusTag = item.online
        ? `<span class="tag tag-success">在线</span>`
        : item.enabled
          ? `<span class="tag tag-error">异常</span>`
          : `<span class="tag tag-muted">已禁用</span>`;
      const emTag = item.is_emergency ? `<span class="tag tag-emergency">紧急</span>` : "";
      return `
        <div class="list-item">
          <strong>${escapeHtml(item.name)}</strong>
          <span class="tag tag-muted">${escapeHtml(label)}</span>
          ${statusTag}
          ${emTag}
          <span class="meta">#${item.id}</span>
        </div>
      `;
    }).join("");
  }

  // 最近推送
  const logsBox = document.getElementById("dashboard-logs");
  const logs = state.logs.slice(0, 10);
  if (!logs.length) {
    logsBox.innerHTML = `<div class="list-item"><span class="meta">暂无发送日志。</span></div>`;
  } else {
    logsBox.innerHTML = logs.map((item) => {
      const roleTag = `<span class="${tagClassForRole(item.role)}">${roleLabel(item.role)}</span>`;
      const successTag = item.success
        ? `<span class="tag tag-success">成功</span>`
        : `<span class="tag tag-error">失败</span>`;
      const errTag = item.success ? "" : errorKindTag(item.error_kind);
      return `
        <div class="list-item">
          <strong>${escapeHtml(item.channel_name)}</strong>
          ${roleTag}
          ${successTag}
          ${errTag}
          <span class="meta">${new Date(item.created_at).toLocaleString()}</span>
          <div class="row-sub">${escapeHtml(item.title)}${item.success ? "" : ` · ${escapeHtml(item.detail)}`}</div>
        </div>
      `;
    }).join("");
  }
}

/* ============ 渠道管理页 ============ */
function renderChannelsPage() {
  const container = document.getElementById("channels-list");
  if (!state.channels.length) {
    container.innerHTML = `<div class="list-item"><span class="meta">还没有渠道，点击右上角「新增渠道」添加。</span></div>`;
    return;
  }

  const mainEnabled = state.channels.filter((c) => c.enabled && !c.is_emergency);
  const emEnabled = state.channels.filter((c) => c.enabled && c.is_emergency)
    .sort((a, b) => (a.priority - b.priority) || (a.id - b.id));
  const disabled = state.channels.filter((c) => !c.enabled);

  const typeOrder = state.metas.map((m) => m.type);
  const groupsByType = new Map();
  for (const ch of mainEnabled) {
    if (!groupsByType.has(ch.type)) groupsByType.set(ch.type, []);
    groupsByType.get(ch.type).push(ch);
  }
  const sortedTypes = Array.from(groupsByType.keys()).sort((a, b) => {
    const ia = typeOrder.indexOf(a);
    const ib = typeOrder.indexOf(b);
    return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
  });
  for (const list of groupsByType.values()) {
    list.sort((a, b) => (a.priority - b.priority) || (a.id - b.id));
  }

  let html = "";

  if (sortedTypes.length) {
    html += `<div class="section-title">主通道链路</div>`;
    html += `<p class="section-desc">按渠道类型分组，组内按优先级逐个尝试。拖拽 ⋮ 手柄或展开编辑可调整顺序。</p>`;
    for (const type of sortedTypes) {
      const list = groupsByType.get(type);
      const meta = state.metas.find((m) => m.type === type);
      const label = meta ? meta.label : type;
      html += `<div class="channel-group" data-type="${escapeHtml(type)}">`;
      html += `<div class="channel-group-head"><div><span class="gtitle">${escapeHtml(label)}</span><span class="gcount">· ${list.length} 个</span></div>`;
      html += `<button class="gadd" data-action="add-type" data-type="${escapeHtml(type)}">${icon("plus", 14)}<span>添加</span></button></div>`;
      html += `<div class="channel-group-body">${list.map((item, idx) => renderMainRow(item, idx, list.length)).join("")}</div>`;
      html += `</div>`;
    }
  }

  if (emEnabled.length) {
    html += `<div class="section-title"><span class="sdot"></span>紧急通道组</div>`;
    html += `<p class="section-desc">全局兜底，主通道全失败后并发发送所有紧急渠道。</p>`;
    html += `<div class="channel-group emergency"><div class="channel-group-body">${emEnabled.map(renderEmergencyRow).join("")}</div>`;
    html += `<div class="channel-group-foot">${icon("info", 14)}<span>紧急渠道不参与顺位排序，触发时全部并发发送。</span></div></div>`;
  }

  if (disabled.length) {
    html += `<div class="section-title muted">已禁用渠道</div>`;
    html += `<p class="section-desc">已停用的渠道，不会参与任何推送链路。</p>`;
    html += `<div class="channel-group"><div class="channel-group-body">${disabled.map(renderDisabledRow).join("")}</div></div>`;
  }

  container.innerHTML = html;
  bindChannelRowEvents(container);
}

function renderMainRow(item, idx, total) {
  const meta = state.metas.find((m) => m.type === item.type);
  const label = meta ? meta.label : item.type;
  const roleTag = idx === 0
    ? `<span class="tag tag-primary">主推送</span>`
    : `<span class="tag tag-backup">备用 ${idx}</span>`;
  const orderTag = `<span class="tag tag-muted">第 ${idx + 1} 顺位</span>`;
  const expanded = state.editingChannelId === item.id;
  return `
    <div class="channel-row ${expanded ? "expanded" : ""}" data-id="${item.id}" data-type="${escapeHtml(item.type)}" draggable="true">
      <div class="channel-row-head">
        <span class="grip" title="拖拽排序">${icon("grip", 16)}</span>
        <span class="cname">${escapeHtml(item.name)}</span>
        <div class="ctags">${roleTag}${orderTag}<span class="tag tag-muted">${escapeHtml(label)}</span></div>
        <span class="cstatus"><span class="dot"></span>已启用</span>
        <span class="cid">#${item.id}</span>
        <div class="cactions">
          <button class="icon-btn" data-action="test" data-id="${item.id}" title="测试">${icon("send", 16)}</button>
          <button class="icon-btn ${expanded ? "expanded" : ""}" data-action="edit" data-id="${item.id}" title="编辑">${icon(expanded ? "chevronDown" : "pen", 16)}</button>
          <button class="icon-btn danger" data-action="delete" data-id="${item.id}" title="删除">${icon("trash", 16)}</button>
        </div>
      </div>
      ${expanded ? renderChannelEditBody(item, idx, total) : ""}
    </div>
  `;
}

function renderEmergencyRow(item) {
  const meta = state.metas.find((m) => m.type === item.type);
  const label = meta ? meta.label : item.type;
  const expanded = state.editingChannelId === item.id;
  return `
    <div class="channel-row ${expanded ? "expanded" : ""}" data-id="${item.id}">
      <div class="channel-row-head">
        <span class="grip" style="cursor:default;color:var(--error);" title="紧急通道">${icon("zap", 16)}</span>
        <span class="cname">${escapeHtml(item.name)}</span>
        <div class="ctags"><span class="tag tag-muted">${escapeHtml(label)}</span><span class="tag tag-emergency">紧急</span><span class="tag tag-muted">并发</span></div>
        <span class="cstatus"><span class="dot"></span>已启用</span>
        <span class="cid">#${item.id}</span>
        <div class="cactions">
          <button class="icon-btn" data-action="test" data-id="${item.id}" title="测试">${icon("send", 16)}</button>
          <button class="icon-btn ${expanded ? "expanded" : ""}" data-action="edit" data-id="${item.id}" title="编辑">${icon(expanded ? "chevronDown" : "pen", 16)}</button>
          <button class="icon-btn danger" data-action="delete" data-id="${item.id}" title="删除">${icon("trash", 16)}</button>
        </div>
      </div>
      ${expanded ? renderChannelEditBody(item, -1, -1) : ""}
    </div>
  `;
}

function renderDisabledRow(item) {
  const meta = state.metas.find((m) => m.type === item.type);
  const label = meta ? meta.label : item.type;
  return `
    <div class="channel-row disabled" data-id="${item.id}">
      <div class="channel-row-head">
        <span class="grip" style="cursor:default;color:var(--bg-400);" title="已禁用">${icon("power", 16)}</span>
        <span class="cname">${escapeHtml(item.name)}</span>
        <div class="ctags"><span class="tag tag-muted">${escapeHtml(label)}</span><span class="tag tag-error">已禁用</span>${item.is_emergency ? `<span class="tag tag-emergency">紧急</span>` : ""}</div>
        <span class="cid">#${item.id}</span>
        <div class="cactions">
          <button class="enable-btn" data-action="toggle-enabled" data-id="${item.id}">${icon("power", 14)}<span>启用</span></button>
          <button class="icon-btn danger" data-action="delete" data-id="${item.id}" title="删除">${icon("trash", 16)}</button>
        </div>
      </div>
    </div>
  `;
}

/* 就地展开编辑表单 */
function renderChannelEditBody(item, idx, total) {
  const meta = state.metas.find((m) => m.type === item.type);
  if (!meta) return `<div class="channel-edit-body"><p class="meta">渠道元数据缺失</p></div>`;

  const config = item.config || {};
  const entries = Object.entries(meta.config_schema);
  const isAdvanced = (s) => typeof s === "object" && s && s.advanced === true;
  const normalFields = entries.filter(([_, s]) => !isAdvanced(s));
  const advancedFields = entries.filter(([_, s]) => isAdvanced(s));

  const renderField = ([key, schema]) => {
    const flabel = typeof schema === "string" ? schema : schema.label;
    const kind = typeof schema === "string" ? "text" : schema.type || "text";
    const inputType = schema.secret ? "password" : kind === "number" ? "number" : "text";
    const required = schema.required ? "required" : "";
    const curVal = config[key] !== undefined && config[key] !== null ? config[key] : (schema.default || "");
    if (kind === "boolean") {
      const checked = curVal === true ? "checked" : "";
      return `<label class="check"><input name="config.${escapeHtml(key)}" type="checkbox" ${checked} /><span>${escapeHtml(flabel)}</span></label>`;
    }
    return `<label><span>${escapeHtml(flabel)}${schema.required ? " *" : ""}</span><input name="config.${escapeHtml(key)}" type="${inputType}" ${required} value="${escapeHtml(curVal)}" /></label>`;
  };

  let targetHtml = "";
  if (meta.target_mode === "external") {
    targetHtml = `<label><span>默认目标 ${meta.target_label ? "(" + escapeHtml(meta.target_label) + ")" : ""}</span><input name="default_target" value="${escapeHtml(item.default_target || "")}" /></label>`;
  }

  const normalHtml = normalFields.map(renderField).join("");
  const advancedHtml = advancedFields.map(renderField).join("");

  const orderBtns = idx >= 0 ? `
      <button type="button" class="btn btn-ghost btn-sm" data-action="move-up" data-id="${item.id}" ${idx === 0 ? "disabled" : ""}>${icon("arrowUp", 14)} 上移</button>
      <button type="button" class="btn btn-ghost btn-sm" data-action="move-down" data-id="${item.id}" ${idx === total - 1 ? "disabled" : ""}>${icon("arrowDown", 14)} 下移</button>` : "";

  const emergencyBtn = item.is_emergency
    ? `<button type="button" class="btn btn-ghost btn-sm" data-action="toggle-emergency" data-id="${item.id}">改回常规通道</button>`
    : `<button type="button" class="btn btn-ghost btn-sm" data-action="toggle-emergency" data-id="${item.id}">改为紧急通道</button>`;

  return `
    <div class="channel-edit-body">
      <form class="form" data-edit-id="${item.id}">
        <label><span>渠道名称</span><input name="name" required value="${escapeHtml(item.name)}" /></label>
        ${targetHtml}
        ${normalHtml}
        ${advancedHtml ? `<details class="advanced"><summary>高级配置（${advancedFields.length} 项）</summary><div class="form">${advancedHtml}</div></details>` : ""}
        <div class="edit-actions">
          <div class="left">
            <label class="check" style="flex-direction:row;align-items:center;gap:8px;">
              <span class="switch"><input type="checkbox" name="enabled" ${item.enabled ? "checked" : ""} /><span class="slider"></span></span>
              <span class="switch-label">启用此渠道</span>
            </label>
            ${orderBtns}
          </div>
          <div class="right">
            ${emergencyBtn}
            <button type="button" class="btn btn-ghost btn-sm" data-action="cancel-edit">取消</button>
            <button type="submit" class="btn btn-primary btn-sm">${icon("check", 14)} 保存</button>
          </div>
        </div>
      </form>
    </div>
  `;
}

function bindChannelRowEvents(container) {
  container.querySelectorAll("button[data-action]").forEach((btn) => {
    btn.addEventListener("click", handleChannelAction);
  });
  container.querySelectorAll("form[data-edit-id]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      submitChannelEdit(Number(form.dataset.editId), form);
    });
  });
  container.querySelectorAll(".channel-row[draggable='true']").forEach((row) => {
    row.addEventListener("dragstart", handleDragStart);
    row.addEventListener("dragover", handleDragOver);
    row.addEventListener("dragleave", handleDragLeave);
    row.addEventListener("drop", handleDrop);
    row.addEventListener("dragend", handleDragEnd);
  });
}

function toggleEditChannel(id) {
  state.editingChannelId = state.editingChannelId === id ? null : id;
  renderChannelsPage();
}

async function submitChannelEdit(id, form) {
  const channel = state.channels.find((c) => c.id === id);
  if (!channel) return;
  const meta = state.metas.find((m) => m.type === channel.type);
  const formData = new FormData(form);
  const config = {};
  for (const [key, value] of formData.entries()) {
    if (key.startsWith("config.")) {
      const name = key.slice("config.".length);
      const schema = (meta && meta.config_schema[name]) || {};
      if (schema.type === "boolean") {
        config[name] = true;
      } else if (value !== "") {
        config[name] = schema.type === "number" ? Number(value) : value;
      }
    }
  }
  if (meta) {
    for (const [key, schema] of Object.entries(meta.config_schema)) {
      if (schema.type === "boolean" && !formData.has(`config.${key}`)) config[key] = false;
    }
  }
  const payload = { name: formData.get("name"), enabled: formData.has("enabled"), config };
  if (meta && meta.target_mode === "external") {
    payload.default_target = formData.get("default_target") || null;
  }
  try {
    await api(`/admin/api/channels/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    toast("已保存");
    state.editingChannelId = null;
    await loadAll();
  } catch (e) {
    toast(`保存失败：${e.message}`, "bad");
  }
}

/* 拖拽排序（同类型组内） */
function handleDragStart(e) {
  const row = e.currentTarget;
  dragData.id = Number(row.dataset.id);
  dragData.type = row.dataset.type;
  row.classList.add("dragging");
  e.dataTransfer.effectAllowed = "move";
  try { e.dataTransfer.setData("text/plain", String(dragData.id)); } catch (_) {}
}
function handleDragOver(e) {
  if (!dragData.id || dragData.type !== e.currentTarget.dataset.type) return;
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
  e.currentTarget.classList.add("drag-over");
}
function handleDragLeave(e) {
  e.currentTarget.classList.remove("drag-over");
}
async function handleDrop(e) {
  e.preventDefault();
  const targetRow = e.currentTarget;
  targetRow.classList.remove("drag-over");
  const targetId = Number(targetRow.dataset.id);
  if (!dragData.id || dragData.id === targetId) return;
  if (dragData.type !== targetRow.dataset.type) return;
  const list = state.channels
    .filter((c) => c.enabled && !c.is_emergency && c.type === dragData.type)
    .sort((a, b) => (a.priority - b.priority) || (a.id - b.id));
  const fromIdx = list.findIndex((c) => c.id === dragData.id);
  const toIdx = list.findIndex((c) => c.id === targetId);
  if (fromIdx === -1 || toIdx === -1) return;
  try {
    if (fromIdx < toIdx) {
      for (let i = fromIdx; i < toIdx; i++) {
        await api(`/admin/api/channels/${dragData.id}/move?direction=down`, { method: "POST" });
      }
    } else {
      for (let i = fromIdx; i > toIdx; i--) {
        await api(`/admin/api/channels/${dragData.id}/move?direction=up`, { method: "POST" });
      }
    }
    state.editingChannelId = null;
    await loadAll();
    toast("顺序已更新");
  } catch (e) {
    toast(`排序失败：${e.message}`, "bad");
    await loadAll();
  }
}
function handleDragEnd(e) {
  e.currentTarget.classList.remove("dragging");
  document.querySelectorAll(".channel-row.drag-over").forEach((r) => r.classList.remove("drag-over"));
  dragData.id = null;
  dragData.type = null;
}

/* ============ 新增渠道表单 ============ */
function renderChannelForm() {
  const form = document.getElementById("channel-form");
  if (!state.metas.length) {
    form.innerHTML = `<p class="meta">渠道元数据加载中…</p>`;
    return;
  }
  const options = state.metas
    .map((meta) => `<option value="${meta.type}">${escapeHtml(meta.label)}</option>`)
    .join("");
  form.innerHTML = `
    <label>
      <span>渠道类型</span>
      <select name="type">${options}</select>
    </label>
    <label>
      <span>名称</span>
      <input name="name" required placeholder="例如：我的 Bark" />
    </label>
    <div id="default-target-wrap"></div>
    <div id="config-fields"></div>
    <div style="display:flex;gap:12px;">
      <button type="submit" class="btn btn-primary">保存渠道</button>
      <button type="button" id="channel-probe-btn" class="btn btn-secondary">先测试一下</button>
    </div>
    <p class="meta">建议先点「先测试一下」确认配置可用再保存。新建渠道默认加入主通道组末尾。需要作为兜底紧急通道时，到「渠道管理」页用"改为紧急"按钮切换。</p>
  `;

  const typeSelect = form.querySelector('select[name="type"]');
  typeSelect.addEventListener("change", () => renderConfigFields(typeSelect.value));
  form.addEventListener("submit", submitChannelForm);
  form.querySelector("#channel-probe-btn").addEventListener("click", () => probeChannelForm(form));
  renderConfigFields(typeSelect.value);
}

function collectChannelFormData(form) {
  const formData = new FormData(form);
  const type = formData.get("type");
  const config = {};
  const meta = state.metas.find((item) => item.type === type);
  for (const [key, value] of formData.entries()) {
    if (key.startsWith("config.")) {
      const name = key.slice("config.".length);
      const schema = (meta && meta.config_schema[name]) || {};
      if (schema.type === "boolean") {
        config[name] = true;
      } else if (value !== "") {
        config[name] = schema.type === "number" ? Number(value) : value;
      }
    }
  }
  if (meta) {
    for (const [key, schema] of Object.entries(meta.config_schema)) {
      if (schema.type === "boolean" && !formData.has(`config.${key}`)) {
        config[key] = false;
      }
    }
  }
  return {
    name: formData.get("name"),
    type,
    enabled: true,
    default_target: formData.get("default_target") || null,
    config,
    is_emergency: formData.get("is_emergency") === "on",
  };
}

async function probeChannelForm(form) {
  const data = collectChannelFormData(form);
  if (!data.name || !data.type) {
    toast("请先填写名称和渠道类型", "bad");
    return;
  }
  const btn = form.querySelector("#channel-probe-btn");
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "测试中…";
  try {
    const result = await api("/admin/api/channels/probe", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (result.success) {
      toast(`测试成功：${result.detail}`, "ok");
    } else {
      const kindLabel = errorKindLabel(result.error_kind);
      const suffix = kindLabel ? `（${kindLabel}）` : "";
      toast(`测试失败${suffix}：${result.detail}`, "bad");
    }
  } catch (e) {
    toast(`测试请求失败：${e.message}`, "bad");
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

function renderConfigFields(type) {
  const meta = state.metas.find((item) => item.type === type);
  if (!meta) return;
  const container = document.getElementById("config-fields");
  const targetWrap = document.getElementById("default-target-wrap");
  if (meta.target_mode === "external") {
    targetWrap.innerHTML = `
      <label>
        <span>默认目标 ${meta.target_label ? "(" + escapeHtml(meta.target_label) + ")" : ""}</span>
        <input name="default_target" placeholder="${escapeHtml(meta.target_label || "")}" />
      </label>
    `;
  } else {
    targetWrap.innerHTML = "";
  }
  const entries = Object.entries(meta.config_schema);
  const isAdvanced = (s) => typeof s === "object" && s && s.advanced === true;
  const normalFields = entries.filter(([_, s]) => !isAdvanced(s));
  const advancedFields = entries.filter(([_, s]) => isAdvanced(s));

  const renderField = ([key, schema]) => {
    const label = typeof schema === "string" ? schema : schema.label;
    const kind = typeof schema === "string" ? "text" : schema.type || "text";
    const inputType = schema.secret ? "password" : kind === "number" ? "number" : "text";
    const required = schema.required ? "required" : "";
    const value = schema.default !== null && schema.default !== undefined ? `value="${escapeHtml(schema.default)}"` : "";
    if (kind === "boolean") {
      const checked = schema.default ? "checked" : "";
      return `
        <label class="check">
          <input name="config.${escapeHtml(key)}" type="checkbox" ${checked} />
          <span>${escapeHtml(label)}</span>
        </label>
      `;
    }
    return `
      <label>
        <span>${escapeHtml(label)}${schema.required ? " *" : ""}</span>
        <input name="config.${escapeHtml(key)}" type="${inputType}" ${required} ${value} />
      </label>
    `;
  };

  const normalHtml = normalFields.map(renderField).join("");
  const advancedHtml = advancedFields.map(renderField).join("");
  container.innerHTML = normalHtml + (advancedHtml ? `
    <details class="advanced">
      <summary>高级配置（${advancedFields.length} 项，通常可不填）</summary>
      <div class="form">${advancedHtml}</div>
    </details>
  ` : "");
}

async function submitChannelForm(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = collectChannelFormData(form);
  try {
    await api("/admin/api/channels", {
      method: "POST",
      body: JSON.stringify(data),
    });
    toast("渠道已保存");
    closeAddDrawer();
    form.reset();
    await loadAll();
  } catch (e) {
    toast(`保存失败：${e.message}`, "bad");
  }
}

async function handleChannelAction(event) {
  const button = event.currentTarget;
  const action = button.dataset.action;

  if (action === "edit") {
    toggleEditChannel(Number(button.dataset.id));
    return;
  }
  if (action === "cancel-edit") {
    state.editingChannelId = null;
    renderChannelsPage();
    return;
  }
  if (action === "add-type") {
    openAddDrawer(button.dataset.type);
    return;
  }

  const id = Number(button.dataset.id);

  try {
    if (action === "delete") {
      if (!confirm("确认删除这个渠道？")) return;
      await api(`/admin/api/channels/${id}`, { method: "DELETE" });
      toast("已删除");
      await loadAll();
      return;
    }

    if (action === "test") {
      const result = await api(`/admin/api/channels/${id}/test`, { method: "POST" });
      const errLabel = result.success ? "" : `（${errorKindLabel(result.error_kind)}）`;
      alert(`${result.channel_name}：${result.success ? "成功" : "失败"}${errLabel}\n${result.detail}`);
      await loadLogs();
      return;
    }

    if (action === "toggle-enabled") {
      const ch = state.channels.find((x) => x.id === id);
      if (!ch) return;
      await api(`/admin/api/channels/${id}`, {
        method: "PUT",
        body: JSON.stringify({ enabled: !ch.enabled }),
      });
      toast(`已${ch.enabled ? "禁用" : "启用"}`);
      await loadAll();
      return;
    }

    if (action === "toggle-emergency") {
      const ch = state.channels.find((x) => x.id === id);
      if (!ch) return;
      await api(`/admin/api/channels/${id}`, {
        method: "PUT",
        body: JSON.stringify({ is_emergency: !ch.is_emergency }),
      });
      toast(ch.is_emergency ? "已改为常规通道" : "已改为紧急通道");
      await loadAll();
      return;
    }

    if (action === "move-up" || action === "move-down") {
      const direction = action === "move-up" ? "up" : "down";
      await api(`/admin/api/channels/${id}/move?direction=${direction}`, { method: "POST" });
      await loadAll();
      return;
    }
  } catch (e) {
    toast(`操作失败：${e.message}`, "bad");
  }
}

/* ============ 发送测试 ============ */
function renderNotifyChannelPicker() {
  const select = document.getElementById("notify-channel-type");
  if (!select) return;
  const typeMap = new Map();
  for (const c of state.channels) {
    const meta = state.metas.find((m) => m.type === c.type);
    const label = meta ? meta.label : c.type;
    typeMap.set(c.type, label);
  }
  const current = select.value;
  select.innerHTML = Array.from(typeMap.entries())
      .map(([type, label]) => `<option value="${escapeHtml(type)}">${escapeHtml(label)}</option>`)
      .join("");
  if (current && typeMap.has(current)) select.value = current;
  else if (typeMap.size) select.value = typeMap.keys().next().value;
}

async function submitNotifyForm(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const channelType = formData.get("channel_type");
  if (!channelType) {
    toast("请先到「渠道管理」页添加渠道，再进行测试发送", "bad");
    return;
  }
  const payload = {
    title: formData.get("title"),
    content: formData.get("content"),
    content_type: formData.get("content_type"),
    channel_type: channelType,
  };

  try {
    const result = await api("/admin/api/notify", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderNotifyResult(result);
    await loadLogs();
    toast(result.success ? "发送完成" : "发送失败", result.success ? "ok" : "bad");
  } catch (e) {
    toast(`发送失败：${e.message}`, "bad");
  }
}

function renderNotifyResult(result) {
  const container = document.getElementById("notify-result");
  const bannerClass = result.success ? "banner-ok" : "banner-bad";

  const roleText = (role) => {
    if (role === "primary") return "主通道";
    if (role === "backup") return "备用通道";
    if (role === "emergency") return "紧急通道";
    return "";
  };
  const bannerText = result.success
    ? `✓ 投递成功 · 经 ${roleText(result.final_role)}「${escapeHtml(result.final_channel_name || "")}」投递（共尝试 ${result.total_attempts} 个渠道，请求 ID：${result.request_id}）`
    : `✗ 投递失败 · 共尝试 ${result.total_attempts} 个渠道均失败（请求 ID：${result.request_id}）`;
  let escalationBanner = "";
  if (result.escalated) {
    escalationBanner = `<div class="banner banner-warn">⚠ 主通道组全部失败，已升级到紧急通道组（并发发送所有紧急渠道）</div>`;
  }

  const renderStep = (step, idx, showArrow) => {
    const cls = step.success ? "ok" : "bad";
    const arrow = showArrow ? `<span class="chain-arrow">→</span>` : "";
    const role = step.role;
    const errTag = step.success ? "" : errorKindTag(step.error_kind);
    return `${arrow}<span class="chain-step ${cls}"><span class="${tagClassForRole(role)}">${roleLabel(role)}</span>${escapeHtml(step.channel_name)} ${step.success ? "✓" : "✗"}${errTag}</span>`;
  };

  const mainAttempts = result.main_attempts || [];
  const mainHtml = mainAttempts.length
    ? `<div class="chain-steps">${mainAttempts.map((s, i) => renderStep(s, i, i > 0)).join("")}</div>`
    : '<p class="meta">没有匹配到主通道。</p>';

  const emAttempts = result.emergency_attempts || [];
  const emHtml = emAttempts.length
    ? `<div class="chain-steps"><span class="tag tag-emergency">并发</span>${emAttempts.map((s, i) => renderStep(s, i, false)).join(" ")}</div>`
    : "";

  const allSteps = [...mainAttempts, ...emAttempts];
  const lastStep = allSteps[allSteps.length - 1];
  const lastDetailHtml = lastStep
    ? (() => {
        const lastErrLabel = lastStep.success ? "" : errorKindLabel(lastStep.error_kind);
        const detailPrefix = lastErrLabel ? `最后详情（${lastErrLabel}）` : "最后详情";
        return `<p class="meta" style="margin-top:12px;">${detailPrefix}：${escapeHtml(lastStep.detail)}</p>`;
      })()
    : "";

  container.innerHTML = `
    <div class="banner ${bannerClass}">${bannerText}</div>
    ${escalationBanner}
    ${mainHtml}
    ${emHtml}
    ${lastDetailHtml}
  `;
}

/* ============ 设置页 ============ */
async function handleChangeKey(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const newKey = formData.get("new_key");
  const confirmKey = formData.get("confirm_key");
  const err = document.getElementById("change-key-error");

  if (newKey !== confirmKey) {
    err.textContent = "两次输入的新 Key 不一致";
    err.style.display = "flex";
    return;
  }
  if (newKey.length < 12) {
    err.textContent = "新 Key 至少 12 位";
    err.style.display = "flex";
    return;
  }

  try {
    await api("/admin/api/auth/change-key", {
      method: "POST",
      body: JSON.stringify({ new_key: newKey }),
    });
    toast("Key 已更新，请用新 Key 重新登录");
    setApiKey(newKey);
    event.currentTarget.reset();
    setTimeout(() => {
      setApiKey("");
      showLogin();
    }, 1200);
  } catch (e) {
    err.textContent = `修改失败：${e.message}`;
    err.style.display = "flex";
  }
}

/* ============ 抽屉（新增渠道） ============ */
function openAddDrawer(preselectType) {
  document.getElementById("add-drawer").classList.add("show");
  document.getElementById("add-drawer-overlay").classList.add("show");
  renderChannelForm();
  if (typeof preselectType === "string") {
    const form = document.getElementById("channel-form");
    const typeSelect = form && form.querySelector('select[name="type"]');
    if (typeSelect) {
      typeSelect.value = preselectType;
      renderConfigFields(preselectType);
    }
  }
}
function closeAddDrawer() {
  document.getElementById("add-drawer").classList.remove("show");
  document.getElementById("add-drawer-overlay").classList.remove("show");
}

/* ============ 移动端侧边栏 ============ */
function openSidebar() {
  document.getElementById("sidebar").classList.add("open");
  document.getElementById("sidebar-overlay").classList.add("show");
}
function closeSidebar() {
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("sidebar-overlay").classList.remove("show");
}

/* ============ 数据加载 ============ */
async function loadStatus() {
  state.status = await api("/admin/api/status");
}
async function loadChannels() {
  state.channels = await api("/admin/api/channels");
}
async function loadLogs() {
  state.logs = await api("/admin/api/logs");
}
async function loadAll() {
  await Promise.all([loadStatus(), loadChannels(), loadLogs()]);
  if (state.route === "dashboard") renderDashboard();
  if (state.route === "channels") renderChannelsPage();
  if (state.route === "send-test") renderNotifyChannelPicker();
}

/* ============ 启动 ============ */
async function bootstrap() {
  state.metas = await api("/admin/api/channel-types");
  await loadAll();
  navigate("dashboard");
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("login-form").addEventListener("submit", handleLogin);
  document.getElementById("logout-btn").addEventListener("click", handleLogout);
  document.getElementById("refresh-btn").addEventListener("click", async () => {
    try {
      await loadAll();
      toast("已刷新");
    } catch (e) {
      toast(`刷新失败：${e.message}`, "bad");
    }
  });
  document.getElementById("reset-key-btn").addEventListener("click", () => {
    setApiKey("");
    showLogin();
  });
  document.getElementById("change-key-form").addEventListener("submit", handleChangeKey);

  // 移动端侧边栏
  document.getElementById("sidebar-toggle").addEventListener("click", openSidebar);
  document.getElementById("sidebar-overlay").addEventListener("click", closeSidebar);

  // 导航
  document.querySelectorAll(".nav-item[data-route]").forEach((item) => {
    item.addEventListener("click", () => navigate(item.dataset.route));
  });

  // 发送测试表单
  document.getElementById("notify-form").addEventListener("submit", submitNotifyForm);

  // 新增渠道抽屉
  document.getElementById("add-channel-btn").addEventListener("click", openAddDrawer);
  document.getElementById("add-drawer-close").addEventListener("click", closeAddDrawer);
  document.getElementById("add-drawer-overlay").addEventListener("click", closeAddDrawer);

  // 启动时检测 setup 模式
  checkSetupMode().then((setupMode) => {
    if (setupMode) {
      setApiKey("");
      renderLoginView(true);
      showLogin();
      return;
    }
    renderLoginView(false);
    if (getApiKey()) {
      api("/admin/api/auth/verify")
        .then(() => {
          showApp();
          bootstrap().catch((e) => {
            toast(`加载失败：${e.message}`, "bad");
          });
        })
        .catch(() => showLogin());
    } else {
      showLogin();
    }
  });
});
