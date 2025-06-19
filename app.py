from flask import Flask, request
from twilio.rest import Client
import os
import re

app = Flask(__name__)

# ✅ Twilio credentials from environment variables
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_SID, TWILIO_TOKEN)

# ✅ Trusted deckhands (in E.164 format)
TRUSTED_NUMBERS = [
    "+12062915442",  # Deckhand 1
    "+12065194774",  # Deckhand 2
    "+14256268364",  # Deckhand 3
]

# ✅ Normalize to digits only for comparison
def normalize_number(number):
    return re.sub(r'\D', '', number)

normalized_trusted = [normalize_number(n) for n in TRUSTED_NUMBERS]

# ✅ Trip state
current_trip = None
claimed_by = None

@app.route("/", methods=["GET"])
def home():
    return "✅ Deckhand Scheduler is Live"

@app.route("/sms", methods=["POST"])
def sms_reply():
    global current_trip, claimed_by

    msg = request.form.get("Body", "").strip().lower()
    sender = request.form.get("From")
    print(f"📩 Incoming From: {sender} | Message: {msg}")

    normalized_sender = normalize_number(sender)

    # ✅ Captain posting a new trip
    if msg.startswith("trip"):
        current_trip = msg[5:].strip().title()
        claimed_by = None

        for number in TRUSTED_NUMBERS:
            client.messages.create(
                to=number,
                from_=TWILIO_NUMBER,
                body=f"🚨 New trip posted: {current_trip}. Reply with 'Y' to claim."
            )

        return "Trip broadcasted", 200

    # ✅ Deckhand claiming a trip
    elif msg == "y":
        if normalized_sender not in normalized_trusted:
            print("⛔ Sender not in trusted list")
            return "Unauthorized", 403

        if not current_trip:
            client.messages.create(
                to=sender,
                from_=TWILIO_NUMBER,
                body="❌ No trip is currently available."
            )
        elif not claimed_by:
            claimed_by = sender
            client.messages.create(
                to=sender,
                from_=TWILIO_NUMBER,
                body=f"✅ You’re confirmed for the trip: {current_trip}."
            )
        else:
            client.messages.create(
                to=sender,
                from_=TWILIO_NUMBER,
                body="⚠️ Sorry, that trip has already been claimed."
            )

        return "Claim processed", 200

    # ✅ Catch-all fallback
    client.messages.create(
        to=sender,
        from_=TWILIO_NUMBER,
        body="ℹ️ Send 'Trip June 29 6AM' to post a trip or reply 'Y' to claim."
    )
    return "Unknown command", 200

if __name__ == "__main__":
    app.run()
