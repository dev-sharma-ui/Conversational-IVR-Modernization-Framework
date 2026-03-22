"""
doctors_db.py
-------------
Purpose: Stores the hospital's doctor information and manages appointment bookings.
This acts as the in-memory database for the IVR system.
In future milestones, replace with PostgreSQL/MongoDB.
"""

# Doctor database keyed by department
DOCTOR_DATABASE = {
    "cardiology": [
        {"id": "DR001", "name": "Dr. Sharma", "time": "10AM - 1PM", "specialization": "Cardiologist"},
        {"id": "DR002", "name": "Dr. Rao",    "time": "3PM - 6PM",  "specialization": "Cardiac Surgeon"},
    ],
    "orthopedics": [
        {"id": "DR003", "name": "Dr. Mehta", "time": "9AM - 12PM", "specialization": "Orthopedic Surgeon"},
        {"id": "DR004", "name": "Dr. Singh", "time": "4PM - 7PM",  "specialization": "Joint Specialist"},
    ],
    "general": [
        {"id": "DR005", "name": "Dr. Verma",  "time": "8AM - 11AM", "specialization": "General Physician"},
        {"id": "DR006", "name": "Dr. Kapoor", "time": "2PM - 5PM",  "specialization": "Family Medicine"},
    ],
    "neurology": [
        {"id": "DR007", "name": "Dr. Iyer",   "time": "10AM - 1PM", "specialization": "Neurologist"},
        {"id": "DR008", "name": "Dr. Bhatia", "time": "3PM - 6PM",  "specialization": "Neuro Surgeon"},
    ],
    "dermatology": [
        {"id": "DR009", "name": "Dr. Gupta",  "time": "9AM - 12PM", "specialization": "Dermatologist"},
        {"id": "DR010", "name": "Dr. Nair",   "time": "2PM - 5PM",  "specialization": "Skin Specialist"},
    ],
}

# In-memory appointments store
# Format: { "DR001_2024-12-20": ["session_id1", "session_id2"] }
APPOINTMENTS = {}


def get_doctors_by_department(department: str):
    """Return list of doctors for a given department."""
    return DOCTOR_DATABASE.get(department.lower(), [])


def get_all_departments():
    """Return list of all available departments."""
    return list(DOCTOR_DATABASE.keys())


def find_doctor_by_name(name: str):
    """
    Search for a doctor by partial name match across all departments.
    Returns (doctor_dict, department) or (None, None).
    """
    name_lower = name.lower()
    for dept, doctors in DOCTOR_DATABASE.items():
        for doc in doctors:
            if name_lower in doc["name"].lower():
                return doc, dept
    return None, None


def book_appointment(doctor_id: str, date: str, session_id: str):
    """
    Book an appointment slot.
    Returns True if booking succeeded, False if slot is full (max 5 per slot).
    """
    key = f"{doctor_id}_{date}"
    if key not in APPOINTMENTS:
        APPOINTMENTS[key] = []
    if len(APPOINTMENTS[key]) >= 5:
        return False
    APPOINTMENTS[key].append(session_id)
    return True


def get_appointment_count(doctor_id: str, date: str):
    """Return number of existing bookings for a doctor on a date."""
    key = f"{doctor_id}_{date}"
    return len(APPOINTMENTS.get(key, []))
