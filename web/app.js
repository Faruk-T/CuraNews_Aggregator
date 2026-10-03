/**
 * CuraNews web client.
 * Server renders the first headlines for crawlers; this module hydrates the
 * interactive feed, reader modal, account, comments and editor desk.
 */

const BASE = resolveBasePath();
const API_BASE = window.CURANEWS_API_BASE ?? BASE;
const READER_KEY_STORAGE = "curanews_reader_key";
const TOKEN_STORAGE = "curanews_token";
const FEED_LIMIT = 48;
const PAGE_SIZE = 20;
const INITIAL_CHUNK = 12;
const NEXT_CHUNK = 9;

const CATEGORY_IMAGES = {
  ekonomi: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&auto=format&fit=crop",
  teknoloji: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop",
  spor: "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800&auto=format&fit=crop",
  gundem: "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=800&auto=format&fit=crop",
  saglik: "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800&auto=format&fit=crop",
  dunya: "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop",
  politika: "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&auto=format&fit=crop",
};
const CATEGORY_NAMES = {
  gundem: "Gündem",
  ekonomi: "Ekonomi",
  teknoloji: "Teknoloji",
  spor: "Spor",
  saglik: "Sağlık",
  dunya: "Dünya",
  politika: "Politika",
};

const $ = (id) => document.getElementById(id);

const els = {
  openEditorBtn: $("openEditorBtn"),
  prefsToggle: $("prefsToggle"),
  prefsPanel: $("prefsPanel"),
  fontBtns: document.querySelectorAll(".font-btn"),
  themeBtns: document.querySelectorAll(".theme-btn"),
  liveClock: $("liveClock"),
  userProfileBtn: $("userProfileBtn"),
  topbarAvatar: $("topbarAvatar"),
  topbarUserName: $("topbarUserName"),
  topbarUserRole: $("topbarUserRole"),

  breakingBanner: $("breakingBanner"),
  breakingLabel: $("breakingLabel"),
  breakingText: $("breakingText"),
  categoryScroll: $("categoryScroll"),

  sectionKicker: $("sectionKicker"),
  feedHeading: $("feedHeading"),
  feedCount: $("feedCount"),
  searchInput: $("searchInput"),
  refreshBtn: $("refreshBtn"),
  viewAll: $("viewAll"),
  viewBookmarks: $("viewBookmarks"),
  viewRead: $("viewRead"),
  bookmarkCount: $("bookmarkCount"),
  featuredSlot: $("featuredSlot"),
  feedList: $("feedList"),
  sentinel: $("infiniteScrollSentinel"),
  spinner: $("infiniteScrollSpinner"),
  scrollEnd: $("infiniteScrollEnd"),
  skeleton: $("skeleton"),
  emptyState: $("emptyState"),
  toast: $("toast"),

  articleModal: $("articleModal"),
  modalCloseBtn: $("modalCloseBtn"),
  modalSourceLogo: $("modalSourceLogo"),
  modalSourceName: $("modalSourceName"),
  modalPublished: $("modalPublished"),
  modalCategory: $("modalCategory"),
  modalReadTime: $("modalReadTime"),
  modalBookmarkBtn: $("modalBookmarkBtn"),
  modalHeroWrap: $("modalHeroWrap"),
  modalHeroImg: $("modalHeroImg"),
  modalVideoWrap: $("modalVideoWrap"),
  modalVideoIframe: $("modalVideoIframe"),
  modalAuthorBox: $("modalAuthorBox"),
  modalAuthorAvatar: $("modalAuthorAvatar"),
  modalAuthorName: $("modalAuthorName"),
  modalAuthorTitle: $("modalAuthorTitle"),
  modalTitle: $("modalTitle"),
  modalSummary: $("modalSummary"),
  modalContent: $("modalContent"),
  modalAttribution: $("modalAttribution"),
  modalAttributionPublisher: $("modalAttributionPublisher"),
  modalExternalLink: $("modalExternalLink"),
  modalMarkReadBtn: $("modalMarkReadBtn"),
  modalShareBtn: $("modalShareBtn"),
  modalPermalink: $("modalPermalink"),

  commentsCount: $("commentsCount"),
  commentForm: $("commentForm"),
  commentText: $("commentText"),
  commentLoginHint: $("commentLoginHint"),
  commentLoginBtn: $("commentLoginBtn"),
  commentsList: $("commentsList"),

  editorModal: $("editorModal"),
  editorCloseBtn: $("editorCloseBtn"),
  editorCancelBtn: $("editorCancelBtn"),
  editorForm: $("editorForm"),

  profileModal: $("profileModal"),
  profileCloseBtn: $("profileCloseBtn"),
  authView: $("authView"),
  profileView: $("profileView"),
  tabLogin: $("tabLogin"),
  tabRegister: $("tabRegister"),
  authLoginForm: $("authLoginForm"),
  authRegisterForm: $("authRegisterForm"),
  profileAvatar: $("profileAvatar"),
  profileFullName: $("profileFullName"),
  profileEmail: $("profileEmail"),
  profileRoleBadge: $("profileRoleBadge"),
  statReadCount: $("statReadCount"),
  statBookmarkCount: $("statBookmarkCount"),
  interestsContainer: $("interestsContainer"),
  saveInterestsBtn: $("saveInterestsBtn"),
  profileLogoutBtn: $("profileLogoutBtn"),

  policyModal: $("policyModal"),
  policyCloseBtn: $("policyCloseBtn"),
  footerPolicyLink: $("footerPolicyLink"),
  cookieBanner: $("cookieConsentBanner"),
  acceptCookiesBtn: $("acceptCookiesBtn"),
  rejectCookiesBtn: $("rejectCookiesBtn"),
  openPolicyBtn: $("openPolicyBtn"),
};

