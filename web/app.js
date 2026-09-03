/**
 * CuraNews Web App (Day 21 — Bundle Edition)
 * Features:
 * - Bundle.app Category Tabs & Breaking News Ticker
 * - In-Site Article Modal Reader with Hotlinked Hero Images & Attribution
 * - Civil Servant & Senior Reader Mode (Font Scaling + Sepya / High Contrast Themes)
 * - Sponsored Ads Integration (Leaderboard + In-Feed Native Cards)
 * - Real-time Filtering, Search, and Read Status
 */

const API_BASE = window.CURANEWS_API_BASE || "";

const els = {
  // Navigation & Preferences
  topAdWrap: document.getElementById("topAdWrap"),
  topAdClose: document.getElementById("topAdClose"),
  categoryScroll: document.getElementById("categoryScroll"),
  liveClock: document.getElementById("liveClock"),
  fontBtns: document.querySelectorAll(".font-btn"),
  themeBtns: document.querySelectorAll(".theme-btn"),

  // Breaking Ticker
  breakingBanner: document.getElementById("breakingBanner"),
  breakingText: document.getElementById("breakingText"),
  breakingOpenBtn: document.getElementById("breakingOpenBtn"),

  // Desk Controls
  userSelect: document.getElementById("userSelect"),
  searchInput: document.getElementById("searchInput"),
  refreshBtn: document.getElementById("refreshBtn"),
  topicCloud: document.getElementById("topicCloud"),
  topicSelect: document.getElementById("topicSelect"),

  // Feed Views
  feedHeading: document.getElementById("feedHeading"),
  sectionKicker: document.getElementById("sectionKicker"),
  feedCount: document.getElementById("feedCount"),
  viewAll: document.getElementById("viewAll"),
  viewRead: document.getElementById("viewRead"),
  featuredSlot: document.getElementById("featuredSlot"),
  feedList: document.getElementById("feedList"),
  skeleton: document.getElementById("skeleton"),
  emptyState: document.getElementById("emptyState"),
  status: document.getElementById("status"),
  error: document.getElementById("error"),
  cacheBadge: document.getElementById("cacheBadge"),

  // In-Site Reader Modal
  articleModal: document.getElementById("articleModal"),
  modalCloseBtn: document.getElementById("modalCloseBtn"),
  modalDismissBtn: document.getElementById("modalDismissBtn"),
  modalSourceLogo: document.getElementById("modalSourceLogo"),
  modalSourceName: document.getElementById("modalSourceName"),
  modalPublished: document.getElementById("modalPublished"),
  modalCategory: document.getElementById("modalCategory"),
  modalReadTime: document.getElementById("modalReadTime"),
  modalHeroWrap: document.getElementById("modalHeroWrap"),
  modalHeroImg: document.getElementById("modalHeroImg"),
  modalTitle: document.getElementById("modalTitle"),
  modalSummary: document.getElementById("modalSummary"),
  modalContent: document.getElementById("modalContent"),
  modalAttributionPublisher: document.getElementById("modalAttributionPublisher"),
  modalExternalLink: document.getElementById("modalExternalLink"),
  modalMarkReadBtn: document.getElementById("modalMarkReadBtn"),
  modalShareBtn: document.getElementById("modalShareBtn"),
};

// Application State
let latestItems = [];
let readItems = [];
let topics = [];
let breakingItems = [];
let currentBreakingIndex = 0;
let breakingInterval = null;
let activeModalArticle = null;

let selectedCategory = "";
let feedView = "all";
let inboxGraceSeconds = 20 * 60;

const PERSONAS = {
  "demo-user-a": { name: "Ada", desk: "Ada’nın Masası", desc: "Ekonomi · Teknoloji · Yapay Zeka" },
  "demo-user-b": { name: "Deniz", desk: "Deniz’in Masası", desc: "Spor · Gündem · Çevre" },
};

