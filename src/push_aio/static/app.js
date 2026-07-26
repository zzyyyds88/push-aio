const API_KEY_STORAGE = "push_aio_api_key";

const state = {
  metas: [],
  channels: [],
  status: null,
  logs: [],
  apiKey: localStorage.getItem(API_KEY_STORAGE) || "",
  route: "dashboard",
};

const ROUTE_TITLES = {
  dashboard: "看板",
  channels: "通知配置",
  settings: "系统设置",
};

/* ============ Key 管理 ============ */
function getApiKey() {
  return state.apiKey || localStorage.getItem(API_KEY_STORAGE) || "";
}

function setApiKey(key) {
  state.apiKey = key;
  if (key) localStorage.setItem(API_KEY_STORAGE, key);
  else localStorage.removeItem(API_KEY_STORAGE);
}

function maskKey(key) {
  if (!key) return "****";
  if (key.length <= 8) return "****";
  return `${key.slice(0, 4)}…${key.slice(-4)}`;
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

async function handleLogin(event) {
  event.preventDefault();
  const input = event.currentTarget.key;
  const key = input.value.trim();
  if (!key) return;
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

function handleLogout() {
  setApiKey("");
  showLogin();
}

/* ============ 路由 ============ */
function navigate(route) {
  if (!ROUTE_TITLES[route]) route = "dashboard";
  state.route = route;
  document.querySelectorAll(".page-content").forEach((el) => {
    el.hidden = el.id !== `page-${route}`;
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.route === route);
  });
  document.getElementById("page-title").textContent = ROUTE_TITLES[route];
  if (route === "dashboard") renderDashboard();
  if (route === "channels") { renderChannelsPage(); renderNotifyChannelPicker(); }
  if (route === "settings") renderSettingsPage();
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
  if (role === "backup") return "tag backup";
  if (role === "emergency") return "tag emergency";
  return "tag primary";
}

function roleLabel(role) {
  if (role === "backup") return "备用";
  if (role === "emergency") return "紧急";
  return "主";
}

/* ============ 错误分类标签 ============ */
// 后端 error_kind → 中文标签 + 颜色，用于日志/测试结果展示
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
  // 限流=橙(backup色) / 认证=红(bad色) / 配置=红 / 网络=橙 / 渠道错误=红
  const cls = kind === "rate_limit" || kind === "network"
    ? "tag backup"
    : "tag bad";
  return `<span class="${cls}">${escapeHtml(label)}</span>`;
}

function parseChannelIds(value) {
  if (!value) return null;
  const ids = [];
  for (const part of String(value).split(",")) {
    const n = Number(part.trim());
    if (Number.isInteger(n)) ids.push(n);
  }
  return ids.length ? ids : null;
}

/* ============ 看板页 ============ */
function renderDashboard() {
  if (!state.status) return;
  document.getElementById("stat-online").textContent = state.status.online_count;
  document.getElementById("stat-enabled").textContent = state.status.enabled_count;
  document.getElementById("stat-emergency").textContent = state.status.emergency_count;
  document.getElementById("stat-supported").textContent = state.status.supported_count;

  // 渠道状态概览
  const channelsBox = document.getElementById("dashboard-channels");
  if (!state.channels.length) {
    channelsBox.innerHTML = `<div class="card meta">还没有渠道，前往「通知配置」新增一个。</div>`;
  } else {
    channelsBox.innerHTML = state.channels
      .map((item) => {
        const meta = state.metas.find((m) => m.type === item.type);
        const label = meta ? meta.label : item.type;
        const statusTag = item.enabled
          ? `<span class="tag ok">在线</span>`
          : `<span class="tag muted">已禁用</span>`;
        const emTag = item.is_emergency ? `<span class="tag emergency">紧急</span>` : "";
        return `
          <article class="card">
            <div class="row">
              <strong>${escapeHtml(item.name)}</strong>
              <span class="tag muted">${escapeHtml(label)}</span>
              ${statusTag}
              ${emTag}
              <span class="meta">#${item.id}</span>
            </div>
          </article>
        `;
      })
      .join("");
  }

  // 最近推送（取最近 10 条）
  const logsBox = document.getElementById("dashboard-logs");
  const logs = state.logs.slice(0, 10);
  if (!logs.length) {
    logsBox.innerHTML = `<div class="card meta">暂无发送日志。</div>`;
  } else {
    logsBox.innerHTML = logs
      .map((item) => {
        const roleTag = `<span class="${tagClassForRole(item.role)}">${roleLabel(item.role)}</span>`;
        const successTag = item.success
          ? `<span class="tag ok">成功</span>`
          : `<span class="tag bad">失败</span>`;
        const errTag = item.success ? "" : errorKindTag(item.error_kind);
        return `
          <article class="card">
            <div class="row">
              <strong>${escapeHtml(item.channel_name)}</strong>
              ${roleTag}
              ${successTag}
              ${errTag}
              <span class="meta">${new Date(item.created_at).toLocaleString()}</span>
            </div>
            <p class="meta">${escapeHtml(item.title)}</p>
            ${item.success ? "" : `<p class="meta">详情：${escapeHtml(item.detail)}</p>`}
          </article>
        `;
      })
      .join("");
  }
}

