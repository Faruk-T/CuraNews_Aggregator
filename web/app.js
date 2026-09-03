/**
 * CuraNews Web App (Day 22 — Community & Editorial Edition)
 * Features:
 * - User Authentication, JWT Session & Profiles
 * - Bookmarks / Favorites Management
 * - In-Site Reader Article Comments & Likes
 * - Onedio-style Editor CMS Panel with Author Box & Video Embed
 * - Bundle.app Category Tabs & Breaking News Ticker
 * - Civil Servant & Senior Reader Mode (Font Scaling + Sepya / High Contrast Themes)
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

  // Topbar Auth & Editor Buttons
  openEditorBtn: document.getElementById("openEditorBtn"),
  userProfileBtn: document.getElementById("userProfileBtn"),
  topbarAvatar: document.getElementById("topbarAvatar"),
  topbarUserName: document.getElementById("topbarUserName"),
  topbarUserRole: document.getElementById("topbarUserRole"),

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
  viewBookmarks: document.getElementById("viewBookmarks"),
  bookmarkCount: document.getElementById("bookmarkCount"),
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
  modalBookmarkBtn: document.getElementById("modalBookmarkBtn"),
  modalHeroWrap: document.getElementById("modalHeroWrap"),
  modalHeroImg: document.getElementById("modalHeroImg"),
  modalVideoWrap: document.getElementById("modalVideoWrap"),
  modalVideoIframe: document.getElementById("modalVideoIframe"),
  modalAuthorBox: document.getElementById("modalAuthorBox"),
  modalAuthorAvatar: document.getElementById("modalAuthorAvatar"),
  modalAuthorName: document.getElementById("modalAuthorName"),
  modalAuthorTitle: document.getElementById("modalAuthorTitle"),
  modalTitle: document.getElementById("modalTitle"),
  modalSummary: document.getElementById("modalSummary"),
  modalContent: document.getElementById("modalContent"),
  modalAttributionPublisher: document.getElementById("modalAttributionPublisher"),
  modalExternalLink: document.getElementById("modalExternalLink"),
  modalMarkReadBtn: document.getElementById("modalMarkReadBtn"),
  modalShareBtn: document.getElementById("modalShareBtn"),

  // Comments
  commentsCount: document.getElementById("commentsCount"),
  commentForm: document.getElementById("commentForm"),
  commentUserAvatar: document.getElementById("commentUserAvatar"),
  commentText: document.getElementById("commentText"),
  commentsList: document.getElementById("commentsList"),

  // Editor Modal
  editorModal: document.getElementById("editorModal"),
  editorCloseBtn: document.getElementById("editorCloseBtn"),
  editorCancelBtn: document.getElementById("editorCancelBtn"),
  editorForm: document.getElementById("editorForm"),
  editorTitle: document.getElementById("editorTitle"),
  editorCategory: document.getElementById("editorCategory"),
  editorAuthorTitle: document.getElementById("editorAuthorTitle"),
  editorSummary: document.getElementById("editorSummary"),
  editorBody: document.getElementById("editorBody"),
  editorImgUrl: document.getElementById("editorImgUrl"),
  editorVideoUrl: document.getElementById("editorVideoUrl"),

  // Profile Modal
  profileModal: document.getElementById("profileModal"),
  profileCloseBtn: document.getElementById("profileCloseBtn"),
  profileDismissBtn: document.getElementById("profileDismissBtn"),
  tabProfile: document.getElementById("tabProfile"),
  tabLogin: document.getElementById("tabLogin"),
  profileView: document.getElementById("profileView"),
  loginView: document.getElementById("loginView"),
  profileAvatarImg: document.getElementById("profileAvatarImg"),
  profileFullName: document.getElementById("profileFullName"),
  profileEmail: document.getElementById("profileEmail"),
  profileRoleBadge: document.getElementById("profileRoleBadge"),
  statReadCount: document.getElementById("statReadCount"),
  statBookmarkCount: document.getElementById("statBookmarkCount"),
  saveInterestsBtn: document.getElementById("saveInterestsBtn"),
  btnSwitchEditor: document.getElementById("btnSwitchEditor"),
  btnSwitchReader: document.getElementById("btnSwitchReader"),
  authLoginForm: document.getElementById("authLoginForm"),
  loginEmail: document.getElementById("loginEmail"),
  loginPassword: document.getElementById("loginPassword"),
  profileLogoutBtn: document.getElementById("profileLogoutBtn"),

  // Cookie & Ad Policies (Day 23)
  cookieConsentBanner: document.getElementById("cookieConsentBanner"),
  acceptCookiesBtn: document.getElementById("acceptCookiesBtn"),
  rejectCookiesBtn: document.getElementById("rejectCookiesBtn"),
  openPolicyBtn: document.getElementById("openPolicyBtn"),
  policyModal: document.getElementById("policyModal"),
  policyCloseBtn: document.getElementById("policyCloseBtn"),
  policyDismissBtn: document.getElementById("policyDismissBtn"),
  footerPolicyLink: document.getElementById("footerPolicyLink"),
};

// Application State
let latestItems = [];
let readItems = [];
let bookmarkItems = [];
let breakingItems = [];
let currentBreakingIndex = 0;
let breakingInterval = null;
let activeModalArticle = null;

let selectedCategory = "";
let feedView = "all"; // 'all', 'bookmarks', 'read'
let inboxGraceSeconds = 20 * 60;

let currentUser = {
  id: null,
  external_key: "demo-editor",
  full_name: "Ahmet Yılmaz",
  email: "editor@curanews.com",
  role: "editor",
  avatar_url: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
  preferences: { categories: ["gundem", "ekonomi", "teknoloji"] },
};

let authToken = localStorage.getItem("curanews_token") || null;

// ========================================================
// AUTH & SESSION MANAGEMENT
// ========================================================
async function initAuth() {
  if (authToken) {
    try {
      const profile = await api("/auth/me", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      currentUser = profile;
    } catch {
      authToken = null;
      localStorage.removeItem("curanews_token");
    }
  }
  updateAuthUI();
}

function updateAuthUI() {
  els.topbarAvatar.src = currentUser.avatar_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150";
  els.topbarUserName.textContent = currentUser.full_name || "Giriş Yap";
  els.topbarUserRole.textContent = currentUser.role === "editor" ? "Editör" : "Okur";

  // Profile modal sync
  els.profileAvatarImg.src = currentUser.avatar_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150";
  els.profileFullName.textContent = currentUser.full_name || "Misafir Kullanıcı";
  els.profileEmail.textContent = currentUser.email || "Giriş yapılmadı";
  els.profileRoleBadge.textContent = currentUser.role === "editor" ? "Kıdemli Editör" : "Kamu / Okur";

  if (els.commentUserAvatar) {
    els.commentUserAvatar.src = currentUser.avatar_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80";
  }

  // Update user select if matching
  if (els.userSelect) {
    els.userSelect.value = currentUser.external_key;
  }
}

async function loginUser(email, password) {
  clearError();
  showStatus("Oturum açılıyor…");
  try {
    const res = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    authToken = res.access_token;
    localStorage.setItem("curanews_token", authToken);
    currentUser = res.user;
    updateAuthUI();
    showStatus(`Hoş geldiniz, ${currentUser.full_name}!`);
    setTimeout(() => showStatus(""), 3000);
    closeProfileModal();
    await loadBookmarks();
    await loadFeed();
  } catch (err) {
    showError(err.message || String(err));
  }
}

function logoutUser() {
  authToken = null;
  localStorage.removeItem("curanews_token");
  currentUser = {
    id: null,
    external_key: "demo-user-a",
    full_name: "Misafir Okur",
    email: null,
    role: "reader",
    avatar_url: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
    preferences: {},
  };
  updateAuthUI();
  closeProfileModal();
  showStatus("Oturum kapatıldı.");
  setTimeout(() => showStatus(""), 2000);
  loadBookmarks();
  loadFeed();
}

// ========================================================
// GOOGLE ANALYTICS 4 & IAB COOKIE / AD CONSENT (DAY 23)
// ========================================================
function trackEvent(eventName, params = {}) {
  if (typeof window.gtag === "function") {
    window.gtag("event", eventName, params);
  }
}

function initCookieConsent() {
  const consent = localStorage.getItem("curanews_cookie_consent");
  if (!consent && els.cookieConsentBanner) {
    els.cookieConsentBanner.hidden = false;
  }

  if (els.acceptCookiesBtn) {
    els.acceptCookiesBtn.addEventListener("click", () => {
      localStorage.setItem("curanews_cookie_consent", "all");
      if (els.cookieConsentBanner) els.cookieConsentBanner.hidden = true;
      trackEvent("cookie_consent_granted", { consent_type: "all" });
    });
  }

  if (els.rejectCookiesBtn) {
    els.rejectCookiesBtn.addEventListener("click", () => {
      localStorage.setItem("curanews_cookie_consent", "essential");
      if (els.cookieConsentBanner) els.cookieConsentBanner.hidden = true;
      trackEvent("cookie_consent_granted", { consent_type: "essential" });
    });
  }

  if (els.openPolicyBtn) {
    els.openPolicyBtn.addEventListener("click", openPolicyModal);
  }

  if (els.footerPolicyLink) {
    els.footerPolicyLink.addEventListener("click", openPolicyModal);
  }

  if (els.policyCloseBtn) {
    els.policyCloseBtn.addEventListener("click", closePolicyModal);
  }

  if (els.policyDismissBtn) {
    els.policyDismissBtn.addEventListener("click", closePolicyModal);
  }
}

function openPolicyModal() {
  if (els.policyModal) {
    els.policyModal.hidden = false;
    document.body.style.overflow = "hidden";
  }
}

function closePolicyModal() {
  if (els.policyModal) {
    els.policyModal.hidden = true;
    document.body.style.overflow = "";
  }
}

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
  trackEvent("theme_change", { theme });
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
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (authToken && !headers.Authorization) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  let response;
  try {
    response = await fetch(url, { ...options, headers });
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
// BOOKMARKS / FAVORİLER
// ========================================================
async function loadBookmarks() {
  try {
    const res = await api(`/bookmarks?user_id=${encodeURIComponent(currentUser.external_key)}`);
    bookmarkItems = res.items || [];
    els.bookmarkCount.textContent = String(bookmarkItems.length);
    els.statBookmarkCount.textContent = String(bookmarkItems.length);
  } catch {
    bookmarkItems = [];
    els.bookmarkCount.textContent = "0";
  }
}

async function toggleBookmark(articleId, button) {
  clearError();
  try {
    const res = await api("/bookmarks", {
      method: "POST",
      body: JSON.stringify({
        article_id: articleId,
        user_id: currentUser.external_key,
      }),
    });

    const isBookmarked = res.is_bookmarked;
    await loadBookmarks();

    // Update in-place
    const item = latestItems.find((i) => i.id === articleId);
    if (item) item.is_bookmarked = isBookmarked;

    if (button) {
      button.classList.toggle("is-bookmarked", isBookmarked);
      button.textContent = isBookmarked ? "★ Kaydedildi" : "⭐ Kaydet";
    }

    showStatus(isBookmarked ? "Haber favorilerinize eklendi." : "Haber favorilerinizden çıkarıldı.");
    setTimeout(() => showStatus(""), 2000);

    if (feedView === "bookmarks") {
      renderFeed();
    }
  } catch (err) {
    showError(err.message || String(err));
  }
}

// ========================================================
// COMMENTS SİSTEMİ
// ========================================================
async function loadComments(articleId) {
  els.commentsList.innerHTML = `<p class="comments-empty">Yorumlar yükleniyor…</p>`;
  try {
    const res = await api(`/articles/${articleId}/comments`);
    const comments = res.items || [];
    els.commentsCount.textContent = String(comments.length);

    if (!comments.length) {
      els.commentsList.innerHTML = `<p class="comments-empty">Henüz yorum yapılmadı. İlk yorumu siz yazın!</p>`;
      return;
    }

    els.commentsList.innerHTML = "";
    comments.forEach((c) => {
      const card = document.createElement("div");
      card.className = "comment-card";
      card.innerHTML = `
        <div class="comment-card-header">
          <div class="comment-user-info">
            <img src="${escapeHtml(c.author_avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80')}" alt="Avatar" class="comment-card-avatar" />
            <span class="comment-author-name">${escapeHtml(c.author_name)}</span>
          </div>
          <span class="comment-time">${relativeTime(c.created_at)}</span>
        </div>
        <div class="comment-card-body">${escapeHtml(c.content)}</div>
        <button type="button" class="comment-like-btn" data-id="${c.id}">
          <span>👍</span> <span class="like-count">${c.likes || 0}</span>
        </button>
      `;

      const likeBtn = card.querySelector(".comment-like-btn");
      likeBtn.onclick = async () => {
        try {
          const lRes = await api(`/comments/${c.id}/like`, { method: "POST" });
          likeBtn.querySelector(".like-count").textContent = String(lRes.likes);
        } catch (e) {
          showError(e.message);
        }
      };

      els.commentsList.appendChild(card);
    });
  } catch {
    els.commentsList.innerHTML = `<p class="comments-empty">Yorumlar alınamadı.</p>`;
  }
}

els.commentForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!activeModalArticle) return;
  const content = els.commentText.value.trim();
  if (!content) return;

  clearError();
  try {
    await api(`/articles/${activeModalArticle.id}/comments`, {
      method: "POST",
      body: JSON.stringify({
        content,
        author_name: currentUser.full_name,
        author_avatar: currentUser.avatar_url,
      }),
    });
    els.commentText.value = "";
    showStatus("Yorumunuz başarıyla yayımlandı!");
    setTimeout(() => showStatus(""), 2500);
    await loadComments(activeModalArticle.id);
  } catch (err) {
    showError(err.message || String(err));
  }
});

// ========================================================
// ONEDIO STYLE EDITOR CMS
// ========================================================
function openEditorModal() {
  els.editorModal.hidden = false;
  document.body.style.overflow = "hidden";
}

function closeEditorModal() {
  els.editorModal.hidden = true;
  document.body.style.overflow = "";
}

els.openEditorBtn.addEventListener("click", openEditorModal);
els.editorCloseBtn.addEventListener("click", closeEditorModal);
els.editorCancelBtn.addEventListener("click", closeEditorModal);

els.editorForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError();

  const payload = {
    title: els.editorTitle.value.trim(),
    category: els.editorCategory.value,
    author_title: els.editorAuthorTitle.value.trim() || "Kıdemli Editör",
    summary: els.editorSummary.value.trim(),
    body: els.editorBody.value.trim(),
    image_url: els.editorImgUrl.value.trim() || null,
    video_url: els.editorVideoUrl.value.trim() || null,
    author_name: currentUser.full_name || "CuraNews Editörü",
    author_avatar: currentUser.avatar_url,
  };

  showStatus("Haber CuraNews Editör Masası'nda yayımlanıyor…");
  try {
    const created = await api("/editor/articles", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    // Add to top of feed
    latestItems.unshift(created);
    closeEditorModal();
    els.editorForm.reset();

    showStatus("Haberiniz canlı akışa başarıyla eklendi! Tebrikler.");
    setTimeout(() => showStatus(""), 4000);
    renderFeed();
  } catch (err) {
    showError(err.message || String(err));
  }
});

// ========================================================
// KULLANICI PROFİLİ VE GİRİŞ MODALİ
// ========================================================
function openProfileModal() {
  updateAuthUI();
  els.profileModal.hidden = false;
  document.body.style.overflow = "hidden";
}

function closeProfileModal() {
  els.profileModal.hidden = true;
  document.body.style.overflow = "";
}

els.userProfileBtn.addEventListener("click", openProfileModal);
els.profileCloseBtn.addEventListener("click", closeProfileModal);
els.profileDismissBtn.addEventListener("click", closeProfileModal);
els.profileLogoutBtn.addEventListener("click", logoutUser);

els.tabProfile.addEventListener("click", () => {
  els.tabProfile.classList.add("is-active");
  els.tabLogin.classList.remove("is-active");
  els.profileView.hidden = false;
  els.loginView.hidden = true;
});

els.tabLogin.addEventListener("click", () => {
  els.tabLogin.classList.add("is-active");
  els.tabProfile.classList.remove("is-active");
  els.profileView.hidden = true;
  els.loginView.hidden = false;
});

// Demo switchers for faculty & jury presentation
els.btnSwitchEditor.addEventListener("click", () => {
  loginUser("editor@curanews.com", "editor123");
});

els.btnSwitchReader.addEventListener("click", () => {
  setTheme("sepya");
  loginUser("okur@curanews.com", "okur123");
});

els.authLoginForm.addEventListener("submit", (e) => {
  e.preventDefault();
  loginUser(els.loginEmail.value.trim(), els.loginPassword.value.trim());
});

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
  trackEvent("article_view", {
    article_id: item.id,
    title: item.title,
    category: item.category,
    source: item.source_name,
    is_editorial: Boolean(item.is_editorial),
  });

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

  // Video embed (if present)
  if (item.video_url) {
    els.modalVideoWrap.hidden = false;
    let embedUrl = item.video_url;
    if (embedUrl.includes("watch?v=")) {
      embedUrl = embedUrl.replace("watch?v=", "embed/");
    }
    els.modalVideoIframe.src = embedUrl;
  } else {
    els.modalVideoWrap.hidden = true;
    els.modalVideoIframe.src = "";
  }

  // Onedio-style author box (if editorial)
  if (item.is_editorial) {
    els.modalAuthorBox.hidden = false;
    els.modalAuthorName.textContent = item.author_display || "Ahmet Yılmaz";
    els.modalAuthorTitle.textContent = item.author_title || "Kıdemli Editör";
    els.modalAuthorAvatar.src = item.author_avatar || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150";
  } else {
    els.modalAuthorBox.hidden = true;
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

  // Bookmark button
  const isBookmarked = bookmarkItems.some((b) => b.id === item.id) || Boolean(item.is_bookmarked);
  els.modalBookmarkBtn.classList.toggle("is-bookmarked", isBookmarked);
  els.modalBookmarkBtn.textContent = isBookmarked ? "★ Kaydedildi" : "⭐ Kaydet";
  els.modalBookmarkBtn.onclick = () => toggleBookmark(item.id, els.modalBookmarkBtn);

  // Read status
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

  // Share
  els.modalShareBtn.onclick = () => {
    navigator.clipboard?.writeText(item.url);
    showStatus("Haber bağlantısı panoya kopyalandı!");
    setTimeout(() => showStatus(""), 3000);
  };

  // Comments
  loadComments(item.id);

  els.articleModal.hidden = false;
  document.body.style.overflow = "hidden";
}

function closeArticleModal() {
  els.articleModal.hidden = true;
  document.body.style.overflow = "";
  els.modalVideoIframe.src = "";
  activeModalArticle = null;
}

els.modalCloseBtn.addEventListener("click", closeArticleModal);
els.modalDismissBtn.addEventListener("click", closeArticleModal);
els.articleModal.addEventListener("click", (e) => {
  if (e.target === els.articleModal) closeArticleModal();
});
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (!els.articleModal.hidden) closeArticleModal();
    if (!els.editorModal.hidden) closeEditorModal();
    if (!els.profileModal.hidden) closeProfileModal();
  }
});

// ========================================================
// FEED RENDERING & FILTERING
// ========================================================
function itemMatchesFilters(item) {
  if (selectedCategory) {
    const itemCat = (item.category || "").toLowerCase();
    if (itemCat !== selectedCategory.toLowerCase()) {
      return false;
    }
  }

  const query = els.searchInput.value.trim().toLowerCase();
  if (query) {
    const haystack = [item.title, item.summary, item.source_name, item.category_name, ...(item.entities || [])]
      .join(" ")
      .toLowerCase();
    if (!haystack.includes(query)) return false;
  }

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

  const isBookmarked = bookmarkItems.some((b) => b.id === item.id) || Boolean(item.is_bookmarked);

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
        <button type="button" class="btn secondary btn-bm-feature">${isBookmarked ? "★ Kaydedildi" : "⭐ Kaydet"}</button>
        <button type="button" class="btn ghost btn-mark-feature">${item.read ? "✓ Okundu" : "Okundu İşaretle"}</button>
      </div>
    </div>
  `;

  els.featuredSlot.querySelector(".featured-title a").onclick = () => openArticleModal(item);
  els.featuredSlot.querySelector(".btn-open-feature").onclick = () => openArticleModal(item);

  const bmBtn = els.featuredSlot.querySelector(".btn-bm-feature");
  bmBtn.onclick = () => toggleBookmark(item.id, bmBtn);

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

  const isBookmarked = bookmarkItems.some((b) => b.id === item.id) || Boolean(item.is_bookmarked);

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
          <button type="button" class="btn-bm-card ${isBookmarked ? 'is-bookmarked' : ''}" title="Favorilere Ekle">${isBookmarked ? '★' : '☆'}</button>
          <button type="button" class="btn-mark-read">${item.read ? "✓" : "Okundu"}</button>
        </div>
        <span class="time-read">${item.read_time_minutes || 1} dk okuma</span>
      </div>
    </div>
  `;

  li.querySelector(".card-title").onclick = () => openArticleModal(item);
  li.querySelector(".btn-read-modal").onclick = () => openArticleModal(item);

  const bmBtn = li.querySelector(".btn-bm-card");
  bmBtn.onclick = () => toggleBookmark(item.id, bmBtn);

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
  let sourceItems = latestItems;
  if (feedView === "bookmarks") {
    sourceItems = bookmarkItems;
  } else if (feedView === "read") {
    sourceItems = readItems;
  }

  const filtered = sourceItems.filter((item) => {
    if (feedView === "all" && item.read && !stillOnMainFeed(item)) return false;
    if (feedView === "read" && !item.read) return false;
    return itemMatchesFilters(item);
  });

  els.feedList.innerHTML = "";
  els.featuredSlot.hidden = true;
  els.emptyState.hidden = filtered.length > 0;

  if (feedView === "bookmarks") {
    els.emptyState.textContent = "Henüz favoriye eklediğiniz bir haber yok. Haber kartlarındaki ⭐ butonuna basarak kaydedebilirsiniz.";
  } else {
    els.emptyState.textContent = "Bu filtreye uygun haber bulunamadı. Kategori veya aramayı temizleyebilirsiniz.";
  }

  const readCount = (readItems.length ? readItems : sourceItems).filter((i) => i.read).length;
  els.feedCount.textContent = filtered.length
    ? `${filtered.length} haber görünür · ${readCount} okundu`
    : "0 haber";

  if (!filtered.length) return;

  renderFeatured(filtered[0]);

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

async function loadFeed(options = {}) {
  const quiet = Boolean(options.quiet);
  clearError();
  if (!quiet) showStatus("Haber masası güncelleniyor…");
  setLoading(true);
  els.refreshBtn.disabled = true;

  try {
    const userId = currentUser.external_key;
    const data = await api(`/feed?user_id=${encodeURIComponent(userId)}&limit=48`);
    latestItems = data.items || [];
    readItems = data.read_items || latestItems.filter((i) => i.read);
    inboxGraceSeconds = Number(data.inbox_grace_seconds) || 20 * 60;

    const cache = data.cache || "—";
    els.cacheBadge.textContent = `cache · ${cache}`;
    els.cacheBadge.dataset.state = cache;

    setupBreakingTicker(latestItems);
    await loadBookmarks();
    renderFeed();

    if (!quiet) {
      showStatus(`${latestItems.length} haber kürate edildi · ${currentUser.full_name} masası aktif`);
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
        user_id: currentUser.external_key,
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
async function init() {
  initAccessibility();
  initCookieConsent();
  setupCategoryNavbar();
  await initAuth();

  els.refreshBtn.addEventListener("click", () => loadFeed());
  els.searchInput.addEventListener("input", () => renderFeed());
  els.topicSelect.addEventListener("change", () => renderFeed());

  els.viewAll.addEventListener("click", () => {
    feedView = "all";
    els.viewAll.classList.add("is-active");
    els.viewBookmarks.classList.remove("is-active");
    els.viewRead.classList.remove("is-active");
    renderFeed();
  });

  els.viewBookmarks.addEventListener("click", () => {
    feedView = "bookmarks";
    els.viewBookmarks.classList.add("is-active");
    els.viewAll.classList.remove("is-active");
    els.viewRead.classList.remove("is-active");
    renderFeed();
  });

  els.viewRead.addEventListener("click", () => {
    feedView = "read";
    els.viewRead.classList.add("is-active");
    els.viewAll.classList.remove("is-active");
    els.viewBookmarks.classList.remove("is-active");
    renderFeed();
  });

  document.querySelectorAll(".persona").forEach((btn) => {
    btn.addEventListener("click", () => {
      els.userSelect.value = btn.dataset.user;
      currentUser.external_key = btn.dataset.user;
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