// ========================================================
// THEME & ACCESSIBILITY (FONT SCALE & SEPYA/MEMUR MODU)
// ========================================================
function initAccessibility() {
  const savedTheme = localStorage.getItem("curanews_theme") || "dark";
  const savedFontSize = localStorage.getItem("curanews_font_size") || "md";

  setTheme(savedTheme);
  setFontSize(savedFontSize);

  els.themeBtns.forEach((btn) => {
    btn.addEventListener("click", () => setTheme(btn.dataset.theme));
  });

  els.fontBtns.forEach((btn) => {
    btn.addEventListener("click", () => setFontSize(btn.dataset.size));
  });

  if (els.topAdClose) {
    els.topAdClose.addEventListener("click", () => {
      els.topAdWrap.style.display = "none";
    });
  }
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("curanews_theme", theme);
  els.themeBtns.forEach((b) => b.classList.toggle("is-active", b.dataset.theme === theme));
}

function setFontSize(size) {
  document.documentElement.dataset.fontSize = size;
  localStorage.setItem("curanews_font_size", size);
  els.fontBtns.forEach((b) => b.classList.toggle("is-active", b.dataset.size === size));
}

// ========================================================
// API CLIENT
// ========================================================
async function api(path, options = {}) {
  const url = `${API_BASE}${path}`;
  let response;
  try {
    response = await fetch(url, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
  } catch {
    throw new Error("API'ye ulaşılamıyor. Sunucuyu `poetry run python scripts/run_api.py` ile başlatın.");
  }
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`API hatası (${response.status}): ${detail || response.statusText}`);
  }
  return response.json();
}

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

// ========================================================
// DATE & FORMATTING HELPERS
// ========================================================
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

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

// ========================================================
// SON DAKİKA (BREAKING NEWS) TICKER
// ========================================================
function setupBreakingTicker(items) {
  breakingItems = items.filter((item) => {
    if (item.is_breaking) return true;
    const title = (item.title || "").toLowerCase();
    return title.includes("son dakika") || title.includes("flaş") || title.includes("acil");
  });

  if (breakingInterval) clearInterval(breakingInterval);

  if (!breakingItems.length) {
    // If no breaking news detected, use the latest 3 items as highlight ticker
    breakingItems = items.slice(0, 4);
  }

  if (breakingItems.length) {
    els.breakingBanner.hidden = false;
    currentBreakingIndex = 0;
    updateBreakingHeadline();
    breakingInterval = setInterval(() => {
      currentBreakingIndex = (currentBreakingIndex + 1) % breakingItems.length;
      updateBreakingHeadline();
    }, 6500);
  }
}

function updateBreakingHeadline() {
  if (!breakingItems.length) return;
  const current = breakingItems[currentBreakingIndex];
  els.breakingText.textContent = current.title;
  els.breakingText.onclick = () => openArticleModal(current);
  els.breakingOpenBtn.onclick = () => openArticleModal(current);
}

// ========================================================
// SITE İÇİ HABER DETAY MODALİ (IN-SITE READER)
// ========================================================
function openArticleModal(item) {
  activeModalArticle = item;
  els.modalTitle.textContent = item.title;
  els.modalSummary.textContent = item.summary || "";

  // Publisher info and logo
  els.modalSourceName.textContent = item.source_name;
  els.modalAttributionPublisher.textContent = item.source_name;
  els.modalExternalLink.href = item.url;

  if (item.source_logo) {
    els.modalSourceLogo.innerHTML = `<img src="${item.source_logo}" alt="${escapeHtml(item.source_name)}" />`;
  } else {
    els.modalSourceLogo.innerHTML = "";
  }

  els.modalPublished.textContent = relativeTime(item.published_at) || formatPublished(item.published_at);
  els.modalCategory.textContent = item.category_name || "Gündem";
  els.modalReadTime.textContent = `${item.read_time_minutes || 1} dk okuma`;

  // Hero image
  if (item.image_url) {
    els.modalHeroWrap.hidden = false;
    els.modalHeroImg.src = item.image_url;
    els.modalHeroImg.onerror = () => {
      els.modalHeroWrap.hidden = true;
    };
  } else {
    els.modalHeroWrap.hidden = true;
  }

  // Multi-paragraph body rendering
  const fullText = item.body || item.summary || "";
  const paragraphs = fullText
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);

  if (paragraphs.length) {
    els.modalContent.innerHTML = paragraphs.map((p) => `<p>${escapeHtml(p)}</p>`).join("");
  } else {
    els.modalContent.innerHTML = `<p>${escapeHtml(item.summary || "Bu haberin detaylı metni kaynak bağlantısında yer almaktadır.")}</p>`;
  }

  // Update read button
  if (item.read) {
    els.modalMarkReadBtn.textContent = "✓ Okundu Olarak İşaretlendi";
    els.modalMarkReadBtn.disabled = true;
  } else {
    els.modalMarkReadBtn.textContent = "Okundu Olarak İşaretle";
    els.modalMarkReadBtn.disabled = false;
    els.modalMarkReadBtn.onclick = async () => {
      await markRead(item.id, els.modalMarkReadBtn);
      item.read = true;
      els.modalMarkReadBtn.textContent = "✓ Okundu";
      els.modalMarkReadBtn.disabled = true;
    };
  }

  // Share button
  els.modalShareBtn.onclick = () => {
    navigator.clipboard?.writeText(item.url);
    showStatus("Haber bağlantısı panoya kopyalandı!");
    setTimeout(() => showStatus(""), 3000);
  };

  els.articleModal.hidden = false;
  document.body.style.overflow = "hidden";
}