const state = {
  items: [],
  readItems: [],
  bookmarks: [],
  view: "all",
  category: "",
  graceSeconds: 20 * 60,
  filtered: [],
  rendered: 0,
  remoteOffset: FEED_LIMIT,
  hasMoreRemote: true,
  fetchingMore: false,
  activeArticle: null,
  token: localStorage.getItem(TOKEN_STORAGE),
  user: null,
};

// ---------------------------------------------------------------- utilities

function resolveBasePath() {
  const meta = document.querySelector('meta[name="curanews-base"]');
  if (meta) return meta.content.replace(/\/$/, "");
  const idx = window.location.pathname.indexOf("/ui");
  return idx > 0 ? window.location.pathname.slice(0, idx) : "";
}

function readerKey() {
  let key = localStorage.getItem(READER_KEY_STORAGE);
  if (!key || !/^guest-[a-f0-9]{24}$/.test(key)) {
    const bytes = crypto.getRandomValues(new Uint8Array(12));
    key = `guest-${Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")}`;
    localStorage.setItem(READER_KEY_STORAGE, key);
  }
  return key;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function safeUrl(value, allowed = ["http:", "https:"]) {
  try {
    const url = new URL(value, window.location.href);
    return allowed.includes(url.protocol) ? url.href : "";
  } catch {
    return "";
  }
}

function safeEmbedUrl(value) {
  const url = safeUrl(value, ["https:"]);
  if (!url) return "";
  const host = new URL(url).hostname;
  return host === "www.youtube-nocookie.com" || host === "player.vimeo.com" ? url : "";
}

function pageHref(item) {
  return item.page_path ? `${BASE}/${item.page_path}` : `${BASE}/ui/?haber=${item.id}`;
}

function categoryImage(category) {
  return CATEGORY_IMAGES[(category || "").toLowerCase()] || CATEGORY_IMAGES.gundem;
}

function initials(name) {
  const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  return (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toLocaleUpperCase("tr-TR");
}

function relativeTime(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const minutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000));
  if (minutes < 1) return "az önce";
  if (minutes < 60) return `${minutes} dk önce`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} sa önce`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days} gün önce`;
  return date.toLocaleDateString("tr-TR", { day: "numeric", month: "long", year: "numeric" });
}

function fullDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("tr-TR", { dateStyle: "long", timeStyle: "short" });
}

let toastTimer = null;
function toast(message, kind = "info") {
  clearTimeout(toastTimer);
  els.toast.textContent = message;
  els.toast.dataset.kind = kind;
  els.toast.hidden = false;
  toastTimer = setTimeout(() => {
    els.toast.hidden = true;
  }, kind === "error" ? 6000 : 3000);
}

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function errorMessage(status, detail) {
  if (typeof detail === "string" && detail) return detail;
  if (Array.isArray(detail) && detail.length) return "Lütfen form alanlarını kontrol edin.";
  if (status === 401) return "Bu işlem için giriş yapmanız gerekiyor.";
  if (status === 403) return "Bu işlem için yetkiniz yok.";
  if (status === 429) return "Çok fazla deneme yaptınız, biraz sonra tekrar deneyin.";
  return "Bir sorun oluştu, lütfen tekrar deneyin.";
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(0, "Sunucuya ulaşılamadı. İnternet bağlantınızı kontrol edin.");
  }
  if (!response.ok) {
    let detail = null;
    try {
      detail = (await response.json()).detail;
    } catch {
      /* non-JSON error body */
    }
    if (response.status === 401 && state.token) signOutLocally();
    throw new ApiError(response.status, errorMessage(response.status, detail));
  }
  return response.json();
}

function readerQuery() {
  return state.user ? "" : `user_id=${encodeURIComponent(readerKey())}`;
}

// Images: CSP forbids inline onerror handlers, so fall back via a capturing listener.
document.addEventListener(
  "error",
  (event) => {
    const img = event.target;
    if (!(img instanceof HTMLImageElement) || img.dataset.fallbackApplied) return;
    img.dataset.fallbackApplied = "1";
    if (img.dataset.fallback) {
      img.src = img.dataset.fallback;
    } else {
      img.style.visibility = "hidden";
    }
  },
  true,
);

// ------------------------------------------------------------- preferences

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

function initPreferences() {
  setTheme(localStorage.getItem("curanews_theme") || "dark");
  setFontSize(localStorage.getItem("curanews_font_size") || "md");
  els.themeBtns.forEach((b) => b.addEventListener("click", () => setTheme(b.dataset.theme)));
  els.fontBtns.forEach((b) => b.addEventListener("click", () => setFontSize(b.dataset.size)));

  const close = () => {
    els.prefsPanel.hidden = true;
    els.prefsToggle.setAttribute("aria-expanded", "false");
  };
  els.prefsToggle.addEventListener("click", (e) => {
    e.stopPropagation();
    const open = els.prefsPanel.hidden;
    els.prefsPanel.hidden = !open;
    els.prefsToggle.setAttribute("aria-expanded", String(open));
  });
  els.prefsPanel.addEventListener("click", (e) => e.stopPropagation());
  document.addEventListener("click", close);
  document.addEventListener("keydown", (e) => e.key === "Escape" && close());
}

