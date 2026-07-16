const state = { dashboard: null, mapFilter: "全部", chatSession: null, sosTimer: null };

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

async function request(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `请求失败：${response.status}`);
  }
  return response.json();
}

function jsonOptions(payload) {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) };
}

function showPanel(name) {
  $$("[data-panel-content]").forEach((panel) => panel.classList.toggle("active", panel.dataset.panelContent === name));
  $$(".safety-nav [data-panel]").forEach((button) => button.classList.toggle("active", button.dataset.panel === name));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { element.hidden = true; }, 3500);
}

async function loadDashboard() {
  state.dashboard = await request("/api/safety/dashboard");
  const status = state.dashboard.campus_status;
  $("#campusStatus").textContent = `校园状态：${status.level}（演示）`;
  $("#statusLevel").textContent = status.level;
  $("#statusSource").textContent = status.source;
  renderNotices();
  renderFacilities();
  renderClasses();
  renderReports();
  renderTrips();
  renderLostFound();
}

function renderNotices() {
  const notices = state.dashboard?.notices || [];
  const markup = notices.map((notice) => `<article class="notice-card ${escapeHtml(notice.level)}"><strong>${escapeHtml(notice.title)}</strong><p>${escapeHtml(notice.action)}</p><small>${escapeHtml(notice.department)} · 有效期：${escapeHtml(notice.valid_until)}</small></article>`).join("");
  $("#overviewNotices").innerHTML = markup;
  $("#noticeList").innerHTML = markup;
}

const pinPositions = [{ left: "47%", top: "18%" }, { left: "70%", top: "40%" }, { left: "30%", top: "67%" }, { left: "69%", top: "71%" }];
function renderFacilities() {
  const all = state.dashboard?.facilities || [];
  const facilities = state.mapFilter === "全部" ? all : all.filter((item) => item.type === state.mapFilter);
  $("#facilityList").innerHTML = facilities.map((item) => `<article class="facility-card"><span class="tag">${escapeHtml(item.type)}</span><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.area)} · ${escapeHtml(item.status)}</p><small>${escapeHtml(item.phone)}</small></article>`).join("") || '<div class="empty-state">当前图层暂无设施</div>';
  $("#mapPins").innerHTML = all.map((item, index) => {
    const visible = state.mapFilter === "全部" || item.type === state.mapFilter;
    const pos = pinPositions[index % pinPositions.length];
    return `<span class="map-pin" style="left:${pos.left};top:${pos.top};${visible ? "" : "display:none"}" title="${escapeHtml(item.name)}"><b>${escapeHtml(item.type.slice(0, 1))}</b></span>`;
  }).join("");
}

function renderClasses() {
  $("#classList").innerHTML = (state.dashboard?.classes || []).map((item) => `<article class="class-card"><span class="tag">${escapeHtml(item.topic)}</span><h2>${escapeHtml(item.title)}</h2><ol>${item.steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ol><button class="secondary-action class-complete" type="button">完成学习</button></article>`).join("");
  $$(".class-complete").forEach((button) => button.addEventListener("click", () => { button.textContent = "已完成"; button.disabled = true; toast("学习记录已保存在当前浏览器"); }));
}

function renderReports() {
  const rows = state.dashboard?.reports || [];
  $("#reportList").innerHTML = rows.length ? rows.map((item) => `<article class="record-card"><header><strong>${escapeHtml(item.category)}</strong><span class="tag">${escapeHtml(item.status)}</span></header><p>${escapeHtml(item.description)}</p><small>${escapeHtml(item.id)} · ${escapeHtml(item.location)} · ${escapeHtml(item.urgency)}</small></article>`).join("") : '<div class="empty-state">暂无安全工单</div>';
}

function renderTrips() {
  const rows = state.dashboard?.trips || [];
  $("#tripList").innerHTML = rows.length ? rows.map((item) => `<article class="record-card"><header><strong>前往 ${escapeHtml(item.destination)}</strong><span class="tag">${escapeHtml(item.status)}</span></header><p>联系人：${escapeHtml(item.contact)} · 预计 ${item.duration_minutes} 分钟</p><small>${escapeHtml(item.id)}</small>${item.status === "守护中" ? `<button class="arrive-button" data-arrive="${escapeHtml(item.id)}">我已安全到达</button>` : ""}</article>`).join("") : '<div class="empty-state">暂无守护行程</div>';
  $$('[data-arrive]').forEach((button) => button.addEventListener("click", async () => {
    await request(`/api/safety/trips/${encodeURIComponent(button.dataset.arrive)}/arrive`, { method: "POST" });
    toast("行程已结束，已标记安全到达"); await loadDashboard();
  }));
}

function renderLostFound() {
  const rows = state.dashboard?.lost_found || [];
  $("#lostList").innerHTML = rows.length ? rows.map((item) => `<article class="record-card"><header><strong>${escapeHtml(item.item_type)} · ${escapeHtml(item.category)}</strong><span class="tag">${escapeHtml(item.status)}</span></header><p>${escapeHtml(item.description)}</p><small>${escapeHtml(item.area)} · ${escapeHtml(item.id)}</small></article>`).join("") : '<div class="empty-state">暂无失物招领信息</div>';
}

function formPayload(form) { return Object.fromEntries(new FormData(form).entries()); }