function closeArticleModal() {
  els.articleModal.hidden = true;
  document.body.style.overflow = "";
  activeModalArticle = null;
}

els.modalCloseBtn.addEventListener("click", closeArticleModal);
els.modalDismissBtn.addEventListener("click", closeArticleModal);
els.articleModal.addEventListener("click", (e) => {
  if (e.target === els.articleModal) closeArticleModal();
});
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !els.articleModal.hidden) closeArticleModal();
});

// ========================================================
// FEED FILTERING & RENDERING
// ========================================================
function itemMatchesFilters(item) {
  // Category tab filter
  if (selectedCategory) {
    const itemCat = (item.category || "").toLowerCase();
    if (itemCat !== selectedCategory.toLowerCase()) {
      return false;
    }
  }

  // Search filter
  const query = els.searchInput.value.trim().toLowerCase();
  if (query) {
    const haystack = [item.title, item.summary, item.source_name, item.category_name, ...(item.entities || [])]
      .join(" ")
      .toLowerCase();
    if (!haystack.includes(query)) return false;
  }

  // Topic filter
  const topic = els.topicSelect.value.trim().toLowerCase();
  if (topic) {
    const haystack = [item.title, item.summary, ...(item.entities || [])].join(" ").toLowerCase();
    if (!haystack.includes(topic)) return false;
  }

  return true;
}

function renderFeatured(item) {
  els.featuredSlot.hidden = false;
  els.featuredSlot.classList.toggle("is-read", Boolean(item.read));

  const imgHtml = item.image_url
    ? `<div class="featured-media"><img src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.title)}" class="featured-img" onerror="this.parentElement.hidden=true;" /></div>`
    : `<div class="featured-media" style="background:linear-gradient(135deg,#1f2937,#111827);display:grid;place-items:center;color:var(--muted);"><span style="font-size:3rem;">📰</span></div>`;

  const logoHtml = item.source_logo
    ? `<span class="source-logo-wrap"><img src="${item.source_logo}" alt="${escapeHtml(item.source_name)}" /></span>`
    : `<span class="badge-cat">${escapeHtml(item.source_name)}</span>`;

  els.featuredSlot.innerHTML = `
    ${imgHtml}
    <div class="featured-content">
      <div class="featured-top-line">
        ${logoHtml}
        <span class="badge-cat">${escapeHtml(item.category_name || "Gündem")}</span>
        <span class="time-read">${relativeTime(item.published_at)} · ${item.read_time_minutes || 1} dk okuma</span>
      </div>
      <h3 class="featured-title"><a href="javascript:void(0)">${escapeHtml(item.title)}</a></h3>
      <p class="featured-summary">${escapeHtml(item.summary || "Haberin detayları için tıklayınız.")}</p>
      <div class="featured-actions">
        <button type="button" class="btn primary btn-open-feature">Haberi Oku</button>
        <a class="btn secondary" href="${item.url}" target="_blank" rel="noopener">Kaynağa Git ↗</a>
        <button type="button" class="btn ghost btn-mark-feature">${item.read ? "✓ Okundu" : "Okundu İşaretle"}</button>
      </div>
    </div>
  `;

  els.featuredSlot.querySelector(".featured-title a").onclick = () => openArticleModal(item);
  els.featuredSlot.querySelector(".btn-open-feature").onclick = () => openArticleModal(item);

  const markBtn = els.featuredSlot.querySelector(".btn-mark-feature");
  if (markBtn && !item.read) {
    markBtn.onclick = () => markRead(item.id, markBtn);
  }
}

