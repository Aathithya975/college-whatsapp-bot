from flask import Flask, request
import google.generativeai as genai
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

FEES = {
    "it": {"management": "₹3,00,000", "counselling": "₹1,50,000"},
    "cse": {"management": "₹3,50,000", "counselling": "₹2,00,000"},
    "mech": {"management": "₹1,50,000", "counselling": "₹70,000"},
    "aiml": {"management": "₹2,50,000", "counselling": "₹1,50,000"},
    "aids": {"management": "₹4,00,000", "counselling": "₹1,50,000"},
    "csbs": {"management": "₹2,00,000", "counselling": "₹1,00,000"},
    "civil": {"management": "₹1,00,000", "counselling": "₹50,000"},
}

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None


def get_direct_reply(user_message):
    text = user_message.lower().strip()

    # greetings
    if text in ["hi", "hello", "hey", "hii"]:
        return (
            "Hello! Welcome to our Engineering College chatbot.\n\n"
            "You can ask about:\n"
            "1. CSE fees\n"
            "2. IT fees\n"
            "3. AIML fees\n"
            "4. AIDS fees\n"
            "5. MECH fees\n"
            "6. CSBS fees\n"
            "7. CIVIL fees"
        )

    # scholarship / quota
    if "7.2" in text or "scholarship" in text or "free seat" in text:
        return "7.2 quota fees are free under government scholarship."

    # all fees
    if text in ["fees", "all fees", "course fees", "courses and fees"]:
        return (
            "Courses & Fees per year:\n\n"
            "IT - Mgmt: ₹3,00,000 | Counselling: ₹1,50,000\n"
            "CSE - Mgmt: ₹3,50,000 | Counselling: ₹2,00,000\n"
            "MECH - Mgmt: ₹1,50,000 | Counselling: ₹70,000\n"
            "AIML - Mgmt: ₹2,50,000 | Counselling: ₹1,50,000\n"
            "AIDS - Mgmt: ₹4,00,000 | Counselling: ₹1,50,000\n"
            "CSBS - Mgmt: ₹2,00,000 | Counselling: ₹1,00,000\n"
            "CIVIL - Mgmt: ₹1,00,000 | Counselling: ₹50,000\n\n"
            "7.2 quota fees are free."
        )

    # department-specific fees
    for dept, fee in FEES.items():
        if dept in text:
            return (
                f"{dept.upper()} Fees per year:\n"
                f"Management Quota: {fee['management']}\n"
                f"Counselling Quota: {fee['counselling']}\n\n"
                f"7.2 quota fees are free."
            )

    return None


def get_gemini_response(user_message):
    if not model:
        return None

    prompt = f"""You are a helpful college admission assistant for an Engineering College in Tamil Nadu, India.
Answer questions about courses and fees only based on the data below.
Reply in the same language the student uses (Tamil or English).
Keep answers short and clear.

{COLLEGE_DATA}

Student question: {user_message}"""

    try:
        response = model.generate_content(prompt)
        if response and hasattr(response, "text") and response.text:
            return response.text.strip()
        return None
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None


def get_reply(user_message):
    # First try direct reply
    direct_reply = get_direct_reply(user_message)
    if direct_reply:
        return direct_reply

    # Then try Gemini
    gemini_reply = get_gemini_response(user_message)
    if gemini_reply:
        return gemini_reply

    # Final fallback
    return (
        "Sorry, I can only answer about college courses and fees right now.\n\n"
        "Try asking like:\n"
        "- CSE fees\n"
        "- IT fees\n"
        "- AIML fees\n"
        "- all fees"
    )


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
    print("WhatsApp API status:", response.status_code)
    print("WhatsApp API response:", response.text)


@app.route("/", methods=["GET"])
def home():
    return "College WhatsApp Bot is Live!", 200


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
    print("Incoming webhook:", data)

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

            reply = get_reply(user_text)
            send_whatsapp_message(from_number, reply)

    except Exception as e:
        print(f"Error: {e}")

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
