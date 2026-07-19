/**
 * SIGNAL — Navigation Tab Module
 * Populates location datalists, handles form submission,
 * displays AI-generated walking directions, and renders a stadium map SVG.
 */

const NavTab = (() => {

  // ── Populate datalists from API ───────────────────────────
  async function loadLocations() {
    try {
      const locations = await window.API.get('/locations');
      const formatted = locations.map(l =>
        l.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
      );

      ['from-datalist', 'to-datalist'].forEach(id => {
        const dl = document.getElementById(id);
        if (!dl) return;
        dl.innerHTML = formatted
          .map(loc => `<option value="${loc}"></option>`)
          .join('');
      });
    } catch {
      // Non-critical — user can still type freely
    }
  }

  // ── Submit navigation request ─────────────────────────────
  async function getDirections() {
    const fromEl  = document.getElementById('from-input');
    const toEl    = document.getElementById('to-input');
    const accEl   = document.getElementById('accessibility-toggle');
    const dirCard = document.getElementById('directions-card');
    const dirText = document.getElementById('directions-content');
    const dirBtn  = document.getElementById('directions-btn');

    const from = fromEl?.value.trim();
    const to   = toEl?.value.trim();

    if (!from || !to) {
      window.showToast('Please enter both a start and destination.', 'error');
      return;
    }

    if (from.toLowerCase() === to.toLowerCase()) {
      window.showToast('Start and destination must be different.', 'error');
      return;
    }

    // Show loading state
    if (dirText) dirText.textContent = '⏳ Calculating route…';
    if (dirCard) dirCard.style.display = 'block';
    if (dirBtn)  { dirBtn.disabled = true; dirBtn.textContent = 'Calculating…'; }

    try {
      const data = await window.API.post('/navigate', {
        from_location: from,
        to_location:   to,
        accessibility: accEl?.checked || false,
        language:      window.SIGNAL_STATE.language,
      });

      if (dirText) {
        dirText.textContent = data.directions;

        // Accessibility note
        if (data.accessibility) {
          const note = document.createElement('p');
          note.style.cssText = 'margin-top:10px;font-size:0.8rem;color:var(--green-400);';
          note.textContent = '♿ Wheelchair-accessible route applied.';
          dirText.after(note);
        }
      }

      // Mock label
      const mockEl = document.getElementById('directions-mock');
      if (mockEl) {
        mockEl.textContent = data.mock
          ? 'Directions from SIGNAL mock engine'
          : 'Directions powered by Gemini AI';
        mockEl.style.display = 'block';
      }

    } catch (err) {
      if (dirText) dirText.textContent = `⚠️ Could not get directions: ${err.message}`;
      window.showToast(err.message, 'error');
    } finally {
      if (dirBtn) { dirBtn.disabled = false; dirBtn.textContent = t('getDirections'); }
    }
  }

  // ── Stadium SVG map ───────────────────────────────────────
  function renderStadiumMap() {
    const mapEl = document.getElementById('stadium-map');
    if (!mapEl) return;

    mapEl.innerHTML = `
      <svg viewBox="0 0 400 360" xmlns="http://www.w3.org/2000/svg" role="img"
           aria-label="Stadium layout map showing gates, stands, and key facilities">
        <defs>
          <linearGradient id="pitchGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%"   stop-color="#1a6b3e"/>
            <stop offset="50%"  stop-color="#22b05e"/>
            <stop offset="100%" stop-color="#1a6b3e"/>
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        <!-- Stadium oval -->
        <ellipse cx="200" cy="180" rx="170" ry="145" fill="none" stroke="rgba(201,168,76,0.25)" stroke-width="2"/>

        <!-- Stands -->
        <!-- North -->
        <path d="M 110 60 Q 200 30 290 60 L 270 90 Q 200 68 130 90 Z"
              fill="rgba(15,31,56,0.9)" stroke="rgba(201,168,76,0.3)" stroke-width="1"/>
        <!-- South -->
        <path d="M 110 300 Q 200 330 290 300 L 270 270 Q 200 292 130 270 Z"
              fill="rgba(15,31,56,0.9)" stroke="rgba(201,168,76,0.3)" stroke-width="1"/>
        <!-- West -->
        <path d="M 42 110 Q 18 180 42 250 L 70 240 Q 50 180 70 120 Z"
              fill="rgba(15,31,56,0.9)" stroke="rgba(201,168,76,0.3)" stroke-width="1"/>
        <!-- East -->
        <path d="M 358 110 Q 382 180 358 250 L 330 240 Q 350 180 330 120 Z"
              fill="rgba(15,31,56,0.9)" stroke="rgba(201,168,76,0.3)" stroke-width="1"/>

        <!-- Pitch -->
        <ellipse cx="200" cy="180" rx="120" ry="100" fill="url(#pitchGrad)" opacity="0.9"/>
        <!-- Centre circle -->
        <circle cx="200" cy="180" r="28" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
        <!-- Centre spot -->
        <circle cx="200" cy="180" r="3" fill="rgba(255,255,255,0.5)"/>
        <!-- Halfway line -->
        <line x1="80" y1="180" x2="320" y2="180" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>
        <!-- Goal areas -->
        <rect x="165" y="88" width="70" height="22" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="1.2"/>
        <rect x="165" y="250" width="70" height="22" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="1.2"/>

        <!-- Gate labels -->
        <g font-family="Inter,sans-serif" font-size="10" font-weight="600" text-anchor="middle">
          <g filter="url(#glow)">
            <rect x="175" y="20" width="50" height="20" rx="4" fill="rgba(201,168,76,0.2)" stroke="rgba(201,168,76,0.5)" stroke-width="1"/>
            <text x="200" y="33" fill="#e8c96a">GATE A</text>

            <rect x="175" y="320" width="50" height="20" rx="4" fill="rgba(201,168,76,0.2)" stroke="rgba(201,168,76,0.5)" stroke-width="1"/>
            <text x="200" y="333" fill="#e8c96a">GATE B</text>

            <rect x="348" y="170" width="46" height="20" rx="4" fill="rgba(201,168,76,0.2)" stroke="rgba(201,168,76,0.5)" stroke-width="1"/>
            <text x="371" y="183" fill="#e8c96a">GATE C</text>

            <rect x="6" y="170" width="46" height="20" rx="4" fill="rgba(201,168,76,0.2)" stroke="rgba(201,168,76,0.5)" stroke-width="1"/>
            <text x="29" y="183" fill="#e8c96a">GATE D</text>
          </g>
        </g>

        <!-- Facility icons -->
        <g font-size="13" text-anchor="middle">
          <!-- Food -->
          <text x="148" y="52" fill="#f1c40f" aria-label="Food Court North">🍔</text>
          <text x="250" y="52" fill="#f1c40f" aria-label="Food Court South">🌮</text>
          <!-- Medical -->
          <text x="344" y="145" fill="#e74c3c" aria-label="Medical Centre">🏥</text>
          <!-- Accessibility -->
          <text x="56" y="145" fill="#3498db" aria-label="Accessibility Services">♿</text>
          <!-- Prayer -->
          <text x="145" y="310" fill="#9b59b6" aria-label="Prayer Room">🕌</text>
          <!-- Family -->
          <text x="56" y="220" fill="#2ecc71" aria-label="Family Zone">👨‍👩‍👧</text>
          <!-- VIP -->
          <text x="344" y="220" fill="#c9a84c" aria-label="VIP Lounge">⭐</text>
        </g>

        <!-- SIGNAL watermark -->
        <text x="200" y="180" font-family="Space Grotesk,sans-serif" font-size="8"
              fill="rgba(255,255,255,0.15)" text-anchor="middle" font-weight="700">SIGNAL</text>

        <!-- Legend -->
        <g transform="translate(10, 335)" font-size="8" font-family="Inter,sans-serif" fill="rgba(138,154,181,0.8)">
          <text x="0" y="0">🏟️ FIFA World Cup 2026 Venue — Schematic Layout</text>
        </g>
      </svg>
    `;
  }

  // ── Initialise ────────────────────────────────────────────
  function init() {
    const dirBtn = document.getElementById('directions-btn');
    if (dirBtn) dirBtn.addEventListener('click', getDirections);

    // Enter key on inputs
    ['from-input', 'to-input'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('keydown', e => { if (e.key === 'Enter') getDirections(); });
    });

    loadLocations();
    renderStadiumMap();
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', NavTab.init);
window.NavTab = NavTab;
