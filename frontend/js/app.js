/**
 * SIGNAL — App Bootstrap & Global State
 * Initialises shared state, API client, routing, and toast notifications.
 */

// ── API Base URL ─────────────────────────────────────────────
const API_BASE = `${window.location.origin}/api`;

// ── Global Application State ─────────────────────────────────
window.SIGNAL_STATE = {
  persona: 'fan',
  language: 'en',
  geminiLive: false,
};

// ── API Client ────────────────────────────────────────────────
const API = {
  async post(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async get(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
};

window.API = API;

// ── Tab Routing ───────────────────────────────────────────────
function initTabs() {
  const buttons = document.querySelectorAll('.tab-btn');
  const panels  = document.querySelectorAll('.tab-panel');

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      buttons.forEach(b => {
        b.classList.toggle('active', b.dataset.tab === target);
        b.setAttribute('aria-selected', b.dataset.tab === target);
      });
      panels.forEach(p => {
        p.classList.toggle('active', p.id === `panel-${target}`);
      });
      // Trigger tab-specific init
      if (target === 'crowd' && window.CrowdTab?.onActivate) window.CrowdTab.onActivate();
    });
  });
}

// ── Health Check ──────────────────────────────────────────────
async function checkGeminiStatus() {
  try {
    const data = await API.get('/health');
    const live  = data.gemini_configured && !data.mock_mode;
    window.SIGNAL_STATE.geminiLive = live;

    const badge = document.getElementById('gemini-badge');
    if (badge) {
      badge.className = `gemini-badge ${live ? 'live' : 'mock'}`;
      badge.querySelector('.badge-text').textContent = live ? 'Gemini Live' : 'Mock Mode';
    }
  } catch {
    // Server may not be up yet — silently degrade
  }
}

// ── Language Change ───────────────────────────────────────────
function onLanguageChange(lang) {
  window.SIGNAL_STATE.language = lang;
  // Update RTL for Arabic
  document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
  document.documentElement.setAttribute('lang', lang);
}

// ── Toast Notifications ───────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'polite');
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

window.showToast = showToast;

// ── Initialise ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  checkGeminiStatus();

  // Language selector
  const langSel = document.getElementById('lang-select');
  if (langSel) {
    langSel.addEventListener('change', e => onLanguageChange(e.target.value));
  }

  // Auto-refresh health status every 30 s
  setInterval(checkGeminiStatus, 30_000);
});