function renderCard(item, index) {
  const li = document.createElement("li");
  li.className = `feed-item${item.read ? " is-read" : ""}`;

  const imgHtml = item.image_url
    ? `<div class="card-media"><img src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.title)}" class="card-img" onerror="this.parentElement.hidden=true;" /></div>`
    : "";

  const logoHtml = item.source_logo
    ? `<span class="source-logo-wrap"><img src="${item.source_logo}" alt="${escapeHtml(item.source_name)}" /></span>`
    : `<span class="badge-cat">${escapeHtml(item.source_name)}</span>`;

  li.innerHTML = `
    ${imgHtml}
    <div class="card-body">
      <div class="card-meta-top">
        ${logoHtml}
        <span class="badge-cat">${escapeHtml(item.category_name || "Gündem")}</span>
        <span class="time-read">${relativeTime(item.published_at)}</span>
      </div>
      <h3 class="card-title">${escapeHtml(item.title)}</h3>
      <p class="card-summary">${escapeHtml(item.summary || "Özet yok.")}</p>
      <div class="card-footer">
        <div class="card-actions-left">
          <button type="button" class="btn-read-modal">Haberi Oku</button>
          <button type="button" class="btn-mark-read">${item.read ? "✓" : "Okundu"}</button>
        </div>
        <span class="time-read">${item.read_time_minutes || 1} dk okuma</span>
      </div>
    </div>
  `;

  li.querySelector(".card-title").onclick = () => openArticleModal(item);
  li.querySelector(".btn-read-modal").onclick = () => openArticleModal(item);

  const markBtn = li.querySelector(".btn-mark-read");
  if (markBtn && !item.read) {
    markBtn.onclick = () => markRead(item.id, markBtn);
  }

  return li;
}

function renderSponsoredCard() {
  const li = document.createElement("li");
  li.className = "feed-item is-sponsored";
  li.innerHTML = `
    <div class="card-body">
      <div class="card-meta-top">
        <span class="sponsored-badge">SPONSORLU</span>
        <span class="time-read">Tanıtım</span>
      </div>
      <h3 class="card-title">CuraNews Pro: Tarafsız ve Hızlı Haber Toplayıcı</h3>
      <p class="card-summary">En seçkin Türk ve dünya haber kaynaklarını tek ekranda toplayan yeni nesil haber masası deneyimi.</p>
      <div class="card-footer">
        <button type="button" class="btn-read-modal" style="background:var(--accent);color:#082823;">İncele →</button>
      </div>
    </div>
  `;
  return li;
}

function renderFeed() {
  const items = feedView === "read" ? readItems : latestItems;
  const filtered = items.filter((item) => {
    if (feedView === "all" && item.read && !stillOnMainFeed(item)) return false;
    if (feedView === "read" && !item.read) return false;
    return itemMatchesFilters(item);
  });

  els.feedList.innerHTML = "";
  els.featuredSlot.hidden = true;
  els.emptyState.hidden = filtered.length > 0;

  const readCount = (readItems.length ? readItems : items).filter((i) => i.read).length;
  els.feedCount.textContent = filtered.length
    ? `${filtered.length} haber görünür · ${readCount} okundu`
    : "0 haber";

  if (!filtered.length) return;

  // Render first item as featured
  renderFeatured(filtered[0]);

  // Render remaining cards, inserting a sponsored card at index 5
  filtered.slice(1).forEach((item, index) => {
    if (index === 4) {
      els.feedList.appendChild(renderSponsoredCard());
    }
    els.feedList.appendChild(renderCard(item, index + 1));
  });
}

function stillOnMainFeed(item) {
  if (!item.read) return true;
  const markedAt = item.read_at ? Date.parse(item.read_at) : NaN;
  if (Number.isNaN(markedAt)) return true;
  return Date.now() - markedAt < inboxGraceSeconds * 1000;
}

