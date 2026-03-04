from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uuid

from nlu.intent_classifier import detect_intent
from nlu.entity_extractor import extract_entities
from nlu.fallback_handler import fallback_response
from dialogue.dialogue_manager import handle_dialogue

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models

class StartCallRequest(BaseModel):
    caller_name: str = "Guest"

class UserInputRequest(BaseModel):
    session_id: str
    message: str


# Session storage
sessions = {}


def create_session(caller_name):

    session_id = str(uuid.uuid4())

    sessions[session_id] = {
        "caller_name": caller_name,
        "state": "welcome",
        "data": {},
        "history": [],
        "start_time": datetime.now()
    }

    return session_id


def get_session(session_id):
    return sessions.get(session_id)


def end_session(session_id):

    if session_id in sessions:
        del sessions[session_id]


# Start Call

@app.post("/ivr/start")
def start_call(request: StartCallRequest):

    session_id = create_session(request.caller_name)

    return {
        "session_id": session_id,
        "reply": f"Welcome to CityCare Hospital, {request.caller_name}. How may I help you today?"
    }


# Handle Input

@app.post("/ivr/input")
def handle_input(request: UserInputRequest):

    session = get_session(request.session_id)

    if not session:
        return {"error": "Session not found or expired."}

    user_message = request.message.strip()

    session["history"].append(user_message)

    # Fallback handling
    fallback = fallback_response(user_message)

    if fallback:
        return {"reply": fallback}

    # Intent detection
    intent = detect_intent(user_message)

    # Entity extraction
    entities = extract_entities(user_message)

    # Dialogue manager
    reply = handle_dialogue(session, intent, entities)

    if session["state"] == "ended":
        end_session(request.session_id)
        return {
            "reply": reply,
            "action": "hangup"
        }

    return {"reply": reply}


@app.get("/")
def root():
    return {"status": "Conversational Hospital IVR Running"}