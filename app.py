from flask import Flask, request
from twilio.rest import Client
import os
import re
import time

app = Flask(__name__)

# ✅ Load credentials from environment
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_SID, TWILIO_TOKEN)

# ✅ Trusted deckhands (must be verified on trial account)
TRUSTED_NUMBERS = [
    "+12062915442",
    "+12065194774",
    "+14256268364"
]

# ✅ Normalize to digits only for comparison
def normalize(number):
    return re.sub(r'\D', '', number)

normalized_trusted = [normalize(n) for n in TRUSTED_NUMBERS]

# ✅ Trip state
current_trip = None
claimed_by = None

@app.route("/", methods=["GET"])
def home():
    return "✅ Deckhand Scheduler Live"

@app.route("/sms", methods=["POST"])
def sms_reply():
    global current_trip, claimed_by

    msg = request.form.get("Body", "").strip().lower()
    sender = request.form.get("From")
    print(f"📩 Incoming From: {sender} | Message: {msg}")

    normalized_sender = normalize(sender)

    # ✅ Captain posts a trip
    if msg.startswith("trip"):
        current_trip = msg[5:].strip().title()
        claimed_by = None

        for number in TRUSTED_NUMBERS:
            try:
                client.messages.create(
                    to=number,
                    from_=TWILIO_NUMBER,
                    body=f"Trip posted: {current_trip}. Reply Y to claim."
                )
                time.sleep(1)
            except Exception as e:
                print(f"❌ Failed to send to {number}: {e}")

        return "Trip broadcasted", 200

    # ✅ Deckhand claims trip
    elif msg == "y":
        if normalized_sender not in normalized_trusted:
            print("⛔ Unauthorized sender")
            return "Unauthorized", 403

        if not current_trip:
            client.messages.create(
                to=sender,
                from_=TWILIO_NUMBER,
                body="No trip is currently available."
            )
        elif not claimed_by:
            claimed_by = sender
            client.messages.create(
                to=sender,
                from_=TWILIO_NUMBER,
                body=f"You are confirmed for the trip: {current_trip}."
            )
        else:
            client.messages.create(
                to=sender,
                from_=TWILIO_NUMBER,
                body="Sorry, that trip has already been claimed."
            )

        return "Claim processed", 200

    # ✅ Catch-all
    client.messages.create(
        to=sender,
        from_=TWILIO_NUMBER,
        body="Send 'Trip June 30 6AM' to post a trip or 'Y' to claim."
    )
    return "Unknown command", 200

if __name__ == "__main__":
    app.run()