// ------------------------------------------------------------------ account

function isEditor() {
  return state.user?.role === "editor";
}

function updateAuthUI() {
  const user = state.user;
  els.topbarAvatar.textContent = user ? initials(user.full_name) : "";
  els.topbarAvatar.classList.toggle("is-guest", !user);
  els.topbarUserName.textContent = user ? user.full_name.split(" ")[0] : "Giriş yap";
  els.topbarUserRole.hidden = !isEditor();
  els.openEditorBtn.hidden = !isEditor();

  els.authView.hidden = Boolean(user);
  els.profileView.hidden = !user;
  if (user) {
    els.profileAvatar.textContent = initials(user.full_name);
    els.profileFullName.textContent = user.full_name;
    els.profileEmail.textContent = user.email || "";
    els.profileRoleBadge.textContent = isEditor() ? "Editör" : "Okur";
    els.statReadCount.textContent = String(user.read_count ?? 0);
    els.statBookmarkCount.textContent = String(user.bookmarks_count ?? state.bookmarks.length);
    const chosen = new Set(user.preferences?.categories || []);
    els.interestsContainer.querySelectorAll("input").forEach((input) => {
      input.checked = chosen.has(input.value);
    });
  }

  const loggedIn = Boolean(user);
  els.commentForm.hidden = !loggedIn;
  els.commentLoginHint.hidden = loggedIn;
}

async function initAuth() {
  if (!state.token) return updateAuthUI();
  try {
    state.user = await api("/auth/me");
  } catch {
    signOutLocally();
  }
  updateAuthUI();
}

function signOutLocally() {
  state.token = null;
  state.user = null;
  localStorage.removeItem(TOKEN_STORAGE);
}

async function completeSignIn(res, greeting) {
  state.token = res.access_token;
  state.user = res.user;
  localStorage.setItem(TOKEN_STORAGE, state.token);
  updateAuthUI();
  closeModal(els.profileModal);
  toast(greeting);
  await Promise.all([loadBookmarks(), loadFeed({ quiet: true })]);
}

async function submitLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  try {
    const res = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: $("loginEmail").value.trim(), password: $("loginPassword").value }),
    });
    form.reset();
    await completeSignIn(res, `Hoş geldiniz, ${res.user.full_name.split(" ")[0]}.`);
  } catch (err) {
    toast(err.message, "error");
  } finally {
    button.disabled = false;
  }
}

async function submitRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  try {
    const res = await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name: $("registerName").value.trim(),
        email: $("registerEmail").value.trim(),
        password: $("registerPassword").value,
      }),
    });
    form.reset();
    await completeSignIn(res, "Üyeliğiniz oluşturuldu.");
  } catch (err) {
    toast(err.message, "error");
  } finally {
    button.disabled = false;
  }
}

function logout() {
  signOutLocally();
  updateAuthUI();
  closeModal(els.profileModal);
  toast("Oturum kapatıldı.");
  loadBookmarks();
  loadFeed({ quiet: true });
}

async function saveInterests() {
  const categories = Array.from(els.interestsContainer.querySelectorAll("input:checked"), (i) => i.value);
  try {
    state.user = await api("/auth/me", {
      method: "PUT",
      body: JSON.stringify({ preferences: { ...(state.user?.preferences || {}), categories } }),
    });
    toast("Tercihleriniz kaydedildi.");
  } catch (err) {
    toast(err.message, "error");
  }
}

function switchAuthTab(tab) {
  const login = tab === "login";
  els.tabLogin.classList.toggle("is-active", login);
  els.tabRegister.classList.toggle("is-active", !login);
  els.authLoginForm.hidden = !login;
  els.authRegisterForm.hidden = login;
}

// ------------------------------------------------------------------ modals

let lastFocus = null;

function openModal(modal) {
  lastFocus = document.activeElement;
  modal.hidden = false;
  document.body.classList.add("modal-open");
  modal.querySelector(".modal-close-btn")?.focus();
}

function closeModal(modal) {
  if (modal.hidden) return;
  modal.hidden = true;
  if (![els.articleModal, els.editorModal, els.profileModal, els.policyModal].some((m) => !m.hidden)) {
    document.body.classList.remove("modal-open");
  }
  lastFocus?.focus?.();
}

function wireModal(modal, closeBtn, onClose = () => closeModal(modal)) {
  closeBtn.addEventListener("click", onClose);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) onClose();
  });
}

// --------------------------------------------------------------- bookmarks

function isBookmarked(item) {
  return state.bookmarks.some((b) => b.id === item.id) || Boolean(item.is_bookmarked);
}

function bookmarkLabel(saved, compact = false) {
  if (compact) return saved ? "★" : "☆";
  return saved ? "★ Kaydedildi" : "☆ Kaydet";
}

