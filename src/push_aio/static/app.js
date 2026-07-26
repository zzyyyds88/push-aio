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
  if (route === "channels") renderChannelsPage();
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
        return `
          <article class="card">
            <div class="row">
              <strong>${escapeHtml(item.channel_name)}</strong>
              ${roleTag}
              ${successTag}
              <span class="meta">${new Date(item.created_at).toLocaleString()}</span>
            </div>
            <p class="meta">${escapeHtml(item.title)}</p>
          </article>
        `;
      })
      .join("");
  }
}

/* ============ 通知配置页 ============ */
function renderChannelsPage() {
  // 渠道列表
  const container = document.getElementById("channels");
  if (!state.channels.length) {
    container.innerHTML = `<div class="card meta">还没有渠道，先在左侧新增一个。</div>`;
    return;
  }
  container.innerHTML = state.channels
    .map((item) => {
      const meta = state.metas.find((m) => m.type === item.type);
      const label = meta ? meta.label : item.type;
      const backupNames = (item.backup_channel_ids || [])
        .map((id) => {
          const c = state.channels.find((x) => x.id === id);
          return c ? c.name : `#${id}`;
        })
        .map((n) => `<span class="tag backup">${escapeHtml(n)}</span>`)
        .join(" ");
      const isEmergency = item.is_emergency;
      return `
        <article class="card">
          <div class="row">
            <strong>${escapeHtml(item.name)}</strong>
            <span class="tag muted">${escapeHtml(label)}</span>
            <span class="tag ${item.enabled ? "ok" : "bad"}">${item.enabled ? "已启用" : "已禁用"}</span>
            ${isEmergency ? `<span class="tag emergency">紧急</span>` : ""}
            <span class="tag muted">优先级 ${item.priority}</span>
            <span class="meta">#${item.id}</span>
          </div>
          <p class="meta">默认目标：${escapeHtml(item.default_target || "无")}</p>
          <p class="meta">备用组：${backupNames || '<span class="meta">未配置</span>'}</p>
          <div class="row">
            <button type="button" data-action="test" data-id="${item.id}">测试</button>
            <button type="button" class="secondary" data-action="backups" data-id="${item.id}">编辑备用组</button>
            <button type="button" class="secondary" data-action="toggle-emergency" data-id="${item.id}">
              ${isEmergency ? "取消紧急" : "标记紧急"}
            </button>
            <button type="button" class="secondary" data-action="toggle-enabled" data-id="${item.id}">
              ${item.enabled ? "禁用" : "启用"}
            </button>
            <button type="button" class="danger" data-action="delete" data-id="${item.id}">删除</button>
          </div>
        </article>
      `;
    })
    .join("");

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
    <label class="check">
      <input type="checkbox" name="is_emergency" />
      <span>标记为紧急通道（用于全失败升级）</span>
    </label>
    <label>
      <span>优先级（数字越小越先尝试，默认 100）</span>
      <input name="priority" type="number" value="100" min="0" max="1000" />
    </label>
    <button type="submit">保存渠道</button>
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

  const priority = Number(formData.get("priority")) || 100;
  try {
    await api("/admin/api/channels", {
      method: "POST",
      body: JSON.stringify({
        name: formData.get("name"),
        type,
        enabled: true,
        default_target: formData.get("default_target") || null,
        config,
        backup_channel_ids: [],
        is_emergency: formData.get("is_emergency") === "on",
        priority,
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
      alert(`${result.channel_name}：${result.success ? "成功" : "失败"}\n${result.detail}`);
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
      toast(ch.is_emergency ? "已取消紧急标记" : "已标记为紧急");
      await loadAll();
      return;
    }

    if (action === "backups") {
      openBackupModal(id);
    }
  } catch (e) {
    toast(`操作失败：${e.message}`, "bad");
  }
}

/* ============ 备用组编辑模态 ============ */
function openBackupModal(channelId) {
  const channel = state.channels.find((x) => x.id === channelId);
  if (!channel) return;
  const candidates = state.channels.filter((x) => x.id !== channelId);
  const selected = new Set(channel.backup_channel_ids || []);
  const root = document.getElementById("modal-root");
  root.innerHTML = `
    <div class="modal" role="dialog" aria-modal="true">
      <h3>编辑备用组 · ${escapeHtml(channel.name)}</h3>
      <p class="meta">主通道发送失败时，按勾选顺序依次尝试这些通道。</p>
      <div class="check-list">
        ${candidates.map((c) => `
          <label>
            <input type="checkbox" value="${c.id}" ${selected.has(c.id) ? "checked" : ""} />
            <span>${escapeHtml(c.name)} · ${escapeHtml(c.type)} ${c.is_emergency ? '<span class="tag emergency">紧急</span>' : ""}</span>
          </label>
        `).join("")}
      </div>
      <div class="modal-foot">
        <button type="button" class="secondary" data-modal-action="cancel">取消</button>
        <button type="button" data-modal-action="save">保存</button>
      </div>
    </div>
  `;
  root.classList.add("show");
  root.setAttribute("aria-hidden", "false");

  root.querySelectorAll("[data-modal-action]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (btn.dataset.modalAction === "cancel") {
        closeBackupModal();
        return;
      }
      const ids = Array.from(root.querySelectorAll('input[type="checkbox"]:checked')).map(
        (i) => Number(i.value)
      );
      try {
        await api(`/admin/api/channels/${channelId}/backups`, {
          method: "PUT",
          body: JSON.stringify({ backup_channel_ids: ids }),
        });
        toast("备用组已更新");
        closeBackupModal();
        await loadAll();
      } catch (e) {
        toast(`保存失败：${e.message}`, "bad");
      }
    });
  });
}

