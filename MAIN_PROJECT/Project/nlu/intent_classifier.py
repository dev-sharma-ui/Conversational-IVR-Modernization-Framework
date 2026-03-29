"""
intent_classifier.py
---------------------
Purpose: Detects the user's intent from natural language input.
Uses Hugging Face zero-shot classification with facebook/bart-large-mnli.
Falls back to keyword matching if the model is unavailable (e.g., no internet or RAM constraints).
"""

import logging

logger = logging.getLogger(__name__)

INTENTS = [
    "check_doctor_availability",
    "book_appointment",
    "cancel_appointment",
    "greeting",
    "goodbye",
    "fallback",
]

# Keyword-based fallback intent map (used if transformer model fails to load)
KEYWORD_INTENT_MAP = {
    "check_doctor_availability": [
        "available", "availability", "doctors", "who is", "which doctor",
        "is there a doctor", "show doctors", "list doctors",
    ],
    "book_appointment": [
        "book", "schedule", "appointment", "reserve", "fix an appointment",
        "i want to book", "i need an appointment",
    ],
    "cancel_appointment": [
        "cancel", "cancellation", "remove appointment", "don't want",
    ],
    "greeting": [
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening", "namaste",
    ],
    "goodbye": [
        "bye", "goodbye", "see you", "thank you", "thanks", "that's all", "done", "exit", "quit",
    ],
}

# Try loading the transformer model; degrade gracefully if unavailable
_classifier = None

def _load_classifier():
    global _classifier
    if _classifier is not None:
        return _classifier
    try:
        from transformers import pipeline
        _classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )
        logger.info("✅ Transformer intent classifier loaded.")
    except Exception as e:
        logger.warning(f"⚠️  Transformer model unavailable, using keyword fallback. Reason: {e}")
        _classifier = None
    return _classifier


def _keyword_detect_intent(text: str) -> str:
    """Simple keyword-based intent detection as a fallback."""
    text_lower = text.lower()
    for intent, keywords in KEYWORD_INTENT_MAP.items():
        for kw in keywords:
            if kw in text_lower:
                return intent
    return "fallback"


def detect_intent(text: str) -> str:
    """
    Detect intent from text.
    Tries transformer model first, falls back to keyword matching.
    """
    clf = _load_classifier()
    if clf is not None:
        try:
            result = clf(text, INTENTS)
            detected = result["labels"][0]
            score = result["scores"][0]
            # If confidence is too low, treat as fallback
            if score < 0.35:
                return "fallback"
            return detected
        except Exception as e:
            logger.warning(f"Transformer inference failed: {e}")

    return _keyword_detect_intent(text)
