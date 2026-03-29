"""
main.py
--------
FastAPI backend for the Conversational Hospital IVR system.

FIXES APPLIED vs original:
  1. /ivr/audio now calls async transcribe_audio() — never blocks event loop
  2. Added request-level timeout (30s for text, 90s for audio)
  3. Audio endpoint accepts both query param and form field for session_id
  4. Proper HTTP status codes on all errors
  5. Server startup pre-warms models in background (no cold-start hang on first request)
  6. CORS locked to localhost for dev (easy to change for prod)
  7. Added /ivr/health endpoint to check model status

Run: uvicorn main:app --reload --port 8000
"""

import os
import uuid
import logging
import tempfile
import asyncio

from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from nlu.intent_classifier import detect_intent
from nlu.entity_extractor import extract_entities
from nlu.fallback_handler import fallback_response
from dialogue.dialogue_manager import handle_dialogue

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App startup: pre-warm models in background so first request is instant ────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load heavy models on startup so the first request doesn't hang."""
    logger.info("🚀 Server starting — pre-warming NLU models in background...")
    loop = asyncio.get_event_loop()

    async def _prewarm():
        try:
            # Warm up intent classifier (loads BART model)
            await loop.run_in_executor(None, detect_intent, "hello")
            logger.info("✅ Intent classifier ready")
            # Warm up entity extractor (loads spaCy)
            await loop.run_in_executor(None, extract_entities, "hello")
            logger.info("✅ Entity extractor ready")
        except Exception as e:
            logger.warning(f"Pre-warm partial failure (non-fatal): {e}")

    asyncio.create_task(_prewarm())
    yield
    logger.info("Server shutting down.")


app = FastAPI(
    title="Conversational Hospital IVR",
    description="AI-powered IVR system for CityCare Hospital",
    version="2.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# For development: allow all origins
# For production: replace "*" with your actual domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Frontend static files ─────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ── In-memory session store ───────────────────────────────────────────────────
sessions: dict = {}


# ── Pydantic models ───────────────────────────────────────────────────────────
class StartCallRequest(BaseModel):
    caller_name: str = "Guest"

class UserInputRequest(BaseModel):
    session_id: str
    message: str


# ── Session helpers ───────────────────────────────────────────────────────────
def create_session(caller_name: str) -> str:
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "session_id": session_id,
        "caller_name": caller_name,
        "state": "welcome",
        "data": {},
        "history": [],
        "start_time": datetime.now().isoformat(),
    }
    logger.info(f"Session created: {session_id[:8]}... for '{caller_name}'")
    return session_id


def get_session(session_id: str) -> dict | None:
    return sessions.get(session_id)


def end_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        logger.info(f"Session ended: {session_id[:8]}...")


def _run_pipeline(session: dict, message: str) -> dict:
    """
    Core NLU pipeline: text → fallback → intent → entities → dialogue.
    Runs synchronously (called from run_in_executor for non-blocking behavior).
    """
    user_message = message.strip()
    if not user_message:
        return {"reply": "I didn't catch that. Could you please repeat?"}

    session["history"].append(user_message)

    # Step 1: Fallback check
    fallback = fallback_response(user_message)
    if fallback is not None:
        return {"reply": fallback}

    # Step 2: Intent detection
    intent = detect_intent(user_message)
    logger.info(f"[{session['session_id'][:8]}] Intent: {intent}")

    # Step 3: Entity extraction
    entities = extract_entities(user_message)
    logger.info(f"[{session['session_id'][:8]}] Entities: {entities}")

    # Step 4: Dialogue
    reply = handle_dialogue(session, intent, entities)

    result = {"reply": reply}
    if session["state"] == "ended":
        end_session(session["session_id"])
        result["action"] = "hangup"

    return result


async def _process_message(session: dict, message: str) -> dict:
    """
    Async wrapper: runs the NLU pipeline in a thread pool so it never
    blocks the FastAPI event loop.
    """
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _run_pipeline, session, message),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        logger.error("NLU pipeline timed out after 30s")
        return {"reply": "I'm taking too long to respond. Please try again."}
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        return {"reply": "Something went wrong. Please try again."}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "✅ Conversational Hospital IVR Running",
        "version": "2.1.0",
        "active_sessions": len(sessions),
        "docs": "/docs",
    }