async function loadBookmarks() {
  try {
    const res = await api(`/bookmarks?${readerQuery()}`);
    state.bookmarks = res.items || [];
  } catch {
    state.bookmarks = [];
  }
  els.bookmarkCount.textContent = String(state.bookmarks.length);
}

async function toggleBookmark(item, button, compact = false) {
  try {
    const res = await api("/bookmarks", {
      method: "POST",
      body: JSON.stringify({ article_id: item.id, user_id: state.user ? null : readerKey() }),
    });
    item.is_bookmarked = res.is_bookmarked;
    await loadBookmarks();
    if (button) {
      button.classList.toggle("is-bookmarked", res.is_bookmarked);
      button.textContent = bookmarkLabel(res.is_bookmarked, compact);
      button.setAttribute("aria-pressed", String(res.is_bookmarked));
    }
    toast(res.is_bookmarked ? "Haber kaydedildi." : "Haber kaydedilenlerden çıkarıldı.");
    if (state.view === "bookmarks") renderFeed();
  } catch (err) {
    toast(err.message, "error");
  }
}

// ------------------------------------------------------------------- reads

function stillOnMainFeed(item) {
  if (!item.read) return true;
  const markedAt = item.read_at ? Date.parse(item.read_at) : NaN;
  if (Number.isNaN(markedAt)) return true;
  return Date.now() - markedAt < state.graceSeconds * 1000;
}

async function markRead(item, button) {
  if (button) {
    button.disabled = true;
  }
  try {
    await api("/reads", {
      method: "POST",
      body: JSON.stringify({ article_id: item.id, user_id: state.user ? null : readerKey(), dwell_ms: 5000 }),
    });
    item.read = true;
    item.read_at = new Date().toISOString();
    if (button) button.textContent = "✓ Okundu";
    toast("Okundu olarak işaretlendi. 20 dakika sonra Okunanlar sekmesine taşınır.");
    loadFeed({ quiet: true, keepScroll: true });
  } catch (err) {
    if (button) button.disabled = false;
    toast(err.message, "error");
  }
}

// ---------------------------------------------------------------- comments

async function loadComments(articleId) {
  els.commentsList.innerHTML = `<p class="comments-empty">Yorumlar yükleniyor…</p>`;
  try {
    const res = await api(`/articles/${articleId}/comments`);
    const comments = res.items || [];
    els.commentsCount.textContent = String(comments.length);
    if (!comments.length) {
      els.commentsList.innerHTML = `<p class="comments-empty">Henüz yorum yok. İlk yorumu siz yazın.</p>`;
      return;
    }
    els.commentsList.replaceChildren(...comments.map(renderComment));
  } catch {
    els.commentsList.innerHTML = `<p class="comments-empty">Yorumlar şu an yüklenemedi.</p>`;
  }
}

function renderComment(c) {
  const card = document.createElement("article");
  card.className = "comment-card";
  card.innerHTML = `
    <header class="comment-card-header">
      <div class="comment-user-info">
        <span class="avatar-initials" aria-hidden="true">${escapeHtml(initials(c.author_name))}</span>
        <span class="comment-author-name">${escapeHtml(c.author_name)}</span>
      </div>
      <time class="comment-time" datetime="${escapeHtml(c.created_at)}">${escapeHtml(relativeTime(c.created_at))}</time>
    </header>
    <p class="comment-card-body">${escapeHtml(c.content)}</p>
    <button type="button" class="comment-like-btn" aria-label="Yorumu beğen">
      <span aria-hidden="true">👍</span> <span class="like-count">${Number(c.likes) || 0}</span>
    </button>`;
  card.querySelector(".comment-like-btn").addEventListener("click", async (event) => {
    if (!state.user) return openAccount("login");
    try {
      const res = await api(`/comments/${c.id}/like`, { method: "POST" });
      event.currentTarget.querySelector(".like-count").textContent = String(res.likes);
    } catch (err) {
      toast(err.message, "error");
    }
  });
  return card;
}

