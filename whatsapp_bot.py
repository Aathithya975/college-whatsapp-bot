from flask import Flask, request
from google import genai
import requests
import os

app = Flask(__name__)

# ========== CONFIG ==========
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = "1030379623495589"
VERIFY_TOKEN = "college_bot_123"
# ============================

COLLEGE_DATA = """
Our Engineering College - Courses & Fees Information:

| Department | Management Quota | Counselling Quota |
|------------|------------------|-------------------|
| IT         | ₹3,00,000        | ₹1,50,000         |
| CSE        | ₹3,50,000        | ₹2,00,000         |
| MECH       | ₹1,50,000        | ₹70,000           |
| AIML       | ₹2,50,000        | ₹1,50,000         |
| AIDS       | ₹4,00,000        | ₹1,50,000         |
| CSBS       | ₹2,00,000        | ₹1,00,000         |
| CIVIL      | ₹1,00,000        | ₹50,000           |

Note: Fees are per year. 7.2 quota fees are free (government scholarship).
"""

client = genai.Client(api_key=GEMINI_API_KEY)


def get_gemini_response(user_message):
    prompt = f"""You are a helpful college admission assistant for an Engineering College in Tamil Nadu, India.
Answer questions about courses and fees only based on the data below.
Reply in the same language the student uses (Tamil or English).
Keep answers short and clear.
If the question is outside courses and fees, politely say you can only help with college admission, department, and fee details.

{COLLEGE_DATA}

Student question: {user_message}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        return "Sorry, I could not generate a reply right now."

    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Sorry, AI response is temporarily unavailable."


def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=data)
    print("WhatsApp API response:", response.status_code, response.text)


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.json

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]

            if message.get("type") != "text":
                return "OK", 200

            from_number = message["from"]
            user_text = message["text"]["body"]

            print(f"Message from {from_number}: {user_text}")

            reply = get_gemini_response(user_text)
            send_whatsapp_message(from_number, reply)

    except Exception as e:
        print(f"Webhook Error: {e}")

    return "OK", 200


@app.route("/", methods=["GET"])
def home():
    return "College WhatsApp Bot is running!", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
