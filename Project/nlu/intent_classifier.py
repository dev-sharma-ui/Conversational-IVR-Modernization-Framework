from transformers import pipeline

classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

INTENTS = [
    "check_doctor_availability",
    "book_appointment",
    "greeting",
    "goodbye",
    "fallback"
]

def detect_intent(text):

    result = classifier(text, INTENTS)

    return result["labels"][0]