async function submitComment(event) {
  event.preventDefault();
  if (!state.activeArticle) return;
  const content = els.commentText.value.trim();
  if (content.length < 2) return;
  const button = els.commentForm.querySelector("button[type=submit]");
  button.disabled = true;
  try {
    await api(`/articles/${state.activeArticle.id}/comments`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
    els.commentText.value = "";
    toast("Yorumunuz yayımlandı.");
    await loadComments(state.activeArticle.id);
  } catch (err) {
    toast(err.message, "error");
  } finally {
    button.disabled = false;
  }
}

// ------------------------------------------------------------ reader modal

function openArticle(item, { push = true } = {}) {
  state.activeArticle = item;
  trackEvent("article_view", { article_id: item.id, category: item.category, source: item.source_name });

  els.modalTitle.textContent = item.title;
  els.modalSourceName.textContent = item.source_name;
  els.modalAttributionPublisher.textContent = item.source_name;
  els.modalPublished.textContent = fullDate(item.published_at);
  els.modalPublished.dateTime = item.published_at || "";
  els.modalCategory.textContent = item.category_name || "Gündem";
  els.modalReadTime.textContent = `${item.read_time_minutes || 1} dk okuma`;

  const logo = safeUrl(item.source_logo, ["data:", "https:"]);
  els.modalSourceLogo.innerHTML = logo ? `<img src="${escapeHtml(logo)}" alt="" />` : "";

  const fallback = categoryImage(item.category);
  els.modalHeroImg.dataset.fallback = fallback;
  delete els.modalHeroImg.dataset.fallbackApplied;
  els.modalHeroImg.style.visibility = "";
  els.modalHeroImg.src = safeUrl(item.image_url) || fallback;
  els.modalHeroImg.alt = item.title;

  const embed = safeEmbedUrl(item.video_url);
  els.modalVideoWrap.hidden = !embed;
  els.modalVideoIframe.src = embed || "about:blank";

  els.modalAuthorBox.hidden = !item.is_editorial;
  if (item.is_editorial) {
    els.modalAuthorName.textContent = item.author_display || "CuraNews Editörü";
    els.modalAuthorTitle.textContent = item.author_title || "Editör";
    els.modalAuthorAvatar.textContent = initials(item.author_display);
  }

  const summary = (item.summary || "").trim();
  const body = (item.body || "").trim();
  const normalize = (s) => s.replace(/\s+/g, " ").trim();
  let paragraphs = body && normalize(body) !== normalize(summary)
    ? body.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean)
    : [];
  if (paragraphs.length && normalize(paragraphs[0]) === normalize(summary)) paragraphs = paragraphs.slice(1);
  els.modalSummary.textContent = summary;
  els.modalSummary.hidden = !summary;
  els.modalContent.innerHTML = paragraphs.map((p) => `<p>${escapeHtml(p)}</p>`).join("");

  els.modalAttribution.hidden = Boolean(item.is_editorial);
  els.modalExternalLink.href = safeUrl(item.url) || "#";
  els.modalExternalLink.textContent = `Haberin tamamını ${item.source_name} sitesinde okuyun ↗`;
  els.modalPermalink.href = pageHref(item);

  const saved = isBookmarked(item);
  els.modalBookmarkBtn.textContent = bookmarkLabel(saved);
  els.modalBookmarkBtn.classList.toggle("is-bookmarked", saved);
  els.modalBookmarkBtn.onclick = () => toggleBookmark(item, els.modalBookmarkBtn);

  els.modalMarkReadBtn.disabled = Boolean(item.read);
  els.modalMarkReadBtn.textContent = item.read ? "✓ Okundu" : "✓ Okudum";
  els.modalMarkReadBtn.onclick = () => markRead(item, els.modalMarkReadBtn);

  els.modalShareBtn.onclick = async () => {
    const url = new URL(pageHref(item), window.location.origin).href;
    try {
      if (navigator.share && matchMedia("(pointer: coarse)").matches) {
        await navigator.share({ title: item.title, url });
      } else {
        await navigator.clipboard.writeText(url);
        toast("Bağlantı kopyalandı.");
      }
    } catch {
      /* user dismissed the share sheet */
    }
  };

  loadComments(item.id);
  openModal(els.articleModal);
  els.articleModal.querySelector(".modal-body").scrollTop = 0;

  if (push) {
    const url = new URL(window.location.href);
    url.searchParams.set("haber", item.id);
    history.pushState({ haber: item.id }, "", url);
  }
  document.title = `${item.title} | CuraNews`;
}

function closeArticle({ pop = false } = {}) {
  if (els.articleModal.hidden) return;
  closeModal(els.articleModal);
  els.modalVideoIframe.src = "about:blank";
  state.activeArticle = null;
  document.title = "CuraNews — Güncel Haberler, Son Dakika ve Gündem";
  if (!pop) {
    const url = new URL(window.location.href);
    if (url.searchParams.has("haber")) {
      url.searchParams.delete("haber");
      history.pushState({}, "", url);
    }
  }
}

async function openArticleById(id) {
  const known = [...state.items, ...state.readItems, ...state.bookmarks].find((i) => i.id === id);
  if (known) return openArticle(known, { push: false });
  try {
    openArticle(await api(`/articles/${encodeURIComponent(id)}`), { push: false });
  } catch {
    toast("Haber bulunamadı.", "error");
  }
}

// --------------------------------------------------------------- rendering

function itemMatchesFilters(item) {
  if (state.category && (item.category || "").toLowerCase() !== state.category) return false;
  const query = els.searchInput.value.trim().toLocaleLowerCase("tr-TR");
  if (!query) return true;
  return [item.title, item.summary, item.source_name, item.category_name, ...(item.entities || [])]
    .join(" ")
    .toLocaleLowerCase("tr-TR")
    .includes(query);
}

function linkClick(item) {
  return (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button === 1) return;
    event.preventDefault();
    openArticle(item);
  };
}

function imageTag(item, className, eager = false) {
  const fallback = categoryImage(item.category);
  const src = safeUrl(item.image_url) || fallback;
  const loading = eager ? 'fetchpriority="high"' : 'loading="lazy" decoding="async"';
  return `<img src="${escapeHtml(src)}" data-fallback="${escapeHtml(fallback)}" alt="" class="${className}" ${loading} />`;
}

function sourceBadge(item) {
  const logo = safeUrl(item.source_logo, ["data:", "https:"]);
  return logo
    ? `<span class="source-logo-wrap"><img src="${escapeHtml(logo)}" alt="${escapeHtml(item.source_name)}" /></span>`
    : `<span class="badge-cat">${escapeHtml(item.source_name)}</span>`;
}

