<div align="center">

<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" />
<img src="https://img.shields.io/badge/spaCy-NLP-09A3D5?style=for-the-badge&logo=spacy&logoColor=white" />
<img src="https://img.shields.io/badge/Whisper-STT-412991?style=for-the-badge&logo=openai&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />

<br/><br/>

```
 ██████╗ ██╗████████╗██╗   ██╗ ██████╗ █████╗ ██████╗ ███████╗
██╔════╝ ██║╚══██╔══╝╚██╗ ██╔╝██╔════╝██╔══██╗██╔══██╗██╔════╝
██║      ██║   ██║    ╚████╔╝ ██║     ███████║██████╔╝█████╗
██║      ██║   ██║     ╚██╔╝  ██║     ██╔══██║██╔══██╗██╔══╝
╚██████╗ ██║   ██║      ██║   ╚██████╗██║  ██║██║  ██║███████╗
 ╚═════╝ ╚═╝   ╚═╝      ╚═╝    ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
```

# 🏥 Conversational IVR Modernization Framework

### *Transforming "Press 1 for Cardiology" into Natural, AI-Powered Conversations*

<br/>

**A full-stack AI conversational IVR system for hospital services** — built with FastAPI, Hugging Face Transformers, spaCy NER, OpenAI Whisper, and a voice-enabled browser UI.

<br/>

