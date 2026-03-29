# =============================================================================
# tests/test_ivr.py
#
# Full test suite for the Conversational IVR Modernization Framework
# Covers: Unit Tests · Integration Tests · E2E Tests · Performance Tests
#         Error Handling Tests · Logging Tests
#
# Run with:
#   cd Project
#   ..\venv\Scripts\python.exe -m pytest tests/test_ivr.py -v
# =============================================================================

import sys
import os
import time
import logging

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app

# ── TestClient setup ──────────────────────────────────────────────────────────
# TestClient MUST be initialized with the FastAPI app instance
# Common mistake from reference code: TestClient() with no argument → TypeError
client = TestClient(app)


# =============================================================================
# LAYER 1 — UNIT TESTS  (< 100ms each)
# Purpose: Test a single function or endpoint in complete isolation.
# These do NOT depend on other modules or external services.
# =============================================================================

class TestUnitFallbackHandler:
    """
    Unit tests for fallback_handler.py
    Tests that edge-case inputs are intercepted before reaching the AI models.
    """

    def test_empty_input_returns_response(self):
        """Empty string should return a 'didn't catch that' message, not crash."""
        from nlu.fallback_handler import fallback_response
        result = fallback_response("")
        assert result is not None
        assert "catch" in result.lower() or "repeat" in result.lower()

    def test_whitespace_only_is_treated_as_empty(self):
        """Pure whitespace should behave the same as empty input."""
        from nlu.fallback_handler import fallback_response
        result = fallback_response("   ")
        assert result is not None

    def test_small_talk_how_are_you(self):
        """'how are you' is small talk — should be handled by fallback, not AI."""
        from nlu.fallback_handler import fallback_response
        result = fallback_response("how are you")
        assert result is not None
        assert "functioning" in result.lower() or "assist" in result.lower()

    def test_emergency_keyword(self):
        """'emergency' should trigger the emergency response immediately."""
        from nlu.fallback_handler import fallback_response
        result = fallback_response("emergency")
        assert result is not None
        assert "112" in result or "emergency" in result.lower()

    def test_real_input_returns_none(self):
        """
        A genuine user message should NOT be caught by the fallback handler.
        It should return None so the AI pipeline runs.
        """
        from nlu.fallback_handler import fallback_response
        result = fallback_response("I need to see a cardiologist")
        assert result is None

    def test_noise_input_caught(self):
        """Filler words like 'um' should be caught by fallback."""
        from nlu.fallback_handler import fallback_response
        result = fallback_response("um")
        assert result is not None

    def test_yes_returns_none(self):
        """'yes' should return None so the dialogue manager handles it."""
        from nlu.fallback_handler import fallback_response
        result = fallback_response("yes")
        assert result is None

    def test_no_returns_none(self):
        """'no' should return None so the dialogue manager handles it."""
        from nlu.fallback_handler import fallback_response
        result = fallback_response("no")
        assert result is None