function renderFeatured(item) {
  const saved = isBookmarked(item);
  els.featuredSlot.hidden = false;
  els.featuredSlot.classList.toggle("is-read", Boolean(item.read));
  els.featuredSlot.innerHTML = `
    <a class="featured-media" href="${escapeHtml(pageHref(item))}" tabindex="-1" aria-hidden="true">${imageTag(item, "featured-img", true)}</a>
    <div class="featured-content">
      <div class="featured-top-line">
        ${sourceBadge(item)}
        <span class="badge-cat">${escapeHtml(item.category_name || "Gündem")}</span>
        <time class="time-read" datetime="${escapeHtml(item.published_at || "")}">${escapeHtml(relativeTime(item.published_at))} · ${item.read_time_minutes || 1} dk okuma</time>
      </div>
      <h2 class="featured-title"><a href="${escapeHtml(pageHref(item))}">${escapeHtml(item.title)}</a></h2>
      <p class="featured-summary">${escapeHtml(item.summary || "")}</p>
      <div class="featured-actions">
        <a class="btn primary" href="${escapeHtml(pageHref(item))}" data-open>Haberi oku</a>
        <button type="button" class="btn secondary" data-bookmark aria-pressed="${saved}">${bookmarkLabel(saved)}</button>
        <button type="button" class="btn ghost" data-read ${item.read ? "disabled" : ""}>${item.read ? "✓ Okundu" : "✓ Okudum"}</button>
      </div>
    </div>`;
  els.featuredSlot.querySelectorAll("a").forEach((a) => a.addEventListener("click", linkClick(item)));
  const bm = els.featuredSlot.querySelector("[data-bookmark]");
  bm.addEventListener("click", () => toggleBookmark(item, bm));
  const rd = els.featuredSlot.querySelector("[data-read]");
  if (!item.read) rd.addEventListener("click", () => markRead(item, rd));
}

function renderCard(item) {
  const li = document.createElement("li");
  li.className = `feed-item${item.read ? " is-read" : ""}`;
  const saved = isBookmarked(item);
  li.innerHTML = `
    <a class="card-media" href="${escapeHtml(pageHref(item))}" tabindex="-1" aria-hidden="true">${imageTag(item, "card-img")}</a>
    <div class="card-body">
      <div class="card-meta-top">
        ${sourceBadge(item)}
        <span class="badge-cat">${escapeHtml(item.category_name || "Gündem")}</span>
      </div>
      <h3 class="card-title"><a href="${escapeHtml(pageHref(item))}">${escapeHtml(item.title)}</a></h3>
      <p class="card-summary">${escapeHtml(item.summary || "")}</p>
      <div class="card-footer">
        <time class="time-read" datetime="${escapeHtml(item.published_at || "")}">${escapeHtml(relativeTime(item.published_at))} · ${item.read_time_minutes || 1} dk</time>
        <div class="card-actions-left">
          <button type="button" class="icon-action${saved ? " is-bookmarked" : ""}" data-bookmark aria-pressed="${saved}" aria-label="Kaydet" title="Kaydet">${bookmarkLabel(saved, true)}</button>
          <button type="button" class="icon-action${item.read ? " is-done" : ""}" data-read ${item.read ? "disabled" : ""} aria-label="Okundu olarak işaretle" title="Okundu olarak işaretle">✓</button>
        </div>
      </div>
    </div>`;
  li.querySelectorAll("a").forEach((a) => a.addEventListener("click", linkClick(item)));
  const bm = li.querySelector("[data-bookmark]");
  bm.addEventListener("click", () => toggleBookmark(item, bm, true));
  const rd = li.querySelector("[data-read]");
  if (!item.read) rd.addEventListener("click", () => markRead(item, rd));
  return li;
}

function sourceItems() {
  if (state.view === "bookmarks") return state.bookmarks;
  if (state.view === "read") return state.readItems;
  return state.items;
}

function renderFeed() {
  state.filtered = sourceItems().filter((item) => {
    if (state.view === "all" && item.read && !stillOnMainFeed(item)) return false;
    return itemMatchesFilters(item);
  });
  state.rendered = 0;
  els.feedList.replaceChildren();
  els.featuredSlot.hidden = true;
  els.scrollEnd.hidden = true;

  const empty = state.filtered.length === 0;
  els.emptyState.hidden = !empty;
  els.emptyState.textContent =
    state.view === "bookmarks"
      ? "Henüz kaydettiğiniz bir haber yok. Kartlardaki ☆ simgesiyle kaydedebilirsiniz."
      : state.view === "read"
        ? "Okundu olarak işaretlediğiniz haberler burada listelenir."
        : "Bu filtreye uygun haber bulunamadı.";

  const heading = state.category ? `${CATEGORY_NAMES[state.category]} haberleri` : "Gündemdeki haberler";
  els.feedHeading.textContent =
    state.view === "bookmarks" ? "Kaydedilenler" : state.view === "read" ? "Okunanlar" : heading;
  els.feedCount.textContent = empty ? "" : `${state.filtered.length} haber`;
  if (empty) return;

  renderFeatured(state.filtered[0]);
  renderNextChunk(INITIAL_CHUNK);
}

