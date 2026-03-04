import spacy

nlp = spacy.load("en_core_web_sm")

DEPARTMENTS = ["cardiology", "orthopedics", "general"]

def extract_entities(text):

    doc = nlp(text)

    entities = {
        "doctor": None,
        "date": None,
        "department": None
    }

    for ent in doc.ents:

        if ent.label_ == "PERSON":
            entities["doctor"] = ent.text

        if ent.label_ == "DATE":
            entities["date"] = ent.text

    lower = text.lower()

    for dept in DEPARTMENTS:
        if dept in lower:
            entities["department"] = dept

    return entities