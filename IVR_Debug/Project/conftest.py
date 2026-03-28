# conftest.py
# ─────────────────────────────────────────────────────────────────────────────
# Pytest configuration file.
# This file runs automatically before any tests.
# Shared fixtures defined here are available to ALL test files.
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os
import pytest

# Make sure the Project directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="module")
def test_client():
    """
    Provides a reusable TestClient instance for the entire test module.
    scope="module" means it's created once per test file, not per test.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def active_session(test_client):
    """
    Creates a fresh IVR session before each test that needs one,
    and cleans it up afterwards.
    This prevents test pollution — each test gets a clean session.
    """
    resp = test_client.post("/ivr/start", json={"caller_name": "FixtureUser"})
    session_id = resp.json()["session_id"]

    yield session_id  # provide session_id to the test

    # Cleanup: delete the session after the test finishes
    test_client.delete(f"/ivr/session/{session_id}")