function renderNextChunk(size = NEXT_CHUNK) {
  const rest = state.filtered.slice(1);
  const slice = rest.slice(state.rendered, state.rendered + size);
  els.feedList.append(...slice.map(renderCard));
  state.rendered += slice.length;
  const exhausted = state.rendered >= rest.length;
  if (exhausted && (state.view !== "all" || !state.hasMoreRemote || els.searchInput.value.trim())) {
    els.scrollEnd.hidden = rest.length === 0;
  }
}

async function fetchMore() {
  if (state.fetchingMore || !state.hasMoreRemote || state.view !== "all" || els.searchInput.value.trim()) return;
  state.fetchingMore = true;
  els.spinner.hidden = false;
  try {
    const cat = state.category ? `&category=${encodeURIComponent(state.category)}` : "";
    const res = await api(`/articles?offset=${state.remoteOffset}&limit=${PAGE_SIZE}${cat}`);
    const known = new Set(state.items.map((i) => i.id));
    const fresh = (res.items || []).filter((i) => !known.has(i.id));
    state.remoteOffset += PAGE_SIZE;
    if (!res.items?.length) state.hasMoreRemote = false;
    if (fresh.length) {
      state.items.push(...fresh);
      state.filtered.push(...fresh.filter(itemMatchesFilters));
      renderNextChunk(NEXT_CHUNK);
      els.feedCount.textContent = `${state.filtered.length} haber`;
    }
  } catch {
    state.hasMoreRemote = false;
  } finally {
    state.fetchingMore = false;
    els.spinner.hidden = true;
    if (!state.hasMoreRemote) els.scrollEnd.hidden = false;
  }
}

function setupInfiniteScroll() {
  new IntersectionObserver(
    (entries) => {
      if (!entries[0]?.isIntersecting || !state.filtered.length) return;
      if (state.rendered < state.filtered.length - 1) renderNextChunk();
      else fetchMore();
    },
    { rootMargin: "400px" },
  ).observe(els.sentinel);
}

// ----------------------------------------------------------- breaking news

let breakingTimer = null;
function setupBreaking(items) {
  clearInterval(breakingTimer);
  const breaking = items.filter((i) => i.is_breaking);
  const list = breaking.length ? breaking : items.slice(0, 5);
  els.breakingBanner.hidden = !list.length;
  if (!list.length) return;
  els.breakingLabel.textContent = breaking.length ? "SON DAKİKA" : "ÖNE ÇIKAN";
  els.breakingBanner.classList.toggle("is-calm", !breaking.length);
  let index = 0;
  const show = () => {
    const current = list[index % list.length];
    els.breakingText.textContent = current.title;
    els.breakingText.href = pageHref(current);
    els.breakingText.onclick = linkClick(current);
    index += 1;
  };
  show();
  if (list.length > 1) breakingTimer = setInterval(show, 7000);
}

// --------------------------------------------------------------- feed load

async function loadFeed({ quiet = false, keepScroll = false } = {}) {
  const hasContent = state.items.length > 0 || els.feedList.children.length > 0;
  if (!hasContent) {
    els.skeleton.hidden = false;
  }
  els.refreshBtn.disabled = true;
  els.refreshBtn.classList.add("is-spinning");
  const scrollY = window.scrollY;
  try {
    const query = readerQuery();
    const data = await api(`/feed?limit=${FEED_LIMIT}${query ? `&${query}` : ""}`);
    state.items = data.items || [];
    state.readItems = data.read_items || [];
    state.graceSeconds = Number(data.inbox_grace_seconds) || 20 * 60;
    state.remoteOffset = FEED_LIMIT;
    state.hasMoreRemote = true;
    setupBreaking(state.items);
    renderFeed();
    if (keepScroll) window.scrollTo({ top: scrollY });
    if (!quiet) toast("Akış güncellendi.");
  } catch (err) {
    if (!hasContent) {
      els.emptyState.hidden = false;
      els.emptyState.textContent = "Haberler şu an yüklenemedi. Lütfen birazdan tekrar deneyin.";
    }
    toast(err.message, "error");
  } finally {
    els.skeleton.hidden = true;
    els.refreshBtn.disabled = false;
    els.refreshBtn.classList.remove("is-spinning");
  }
}

function setView(view) {
  state.view = view;
  for (const [btn, name] of [[els.viewAll, "all"], [els.viewBookmarks, "bookmarks"], [els.viewRead, "read"]]) {
    btn.classList.toggle("is-active", name === view);
    btn.setAttribute("aria-selected", String(name === view));
  }
  renderFeed();
}

function setCategory(slug, { push = true } = {}) {
  state.category = slug;
  els.categoryScroll.querySelectorAll(".cat-pill").forEach((pill) => {
    const active = (pill.dataset.category || "") === slug;
    pill.classList.toggle("is-active", active);
    if (active) pill.setAttribute("aria-current", "page");
    else pill.removeAttribute("aria-current");
  });
  if (push) {
    const url = new URL(window.location.href);
    if (slug) url.searchParams.set("kategori", slug);
    else url.searchParams.delete("kategori");
    history.replaceState(history.state, "", url);
  }
  state.hasMoreRemote = true;
  state.remoteOffset = FEED_LIMIT;
  if (state.items.length) renderFeed();
}

