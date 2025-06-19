from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Global variables to track trip status
current_trip = None
claimed_by = None

@app.route("/", methods=["GET"])
def home():
    return "✅ Deckhand SMS Scheduler is running!"

@app.route("/sms", methods=["POST"])
def sms_reply():
    global current_trip, claimed_by

    msg = request.form.get('Body', '').strip().lower()
    sender = request.form.get('From')
    resp = MessagingResponse()

    if msg.startswith("trip"):
        current_trip = msg[5:].strip().title()
        claimed_by = None
        resp.message(f"Trip posted: {current_trip}.")
    elif msg == "y":
        if not current_trip:
            resp.message("No trip is currently available.")
        elif not claimed_by:
            claimed_by = sender
            resp.message(f"You’re confirmed for the trip: {current_trip}.")
        else:
            resp.message("Sorry, that trip has already been claimed.")
    else:
        resp.message("Send 'Trip June 28 6AM' or reply 'Y' to claim.")

    return Response(str(resp), mimetype="application/xml")

if __name__ == "__main__":
    app.run()