class TestUnitDoctorsDB:
    """
    Unit tests for data/doctors_db.py
    Tests that the doctor database functions return correct data.
    """

    def test_get_doctors_cardiology_returns_list(self):
        """Cardiology department should have at least one doctor."""
        from data.doctors_db import get_doctors_by_department
        doctors = get_doctors_by_department("cardiology")
        assert isinstance(doctors, list)
        assert len(doctors) > 0

    def test_get_doctors_unknown_department_returns_empty(self):
        """An unknown department should return an empty list, not crash."""
        from data.doctors_db import get_doctors_by_department
        doctors = get_doctors_by_department("dentistry")
        assert doctors == []

    def test_doctor_record_has_required_fields(self):
        """Every doctor record must have id, name, time, and specialization."""
        from data.doctors_db import get_doctors_by_department
        doctors = get_doctors_by_department("cardiology")
        for doc in doctors:
            assert "id" in doc
            assert "name" in doc
            assert "time" in doc
            assert "specialization" in doc

    def test_find_doctor_by_name_partial_match(self):
        """find_doctor_by_name should find 'Dr. Sharma' when given 'sharma'."""
        from data.doctors_db import find_doctor_by_name
        doctor, dept = find_doctor_by_name("sharma")
        assert doctor is not None
        assert "Sharma" in doctor["name"]
        assert dept == "cardiology"

    def test_find_doctor_by_name_not_found(self):
        """A name that doesn't exist in the DB should return (None, None)."""
        from data.doctors_db import find_doctor_by_name
        doctor, dept = find_doctor_by_name("Dr. XYZ Fake")
        assert doctor is None
        assert dept is None

    def test_book_appointment_succeeds(self):
        """Booking a valid slot should return True."""
        from data.doctors_db import book_appointment
        result = book_appointment("DR001", "Friday, 10 April 2026", "test-session-001")
        assert result is True

    def test_book_appointment_slot_limit(self):
        """After 5 bookings, a slot should be full and return False."""
        from data.doctors_db import book_appointment, APPOINTMENTS
        date = "Friday, 17 April 2026"
        key = f"DR002_{date}"
        APPOINTMENTS.pop(key, None)
        for i in range(5):
            book_appointment("DR002", date, f"session-{i}")
        result = book_appointment("DR002", date, "session-overflow")
        assert result is False

    def test_get_all_departments_returns_expected(self):
        """All 5 departments should be present."""
        from data.doctors_db import get_all_departments
        depts = get_all_departments()
        assert "cardiology" in depts
        assert "orthopedics" in depts
        assert "general" in depts
        assert "neurology" in depts
        assert "dermatology" in depts


class TestUnitDateValidator:
    """
    Unit tests for data/date_validator.py
    Tests that date parsing and validation works correctly.
    """

    def _next_valid_weekday(self):
        """Helper: returns tomorrow or the next non-Sunday date as a string."""
        from datetime import date, timedelta
        today = date.today()
        candidate = today + timedelta(days=1)
        while candidate.weekday() == 6:  # skip Sunday — hospital closed
            candidate += timedelta(days=1)
        return candidate

    def test_past_date_is_rejected(self):
        """A date in the past should be invalid."""
        from data.date_validator import validate_date
        result = validate_date("23rd March 2026")
        assert result["valid"] is False
        assert "passed" in result["error"].lower() or "past" in result["error"].lower()

    def test_tomorrow_is_valid(self):
        """A future weekday should always be valid."""
        from data.date_validator import validate_date
        candidate = self._next_valid_weekday()
        date_str = candidate.strftime("%d %B %Y")
        result = validate_date(date_str)
        assert result["valid"] is True
        assert result["formatted"] is not None

    def test_next_monday_is_valid(self):
        """'next monday' should resolve to a valid future date."""
        from data.date_validator import validate_date
        result = validate_date("next monday")
        assert result["valid"] is True
        assert "Monday" in result["formatted"]

    def test_sunday_is_rejected(self):
        """Hospital is closed on Sundays — should be rejected."""
        from data.date_validator import validate_date
        result = validate_date("next sunday")
        assert result["valid"] is False
        assert "sunday" in result["error"].lower() or "closed" in result["error"].lower()

    def test_today_is_rejected(self):
        """Same-day booking is not allowed."""
        from data.date_validator import validate_date
        result = validate_date("today")
        assert result["valid"] is False

    def test_far_future_date_rejected(self):
        """Dates more than 90 days ahead should be rejected."""
        from data.date_validator import validate_date
        result = validate_date("1st January 2030")
        assert result["valid"] is False
        assert "advance" in result["error"].lower() or "90" in result["error"]

    def test_garbage_input_rejected(self):
        """Completely unrecognizable input should be rejected gracefully."""
        from data.date_validator import validate_date
        result = validate_date("blahblahblah")
        assert result["valid"] is False
        assert result["error"] is not None

    def test_iso_format_date(self):
        """ISO format like '2026-04-15' should be parsed correctly."""
        from data.date_validator import validate_date
        result = validate_date("2026-04-15")
        assert result["valid"] is True

    def test_formatted_output_is_human_readable(self):
        """Valid dates should return a nicely formatted string like 'Monday, 30 March 2026'."""
        from data.date_validator import validate_date
        candidate = self._next_valid_weekday()
        date_str = candidate.strftime("%d %B %Y")
        result = validate_date(date_str)
        assert result["valid"] is True
        assert result["formatted"] is not None
        assert str(candidate.year) in result["formatted"]


