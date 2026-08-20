const API_BASE = window.CURANEWS_API_BASE || "";

const els = {
  userSelect: document.getElementById("userSelect"),
  topicSelect: document.getElementById("topicSelect"),
  topicCloud: document.getElementById("topicCloud"),
  searchInput: document.getElementById("searchInput"),
  refreshBtn: document.getElementById("refreshBtn"),
  feedList: document.getElementById("feedList"),
  featuredSlot: document.getElementById("featuredSlot"),
  emptyState: document.getElementById("emptyState"),
  cacheBadge: document.getElementById("cacheBadge"),
  status: document.getElementById("status"),
  error: document.getElementById("error"),
  skeleton: document.getElementById("skeleton"),
  feedCount: document.getElementById("feedCount"),
  feedHeading: document.getElementById("feedHeading"),
  liveClock: document.getElementById("liveClock"),
  viewAll: document.getElementById("viewAll"),
  viewRead: document.getElementById("viewRead"),
};

let latestItems = [];
let readItems = [];
let topics = [];
let feedView = "all";
let inboxGraceSeconds = 20 * 60;

const PERSONAS = {
  "demo-user-a": { name: "Ada", desk: "Ada’nın masası" },
  "demo-user-b": { name: "Deniz", desk: "Deniz’in masası" },
};

function showError(message) {
  els.error.hidden = false;
  els.error.textContent = message;
}

function clearError() {
  els.error.hidden = true;
  els.error.textContent = "";
}

function showStatus(message) {
  els.status.hidden = !message;
  els.status.textContent = message || "";
}

function setLoading(isLoading) {
  els.skeleton.hidden = !isLoading;
  if (isLoading) {
    els.feedList.innerHTML = "";
    els.featuredSlot.hidden = true;
    els.emptyState.hidden = true;
  }
}

async function api(path, options = {}) {
  const url = `${API_BASE}${path}`;
  let response;
  try {
    response = await fetch(url, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
  } catch {
    throw new Error(
      "API'ye ulaşılamıyor. Sunucuyu `poetry run python scripts/run_api.py` ile başlatın."
    );
  }
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`API hatası (${response.status}): ${detail || response.statusText}`);
  }
  return response.json();
}

function itemMatchesFilters(item) {
  const topic = els.topicSelect.value.trim().toLowerCase();
  const query = els.searchInput.value.trim().toLowerCase();
  const hay = [item.title, item.summary, item.source_name, item.category, ...(item.entities || [])]
    .join(" ")
    .toLowerCase();
  if (topic && !hay.includes(topic) && !(item.category || "").toLowerCase().includes(topic)) {
    return false;
  }
  if (query && !hay.includes(query)) return false;
  return true;
}

