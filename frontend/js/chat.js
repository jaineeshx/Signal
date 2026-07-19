/**
 * SIGNAL — Chat Tab Module
 * Manages the AI chat interface: persona selection, message sending,
 * conversation history, typing indicators, and quick-action chips.
 */

const Chat = (() => {
  // ── State ──────────────────────────────────────────────────
  const history = []; // [{role, content}]

  // ── DOM refs (set after DOMContentLoaded) ──────────────────
  let messagesEl, textareaEl, sendBtnEl, typingEl;

  // ── Persona metadata ───────────────────────────────────────
  const PERSONAS = {
    fan:       { icon: '⚽', name: 'Fan',         desc: 'Match-day help' },
    staff:     { icon: '🦺', name: 'Venue Staff',  desc: 'Operations' },
    volunteer: { icon: '🤝', name: 'Volunteer',    desc: 'Task support' },
    organizer: { icon: '📊', name: 'Organizer',    desc: 'Analytics' },
  };

  // ── Quick actions per persona ──────────────────────────────
  const QUICK_ACTIONS = {
    fan:       ['🪑 Find my seat', '🍔 Nearest food', '🚗 Transport options', '♿ Accessibility', '📅 Match schedule'],
    staff:     ['🚨 Report incident', '👥 Zone density alert', '🏥 Medical escalation', '📋 Shift briefing'],
    volunteer: ['📍 Lost & found', '🆘 First aid location', '📻 Who to contact', '👋 Fan direction tips'],
    organizer: ['📈 Crowd risk summary', '🌱 Sustainability update', '🔄 Resource reallocation', '📊 Zone analytics'],
  };

  // ── Render a message bubble ────────────────────────────────
  function renderMessage(role, content) {
    const isUser = role === 'user';
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const wrapper = document.createElement('div');
    wrapper.className = `message ${isUser ? 'user' : 'ai'}`;
    wrapper.setAttribute('role', 'listitem');

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.setAttribute('aria-hidden', 'true');
    avatar.textContent = isUser ? '👤' : '🤖';

    const msgContent = document.createElement('div');
    msgContent.className = 'msg-content';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = content;

    const meta = document.createElement('div');
    meta.className = 'msg-meta';
    meta.textContent = isUser
      ? `You · ${time}`
      : `SIGNAL (${PERSONAS[window.SIGNAL_STATE.persona]?.name || 'AI'}) · ${time}`;

    msgContent.append(bubble, meta);
    wrapper.append(avatar, msgContent);
    return wrapper;
  }

  // ── Show / hide typing indicator ───────────────────────────
  function setTyping(visible) {
    if (typingEl) {
      typingEl.classList.toggle('visible', visible);
      if (visible) scrollToBottom();
    }
    if (sendBtnEl) sendBtnEl.disabled = visible;
    if (textareaEl) textareaEl.disabled = visible;
  }

  // ── Scroll chat to bottom ──────────────────────────────────
  function scrollToBottom() {
    if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  // ── Remove empty-state placeholder ────────────────────────
  function removeEmptyState() {
    const empty = document.getElementById('chat-empty-state');
    if (empty) empty.remove();
  }

  // ── Send a message ─────────────────────────────────────────
  async function sendMessage(text) {
    const trimmed = (text || textareaEl?.value || '').trim();
    if (!trimmed) return;

    removeEmptyState();

    // Append user message
    history.push({ role: 'user', content: trimmed });
    messagesEl.appendChild(renderMessage('user', trimmed));
    if (textareaEl) textareaEl.value = '';
    autoResizeTextarea();
    scrollToBottom();
    setTyping(true);

    try {
      const data = await window.API.post('/chat', {
        message: trimmed,
        persona: window.SIGNAL_STATE.persona,
        language: window.SIGNAL_STATE.language,
        context: history.slice(-10).map(h => ({ role: h.role, content: h.content })),
      });

      const reply = data.reply || 'Sorry, I could not generate a response.';
      history.push({ role: 'model', content: reply });
      messagesEl.appendChild(renderMessage('ai', reply));

    } catch (err) {
      const errMsg = err.message.includes('fetch')
        ? t('errorNetwork')
        : `${t('errorGeneral')} (${err.message})`;
      messagesEl.appendChild(renderMessage('ai', `⚠️ ${errMsg}`));
      window.showToast(errMsg, 'error');
    } finally {
      setTyping(false);
      scrollToBottom();
    }
  }

  // ── Auto-resize textarea ───────────────────────────────────
  function autoResizeTextarea() {
    if (!textareaEl) return;
    textareaEl.style.height = 'auto';
    textareaEl.style.height = `${Math.min(textareaEl.scrollHeight, 140)}px`;
  }

  // ── Switch persona ─────────────────────────────────────────
  function switchPersona(persona) {
    window.SIGNAL_STATE.persona = persona;

    // Update button states
    document.querySelectorAll('.persona-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.persona === persona);
      btn.setAttribute('aria-pressed', btn.dataset.persona === persona);
    });

    // Update quick-action chips
    renderQuickActions(persona);
  }

  // ── Render quick-action chips ──────────────────────────────
  function renderQuickActions(persona) {
    const list = document.getElementById('quick-actions-list');
    if (!list) return;

    list.innerHTML = '';
    (QUICK_ACTIONS[persona] || []).forEach(action => {
      const btn = document.createElement('button');
      btn.className = 'quick-chip';
      btn.textContent = action;
      btn.setAttribute('aria-label', `Quick action: ${action}`);
      btn.addEventListener('click', () => sendMessage(action.replace(/^[^\s]+ /, '')));
      list.appendChild(btn);
    });
  }

  // ── Initialise ─────────────────────────────────────────────
  function init() {
    messagesEl = document.getElementById('chat-messages');
    textareaEl = document.getElementById('chat-textarea');
    sendBtnEl  = document.getElementById('chat-send-btn');
    typingEl   = document.getElementById('typing-indicator');

    // Send on button click
    if (sendBtnEl) {
      sendBtnEl.addEventListener('click', () => sendMessage());
    }

    // Send on Enter (Shift+Enter = newline)
    if (textareaEl) {
      textareaEl.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
      textareaEl.addEventListener('input', autoResizeTextarea);
    }

    // Persona buttons
    document.querySelectorAll('.persona-btn').forEach(btn => {
      btn.addEventListener('click', () => switchPersona(btn.dataset.persona));
    });

    // Initial quick actions
    renderQuickActions(window.SIGNAL_STATE.persona);
  }

  return { init, sendMessage, switchPersona };
})();

document.addEventListener('DOMContentLoaded', Chat.init);
window.Chat = Chat;