class TestUnitEntityExtractor:
    """
    Unit tests for nlu/entity_extractor.py
    Tests the alias mapping and regex extraction (no AI model needed).
    """

    def test_heart_maps_to_cardiology(self):
        from nlu.entity_extractor import _extract_department
        assert _extract_department("I have a heart problem") == "cardiology"

    def test_cardiologist_maps_to_cardiology(self):
        from nlu.entity_extractor import _extract_department
        assert _extract_department("I need a cardiologist") == "cardiology"

    def test_knee_maps_to_orthopedics(self):
        from nlu.entity_extractor import _extract_department
        assert _extract_department("my knee hurts") == "orthopedics"

    def test_skin_maps_to_dermatology(self):
        from nlu.entity_extractor import _extract_department
        assert _extract_department("I have a skin rash") == "dermatology"

    def test_migraine_maps_to_neurology(self):
        from nlu.entity_extractor import _extract_department
        assert _extract_department("I have a migraine") == "neurology"

    def test_unknown_returns_none(self):
        from nlu.entity_extractor import _extract_department
        assert _extract_department("I want to see a doctor") is None

    def test_tomorrow_extracted(self):
        from nlu.entity_extractor import _extract_date_regex
        result = _extract_date_regex("I need an appointment tomorrow")
        assert result == "tomorrow"

    def test_next_friday_extracted(self):
        from nlu.entity_extractor import _extract_date_regex
        result = _extract_date_regex("Can I come next Friday")
        assert result is not None
        assert "friday" in result.lower()


# =============================================================================
# LAYER 2 — INTEGRATION TESTS  (~1–5 seconds each)
# Purpose: Verify that API endpoints correctly talk to sessions and the DB.
# =============================================================================

