<div align="center">
  <h1>⚡ SIGNAL</h1>
  <p><strong>Smart Intelligent Guide for Navigation and Live-operations</strong></p>
  <p><i>A GenAI-powered full-stack solution designed for the FIFA World Cup 2026</i></p>
</div>

---

## 🎯 Chosen Vertical
**Operational Intelligence + Fan Experience**

This solution combines multiple capabilities requested in the challenge:
- **Navigation & Accessibility**: AI-powered step-by-step stadium directions with wheelchair-accessible routing.
- **Crowd Management & Operational Intelligence**: Real-time zone density monitoring that automatically generates actionable GenAI advisories for venue staff.
- **Multilingual Assistance**: An 8-language AI chatbot that dynamically translates interactions and adapts to the user's role (Fan, Staff, Volunteer, Organizer).

---

## 💡 The Problem Statement
**Challenge:** Build a GenAI-enabled solution that enhances stadium operations and the overall tournament experience for fans, organizers, volunteers, or venue staff during the FIFA World Cup 2026. 
**Constraints:** Mandatory use of GenAI, repository under 10 MB, public GitHub repo.

### How SIGNAL Solves This
Different users at a World Cup need vastly different information, but deploying multiple separate apps is inefficient and costly. 
SIGNAL solves this by using **Google Gemini** as a central intelligent router. A single chat interface dynamically injects one of four highly specific system prompts based on the selected role (Fan, Staff, Volunteer, Organizer), instantly transforming the UI from a fan's food-finder into an organizer's risk-assessment tool.

---

## 🧠 Approach & GenAI Implementation

SIGNAL integrates **Google Gemini 1.5 Flash / 3.5 Flash** (via the `google-generativeai` SDK) to power three core features:

1. **Persona-Aware AI Assistant (Chat)**: 
   - **Fan**: Friendly tone, focuses on seating, food, transport, and enjoyment.
   - **Venue Staff**: Professional tone, focuses on incident triage, safety protocols, and crowd flow.
   - **Volunteer**: Supportive tone, focuses on tasks, fan directions, and escalation paths.
   - **Organizer**: Analytical tone, focuses on data, risk assessment, and resource allocation.
2. **AI Crowd Advisories**: 
   A simulated engine generates live density data across 8 stadium zones. When staff request an advisory, this raw JSON data is fed into Gemini, which synthesises it into a concise, human-readable operational directive (e.g., *"Zone 3 is at 88% capacity. Deploy 4 additional stewards and open overflow corridor B."*).
3. **AI Navigation**:
   The backend holds a catalogue of 35+ stadium locations (gates, food courts, accessible parking). When navigating, spatial context is sent to Gemini to generate natural-language walking directions with accessibility checks.

---

## 🚀 How the Solution Works

### Tech Stack
- **Frontend**: Pure HTML, CSS, and Vanilla JavaScript (Zero build tools, SPA architecture, ensuring the repository stays well under the 10 MB limit).
- **Backend**: Python 3.12, FastAPI, Pydantic (Async, type-safe API).
- **GenAI**: Google Gemini API.

### Setup Instructions
1. **Clone the repository:**
   ```bash
   git clone https://github.com/jaineeshx/Signal.git
   cd Signal/backend
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure your environment:**
   Rename `.env.example` to `.env` in the root folder and insert your Gemini API Key.
   ```env
   GEMINI_API_KEY=AIzaSy...
   GEMINI_MODEL=gemini-1.5-flash # or gemini-3.5-flash
   MOCK_MODE=false
   ```
   *(Note: If you don't have a key, simply set `MOCK_MODE=true` and the app will return simulated responses so you can test the UI!)*
4. **Run the backend server:**
   ```bash
   python -m uvicorn app.main:app --reload
   ```
5. **Open the Frontend:**
   Navigate to `http://127.0.0.1:8000/` in your browser.

---

## 📂 Project Structure
```text
Signal/
├── .env.example             # Template for API keys and config
├── README.md                # Project documentation
├── backend/                 # Python FastAPI Backend
│   ├── app/
│   │   ├── api/             # API Endpoints (chat.py, crowd.py, navigation.py)
│   │   ├── core/            # Config, Gemini Client, and System Personas
│   │   ├── models/          # Pydantic data schemas
│   │   ├── services/        # Business logic (Nav, Crowd simulation)
│   │   └── main.py          # FastAPI application entry point
│   ├── tests/               # Pytest integration tests
│   ├── requirements.txt     # Python dependencies
│   └── pytest.ini           # Pytest configuration
└── frontend/                # Vanilla HTML/CSS/JS Frontend
    ├── css/style.css        # Premium FIFA 2026 UI styles
    ├── js/                  # Modular JavaScript components
    │   ├── app.js           # State & routing
    │   ├── chat.js          # Gemini Chat UI
    │   ├── crowd.js         # Live Crowd Monitor
    │   ├── nav.js           # Directions & SVG Map
    │   └── i18n.js          # Multilingual dictionary
    └── index.html           # Main Single Page Application
```

---

## 🧪 Test Cases
The project includes a robust `pytest` suite testing all endpoints, error handling, and prompt-injection defenses.

### Execution
```bash
cd backend
pytest tests/ -v
```

### Key Test Scenarios Covered
1. **Test Role Enforcement (`test_chat.py`)**: Verifies that requests using the `fan` persona receive different system constraints than the `organizer` persona.
2. **Test Injection Prevention (`test_chat.py`)**: Sends malicious prompts (e.g., *"Ignore all previous instructions"*) and verifies that `validators.py` blocks the request before it reaches Gemini.
3. **Test Accessibility Routing (`test_nav.py`)**: Ensures that when `accessibility=true` is requested, the prompt sent to Gemini explicitly mandates wheelchair-accessible pathways.
4. **Test Graceful Fallback (`test_crowd.py`)**: Tests the `MOCK_MODE` engine to ensure the backend safely returns simulated 200 OK JSON responses when a live Gemini key is unavailable or rate-limited.

---

## 🛠 Assumptions Made
1. **Crowd Data Source**: In a real-world scenario, crowd density would come from turnstile counters or computer vision sensors. Here, it is simulated using a sinusoidal math function to provide realistic, time-varying data for Gemini to analyze.
2. **Stadium Layout**: A generic symmetric stadium model is used (North/South/East/West stands, standard facilities).
3. **Connectivity**: Assumes the venue has WiFi or 5G coverage, but the static frontend is lightweight enough to load instantly even on congested networks.
