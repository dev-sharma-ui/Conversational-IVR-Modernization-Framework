from data.doctors_db import DOCTOR_DATABASE


def handle_dialogue(session, intent, entities):

    state = session["state"]
    data = session["data"]

    # Store extracted entities
    for key, value in entities.items():
        if value:
            data[key] = value

    # Greeting state
    if state == "welcome":

        if intent == "greeting":
            return "Welcome to CityCare Hospital. How may I help you?"

        session["state"] = "collecting_info"

    # Slot filling state
    if session["state"] == "collecting_info":

        if not data.get("department"):
            return "Which department are you looking for? Cardiology, Orthopedics, or General?"

        if not data.get("date"):
            return "Please tell the appointment date."

        department = data["department"]
        date = data["date"]

        doctors = DOCTOR_DATABASE.get(department, [])

        if not doctors:
            return "Sorry, no doctors available in that department."

        doctor_list = "\n".join(
            [f"{d['name']} ({d['time']})" for d in doctors]
        )

        session["state"] = "show_availability"

        return (
            f"Doctors available in {department} on {date}:\n"
            f"{doctor_list}\n"
            f"Would you like to book an appointment?"
        )

    if state == "show_availability":

        last_input = session["history"][-1].lower()

        if "yes" in last_input:

            session["state"] = "booking"

            return "Please tell me which doctor you want to book."

        if "no" in last_input:

            session["state"] = "ended"

            return "Thank you for contacting CityCare Hospital."

        return "Please answer yes or no."

    if state == "booking":

        doctor = entities.get("doctor")

        if doctor:

            session["data"]["doctor"] = doctor
            session["state"] = "ended"

            return f"Your appointment with {doctor} has been booked."

        return "Please tell the doctor's name."

    return "I'm sorry, something went wrong."