function relativeTime(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const delta = Date.now() - date.getTime();
  const minutes = Math.round(delta / 60000);
  if (minutes < 1) return "şimdi";
  if (minutes < 60) return `${minutes} dk önce`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} sa önce`;
  const days = Math.round(hours / 24);
  return `${days} gün önce`;
}

function formatPublished(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("tr-TR", { dateStyle: "medium", timeStyle: "short" });
}

const NOISE_TAGS = /^(devamı|devami|okunma|yorum|world|general|news|topic|gundem|gündem)$/i;

function entityLabel(raw) {
  const text = String(raw || "");
  return text.includes(":") ? text.split(":").slice(1).join(":") : text;
}

function isUsefulLabel(label, title) {
  const value = String(label || "").trim();
  if (value.length < 3 || value.length > 28) return false;
  if (NOISE_TAGS.test(value)) return false;
  if (/^\d+$/.test(value)) return false;
  if (title && value.length > 18 && title.toLowerCase().includes(value.toLowerCase())) return false;
  return true;
}

function categoryLabel(raw) {
  const key = String(raw || "").toLowerCase();
  const map = {
    sports: "Spor",
    sport: "Spor",
    world: "",
    general: "",
    turkey: "Türkiye",
    economy: "Ekonomi",
    tech: "Teknoloji",
    technology: "Teknoloji",
  };
  if (key in map) return map[key];
  return raw;
}

function cardMeta(item) {
  const source = escapeHtml(item.source_name || "kaynak");
  const when = relativeTime(item.published_at) || formatPublished(item.published_at);
  const category = categoryLabel(item.category);
  const tags = (item.entities || [])
    .map(entityLabel)
    .filter((label) => isUsefulLabel(label, item.title))
    .slice(0, 2)
    .map((tag) => `<span class="pill">${escapeHtml(tag)}</span>`)
    .join("");
  return `
    <p class="meta-line">
      <span class="pill">${source}</span>
      ${category ? `<span class="pill">${escapeHtml(category)}</span>` : ""}
      ${when ? `<span>${escapeHtml(when)}</span>` : ""}
      ${tags}
    </p>
  `;
}

function readButton(item) {
  if (item.read) {
    return `<button type="button" class="btn success" disabled>Okundu</button>`;
  }
  return `<button type="button" class="btn primary" data-id="${item.id}">Okundu işaretle</button>`;
}

function renderFeatured(item, index) {
  els.featuredSlot.hidden = false;
  els.featuredSlot.classList.remove("is-leaving");
  els.featuredSlot.classList.toggle("is-read", Boolean(item.read));
  els.featuredSlot.innerHTML = `
    <p class="featured-rank">${item.read ? "Okundu" : "Öne çıkan"}</p>
    <h3 class="featured-title">
      <a href="${item.url}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a>
    </h3>
    <p class="featured-summary">${escapeHtml(item.summary || "Özet yok.")}</p>
    <div class="featured-actions">
      ${cardMeta(item)}
      <a class="btn ghost" href="${item.url}" target="_blank" rel="noopener">Habere git</a>
      ${readButton(item)}
    </div>
  `;
  const markBtn = els.featuredSlot.querySelector("button.primary");
  if (markBtn) {
    markBtn.addEventListener("click", (event) => markRead(item.id, event.currentTarget));
  }
}

function renderCard(item, index) {
  const li = document.createElement("li");
  li.className = `feed-item${item.read ? " is-read" : ""}`;
  li.style.animationDelay = `${index * 0.06}s`;
  li.innerHTML = `
    <div class="feed-rank">${item.read ? "Okundu" : `Haber ${index + 1}`}</div>
    <h3 class="feed-title">
      <a href="${item.url}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a>
    </h3>
    <p class="feed-summary">${escapeHtml(item.summary || "Özet yok.")}</p>
    <div class="feed-footer">
      ${cardMeta(item)}
      <div class="feed-actions">
        <a class="btn quiet" href="${item.url}" target="_blank" rel="noopener">Habere git</a>
        ${readButton(item)}
      </div>
    </div>
  `;
  const markBtn = li.querySelector("button.primary");
  if (markBtn) {
    markBtn.addEventListener("click", () => markRead(item.id, markBtn));
  }
  return li;
}

function stillOnMainFeed(item) {
  if (!item.read) return true;
  const markedAt = item.read_at ? Date.parse(item.read_at) : NaN;
  if (Number.isNaN(markedAt)) return true;
  return Date.now() - markedAt < inboxGraceSeconds * 1000;
}

function sourceItems() {
  return feedView === "read" ? readItems : latestItems;
}

function renderFeed() {
  const items = sourceItems();
  const filtered = items.filter((item) => {
    if (feedView === "all" && !stillOnMainFeed(item)) return false;
    if (feedView === "read" && !item.read) return false;
    return itemMatchesFilters(item);
  });
  els.feedList.innerHTML = "";
  els.featuredSlot.hidden = true;
  els.featuredSlot.classList.remove("is-leaving", "is-read");
  els.featuredSlot.innerHTML = "";
  els.emptyState.hidden = filtered.length > 0;
  els.emptyState.textContent =
    feedView === "read"
      ? "Henüz okunan haber yok. Akışta bir haberi yeşil yapmak için Okundu işaretle."
      : "Bu filtreye uygun haber yok. Konuyu veya aramayı temizle.";
  const readCount = (readItems.length ? readItems : items).filter((item) => item.read).length;
  els.feedCount.textContent = filtered.length
    ? `${filtered.length} haber görünür · ${readCount} okundu`
    : "0 haber";

  if (!filtered.length) return;

  renderFeatured(filtered[0], 0);
  filtered.slice(1).forEach((item, index) => {
    els.feedList.appendChild(renderCard(item, index + 1));
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderTopicCloud() {
  els.topicCloud.innerHTML = "";
  const all = document.createElement("button");
  all.type = "button";
  all.className = `chip${els.topicSelect.value ? "" : " is-active"}`;
  all.textContent = "Tümü";
  all.addEventListener("click", () => setTopic(""));
  els.topicCloud.appendChild(all);

  for (const topic of topics) {
    const label = entityLabel(topic.label);
    if (!isUsefulLabel(label, "")) continue;
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `chip${els.topicSelect.value === topic.normalized ? " is-active" : ""}`;
    chip.textContent = `${label} · ${topic.article_count}`;
    chip.addEventListener("click", () => setTopic(topic.normalized));
    els.topicCloud.appendChild(chip);
    if (els.topicCloud.children.length >= 11) break;
  }
}

function setTopic(value) {
  els.topicSelect.value = value;
  renderTopicCloud();
  renderFeed();
}

function syncPersonas() {
  const current = els.userSelect.value;
  document.querySelectorAll(".persona").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.user === current);
  });
  const persona = PERSONAS[current];
  if (persona) els.feedHeading.textContent = persona.desk;
}

async function loadTopics() {
  try {
    const data = await api("/topics?limit=30");
    topics = data.items || [];
    const current = els.topicSelect.value;
    els.topicSelect.innerHTML = `<option value="">Tümü</option>`;
    for (const topic of topics) {
      const opt = document.createElement("option");
      opt.value = topic.normalized;
      opt.textContent = `${topic.label} (${topic.article_count})`;
      els.topicSelect.appendChild(opt);
    }
    els.topicSelect.value = current;
    renderTopicCloud();
  } catch {
    renderTopicCloud();
  }
}

async function loadFeed(options = {}) {
  const quiet = Boolean(options.quiet);
  clearError();
  if (!quiet) showStatus("Masa kuruluyor…");
  setLoading(true);
  els.refreshBtn.disabled = true;
  try {
    const userId = els.userSelect.value;
    const data = await api(`/feed?user_id=${encodeURIComponent(userId)}&limit=36`);
    latestItems = data.items || [];
    readItems = data.read_items || latestItems.filter((item) => item.read);
    inboxGraceSeconds = Number(data.inbox_grace_seconds) || 20 * 60;
    const cache = data.cache || "—";
    els.cacheBadge.textContent = `cache · ${cache}`;
    els.cacheBadge.dataset.state = cache;
    renderFeed();
    if (!quiet) {
      showStatus(
        latestItems.length
          ? `${latestItems.length} haber kürate edildi · ${PERSONAS[userId]?.name || userId}`
          : "Akış boş — Docker açık mı? `poetry run python scripts/refresh_news.py` çalıştırın."
      );
    }
  } catch (err) {
    latestItems = [];
    readItems = [];
    els.feedList.innerHTML = "";
    els.featuredSlot.hidden = true;
    els.emptyState.hidden = true;
    els.cacheBadge.textContent = "cache · —";
    els.cacheBadge.dataset.state = "";
    if (!quiet) showStatus("");
    showError(err.message || String(err));
  } finally {
    setLoading(false);
    els.refreshBtn.disabled = false;
  }
}

async function markRead(articleId, button) {
  clearError();
  button.disabled = true;
  const previous = button.textContent;
  const card = button.closest(".feed-item, .featured");
  const title = card?.querySelector("h3")?.textContent?.trim() || "haber";
  button.textContent = "Kaydediliyor…";
  try {
    await api("/reads", {
      method: "POST",
      body: JSON.stringify({
        user_id: els.userSelect.value,
        article_id: articleId,
        dwell_ms: 5000,
      }),
    });
    await loadTopics();
    await loadFeed({ quiet: true });
    showStatus(`Okundu: «${title}». 20 dakika ana akışta yeşil kalır, sonra Okunanlar’a geçer.`);
  } catch (err) {
    showError(err.message || String(err));
    button.disabled = false;
    button.textContent = previous;
  }
}

function tickClock() {
  els.liveClock.textContent = new Date().toLocaleTimeString("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

els.refreshBtn.addEventListener("click", loadFeed);
els.userSelect.addEventListener("change", () => {
  syncPersonas();
  loadFeed();
});
els.topicSelect.addEventListener("change", () => renderFeed());
els.searchInput.addEventListener("input", () => renderFeed());

function setFeedView(view) {
  feedView = view;
  els.viewAll.classList.toggle("is-active", view === "all");
  els.viewRead.classList.toggle("is-active", view === "read");
  renderFeed();
}

els.viewAll.addEventListener("click", () => setFeedView("all"));
els.viewRead.addEventListener("click", () => setFeedView("read"));

document.querySelectorAll(".persona").forEach((button) => {
  button.addEventListener("click", () => {
    els.userSelect.value = button.dataset.user;
    syncPersonas();
    loadFeed();
  });
});

tickClock();
setInterval(tickClock, 1000);
setInterval(() => {
  if (feedView === "all" && latestItems.some((item) => item.read)) {
    renderFeed();
  }
}, 30000);
syncPersonas();
await loadTopics();
await loadFeed();