// ----------------------------------------------------------------- editor

async function submitEditor(event) {
  event.preventDefault();
  const button = els.editorForm.querySelector("button[type=submit]");
  button.disabled = true;
  try {
    const created = await api("/editor/articles", {
      method: "POST",
      body: JSON.stringify({
        title: $("editorTitle").value.trim(),
        category: $("editorCategory").value,
        author_title: $("editorAuthorTitle").value.trim() || "Editör",
        summary: $("editorSummary").value.trim(),
        body: $("editorBody").value.trim(),
        image_url: $("editorImgUrl").value.trim() || null,
        video_url: $("editorVideoUrl").value.trim() || null,
      }),
    });
    state.items.unshift(created);
    els.editorForm.reset();
    closeModal(els.editorModal);
    renderFeed();
    toast("Haber yayımlandı.");
  } catch (err) {
    toast(err.message, "error");
  } finally {
    button.disabled = false;
  }
}

// ------------------------------------------------------- consent & analytics

function gaId() {
  return document.querySelector('meta[name="curanews-ga"]')?.content || "";
}

function trackEvent(name, params = {}) {
  if (typeof window.gtag === "function") window.gtag("event", name, params);
}

function loadAnalytics(id) {
  if (window.gtag) return;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() {
    window.dataLayer.push(arguments);
  };
  window.gtag("js", new Date());
  window.gtag("config", id, { anonymize_ip: true });
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(id)}`;
  document.head.append(script);
}

function initConsent() {
  const id = gaId();
  const consent = localStorage.getItem("curanews_cookie_consent");
  if (!id) return;
  if (consent === "all") return loadAnalytics(id);
  if (consent) return;
  els.cookieBanner.hidden = false;
  els.acceptCookiesBtn.addEventListener("click", () => {
    localStorage.setItem("curanews_cookie_consent", "all");
    els.cookieBanner.hidden = true;
    loadAnalytics(id);
  });
  els.rejectCookiesBtn.addEventListener("click", () => {
    localStorage.setItem("curanews_cookie_consent", "necessary");
    els.cookieBanner.hidden = true;
  });
}

// ------------------------------------------------------------------- init

function openAccount(tab = "login") {
  updateAuthUI();
  if (!state.user) switchAuthTab(tab);
  openModal(els.profileModal);
}

function tickClock() {
  els.liveClock.textContent = new Date().toLocaleDateString("tr-TR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function bindEvents() {
  els.userProfileBtn.addEventListener("click", () => openAccount("login"));
  els.commentLoginBtn.addEventListener("click", () => openAccount("login"));
  els.tabLogin.addEventListener("click", () => switchAuthTab("login"));
  els.tabRegister.addEventListener("click", () => switchAuthTab("register"));
  els.authLoginForm.addEventListener("submit", submitLogin);
  els.authRegisterForm.addEventListener("submit", submitRegister);
  els.profileLogoutBtn.addEventListener("click", logout);
  els.saveInterestsBtn.addEventListener("click", saveInterests);
  els.commentForm.addEventListener("submit", submitComment);
  els.editorForm.addEventListener("submit", submitEditor);
  els.openEditorBtn.addEventListener("click", () => openModal(els.editorModal));
  els.editorCancelBtn.addEventListener("click", () => closeModal(els.editorModal));

  wireModal(els.articleModal, els.modalCloseBtn, () => closeArticle());
  wireModal(els.editorModal, els.editorCloseBtn);
  wireModal(els.profileModal, els.profileCloseBtn);
  wireModal(els.policyModal, els.policyCloseBtn);
  els.footerPolicyLink.addEventListener("click", () => openModal(els.policyModal));
  els.openPolicyBtn.addEventListener("click", () => openModal(els.policyModal));

  window.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (!els.articleModal.hidden) closeArticle();
    [els.editorModal, els.profileModal, els.policyModal].forEach(closeModal);
  });
  window.addEventListener("popstate", () => {
    const id = new URL(window.location.href).searchParams.get("haber");
    if (id) openArticleById(id);
    else closeArticle({ pop: true });
  });

  els.refreshBtn.addEventListener("click", () => loadFeed());
  let searchTimer = null;
  els.searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(renderFeed, 150);
  });
  els.viewAll.addEventListener("click", () => setView("all"));
  els.viewBookmarks.addEventListener("click", () => setView("bookmarks"));
  els.viewRead.addEventListener("click", () => setView("read"));
  els.categoryScroll.querySelectorAll(".cat-pill").forEach((pill) => {
    pill.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey) return;
      event.preventDefault();
      setCategory(pill.dataset.category || "");
    });
  });
}

async function init() {
  initPreferences();
  bindEvents();
  tickClock();
  initConsent();
  setupInfiniteScroll();

  const params = new URL(window.location.href).searchParams;
  const initialCategory = params.get("kategori") || params.get("category") || "";
  if (CATEGORY_NAMES[initialCategory]) setCategory(initialCategory, { push: false });

  await initAuth();
  await Promise.all([loadBookmarks(), loadFeed({ quiet: true })]);

  const deepLink = params.get("haber");
  if (deepLink) openArticleById(deepLink);
}

init();
