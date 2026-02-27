from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uuid

app = FastAPI()

# Enable CORS for frontend connection
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



# In-Memory Session Storage

sessions = {}

# Mock Doctor Database
DOCTOR_DATABASE = {
    "cardiology": ["Dr. Sharma (10AM-1PM)", "Dr. Rao (3PM-6PM)"],
    "orthopedics": ["Dr. Mehta (9AM-12PM)", "Dr. Singh (4PM-7PM)"],
    "general": ["Dr. Verma (8AM-11AM)", "Dr. Kapoor (2PM-5PM)"]
}



# Helper Functions


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


def detect_department(text):
    text = text.lower()
    for dept in DOCTOR_DATABASE.keys():
        if dept in text:
            return dept
    return None


def validate_date(date_text):
    try:
        datetime.strptime(date_text, "%d-%m-%Y")
        return True
    except:
        return False



# API Routes


@app.post("/ivr/start")
def start_call(request: StartCallRequest):
    session_id = create_session(request.caller_name)

    return {
        "session_id": session_id,
        "reply": f"Welcome to CityCare Hospital, {request.caller_name}. "
                 f"You can inquire about doctor availability. "
                 f"Please tell me the department: Cardiology, Orthopedics, or General."
    }


@app.post("/ivr/input")
def handle_input(request: UserInputRequest):

    session = get_session(request.session_id)

    if not session:
        return {"error": "Session not found or expired."}

    user_message = request.message.strip()
    session["history"].append(user_message)

    state = session["state"]


    # STATE: Welcome -> Ask Department

    if state == "welcome":
        department = detect_department(user_message)

        if not department:
            return {
                "reply": "Please specify a valid department: Cardiology, Orthopedics, or General."
            }

        session["data"]["department"] = department
        session["state"] = "ask_date"

        return {
            "reply": f"You selected {department.capitalize()}. "
                     f"Please enter the date in DD-MM-YYYY format."
        }


    # STATE: Ask Date

    elif state == "ask_date":

        if not validate_date(user_message):
            return {
                "reply": "Invalid date format. Please enter date as DD-MM-YYYY."
            }

        session["data"]["date"] = user_message
        department = session["data"]["department"]
        doctors = DOCTOR_DATABASE.get(department, [])

        session["state"] = "show_availability"

        doctor_list = "\n".join(doctors)

        return {
            "reply": f"Available doctors in {department.capitalize()} on {user_message}:\n"
                     f"{doctor_list}\n\n"
                     f"Would you like to check another department? (yes/no)"
        }


    # STATE: Show Availability

    elif state == "show_availability":

        if user_message.lower() == "yes":
            session["state"] = "welcome"
            session["data"] = {}
            return {
                "reply": "Sure. Please tell me the department: Cardiology, Orthopedics, or General."
            }

        elif user_message.lower() == "no":
            session["state"] = "ended"
            end_session(request.session_id)
            return {
                "reply": "Thank you for contacting CityCare Hospital. Have a good day!",
                "action": "hangup"
            }

        else:
            return {
                "reply": "Please answer with 'yes' or 'no'."
            }

    return {"reply": "Something went wrong. Please restart the call."}


@app.get("/")
def root():
    return {"status": "Hospital Conversational IVR Running"}


