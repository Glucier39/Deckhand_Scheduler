from flask import Flask, request
from twilio.rest import Client
import os

app = Flask(__name__)

# ✅ Load credentials from Render environment variables
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_SID, TWILIO_TOKEN)

# ✅ Trusted deckhands
TRUSTED_NUMBERS = [
    "+12065551111",  # Deckhand 1
    "+12068882222",  # Deckhand 2
    "+12067773333",  # Deckhand 3
]

# ✅ Trip state
current_trip = None
claimed_by = None

@app.route("/", methods=["GET"])
def home():
    return "✅ Deckhand Trip Scheduler is Live"

@app.route("/sms", methods=["POST"])
def sms_reply():
    global current_trip, claimed_by

    msg = request.form.get("Body", "").strip().lower()
    sender = request.form.get("From")

    # ✅ Captain posts a new trip
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

    # ✅ Deckhand claims a trip
    elif msg == "y":
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

    else:
        client.messages.create(
            to=sender,
            from_=TWILIO_NUMBER,
            body="ℹ️ Send 'Trip June 29 6AM' to post a trip or 'Y' to claim."
        )
        return "Unknown command", 200

if __name__ == "__main__":
    app.run()
