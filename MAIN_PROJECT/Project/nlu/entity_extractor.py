"""
entity_extractor.py
--------------------
Purpose: Extracts structured entities (doctor name, date, department) from user text.
Uses spaCy NER for PERSON and DATE, plus keyword matching for departments.
Falls back gracefully if spaCy model is not installed.
"""

import logging
import re

logger = logging.getLogger(__name__)

DEPARTMENTS = [
    "cardiology",
    "orthopedics",
    "general",
    "neurology",
    "dermatology",
]

# Department alias map — handles common user phrasings
DEPARTMENT_ALIASES = {
    # Cardiology
    "heart": "cardiology",
    "cardiac": "cardiology",
    "cardiologist": "cardiology",
    "cardio": "cardiology",
    "chest pain": "cardiology",
    # Orthopedics
    "bone": "orthopedics",
    "joint": "orthopedics",
    "spine": "orthopedics",
    "orthopedic": "orthopedics",
    "ortho": "orthopedics",
    "knee": "orthopedics",
    "back pain": "orthopedics",
    # Neurology
    "nerve": "neurology",
    "brain": "neurology",
    "neuro": "neurology",
    "neurologist": "neurology",
    "headache": "neurology",
    "migraine": "neurology",
    # Dermatology
    "skin": "dermatology",
    "dermatologist": "dermatology",
    "rash": "dermatology",
    "acne": "dermatology",
    # General
    "gp": "general",
    "physician": "general",
    "family": "general",
    "checkup": "general",
    "check up": "general",
    "general physician": "general",
}

_nlp = None

def _load_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
        logger.info("✅ spaCy model loaded.")
    except Exception as e:
        logger.warning(f"⚠️  spaCy unavailable, using regex fallback. Reason: {e}")
        _nlp = None
    return _nlp


def _extract_department(text: str):
    """Extract department from text using keywords and aliases."""
    lower = text.lower()
    # Direct department name match
    for dept in DEPARTMENTS:
        if dept in lower:
            return dept
    # Alias match
    for alias, dept in DEPARTMENT_ALIASES.items():
        if alias in lower:
            return dept
    return None


def _extract_date_regex(text: str):
    """
    Extract date from text using regex patterns.
    Handles formats like: tomorrow, next Monday, 25th December, December 25, 2024-12-25, 25/12/2024
    """
    lower = text.lower()

    # Natural language dates
    natural = re.search(
        r"\b(today|tomorrow|day after tomorrow|next (monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
        lower
    )
    if natural:
        return natural.group(0)

    # DD Month / Month DD patterns
    month_names = (
        r"(january|february|march|april|may|june|july|august|"
        r"september|october|november|december|jan|feb|mar|apr|"
        r"jun|jul|aug|sep|oct|nov|dec)"
    )
    date_pattern = re.search(
        rf"\b(\d{{1,2}}(?:st|nd|rd|th)?\s+{month_names}(?:\s+\d{{4}})?|{month_names}\s+\d{{1,2}}(?:st|nd|rd|th)?(?:\s+\d{{4}})?)\b",
        lower,
        re.IGNORECASE,
    )
    if date_pattern:
        return date_pattern.group(0).strip()

    # Numeric formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY
    numeric = re.search(
        r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        text
    )
    if numeric:
        return numeric.group(0)

    return None


def extract_entities(text: str) -> dict:
    """
    Extract entities from user text.
    Returns dict with keys: doctor, date, department (each may be None).
    """
    entities = {
        "doctor": None,
        "date": None,
        "department": None,
    }

    # Extract department (always use keyword method — more reliable)
    entities["department"] = _extract_department(text)

    # Try spaCy for doctor name and date
    nlp = _load_nlp()
    if nlp is not None:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ == "PERSON" and entities["doctor"] is None:
                    entities["doctor"] = ent.text
                if ent.label_ == "DATE" and entities["date"] is None:
                    entities["date"] = ent.text
        except Exception as e:
            logger.warning(f"spaCy inference failed: {e}")

    # If spaCy didn't find a date, try regex
    if entities["date"] is None:
        entities["date"] = _extract_date_regex(text)

    # If spaCy didn't find a doctor name, check for "Dr." prefix
    if entities["doctor"] is None:
        dr_match = re.search(r"\bdr\.?\s+[a-z]+\b", text, re.IGNORECASE)
        if dr_match:
            entities["doctor"] = dr_match.group(0)

    return entities
