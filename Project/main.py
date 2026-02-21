from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather

app = FastAPI()

@app.post("/ivr")
async def ivr():
    response = VoiceResponse()

    gather = Gather(
        num_digits=1,
        action="/handle-input",
        method="POST"
    )
    gather.say("Welcome to the Modern IVR System. Press 1 for Sales. Press 2 for Support.")
    response.append(gather)

    response.say("No input received. Goodbye.")

    return Response(content=str(response), media_type="application/xml")


from fastapi import Form

@app.post("/handle-input")
async def handle_input(Digits: str = Form(...)):
    response = VoiceResponse()

    if Digits == "1":
        response.say("You selected Sales.")
    elif Digits == "2":
        response.say("You selected Support.")
    else:
        response.say("Invalid option.")

    return Response(content=str(response), media_type="application/xml")

# Simple IVR Flow Overview:
# 1. User dials your Azure phone number (+1234567890)
# 2. Azure receives the call
# 3. Azure sends HTTP POST
# 4. Our FastAPI code
# endpoint
# the call (call_automation_client.answer_call)
# answers
# /acs/incoming-call
# to our
# 5. Azure connects the call
# AAA
# 6. Our code plays
# 7. Our code starts
# for
# DTMF
# User can now hear you
# welcome message using TTS
# listening
# (Text-to-Speech)
# (key presses)
# 8. User presses
# 1
# 9. Azure sends event
# 10.
# to your
# ARAARAAA
# 11. Our code decides:
# event
# "1 means booking menu"
# 12. Our code plays booking menu
# Our code receives
# SAAF
# /acs/callbacks endpoint
# "user pressed 1"
# SAAR
# and
# 50
# or   








# P3L329HXQJTJJHA61S535UYS