// ========================================================
// CATEGORIES NAVIGATION (BUNDLE.APP STYLE)
// ========================================================
function setupCategoryNavbar() {
  const pills = els.categoryScroll.querySelectorAll(".cat-pill");
  pills.forEach((pill) => {
    pill.addEventListener("click", () => {
      pills.forEach((p) => p.classList.remove("is-active"));
      pill.classList.add("is-active");
      selectedCategory = pill.dataset.category || "";
      renderFeed();
    });
  });
}

// ========================================================
// FEED LOADER & ACTIONS
// ========================================================
async function loadFeed(options = {}) {
  const quiet = Boolean(options.quiet);
  clearError();
  if (!quiet) showStatus("Haber masası güncelleniyor…");
  setLoading(true);
  els.refreshBtn.disabled = true;

  try {
    const userId = els.userSelect.value;
    const data = await api(`/feed?user_id=${encodeURIComponent(userId)}&limit=48`);
    latestItems = data.items || [];
    readItems = data.read_items || latestItems.filter((i) => i.read);
    inboxGraceSeconds = Number(data.inbox_grace_seconds) || 20 * 60;

    const cache = data.cache || "—";
    els.cacheBadge.textContent = `cache · ${cache}`;
    els.cacheBadge.dataset.state = cache;

    setupBreakingTicker(latestItems);
    renderFeed();

    if (!quiet) {
      const persona = PERSONAS[userId]?.name || userId;
      showStatus(
        latestItems.length
          ? `${latestItems.length} haber kürate edildi · ${persona} profili aktif`
          : "Akış hazır. Yeni haberleri çekmek için `poetry run python scripts/refresh_news.py` çalıştırın."
      );
    }
  } catch (err) {
    latestItems = [];
    readItems = [];
    els.feedList.innerHTML = "";
    els.featuredSlot.hidden = true;
    showError(err.message || String(err));
  } finally {
    setLoading(false);
    els.refreshBtn.disabled = false;
  }
}

async function markRead(articleId, button) {
  clearError();
  if (button) {
    button.disabled = true;
    button.textContent = "Kaydediliyor…";
  }

  try {
    await api("/reads", {
      method: "POST",
      body: JSON.stringify({
        user_id: els.userSelect.value,
        article_id: articleId,
        dwell_ms: 5000,
      }),
    });
    await loadFeed({ quiet: true });
    showStatus("Haber okundu olarak kaydedildi.");
    setTimeout(() => showStatus(""), 2500);
  } catch (err) {
    showError(err.message || String(err));
    if (button) {
      button.disabled = false;
      button.textContent = "Okundu";
    }
  }
}

function syncPersonas() {
  const current = els.userSelect.value;
  document.querySelectorAll(".persona").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.user === current);
  });
  const persona = PERSONAS[current];
  if (persona) {
    els.feedHeading.textContent = persona.desk;
    els.sectionKicker.textContent = `Bundle Akışı · ${persona.desc}`;
  }
}

function tickClock() {
  els.liveClock.textContent = new Date().toLocaleTimeString("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ========================================================
// INITIALIZATION
// ========================================================
function init() {
  initAccessibility();
  setupCategoryNavbar();

  els.refreshBtn.addEventListener("click", () => loadFeed());
  els.userSelect.addEventListener("change", () => {
    syncPersonas();
    loadFeed();
  });
  els.searchInput.addEventListener("input", () => renderFeed());
  els.topicSelect.addEventListener("change", () => renderFeed());

  els.viewAll.addEventListener("click", () => {
    feedView = "all";
    els.viewAll.classList.add("is-active");
    els.viewRead.classList.remove("is-active");
    renderFeed();
  });

  els.viewRead.addEventListener("click", () => {
    feedView = "read";
    els.viewRead.classList.add("is-active");
    els.viewAll.classList.remove("is-active");
    renderFeed();
  });

  document.querySelectorAll(".persona").forEach((btn) => {
    btn.addEventListener("click", () => {
      els.userSelect.value = btn.dataset.user;
      syncPersonas();
      loadFeed();
    });
  });

  tickClock();
  setInterval(tickClock, 1000);

  syncPersonas();
  loadFeed();
}

init();
