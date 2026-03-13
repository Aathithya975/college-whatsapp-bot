from flask import Flask, request
import google.generativeai as genai
import requests
import os

app = Flask(__name__)

# ========== CONFIG ==========
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # உங்க Gemini API key இங்க போடுங்க
WHATSAPP_TOKEN = "YOUR_WHATSAPP_TOKEN"  # Meta access token இங்க போடுங்க
PHONE_NUMBER_ID = "1030379623495589"    # உங்க Phone Number ID (already இருக்கு)
VERIFY_TOKEN = "college_bot_123"        # நீங்களே set பண்ணலாம்
# ============================

# College Fees Data (உங்க Excel-இல் இருந்து)
COLLEGE_DATA = """
Our Engineering College - Courses & Fees Information:

| Department | Management Quota | Counselling Quota |
|------------|-----------------|-------------------|
| IT         | ₹3,00,000       | ₹1,50,000         |
| CSE        | ₹3,50,000       | ₹2,00,000         |
| MECH       | ₹1,50,000       | ₹70,000           |
| AIML       | ₹2,50,000       | ₹1,50,000         |
| AIDS       | ₹4,00,000       | ₹1,50,000         |
| CSBS       | ₹2,00,000       | ₹1,00,000         |
| CIVIL      | ₹1,00,000       | ₹50,000           |

Note: Fees are per year. 7.2 quota fees are free (government scholarship).
"""

# Gemini Setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

def get_gemini_response(user_message):
    prompt = f"""You are a helpful college admission assistant for an Engineering College in Tamil Nadu, India.
Answer questions about courses and fees only based on the data below.
Reply in the same language the student uses (Tamil or English).
Keep answers short and clear.

{COLLEGE_DATA}

Student question: {user_message}"""
    
    response = model.generate_content(prompt)
    return response.text

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
    requests.post(url, headers=headers, json=data)

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
            from_number = message["from"]
            user_text = message["text"]["body"]
            
            print(f"Message from {from_number}: {user_text}")
            
            # Gemini-ஆல் answer generate பண்ணு
            reply = get_gemini_response(user_text)
            
            # WhatsApp-ல reply அனுப்பு
            send_whatsapp_message(from_number, reply)
    except Exception as e:
        print(f"Error: {e}")
    
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