class TestIntegrationSessionManagement:
    """
    Integration tests for session creation, retrieval and deletion.
    """

    def test_start_call_creates_session(self):
        """POST /ivr/start should create a session and return a session_id."""
        resp = client.post("/ivr/start", json={"caller_name": "Rahul"})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "reply" in data
        assert len(data["session_id"]) > 0

    def test_start_call_welcome_message_contains_name(self):
        """The welcome message should include the caller's name."""
        resp = client.post("/ivr/start", json={"caller_name": "Priya"})
        assert resp.status_code == 200
        assert "Priya" in resp.json()["reply"]

    def test_start_call_without_name_uses_guest(self):
        """If no name is given, system should use 'Guest' as default."""
        resp = client.post("/ivr/start", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data

    def test_get_session_info_after_start(self):
        """GET /ivr/session/{id} should return session state after creation."""
        start = client.post("/ivr/start", json={"caller_name": "Dev"})
        sid = start.json()["session_id"]
        resp = client.get(f"/ivr/session/{sid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["caller_name"] == "Dev"
        assert data["state"] == "welcome" or data["state"] == "collecting_info"

    def test_delete_session_removes_it(self):
        """DELETE /ivr/session/{id} should remove the session."""
        start = client.post("/ivr/start", json={"caller_name": "Test"})
        sid = start.json()["session_id"]
        delete = client.delete(f"/ivr/session/{sid}")
        assert delete.status_code == 200
        resp = client.get(f"/ivr/session/{sid}")
        assert resp.status_code == 404

    def test_input_to_nonexistent_session_returns_404(self):
        """Sending input to a session that doesn't exist should return 404."""
        resp = client.post("/ivr/input", json={
            "session_id": "fake-session-id-00000",
            "message": "hello"
        })
        assert resp.status_code == 404


class TestIntegrationConversationFlow:
    """
    Integration tests verifying the conversation state machine
    correctly transitions states as user sends messages.
    """

    def _start(self, name="TestUser"):
        resp = client.post("/ivr/start", json={"caller_name": name})
        return resp.json()["session_id"]

    def _send(self, sid, message):
        resp = client.post("/ivr/input", json={
            "session_id": sid,
            "message": message
        })
        return resp.json()

    def test_greeting_moves_to_collecting_info(self):
        """After greeting, system should ask for department."""
        sid = self._start()
        data = self._send(sid, "hello")
        assert "reply" in data
        assert any(word in data["reply"].lower() for word in
                   ["department", "cardiology", "orthopedics"])

    def test_department_given_asks_for_date(self):
        """After giving department, system should ask for date."""
        sid = self._start()
        self._send(sid, "hello")
        data = self._send(sid, "cardiology")
        assert "date" in data["reply"].lower() or "appointment" in data["reply"].lower()

    def test_past_date_is_rejected_in_conversation(self):
        """Providing a past date should trigger rejection and re-ask."""
        sid = self._start()
        self._send(sid, "hello")
        self._send(sid, "cardiology")
        data = self._send(sid, "23rd March 2026")
        assert any(word in data["reply"].lower() for word in
                   ["passed", "past", "already", "future"])

    def test_valid_date_shows_doctors(self):
        """After valid department + date, system should show available doctors."""
        sid = self._start()
        self._send(sid, "hello")
        self._send(sid, "cardiology")
        data = self._send(sid, "next friday")
        assert any(word in data["reply"].lower() for word in
                   ["dr.", "doctor", "available", "sharma", "rao"])

    def test_session_state_tracked_in_db(self):
        """Session state in /ivr/session should reflect conversation progress."""
        sid = self._start()
        self._send(sid, "hello")
        self._send(sid, "cardiology")
        resp = client.get(f"/ivr/session/{sid}")
        data = resp.json()
        assert data["state"] != "welcome"
        assert data["data"].get("department") == "cardiology"


# =============================================================================
# LAYER 3 — END-TO-END (E2E) TESTS  (~10–30 seconds each)
# Purpose: Simulate a complete real user call from start to finish.
# =============================================================================

class TestE2EFullCallFlow:
    """
    E2E tests simulating a complete IVR call journey.
    """

    def test_full_happy_path_text_booking(self):
        """
        User Story: Book a cardiology appointment for next Friday with Dr. Sharma.
        Full flow: start → greet → department → date → yes → doctor → confirm
        """
        # Step 1: Start the call
        start = client.post("/ivr/start", json={"caller_name": "Rahul"})
        assert start.status_code == 200
        sid = start.json()["session_id"]
        assert "Welcome" in start.json()["reply"]

        # Step 2: Send greeting
        resp = client.post("/ivr/input", json={"session_id": sid, "message": "hello"})
        assert resp.status_code == 200

        # Step 3: Give department
        resp = client.post("/ivr/input", json={"session_id": sid, "message": "cardiology"})
        assert resp.status_code == 200
        assert "date" in resp.json()["reply"].lower() or \
               "appointment" in resp.json()["reply"].lower()

        # Step 4: Give valid future date
        resp = client.post("/ivr/input", json={"session_id": sid, "message": "next friday"})
        assert resp.status_code == 200
        reply = resp.json()["reply"].lower()
        assert "dr." in reply or "sharma" in reply or "available" in reply

        # Step 5: Confirm booking
        resp = client.post("/ivr/input", json={"session_id": sid, "message": "yes"})
        assert resp.status_code == 200

        # Step 6: Select doctor
        resp = client.post("/ivr/input", json={"session_id": sid, "message": "Dr. Sharma"})
        assert resp.status_code == 200
        reply = resp.json()["reply"]
        assert "booked" in reply.lower() or "appointment" in reply.lower()

        print("E2E happy path completed successfully")

    def test_full_flow_with_alias_department(self):
        """
        User Story: Caller says 'heart doctor' instead of 'cardiology'.
        The alias map should resolve it correctly.
        """
        start = client.post("/ivr/start", json={"caller_name": "Anita"})
        sid = start.json()["session_id"]
        client.post("/ivr/input", json={"session_id": sid, "message": "hello"})
        resp = client.post("/ivr/input", json={
            "session_id": sid,
            "message": "I have a heart problem"
        })
        assert resp.status_code == 200
        reply = resp.json()["reply"].lower()
        assert "date" in reply or "appointment" in reply

    def test_goodbye_ends_session(self):
        """
        User Story: Caller changes their mind and says goodbye.
        Session should end cleanly.
        """
        start = client.post("/ivr/start", json={"caller_name": "User"})
        sid = start.json()["session_id"]
        client.post("/ivr/input", json={"session_id": sid, "message": "hello"})
        resp = client.post("/ivr/input", json={"session_id": sid, "message": "goodbye"})
        assert resp.status_code == 200
        reply = resp.json()["reply"].lower()
        assert "thank" in reply or "goodbye" in reply or "bye" in reply

    def test_invalid_department_then_correct(self):
        """
        Edge Case: Caller gives invalid department first, then corrects it.
        """
        start = client.post("/ivr/start", json={"caller_name": "Test"})
        sid = start.json()["session_id"]
        client.post("/ivr/input", json={"session_id": sid, "message": "hello"})
        resp = client.post("/ivr/input", json={
            "session_id": sid,
            "message": "dentistry"
        })
        assert resp.status_code == 200
        resp = client.post("/ivr/input", json={
            "session_id": sid,
            "message": "cardiology"
        })
        assert resp.status_code == 200

    def test_user_says_no_to_booking(self):
        """
        Edge Case: After seeing doctors, user says 'no' to booking.
        Call should end gracefully.
        """
        start = client.post("/ivr/start", json={"caller_name": "User"})
        sid = start.json()["session_id"]
        client.post("/ivr/input", json={"session_id": sid, "message": "hello"})
        client.post("/ivr/input", json={"session_id": sid, "message": "cardiology"})
        client.post("/ivr/input", json={"session_id": sid, "message": "next friday"})
        resp = client.post("/ivr/input", json={"session_id": sid, "message": "no"})
        assert resp.status_code == 200
        reply = resp.json()["reply"].lower()
        assert "thank" in reply or "goodbye" in reply

        print("E2E no-booking flow completed successfully")

    def test_session_cleared_after_call_ends(self):
        """
        After session ends (hangup), sending another message should return 404.
        """
        start = client.post("/ivr/start", json={"caller_name": "User"})
        sid = start.json()["session_id"]
        client.post("/ivr/input", json={"session_id": sid, "message": "hello"})
        resp = client.post("/ivr/input", json={"session_id": sid, "message": "goodbye"})
        if resp.json().get("action") == "hangup":
            follow = client.post("/ivr/input", json={
                "session_id": sid,
                "message": "hello again"
            })
            assert follow.status_code == 404


# =============================================================================
# LAYER 4 — PERFORMANCE / LOAD TESTS
# =============================================================================

class TestPerformance:
    """
    Performance tests measuring response time under load.
    """

    IVR_URL = "http://localhost:8000"

    def test_root_endpoint_response_time(self):
        """Health check endpoint should respond in under 500ms."""
        start = time.time()
        resp = client.get("/")
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 0.5, f"Root endpoint too slow: {elapsed:.2f}s"

    def test_start_call_response_time(self):
        """Starting a call should complete in under 1 second."""
        start = time.time()
        resp = client.post("/ivr/start", json={"caller_name": "PerfTest"})
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 1.0, f"/ivr/start too slow: {elapsed:.2f}s"

    def test_multiple_concurrent_sessions(self):
        """
        Simulate 10 callers starting sessions simultaneously.
        All should succeed with unique session IDs.
        """
        session_ids = []
        for i in range(10):
            resp = client.post("/ivr/start", json={"caller_name": f"User{i}"})
            assert resp.status_code == 200
            session_ids.append(resp.json()["session_id"])
        assert len(set(session_ids)) == 10, "Duplicate session IDs detected!"
        print(f"Created 10 concurrent sessions successfully")

    def test_load_test_20_requests(self):
        """
        Send 20 sequential requests and measure average response time.
        Average must be under 2 seconds per request.
        """
        num_requests = 20
        success = 0
        start_time = time.time()

        for i in range(num_requests):
            resp = client.post("/ivr/start", json={"caller_name": f"LoadTest{i}"})
            if resp.status_code == 200:
                success += 1

        total_time = time.time() - start_time
        avg_time = total_time / num_requests

        print(f"Sent {num_requests} requests, {success} succeeded")
        print(f"Average response time: {avg_time:.2f}s")

        assert success == num_requests, f"Only {success}/{num_requests} succeeded"
        assert avg_time < 2.0, f"Average response time too slow: {avg_time:.2f}s"


# =============================================================================
# LAYER 5 — ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """
    Tests that the system handles bad inputs and edge cases gracefully.
    """

    def test_get_nonexistent_session_returns_404(self):
        """GET on a session that doesn't exist should return 404."""
        resp = client.get("/ivr/session/nonexistent-session-id")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_delete_nonexistent_session_returns_404(self):
        """DELETE on a session that doesn't exist should return 404."""
        resp = client.delete("/ivr/session/nonexistent-session-id")
        assert resp.status_code == 404

    def test_input_missing_fields_returns_422(self):
        """
        POST /ivr/input without required fields should return 422.
        FastAPI automatically returns 422 Unprocessable Entity for invalid payloads.
        """
        resp = client.post("/ivr/input", json={})
        assert resp.status_code == 422

    def test_start_call_with_empty_name_uses_guest(self):
        """Empty string for caller_name should default to 'Guest', not crash."""
        resp = client.post("/ivr/start", json={"caller_name": ""})
        assert resp.status_code == 200

    def test_very_long_message_handled(self):
        """Extremely long input should not crash the server."""
        start = client.post("/ivr/start", json={"caller_name": "Test"})
        sid = start.json()["session_id"]
        long_msg = "cardiology " * 200
        resp = client.post("/ivr/input", json={
            "session_id": sid,
            "message": long_msg
        })
        assert resp.status_code == 200

    def test_special_characters_in_message(self):
        """Messages with special characters should not crash the server."""
        start = client.post("/ivr/start", json={"caller_name": "Test"})
        sid = start.json()["session_id"]
        resp = client.post("/ivr/input", json={
            "session_id": sid,
            "message": "!@#$%^&*() <script>alert('xss')</script>"
        })
        assert resp.status_code == 200

    def test_root_always_returns_200(self):
        """Health check must always be available."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "status" in resp.json()

    def test_health_endpoint_returns_model_status(self):
        """GET /ivr/health should return model loading status."""
        resp = client.get("/ivr/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "intent_classifier" in data
        assert "entity_extractor" in data


# =============================================================================
# LAYER 6 — LOGGING TESTS
# =============================================================================

class TestLogging:
    """
    Tests that critical events are being logged.
    """

    def test_session_creation_is_logged(self, caplog):
        """Creating a session should produce a log entry."""
        with caplog.at_level(logging.INFO):
            client.post("/ivr/start", json={"caller_name": "LogTest"})
        assert any("session" in record.message.lower() or
                   "created" in record.message.lower()
                   for record in caplog.records)

    def test_session_end_is_logged(self, caplog):
        """Ending a session should produce a log entry."""
        start = client.post("/ivr/start", json={"caller_name": "LogTest"})
        sid = start.json()["session_id"]
        with caplog.at_level(logging.INFO):
            client.delete(f"/ivr/session/{sid}")
        assert any("session" in record.message.lower() or
                   "ended" in record.message.lower()
                   for record in caplog.records)
