"""
fallback_handler.py
--------------------
Purpose: Intercepts edge-case or conversational inputs before they reach the NLU pipeline.
Handles silence, small talk, noise, confusion signals, and repeated requests.
Returns a response string if the input is a fallback case, otherwise returns None
so the pipeline continues normally.
"""

# Exact phrase → response
EXACT_RESPONSES = {
    "":                      "I didn't catch that. Could you please repeat?",
    "how are you":           "I am functioning properly. How may I assist you today?",
    "who are you":           "I am CityCare Hospital's automated assistant. I can help you check doctor availability and book appointments.",
    "what can you do":       "I can check doctor availability, book appointments, and help you navigate hospital services.",
    "help":                  "You can say things like: 'Check doctors in cardiology', 'Book an appointment', or 'What departments are available?'",
    "repeat":                "Sure. Please tell me which department you are looking for.",
    "say that again":        "Sure. Please tell me which department you are looking for.",
    "other options":         "You can check doctor availability or book an appointment. Which would you prefer?",
    "i don't know":          "No problem. You can choose from: Cardiology, Orthopedics, General, Neurology, or Dermatology.",
    "i am not sure":         "That's okay. Take your time. Which department do you need assistance with?",
    "ok":                    "Alright, how may I further assist you?",
    "okay":                  "Alright, how may I further assist you?",
    "yes":                   None,   # Let dialogue manager handle yes/no
    "no":                    None,
}

# Partial phrase → response
PARTIAL_RESPONSES = [
    (["sorry", "excuse me"],           "No problem at all. How can I help you?"),
    (["noise", "bad connection"],      "I'm having trouble understanding. Could you please speak clearly?"),
    (["wait", "hold on", "one sec"],   "Of course, take your time. I'm here whenever you're ready."),
    (["speak to human", "real person", "agent", "operator"],
                                       "I understand. Please stay on the line and I will transfer you to a human agent."),
    (["what departments", "which departments", "list departments", "available departments"],
                                       "We have: Cardiology, Orthopedics, General, Neurology, and Dermatology. Which one do you need?"),
    (["emergency", "urgent"],          "For emergencies, please call 112 immediately or visit our emergency ward. How else can I help?"),
]

# Noise / unclear input patterns (very short or non-alphabetic input)
NOISE_PATTERNS = ["...", "???", "hmm", "uh", "uhh", "um", "umm", "ah", "ahh", "eh"]


def fallback_response(text: str):
    """
    Check if the input is a fallback/edge case.
    Returns a response string if matched, otherwise returns None.
    """
    stripped = text.strip()
    lower = stripped.lower()

    # Empty or whitespace
    if not stripped:
        return "I didn't catch that. Could you please repeat?"

    # Noise / filler words
    if lower in NOISE_PATTERNS or (len(lower) <= 2 and not lower.isalpha()):
        return "I didn't quite understand that. Could you speak a bit more clearly?"

    # Exact match
    if lower in EXACT_RESPONSES:
        result = EXACT_RESPONSES[lower]
        return result  # May be None — that's intentional (let pipeline handle yes/no)

    # Partial / keyword match
    for keywords, response in PARTIAL_RESPONSES:
        if any(kw in lower for kw in keywords):
            return response

    return None