function closeBackupModal() {
  const root = document.getElementById("modal-root");
  root.classList.remove("show");
  root.setAttribute("aria-hidden", "true");
  root.innerHTML = "";
}

/* ============ 测试发送 ============ */
async function submitNotifyForm(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const channelIds = parseChannelIds(formData.get("channel_ids"));
  const payload = {
    title: formData.get("title"),
    content: formData.get("content"),
    content_type: formData.get("content_type"),
  };
  if (channelIds) payload.channel_ids = channelIds;

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
    escalationBanner = `<div class="banner warn">⚠ 主链全部失败，已自动升级到紧急通道</div>`;
  }

  const chainsHtml = (result.chains || []).map((chain) => {
    const steps = [chain.primary, ...chain.backups];
    const stepsHtml = steps
      .map((step, idx) => {
        const cls = step.success ? "ok" : "bad";
        const arrow = idx > 0 ? `<span class="chain-arrow">→</span>` : "";
        const role = step.role;
        return `${arrow}<span class="chain-step ${cls}"><span class="${tagClassForRole(role)}">${roleLabel(role)}</span>${escapeHtml(step.channel_name)} ${step.success ? "✓" : "✗"}</span>`;
      })
      .join("");
    const headTag = chain.success
      ? `<span class="tag ok">链路成功</span>`
      : `<span class="tag bad">链路失败</span>`;
    const lastDetail = steps[steps.length - 1].detail;
    return `
      <div class="chain">
        <div class="chain-head">
          <strong>${escapeHtml(chain.primary.channel_name)}</strong>
          ${headTag}
        </div>
        <div class="chain-steps">${stepsHtml}</div>
        <div class="chain-detail">最后详情：${escapeHtml(lastDetail)}</div>
      </div>
    `;
  }).join("");

  const emHtml = (result.emergency_attempts || []).length
    ? result.emergency_attempts
        .map((e) => {
          const cls = e.success ? "ok" : "bad";
          return `<div class="chain-step ${cls}"><span class="tag emergency">紧急</span>${escapeHtml(e.channel_name)} ${e.success ? "✓" : "✗"}</div>`;
        })
        .join("")
    : "";

  container.innerHTML = `
    <div class="banner ${bannerClass}">${bannerText}</div>
    ${escalationBanner}
    ${chainsHtml || '<div class="meta">没有匹配到主通道。</div>'}
    ${emHtml ? `<div class="chain-steps" style="margin-top:8px;">${emHtml}</div>` : ""}
  `;
}

/* ============ 系统设置页 ============ */
function renderSettingsPage() {
  const masked = maskKey(getApiKey());
  document.getElementById("settings-key-masked").textContent = masked;
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
  if (state.route === "channels") renderChannelsPage();
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
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      navigate(item.dataset.route);
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
