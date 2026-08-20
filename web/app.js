const API_BASE = window.CURANEWS_API_BASE || "";

const els = {
  userSelect: document.getElementById("userSelect"),
  topicSelect: document.getElementById("topicSelect"),
  refreshBtn: document.getElementById("refreshBtn"),
  feedList: document.getElementById("feedList"),
  emptyState: document.getElementById("emptyState"),
  cacheBadge: document.getElementById("cacheBadge"),
  status: document.getElementById("status"),
  error: document.getElementById("error"),
};

let latestItems = [];

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

function itemMatchesTopic(item, topic) {
  if (!topic) return true;
  const needle = topic.toLowerCase();
  const hay = [...(item.entities || []), item.category || ""].join(" ").toLowerCase();
  return hay.includes(needle);
}

function renderFeed(items) {
  const topic = els.topicSelect.value.trim().toLowerCase();
  const filtered = items.filter((item) => itemMatchesTopic(item, topic));
  els.feedList.innerHTML = "";
  els.emptyState.hidden = filtered.length > 0;

  filtered.forEach((item, index) => {
    const li = document.createElement("li");
    li.className = "feed-item";
    li.style.animationDelay = `${index * 0.05}s`;

    const entities = (item.entities || []).slice(0, 4).join(" · ") || "etiket yok";
    const score = item.score == null ? "—" : Number(item.score).toFixed(3);

    li.innerHTML = `
      <div class="feed-rank">#${index + 1} · skor ${score}</div>
      <h3 class="feed-title"><a href="${item.url}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a></h3>
      <p class="feed-summary">${escapeHtml(item.summary || "Özet yok.")}</p>
      <div class="feed-footer">
        <p class="meta-line">
          ${escapeHtml(item.source_name || "kaynak")}
          <span class="entities"> · ${escapeHtml(entities)}</span>
        </p>
        <button type="button" class="btn primary" data-id="${item.id}">Okundu işaretle</button>
      </div>
    `;

    const button = li.querySelector("button");
    button.addEventListener("click", () => markRead(item.id, button));
    els.feedList.appendChild(li);
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function loadTopics() {
  try {
    const data = await api("/topics?limit=30");
    const current = els.topicSelect.value;
    els.topicSelect.innerHTML = `<option value="">Tümü</option>`;
    for (const topic of data.items || []) {
      const opt = document.createElement("option");
      opt.value = topic.normalized;
      opt.textContent = `${topic.label} (${topic.article_count})`;
      els.topicSelect.appendChild(opt);
    }
    els.topicSelect.value = current;
  } catch {
    // Topics are optional for the first paint; feed error handles hard failures.
  }
}

async function loadFeed() {
  clearError();
  showStatus("Akış yükleniyor…");
  els.refreshBtn.disabled = true;
  try {
    const userId = els.userSelect.value;
    const data = await api(`/feed?user_id=${encodeURIComponent(userId)}&limit=12`);
    latestItems = data.items || [];
    els.cacheBadge.textContent = `cache: ${data.cache || "—"}`;
    renderFeed(latestItems);
    showStatus(
      latestItems.length
        ? `${latestItems.length} haber · kullanıcı ${userId}`
        : "Akış boş — seed_demo_users.py çalıştırılmış mı?"
    );
  } catch (err) {
    latestItems = [];
    els.feedList.innerHTML = "";
    els.emptyState.hidden = true;
    els.cacheBadge.textContent = "cache: —";
    showStatus("");
    showError(err.message || String(err));
  } finally {
    els.refreshBtn.disabled = false;
  }
}

async function markRead(articleId, button) {
  clearError();
  button.disabled = true;
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
    showStatus("Okundu kaydedildi — akış yeniden sıralanıyor…");
    await loadFeed();
  } catch (err) {
    showError(err.message || String(err));
    button.disabled = false;
    button.textContent = "Okundu işaretle";
  }
}

els.refreshBtn.addEventListener("click", loadFeed);
els.userSelect.addEventListener("change", loadFeed);
els.topicSelect.addEventListener("change", () => renderFeed(latestItems));

await loadTopics();
await loadFeed();