function bindForms() {
  $("#reportForm").addEventListener("submit", async (event) => {
    event.preventDefault(); const form = event.currentTarget; const result = $("#reportResult"); result.textContent = "正在提交…";
    try { const data = await request("/api/safety/reports", jsonOptions(formPayload(form))); result.textContent = `提交成功，工单号：${data.id}`; form.reset(); await loadDashboard(); }
    catch (error) { result.textContent = error.message; }
  });
  $("#tripForm").addEventListener("submit", async (event) => {
    event.preventDefault(); const form = event.currentTarget; const payload = formPayload(form); payload.duration_minutes = Number(payload.duration_minutes); const result = $("#tripResult"); result.textContent = "正在创建…";
    try { const data = await request("/api/safety/trips", jsonOptions(payload)); result.textContent = `守护已开始：${data.id}（原型不会发送真实通知）`; form.reset(); await loadDashboard(); }
    catch (error) { result.textContent = error.message; }
  });
  $("#lostForm").addEventListener("submit", async (event) => {
    event.preventDefault(); const form = event.currentTarget; const result = $("#lostResult"); result.textContent = "正在发布…";
    try { const data = await request("/api/safety/lost-found", jsonOptions(formPayload(form))); result.textContent = `发布成功：${data.id}，等待核验`; form.reset(); await loadDashboard(); }
    catch (error) { result.textContent = error.message; }
  });
  $("#sosForm").addEventListener("submit", async (event) => {
    event.preventDefault(); const result = $("#sosResult"); result.textContent = "正在保存演示求助记录…";
    try {
      const data = await request("/api/safety/sos", jsonOptions(formPayload(event.currentTarget)));
      result.innerHTML = `<strong>${escapeHtml(data.status)}</strong><br>编号：${escapeHtml(data.id)}<br>${escapeHtml(data.message)}<br><button class="secondary-action" id="cancelSosRecord" type="button">10秒内标记为误触</button>`;
      $("#cancelSosRecord").addEventListener("click", async () => { const cancelled = await request(`/api/safety/sos/${encodeURIComponent(data.id)}/cancel`, { method: "POST" }); result.textContent = `${cancelled.id}：${cancelled.status}`; });
    } catch (error) { result.textContent = error.message; }
  });
}

function bindSos() {
  const button = $("#sosButton");
  const start = (event) => { event.preventDefault(); button.classList.add("holding"); state.sosTimer = setTimeout(() => { button.classList.remove("holding"); $("#sosModal").hidden = false; }, 2000); };
  const stop = () => { clearTimeout(state.sosTimer); button.classList.remove("holding"); };
  button.addEventListener("pointerdown", start); button.addEventListener("pointerup", stop); button.addEventListener("pointerleave", stop); button.addEventListener("pointercancel", stop);
  button.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") $("#sosModal").hidden = false; });
  $("#closeSos").addEventListener("click", () => { $("#sosModal").hidden = true; });
  $("#sosModal").addEventListener("click", (event) => { if (event.target === event.currentTarget) event.currentTarget.hidden = true; });
  $("#locateButton").addEventListener("click", () => {
    if (!navigator.geolocation) return toast("当前浏览器不支持定位");
    $("#locateButton").textContent = "正在定位…";
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => { $("#sosLocation").value = `${coords.latitude.toFixed(6)}, ${coords.longitude.toFixed(6)}`; $("#locateButton").textContent = "定位已获取"; },
      () => { $("#locateButton").textContent = "定位失败，请手动填写"; }, { enableHighAccuracy: true, timeout: 8000 }
    );
  });
}

function bindChat() {
  $$(".prompt-row button").forEach((button) => button.addEventListener("click", () => { $("#safetyInput").value = button.textContent; $("#safetyInput").focus(); }));
  $("#safetyChatForm").addEventListener("submit", async (event) => {
    event.preventDefault(); const input = $("#safetyInput"); const message = input.value.trim(); if (!message) return; input.value = "";
    const messages = $("#safetyMessages"); messages.insertAdjacentHTML("beforeend", `<div class="user-message">${escapeHtml(message)}</div><div class="bot-message pending">正在判断风险并整理行动建议…</div>`); messages.scrollTop = messages.scrollHeight;
    const pending = $(".pending", messages);
    try { const data = await request("/api/chat", jsonOptions({ mode: "safety", message, session_id: state.chatSession })); state.chatSession = data.session_id; pending.textContent = data.answer; }
    catch (error) { pending.textContent = `暂时无法获取建议：${error.message}。现实紧急危险请立即拨打110、119或120。`; }
    pending.classList.remove("pending"); messages.scrollTop = messages.scrollHeight;
  });
}

function bindNavigation() {
  $$("[data-panel]").forEach((button) => button.addEventListener("click", () => showPanel(button.dataset.panel)));
  $$('[data-go]').forEach((button) => button.addEventListener("click", () => showPanel(button.dataset.go)));
  $$("#mapFilters button").forEach((button) => button.addEventListener("click", () => { state.mapFilter = button.dataset.filter; $$("#mapFilters button").forEach((item) => item.classList.toggle("active", item === button)); renderFacilities(); }));
}

async function init() {
  bindNavigation(); bindForms(); bindSos(); bindChat();
  try { await loadDashboard(); } catch (error) { toast(`安全数据加载失败：${error.message}`); $("#campusStatus").textContent = "服务暂不可用"; }
}

init();
