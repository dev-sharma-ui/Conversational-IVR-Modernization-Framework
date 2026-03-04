def fallback_response(text):

    text = text.lower().strip()

    if text == "":
        return "I didn't hear anything. Could you repeat?"

    if "how are you" in text:
        return "I am functioning properly. How may I assist you?"

    if "repeat" in text:
        return "Sure. Please tell me the department you are looking for."

    if "other options" in text:
        return "You can check doctor availability or book an appointment."

    if "i don't know" in text:
        return "No problem. Please tell me which department you need."

    return None