/* ============ 通知配置页 ============ */
function renderChannelsPage() {
  // 渠道列表按"主通道组 / 紧急通道组"分区显示
  const container = document.getElementById("channels");
  if (!state.channels.length) {
    container.innerHTML = `<div class="card meta">还没有渠道，先在左侧新增一个。</div>`;
    return;
  }

  // 按启用状态 + is_emergency 分组；禁用渠道单独一列
  const mainEnabled = state.channels.filter((c) => c.enabled && !c.is_emergency)
    .sort((a, b) => (a.priority - b.priority) || (a.id - b.id));
  const emEnabled = state.channels.filter((c) => c.enabled && c.is_emergency)
    .sort((a, b) => (a.priority - b.priority) || (a.id - b.id));
  const disabled = state.channels.filter((c) => !c.enabled);

  const renderCard = (item, idx, total) => {
    const meta = state.metas.find((m) => m.type === item.type);
    const label = meta ? meta.label : item.type;
    const isEmergency = item.is_emergency;
    const orderTag = `<span class="tag muted">第 ${idx + 1} 顺位</span>`;
    const upDisabled = idx === 0 ? "disabled" : "";
    const downDisabled = idx === total - 1 ? "disabled" : "";
    return `
      <article class="card">
        <div class="row">
          <strong>${escapeHtml(item.name)}</strong>
          <span class="tag muted">${escapeHtml(label)}</span>
          <span class="tag ok">已启用</span>
          ${isEmergency ? `<span class="tag emergency">紧急</span>` : ""}
          ${orderTag}
          <span class="meta">#${item.id}</span>
        </div>
        <p class="meta">默认目标：${escapeHtml(item.default_target || "无")}</p>
        <div class="row">
          <button type="button" data-action="test" data-id="${item.id}">测试</button>
          <button type="button" class="secondary" data-action="move-up" data-id="${item.id}" ${upDisabled}>上移</button>
          <button type="button" class="secondary" data-action="move-down" data-id="${item.id}" ${downDisabled}>下移</button>
          <button type="button" class="secondary" data-action="toggle-emergency" data-id="${item.id}">
            ${isEmergency ? "改为常规" : "改为紧急"}
          </button>
          <button type="button" class="secondary" data-action="toggle-enabled" data-id="${item.id}">禁用</button>
          <button type="button" class="danger" data-action="delete" data-id="${item.id}">删除</button>
        </div>
      </article>
    `;
  };

  const renderDisabledCard = (item) => {
    const meta = state.metas.find((m) => m.type === item.type);
    const label = meta ? meta.label : item.type;
    return `
      <article class="card">
        <div class="row">
          <strong>${escapeHtml(item.name)}</strong>
          <span class="tag muted">${escapeHtml(label)}</span>
          <span class="tag bad">已禁用</span>
          ${item.is_emergency ? `<span class="tag emergency">紧急</span>` : ""}
          <span class="meta">#${item.id}</span>
        </div>
        <div class="row">
          <button type="button" data-action="toggle-enabled" data-id="${item.id}">启用</button>
          <button type="button" class="danger" data-action="delete" data-id="${item.id}">删除</button>
        </div>
      </article>
    `;
  };

  let html = "";
  if (mainEnabled.length) {
    html += `<h3 class="group-title">主通道组（按顺序逐个尝试）</h3>`;
    html += mainEnabled.map((item, idx) => renderCard(item, idx, mainEnabled.length)).join("");
  }
  if (emEnabled.length) {
    html += `<h3 class="group-title">紧急通道组（主通道全失败后升级）</h3>`;
    html += emEnabled.map((item, idx) => renderCard(item, idx, emEnabled.length)).join("");
  }
  if (disabled.length) {
    html += `<h3 class="group-title">已禁用渠道</h3>`;
    html += disabled.map(renderDisabledCard).join("");
  }
  if (!mainEnabled.length && !emEnabled.length && !disabled.length) {
    html = `<div class="card meta">还没有渠道，先在左侧新增一个。</div>`;
  }

  container.innerHTML = html;
  container.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", handleChannelAction);
  });
}

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
    <div id="default-target-wrap" class="form"></div>
    <div id="config-fields" class="form"></div>
    <button type="submit">保存渠道</button>
    <p class="meta">新建渠道默认加入主通道组末尾。需要作为兜底紧急通道时，在右侧渠道列表用"改为紧急"按钮切换。</p>
  `;

  const typeSelect = form.querySelector('select[name="type"]');
  typeSelect.addEventListener("change", () => renderConfigFields(typeSelect.value));
  form.addEventListener("submit", submitChannelForm);
  renderConfigFields(typeSelect.value);
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
  const requiredFields = entries.filter(([_, s]) => s && s.required);
  const optionalFields = entries.filter(([_, s]) => !s || !s.required);

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

  const requiredHtml = requiredFields.map(renderField).join("");
  const optionalHtml = optionalFields.map(renderField).join("");
  container.innerHTML = requiredHtml + (optionalHtml ? `
    <details class="advanced">
      <summary>高级配置（${optionalFields.length} 项，通常可不填）</summary>
      <div class="form">${optionalHtml}</div>
    </details>
  ` : "");
}

async function submitChannelForm(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const type = formData.get("type");
  const config = {};
  for (const [key, value] of formData.entries()) {
    if (key.startsWith("config.")) {
      const name = key.slice("config.".length);
      const schema = state.metas.find((item) => item.type === type).config_schema[name] || {};
      if (schema.type === "boolean") {
        config[name] = true;
      } else if (value !== "") {
        config[name] = schema.type === "number" ? Number(value) : value;
      }
    }
  }

  const meta = state.metas.find((item) => item.type === type);
  for (const [key, schema] of Object.entries(meta.config_schema)) {
    if (schema.type === "boolean" && !formData.has(`config.${key}`)) {
      config[key] = false;
    }
  }

  try {
    await api("/admin/api/channels", {
      method: "POST",
      body: JSON.stringify({
        name: formData.get("name"),
        type,
        enabled: true,
        default_target: formData.get("default_target") || null,
        config,
        is_emergency: formData.get("is_emergency") === "on",
      }),
    });
    toast("渠道已保存");
    event.currentTarget.reset();
    renderConfigFields(type);
    await loadAll();
  } catch (e) {
    toast(`保存失败：${e.message}`, "bad");
  }
}

async function handleChannelAction(event) {
  const button = event.currentTarget;
  const id = Number(button.dataset.id);
  const action = button.dataset.action;

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

/* ============ 测试发送 ============ */
function renderNotifyChannelPicker() {
  // 渲染测试发送的渠道多选列表（默认折叠，不勾选=走全自动调度）
  const container = document.getElementById("notify-channel-picker");
  if (!container) return;
  if (!state.channels.length) {
    container.innerHTML = `<p class="meta">还没有渠道可测试</p>`;
    return;
  }
  container.innerHTML = state.channels
    .map((c) => {
      const meta = state.metas.find((m) => m.type === c.type);
      const label = meta ? meta.label : c.type;
      const emTag = c.is_emergency ? `<span class="tag emergency">紧急</span>` : "";
      const enTag = c.enabled
        ? `<span class="tag ok">启用</span>`
        : `<span class="tag bad">禁用</span>`;
      return `
        <label>
          <input type="checkbox" value="${c.id}" data-pick="1" />
          <span>${escapeHtml(c.name)} · ${escapeHtml(label)} ${enTag} ${emTag}</span>
        </label>
      `;
    })
    .join("");
}

async function submitNotifyForm(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = {
    title: formData.get("title"),
    content: formData.get("content"),
    content_type: formData.get("content_type"),
  };
  // 读取勾选的渠道 ID；未勾选则不传 channel_ids，走全自动调度
  const picker = document.getElementById("notify-channel-picker");
  if (picker) {
    const checked = Array.from(picker.querySelectorAll('input[data-pick="1"]:checked'))
      .map((i) => Number(i.value));
    if (checked.length) payload.channel_ids = checked;
  }

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
  const bannerClass = result.success ? "ok" : "bad";
  const bannerText = result.success
    ? `✓ 整体投递成功（请求 ID：${result.request_id}）`
    : `✗ 整体投递失败（请求 ID：${result.request_id}）`;
  let escalationBanner = "";
  if (result.escalated) {
    escalationBanner = `<div class="banner warn">⚠ 主通道组全部失败，已自动升级到紧急通道组</div>`;
  }

  // 渲染单条尝试步骤
  const renderStep = (step, idx, total, showArrow) => {
    const cls = step.success ? "ok" : "bad";
    const arrow = showArrow ? `<span class="chain-arrow">→</span>` : "";
    const role = step.role;
    const errTag = step.success ? "" : errorKindTag(step.error_kind);
    return `${arrow}<span class="chain-step ${cls}"><span class="${tagClassForRole(role)}">${roleLabel(role)}</span>${escapeHtml(step.channel_name)} ${step.success ? "✓" : "✗"}${errTag}</span>`;
  };

  // 主通道组：一条链
  const mainAttempts = result.main_attempts || [];
  const mainHtml = mainAttempts.length
    ? `<div class="chain-steps">${mainAttempts.map((s, i) => renderStep(s, i, mainAttempts.length, i > 0)).join("")}</div>`
    : '<div class="meta">没有匹配到主通道。</div>';

  // 紧急通道组
  const emAttempts = result.emergency_attempts || [];
  const emHtml = emAttempts.length
    ? `<div class="chain-steps" style="margin-top:8px;">${emAttempts.map((s, i) => renderStep(s, i, emAttempts.length, i > 0)).join("")}</div>`
    : "";

  // 最后一条尝试的详情
  const allSteps = [...mainAttempts, ...emAttempts];
  const lastStep = allSteps[allSteps.length - 1];
  const lastDetailHtml = lastStep
    ? (() => {
        const lastErrLabel = lastStep.success ? "" : errorKindLabel(lastStep.error_kind);
        const detailPrefix = lastErrLabel ? `最后详情（${lastErrLabel}）` : "最后详情";
        return `<div class="chain-detail">${detailPrefix}：${escapeHtml(lastStep.detail)}</div>`;
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

/* ============ 系统设置页 ============ */
function renderSettingsPage() {
  // 重置错误提示
  const err = document.getElementById("change-key-error");
  err.style.display = "none";
  err.textContent = "";
  const form = document.getElementById("change-key-form");
  if (form) form.reset();
}

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
    // 用新 Key 更新本地存储，避免立即跳登录后还在用旧 Key
    setApiKey(newKey);
    event.currentTarget.reset();
    // 短暂延迟后跳登录页（强制重新输入，确认新 Key 已记住）
    setTimeout(() => {
      setApiKey("");
      showLogin();
    }, 1200);
  } catch (e) {
    err.textContent = `修改失败：${e.message}`;
    err.style.display = "flex";
  }
}

/* ============ 移动端侧边栏抽屉 ============ */
function openSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");
  sidebar.classList.add("open");
  overlay.classList.add("show");
  overlay.setAttribute("aria-hidden", "false");
}

function closeSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");
  sidebar.classList.remove("open");
  overlay.classList.remove("show");
  overlay.setAttribute("aria-hidden", "true");
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
  // 刷新当前页
  if (state.route === "dashboard") renderDashboard();
  if (state.route === "channels") { renderChannelsPage(); renderNotifyChannelPicker(); }
  if (state.route === "settings") renderSettingsPage();
}

/* ============ 启动 ============ */
async function bootstrap() {
  state.metas = await api("/admin/api/channel-types");
  renderChannelForm();
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

  // 移动端侧边栏抽屉
  document.getElementById("sidebar-toggle").addEventListener("click", openSidebar);
  document.getElementById("sidebar-close").addEventListener("click", closeSidebar);
  document.getElementById("sidebar-overlay").addEventListener("click", closeSidebar);

  document.querySelectorAll(".nav-item[data-route]").forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      navigate(item.dataset.route);
      // 移动端点击后自动收起侧边栏
      if (window.innerWidth <= 768) closeSidebar();
    });
  });
  // 通知配置页的测试发送表单
  document.getElementById("notify-form").addEventListener("submit", submitNotifyForm);

  // 已有 Key 则尝试登录，否则显示登录页
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
