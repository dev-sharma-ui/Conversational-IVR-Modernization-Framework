"""
dialogue_manager.py
--------------------
Purpose: The brain of the IVR system. Implements a slot-filling state machine
that guides the conversation from greeting → collecting info → showing availability
→ booking confirmation → ended.

States:
  welcome          → Initial state when call is started
  collecting_info  → Gathering department and date from user
  show_availability → Presented doctor list, waiting for yes/no
  select_doctor    → Waiting for user to pick a doctor
  confirm_booking  → Appointment confirmed, ending call
  ended            → Session cleanup triggered
"""

import logging
from data.doctors_db import (
    get_doctors_by_department,
    get_all_departments,
    find_doctor_by_name,
    book_appointment,
)
from data.date_validator import validate_date

logger = logging.getLogger(__name__)


def handle_dialogue(session: dict, intent: str, entities: dict) -> str:
    """
    Main dialogue handler. Updates session state and returns the next system response.
    """
    state = session["state"]
    data = session["data"]
    caller = session.get("caller_name", "there")

    # Always merge any newly extracted entities into session data
    for key, value in entities.items():
        if value and not data.get(key):
            data[key] = value

    # ── STATE: welcome ────────────────────────────────────────────────────────
    if state == "welcome":
        if intent == "goodbye":
            session["state"] = "ended"
            return f"Thank you for calling CityCare Hospital, {caller}. Goodbye!"

        # Move to collecting info regardless of intent
        session["state"] = "collecting_info"
        # Fall through to collecting_info immediately

    # ── STATE: collecting_info ────────────────────────────────────────────────
    if session["state"] == "collecting_info":
        # Check if user wants to end
        if intent == "goodbye":
            session["state"] = "ended"
            return "Thank you for calling CityCare Hospital. Have a great day!"

        # Ask for department if missing
        if not data.get("department"):
            depts = ", ".join(d.capitalize() for d in get_all_departments())
            return f"Which department are you looking for? We have: {depts}."

        # Ask for date if missing
        if not data.get("date"):
            from datetime import date as _date
            today_str = _date.today().strftime("%A, %d %B %Y")
            return f"Please tell me the preferred appointment date. Today is {today_str}."

        # ── Validate the date ─────────────────────────────────────────────────
        date_result = validate_date(data["date"])

        if not date_result["valid"]:
            # Date is invalid (past, too far ahead, Sunday, unparseable)
            # Clear the bad date so we ask again
            data.pop("date", None)
            return date_result["error"] + "\nPlease tell me a valid appointment date."

        # Date is valid — store the nicely formatted version
        # e.g. "Monday, 30 March 2026" instead of raw "next monday"
        data["date"] = date_result["formatted"]

        # Both slots filled — query the database
        department = data["department"]
        date = data["date"]
        doctors = get_doctors_by_department(department)

        if not doctors:
            # Unknown department — reset and ask again
            data.pop("department", None)
            depts = ", ".join(d.capitalize() for d in get_all_departments())
            return f"Sorry, I couldn't find that department. Please choose from: {depts}."

        # Build doctor list string
        doctor_lines = "\n".join(
            f"  • {d['name']} ({d['specialization']}) — Available: {d['time']}"
            for d in doctors
        )
        session["state"] = "show_availability"
        session["data"]["available_doctors"] = doctors  # store for later booking

        return (
            f"Here are the doctors available in {department.capitalize()} on {date}:\n"
            f"{doctor_lines}\n\n"
            f"Would you like to book an appointment with one of them? (Yes / No)"
        )

    # ── STATE: show_availability ──────────────────────────────────────────────
    if state == "show_availability":
        last_input = session["history"][-1].lower() if session["history"] else ""

        if "yes" in last_input or intent == "book_appointment":
            session["state"] = "select_doctor"
            available = data.get("available_doctors", [])
            names = ", ".join(d["name"] for d in available)
            return f"Great! Please tell me which doctor you'd like to book. Available: {names}."

        if "no" in last_input or intent == "goodbye":
            session["state"] = "ended"
            return "Alright. Thank you for calling CityCare Hospital. Have a great day!"

        return "I didn't catch that. Would you like to book an appointment? Please say Yes or No."

    # ── STATE: select_doctor ──────────────────────────────────────────────────
    if state == "select_doctor":
        doctor_name = entities.get("doctor") or data.get("doctor")

        if not doctor_name:
            # Try to find a doctor name in the last user message
            last_msg = session["history"][-1] if session["history"] else ""
            available = data.get("available_doctors", [])
            for doc in available:
                # Check if any part of the doctor's last name was mentioned
                last_name = doc["name"].split()[-1].lower()
                if last_name in last_msg.lower():
                    doctor_name = doc["name"]
                    break

        if not doctor_name:
            return "Please tell me the doctor's name you'd like to book with."

        # Validate doctor exists in available list
        available = data.get("available_doctors", [])
        matched_doctor = None
        for doc in available:
            if doctor_name.lower() in doc["name"].lower():
                matched_doctor = doc
                break

        # Also try global search if not found in current list
        if not matched_doctor:
            matched_doctor, _ = find_doctor_by_name(doctor_name)

        if not matched_doctor:
            names = ", ".join(d["name"] for d in available)
            return f"Sorry, I couldn't find that doctor. Please choose from: {names}."

        # Book the appointment
        date = data.get("date", "the selected date")
        session_id = session.get("session_id", "unknown")
        success = book_appointment(matched_doctor["id"], date, session_id)

        if not success:
            return (
                f"Sorry, {matched_doctor['name']} has no available slots on {date}. "
                f"Please choose a different doctor or date."
            )

        data["doctor"] = matched_doctor["name"]
        data["doctor_id"] = matched_doctor["id"]
        session["state"] = "ended"

        return (
            f"✅ Your appointment with {matched_doctor['name']} "
            f"({matched_doctor['specialization']}) has been booked for {date}.\n"
            f"Timing: {matched_doctor['time']}.\n"
            f"Thank you for calling CityCare Hospital, {caller}. Have a healthy day!"
        )

    # ── STATE: ended (shouldn't normally reach here) ──────────────────────────
    if state == "ended":
        return "This session has ended. Thank you for calling CityCare Hospital."

    # Catch-all
    logger.error(f"Unhandled dialogue state: {state}")
    return "I'm sorry, something went wrong. Please try again or call back."