[**📺 Demo**](#-demo) · [**⚡ Quick Start**](#-quick-start) · [**🏗️ Architecture**](#️-architecture) · [**📡 API Reference**](#-api-reference) · [**🗺️ Roadmap**](#️-roadmap)

<br/>

---

</div>

## 📖 Table of Contents

- [✨ What is This?](#-what-is-this)
- [🎯 Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [📁 Project Structure](#-project-structure)
- [⚡ Quick Start](#-quick-start)
- [📡 API Reference](#-api-reference)
- [🧠 How the AI Pipeline Works](#-how-the-ai-pipeline-works)
- [🎤 Voice Flow](#-voice-flow)
- [💬 Conversation Example](#-conversation-example)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ What is This?

Traditional IVR (Interactive Voice Response) systems are painful. They force callers through rigid menus, understand nothing natural, and break the moment someone says something unexpected.

**This project replaces that.** It's a conversational AI backend + frontend that lets hospital patients:

- 🗣️ **Speak or type naturally** — *"I need to see a heart doctor next Monday"*
- 🤖 **Get intelligent responses** — intent detected, entities extracted, slots filled
- 📅 **Book real appointments** — validated against a live doctor database
- 🔊 **Hear responses spoken aloud** — fully automated voice interaction

> Built as a Final Year Engineering Project, this system demonstrates how modern NLP can modernize legacy telephony infrastructure in critical sectors like healthcare.

---

## 🎯 Features

| Feature | Description |
|---------|-------------|
| 🧠 **Zero-Shot Intent Classification** | Uses `facebook/bart-large-mnli` — no labeled training data needed |
| 🔍 **Smart Entity Extraction** | spaCy NER + regex for doctor names, dates, departments + alias mapping |
| 💬 **Slot-Filling Dialogue** | State machine that collects info in any order from natural speech |
| 🎤 **Voice Input** | Browser microphone → Whisper STT → NLU pipeline |
| 🔊 **Text-to-Speech Output** | Browser SpeechSynthesis API reads every response aloud |
| 🛡️ **Graceful Fallback** | 15+ edge cases handled before hitting the AI layer |
| ✅ **Real Appointment Booking** | Database-validated doctor selection and slot management |
| 📡 **REST API** | Clean FastAPI endpoints with auto-generated Swagger docs |
| 🎨 **Modern Web UI** | Dark call-screen UI with waveform visualizer and live transcription |
| 🔁 **Graceful Degradation** | Keyword fallback if BART/spaCy models unavailable |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CALLER (Browser UI)                          │
│                  Types text  OR  Records voice                      │
└────────────────────┬───────────────────────┬────────────────────────┘
                     │ Text                  │ Audio (WebM/WAV)
                     ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (main.py)                      │
│                                                                     │
│   POST /ivr/input              POST /ivr/audio                      │
│         │                            │                              │
│         │                   ┌────────▼─────────┐                   │
│         │                   │  Whisper (STT)   │  speech_to_text.py│
│         │                   └────────┬─────────┘                   │
│         └────────────────────────────┘                              │
│                             │  text                                 │
│                             ▼                                       │
│                  ┌──────────────────────┐                           │
│                  │   Fallback Handler   │  nlu/fallback_handler.py  │
│                  │  (edge cases, noise) │                           │
│                  └──────┬───────────────┘                           │
│                         │ (if not fallback)                         │
│                         ▼                                           │
│                  ┌──────────────────────┐                           │
│                  │  Intent Classifier   │  nlu/intent_classifier.py │
│                  │  (BART zero-shot)    │                           │
│                  └──────┬───────────────┘                           │
│                         │                                           │
│                         ▼                                           │
│                  ┌──────────────────────┐                           │
│                  │  Entity Extractor    │  nlu/entity_extractor.py  │
│                  │  (spaCy + regex)     │                           │
│                  └──────┬───────────────┘                           │
│                         │  intent + entities                        │
│                         ▼                                           │
│                  ┌──────────────────────┐                           │
│                  │  Dialogue Manager    │  dialogue/dialogue_mgr.py │
│                  │  (State Machine)     │                           │
│                  │                      │                           │
│                  │  welcome             │                           │
│                  │    ↓                 │                           │
│                  │  collecting_info     │◄── data/doctors_db.py     │
│                  │    ↓                 │                           │
│                  │  show_availability   │                           │
│                  │    ↓                 │                           │
│                  │  select_doctor       │                           │
│                  │    ↓                 │                           │
│                  │  ended               │                           │
│                  └──────┬───────────────┘                           │
│                         │  JSON response                            │
└─────────────────────────┼───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser Frontend                             │
│           Displays reply text + SpeechSynthesis speaks it          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Conversational-IVR-Modernization-Framework/
│
├── 📂 Project/                          # Backend application
│   │
│   ├── 🐍 main.py                       # FastAPI server · session mgmt · all endpoints
│   │
│   ├── 📂 nlu/                          # Natural Language Understanding layer
│   │   ├── intent_classifier.py         # BART zero-shot intent detection
│   │   ├── entity_extractor.py          # spaCy NER + regex entity extraction
│   │   └── fallback_handler.py          # Edge-case / small-talk interception
│   │
│   ├── 📂 dialogue/                     # Conversation management
│   │   └── dialogue_manager.py          # Slot-filling state machine
│   │
│   ├── 📂 data/                         # Data layer
│   │   └── doctors_db.py               # Doctor DB · booking records · availability
│   │
│   └── 📂 speech/                       # Audio processing
│       └── speech_to_text.py            # Whisper audio transcription
│
├── 📂 frontend/                         # Browser-based IVR UI
│   └── index.html                       # Single-file web app (HTML + CSS + JS)
│
├── 📄 requirements.txt                  # Python dependencies
├── 📄 README.md                         # This file
├── 📄 .gitignore
└── 📄 LICENSE
```

---

## ⚡ Quick Start

### Prerequisites

- Python **3.10+**
- pip
- 4 GB RAM minimum *(for BART model)*
- Microphone *(optional, for voice features)*

---

### 1️⃣ Clone the repo

```bash
git clone https://github.com/dev-sharma-ui/Conversational-IVR-Modernization-Framework.git
cd Conversational-IVR-Modernization-Framework
```

### 2️⃣ Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Download the spaCy language model

```bash
python -m spacy download en_core_web_sm
```

### 5️⃣ Start the backend server

```bash
cd Project
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     ✅ Transformer intent classifier loaded.
INFO:     ✅ spaCy model loaded.
```

### 6️⃣ Open the frontend

Option A — Direct file:
```
Open  frontend/index.html  in your browser
```

Option B — Served by FastAPI:
```
http://localhost:8000/frontend
```

Option C — Swagger API docs:
```
http://localhost:8000/docs
```

---

### 🌐 Expose with ngrok *(optional — for remote testing or mobile)*

```bash
ngrok http 8000
```

Copy the HTTPS URL into `frontend/index.html` → change `API_BASE`:
```javascript
const API_BASE = "https://your-ngrok-url.ngrok-free.app";
```

---

## 📡 API Reference

### `POST /ivr/start`
Start a new IVR call session.

**Request:**
```json
{
  "caller_name": "Rahul Sharma"
}
```

**Response:**
```json
{
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "reply": "Welcome to CityCare Hospital, Rahul Sharma! I'm your automated assistant..."
}
```

---

### `POST /ivr/input`
Send a text message to the IVR.

**Request:**
```json
{
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "message": "I need to see a cardiologist next Monday"
}
```

**Response:**
```json
{
  "reply": "Here are the doctors available in Cardiology on next Monday:\n  • Dr. Sharma (Cardiologist) — Available: 10AM - 1PM\n  • Dr. Rao (Cardiac Surgeon) — Available: 3PM - 6PM\n\nWould you like to book an appointment with one of them? (Yes / No)"
}
```

---

### `POST /ivr/audio?session_id={id}`
Send a voice recording. The backend transcribes it with Whisper and processes it through the same NLU pipeline.

**Request:** `multipart/form-data` with audio file (WebM, WAV, MP3, OGG)

**Response:**
```json
{
  "reply": "Great! Please tell me which doctor you'd like to book.",
  "transcribed": "yes please go ahead"
}
```

---

### `GET /ivr/session/{session_id}`
Retrieve current session state.

**Response:**
```json
{
  "session_id": "f47ac10b...",
  "caller_name": "Rahul Sharma",
  "state": "show_availability",
  "history": ["hello", "cardiology next monday"],
  "data": { "department": "cardiology", "date": "next monday" },
  "start_time": "2024-12-20T10:30:00"
}
```

---

### `DELETE /ivr/session/{session_id}`
Manually terminate a session (e.g. user closes browser tab).

---

### `GET /`
Health check.

```json
{
  "status": "✅ Conversational Hospital IVR is running",
  "version": "2.0.0",
  "active_sessions": 3
}
```

---

## 🧠 How the AI Pipeline Works

### Intent Classification
Uses `facebook/bart-large-mnli` — a **zero-shot** classifier. No training data, no fine-tuning. Simply describes each intent in plain English and lets the model decide.

```python
INTENTS = [
    "check_doctor_availability",
    "book_appointment",
    "cancel_appointment",
    "greeting",
    "goodbye",
    "fallback"
]
```

If confidence score < **0.35**, falls back to keyword-based detection automatically.

---

### Entity Extraction
Three-layer extraction strategy:

```
Layer 1: spaCy NER          → PERSON (doctor names), DATE (appointment dates)
Layer 2: Regex patterns      → "tomorrow", "25th December", "2024-12-25"
Layer 3: Keyword aliases     → "heart" → cardiology, "bone" → orthopedics
```

**Department aliases supported:**

| User says | Resolved to |
|-----------|-------------|
| heart, cardiac | cardiology |
| bone, joint, spine | orthopedics |
| skin | dermatology |
| nerve, brain | neurology |
| gp, physician, family | general |

---

### Dialogue State Machine

```
[welcome]
    │
    ▼ (any input)
[collecting_info]
    │
    ├─ missing department? → "Which department?"
    ├─ missing date?       → "What date?"
    │
    ▼ (both collected)
[show_availability]
    │
    ├─ "yes" → [select_doctor]
    └─ "no"  → [ended]
         │
         ▼
    [select_doctor]
         │
         ▼ (doctor validated against DB)
    [ended] → session deleted, "hangup" action returned
```

---

### Fallback Handler
Intercepts 15+ conversational edge cases **before** the AI layer:

| Input | Response |
|-------|----------|
| *(empty / silence)* | "I didn't catch that. Could you please repeat?" |
| "how are you" | "I am functioning properly. How may I assist you?" |
| "emergency" | "For emergencies, please call 112 immediately..." |
| "speak to a human" | "Please stay on the line, I will transfer you..." |
| "what departments" | Lists all available departments |
| "um", "uh", "..." | "I didn't quite understand. Could you speak clearly?" |

---

## 🎤 Voice Flow

```
1. User clicks 🎤 "Hold to Speak"
2. Browser MediaRecorder API captures audio → WebM blob
3. Waveform visualizer animates in real-time
4. User clicks "Stop Recording"
5. Audio blob POST'd to /ivr/audio?session_id=xxx
6. faster-whisper transcribes audio → text
7. Transcription displayed in chat ("🎤 [voice message]" + chip showing text)
8. Text passes through full NLU pipeline
9. Response returned as JSON
10. Browser SpeechSynthesis API reads response aloud
11. Caller hears the response spoken
```

---

## 💬 Conversation Example

```
🤖  Welcome to CityCare Hospital, Priya! How may I help you today?

👤  Hi, I need to see a doctor for my heart

🤖  Which department are you looking for?
    We have: Cardiology, Orthopedics, General, Neurology, Dermatology.

    (Priya already said "heart" — entity extractor maps it to cardiology)
    → Actually skips this and asks for date instead:

🤖  Please tell me the preferred appointment date.

👤  Next Friday

🤖  Here are the doctors available in Cardiology on next Friday:
      • Dr. Sharma (Cardiologist) — Available: 10AM - 1PM
      • Dr. Rao (Cardiac Surgeon) — Available: 3PM - 6PM

    Would you like to book an appointment with one of them? (Yes / No)

👤  Yes please

🤖  Great! Please tell me which doctor you'd like to book.
    Available: Dr. Sharma, Dr. Rao.

👤  Dr. Sharma

🤖  ✅ Your appointment with Dr. Sharma (Cardiologist) has been booked for next Friday.
    Timing: 10AM - 1PM.
    Thank you for calling CityCare Hospital, Priya. Have a healthy day!

    [Call Ended — session deleted]
```

---

## ⚙️ Configuration

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `WHISPER_MODEL_SIZE` | `base`  | Whisper model size: `tiny` (fast) · `base` · `small` · `medium` (accurate) |

Set it before running:
```bash
# Linux / macOS
export WHISPER_MODEL_SIZE=small
uvicorn main:app --port 8000

# Windows
set WHISPER_MODEL_SIZE=small
uvicorn main:app --port 8000
```

---

## 🏥 Available Departments & Doctors

| Department | Doctor | Specialization | Hours |
|------------|--------|----------------|-------|
| Cardiology | Dr. Sharma | Cardiologist | 10AM – 1PM |
| Cardiology | Dr. Rao | Cardiac Surgeon | 3PM – 6PM |
| Orthopedics | Dr. Mehta | Orthopedic Surgeon | 9AM – 12PM |
| Orthopedics | Dr. Singh | Joint Specialist | 4PM – 7PM |
| General | Dr. Verma | General Physician | 8AM – 11AM |
| General | Dr. Kapoor | Family Medicine | 2PM – 5PM |
| Neurology | Dr. Iyer | Neurologist | 10AM – 1PM |
| Neurology | Dr. Bhatia | Neuro Surgeon | 3PM – 6PM |
| Dermatology | Dr. Gupta | Dermatologist | 9AM – 12PM |
| Dermatology | Dr. Nair | Skin Specialist | 2PM – 5PM |

---

## 🗺️ Roadmap

### ✅ Completed (Milestones 1–4)
- [x] Traditional IVR research & gap analysis
- [x] Rule-based IVR backend (FastAPI + sessions)
- [x] AI NLU layer (BART intent + spaCy entities + fallback)
- [x] Dialogue manager (slot-filling state machine)
- [x] Whisper speech-to-text integration
- [x] Voice-enabled browser frontend
- [x] Text-to-speech output
- [x] Validated appointment booking
- [x] End-to-end testing & deployment

### 🔜 Upcoming
- [ ] PostgreSQL / MongoDB for persistent appointment storage
- [ ] Admin dashboard for hospital staff
- [ ] Real-time audio streaming via WebSockets
- [ ] Multi-language support (Hindi, Tamil, Kannada)
- [ ] Twilio integration for real phone calls
- [ ] ElevenLabs / Azure TTS for professional voice output
- [ ] Call analytics dashboard
- [ ] HIPAA-compliant data handling
- [ ] Fine-tuned medical NLP for clinical entities
- [ ] EHR (Electronic Health Record) integration

---

## 🤝 Contributing

Contributions are welcome! Here's how:

```bash
# 1. Fork the repo
# 2. Create a feature branch
git checkout -b feature/your-feature-name

# 3. Make your changes and commit
git commit -m "feat: add your feature description"

# 4. Push and open a Pull Request
git push origin feature/your-feature-name
```

**Please follow these guidelines:**
- Keep each PR focused on a single feature or fix
- Add comments to new functions explaining their purpose
- Test your changes before submitting
- Update this README if you add new endpoints or modules

---

## 🐛 Known Issues

| Issue | Status | Notes |
|-------|--------|-------|
| Sessions lost on server restart | 🟡 Known | In-memory store — Redis/PostgreSQL planned |
| BART model slow on first load | 🟡 Known | ~30s cold start; subsequent calls are fast |
| CORS set to `*` | 🟡 Dev only | Restrict `allow_origins` before production deploy |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ as a Final Year Engineering Project**

*Conversational IVR Modernization Framework — CityCare Hospital*

<br/>

⭐ **If you found this useful, please star the repo!** ⭐

<br/>

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=flat-square&logo=huggingface&logoColor=black)
![spaCy](https://img.shields.io/badge/spaCy-09A3D5?style=flat-square)
![Whisper](https://img.shields.io/badge/Whisper-412991?style=flat-square&logo=openai&logoColor=white)

</div>