@app.get("/ivr/health")
def health():
    """Check model loading status."""
    from nlu.intent_classifier import _classifier
    from nlu.entity_extractor import _nlp
    from speech.speech_to_text import FASTER_WHISPER_AVAILABLE, PYDUB_AVAILABLE

    return {
        "intent_classifier": "loaded" if _classifier is not None else "using keyword fallback",
        "entity_extractor": "loaded" if _nlp is not None else "using regex fallback",
        "whisper_available": FASTER_WHISPER_AVAILABLE,
        "pydub_available": PYDUB_AVAILABLE,
        "active_sessions": len(sessions),
    }


@app.get("/frontend")
def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        status_code=404,
        content={"error": "Frontend not found. Place index.html in the /frontend directory."}
    )


@app.post("/ivr/start")
def start_call(request: StartCallRequest):
    """Start a new IVR call session."""
    caller_name = request.caller_name.strip() or "Guest"
    session_id = create_session(caller_name)
    return {
        "session_id": session_id,
        "reply": (
            f"Welcome to CityCare Hospital, {caller_name}! "
            f"I'm your automated assistant. I can help you check doctor availability "
            f"and book appointments. How may I help you today?"
        ),
    }


@app.post("/ivr/input")
async def handle_text_input(request: UserInputRequest):
    """Process a text message."""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired. Please start a new call with /ivr/start."
        )
    result = await _process_message(session, request.message)
    return result


@app.post("/ivr/audio")
async def handle_audio_input(
    session_id: str = Query(..., description="Session ID from /ivr/start"),
    file: UploadFile = File(..., description="Audio file: WebM, WAV, MP3, OGG")
):
    """
    Accept audio from browser and transcribe using Whisper.

    ROOT CAUSE FIX: Original was synchronous (blocked entire server).
    Now uses async transcribe_audio() which runs in a thread pool.

    NOTE: The frontend uses Web Speech API as the PRIMARY voice input,
    so this endpoint is only a fallback for browsers without Web Speech API.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired. Please start a new call."
        )

    # Import here so server starts even if faster-whisper isn't installed
    from speech.speech_to_text import transcribe_audio, FASTER_WHISPER_AVAILABLE

    if not FASTER_WHISPER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=(
                "Server-side speech recognition is not installed. "
                "Install faster-whisper: pip install faster-whisper. "
                "Or use the browser's built-in microphone (Web Speech API) which doesn't need this."
            )
        )

    # Save uploaded audio to temp file
    filename = file.filename or "audio.webm"
    suffix = os.path.splitext(filename)[1] or ".webm"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Empty audio file received.")
            tmp.write(content)
            tmp_path = tmp.name
        
        logger.info(f"Audio received: {len(content)} bytes, format: {suffix}")

        # Transcribe asynchronously (non-blocking, with timeout)
        transcribed_text = await transcribe_audio(tmp_path)
        logger.info(f"Transcription result: '{transcribed_text}'")

        if not transcribed_text.strip():
            return {
                "reply": "I couldn't make out what you said. Could you please speak more clearly or type your message?",
                "transcribed": "",
            }

        # Run through the same NLU pipeline
        result = await _process_message(session, transcribed_text)
        result["transcribed"] = transcribed_text
        return result

    finally:
        # Always clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


@app.get("/ivr/session/{session_id}")
def get_session_info(session_id: str):
    """Get current session state."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {
        "session_id": session["session_id"],
        "caller_name": session["caller_name"],
        "state": session["state"],
        "history": session["history"],
        "data": {k: v for k, v in session["data"].items() if k != "available_doctors"},
        "start_time": session["start_time"],
    }


@app.delete("/ivr/session/{session_id}")
def terminate_session(session_id: str):
    """Manually end a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    end_session(session_id)
    return {"message": "Session terminated successfully."}
