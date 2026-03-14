from flask import Flask, request
import os
import requests
import google.generativeai as genai

app = Flask(__name__)

# =========================
# ENV CONFIG
# =========================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = "1030379623495589"
VERIFY_TOKEN = "college_bot_123"

# =========================
# COLLEGE DETAILS
# =========================
COLLEGE_NAME = "V.S.B ENGINEERING COLLEGE"
COLLEGE_LOCATION = "Karur"
COLLEGE_EMAIL = "admission@vsbec.com"
COLLEGE_PHONE = "9994496212"
COLLEGE_WEBSITE = "https://vsbec.edu.in/"
COLLEGE_ADMISSION_LINK = "https://vsbec.edu.in/contact-us/"

UG_COURSES = [
    "IT",
    "CSE",
    "AIML",
    "EEE",
    "ECE",
    "CIVIL",
    "CHEMICAL",
    "AIDS",
    "CCE",
    "CSBS"
]

PG_COURSES = [
    "MBA",
    "M.Tech",
    "M.Sc",
    "MA"
]

FEE_TYPES = ["Merit", "Management", "Counselling", "7.5 Fee"]

ug_courses_text = "\n".join([f"• {course}" for course in UG_COURSES])
pg_courses_text = "\n".join([f"• {course}" for course in PG_COURSES])

COLLEGE_CONTEXT = f"""
College Name: {COLLEGE_NAME}
Location: {COLLEGE_LOCATION}
Email: {COLLEGE_EMAIL}
Phone: {COLLEGE_PHONE}
Website: {COLLEGE_WEBSITE}
UG Courses: {", ".join(UG_COURSES)}
PG Courses: {", ".join(PG_COURSES)}
Fee Types: Merit, Management, Counselling, 7.5 Fee
Admission Info: {COLLEGE_ADMISSION_LINK}
"""

# =========================
# GEMINI SETUP
# =========================
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

# =========================
# WHATSAPP SENDERS
# =========================
def send_text(to, message):
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
    print("TEXT STATUS:", response.status_code)
    print("TEXT RESPONSE:", response.text)


def send_menu(to):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "🎓 VSB Engineering College Bot"
            },
            "body": {
                "text": (
                    "👋 Welcome to V.S.B Engineering College Assistant.\n\n"
                    "Please choose an option below:"
                )
            },
            "footer": {
                "text": "✨ Quick college help"
            },
            "action": {
                "button": "📋 Open Menu",
                "sections": [
                    {
                        "title": "📚 College Information",
                        "rows": [
                            {
                                "id": "about_college",
                                "title": "🏫 About College",
                                "description": "View college basic details"
                            },
                            {
                                "id": "courses_info",
                                "title": "🎓 Courses",
                                "description": "UG and PG course details"
                            },
                            {
                                "id": "fees_info",
                                "title": "💰 Fees Details",
                                "description": "Merit, Management, Counselling, 7.5"
                            },
                            {
                                "id": "admission_info",
                                "title": "📝 Admission Info",
                                "description": "Admission enquiry details"
                            },
                            {
                                "id": "contact_info",
                                "title": "📞 Contact",
                                "description": "Phone and email details"
                            },
                            {
                                "id": "location_info",
                                "title": "📍 Location",
                                "description": "College location and website"
                            }
                        ]
                    }
                ]
            }
        }
    }

    response = requests.post(url, headers=headers, json=data)
    print("MENU STATUS:", response.status_code)
    print("MENU RESPONSE:", response.text)


# =========================
# STATIC SMART REPLIES
# =========================
def get_static_reply(text):
    msg = text.lower().strip()

    greetings = ["hi", "hello", "hey", "hii", "menu", "start", "vanakkam", "வணக்கம்"]
    if msg in greetings:
        return "SHOW_MENU"

    if "about" in msg or "college" in msg:
        return (
            f"🏫 *{COLLEGE_NAME}*\n\n"
            f"📍 Location: {COLLEGE_LOCATION}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}\n"
            f"📧 Email: {COLLEGE_EMAIL}\n"
            f"📞 Phone: {COLLEGE_PHONE}"
        )

    if "course" in msg or "courses" in msg or msg == "ug" or msg == "pg":
        return (
            "🎓 *Courses Available*\n\n"
            "*UG Courses:*\n"
            f"{ug_courses_text}\n\n"
            "*PG Courses:*\n"
            f"{pg_courses_text}\n\n"
            f"🌐 Website:\n{COLLEGE_WEBSITE}"
        )

    if msg in [course.lower() for course in UG_COURSES + PG_COURSES]:
        return (
            f"🎓 *{msg.upper()} Course Information*\n\n"
            f"{msg.upper()} is available in {COLLEGE_NAME}.\n\n"
            f"📞 For admission and department details:\n"
            f"Phone: {COLLEGE_PHONE}\n"
            f"Email: {COLLEGE_EMAIL}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}"
        )

    if "fee" in msg or "fees" in msg or "management" in msg or "merit" in msg or "counselling" in msg or "7.5" in msg:
        return (
            "💰 *Fee Categories Available*\n\n"
            "• Merit\n"
            "• Management\n"
            "• Counselling\n"
            "• 7.5 Fee\n\n"
            "📞 For exact fee details, please contact the admission office.\n"
            f"Phone: {COLLEGE_PHONE}\n"
            f"Email: {COLLEGE_EMAIL}"
        )

    if "admission" in msg or "apply" in msg:
        return (
            "📝 *Admission Information*\n\n"
            "For admission enquiry and support, please use the official contact page:\n"
            f"{COLLEGE_ADMISSION_LINK}"
        )

    if "contact" in msg or "phone" in msg or "email" in msg or "mail" in msg:
        return (
            "📞 *Contact Details*\n\n"
            f"📱 Phone: {COLLEGE_PHONE}\n"
            f"📧 Email: {COLLEGE_EMAIL}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}"
        )

    if "location" in msg or "address" in msg or "where" in msg:
        return (
            "📍 *College Location*\n\n"
            f"{COLLEGE_NAME}\n"
            f"{COLLEGE_LOCATION}\n\n"
            f"🌐 Website:\n{COLLEGE_WEBSITE}"
        )

    return None


# =========================
# MENU OPTION REPLIES
# =========================
def handle_menu_selection(selected_id):
    if selected_id == "about_college":
        return (
            f"🏫 *{COLLEGE_NAME}*\n\n"
            f"📍 Location: {COLLEGE_LOCATION}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}\n"
            f"📧 Email: {COLLEGE_EMAIL}\n"
            f"📞 Phone: {COLLEGE_PHONE}"
        )

    if selected_id == "courses_info":
        return (
            "🎓 *Courses Available*\n\n"
            "*UG Courses:*\n"
            f"{ug_courses_text}\n\n"
            "*PG Courses:*\n"
            f"{pg_courses_text}\n\n"
            f"🌐 Website:\n{COLLEGE_WEBSITE}"
        )

    if selected_id == "fees_info":
        return (
            "💰 *Fee Categories*\n\n"
            "• Merit\n"
            "• Management\n"
            "• Counselling\n"
            "• 7.5 Fee\n\n"
            "📞 For exact fee details, contact admission office.\n"
            f"Phone: {COLLEGE_PHONE}\n"
            f"Email: {COLLEGE_EMAIL}"
        )

    if selected_id == "admission_info":
        return (
            "📝 *Admission Info*\n\n"
            "For admission enquiry, use the official page:\n"
            f"{COLLEGE_ADMISSION_LINK}"
        )

    if selected_id == "contact_info":
        return (
            "📞 *Contact Details*\n\n"
            f"📱 Phone: {COLLEGE_PHONE}\n"
            f"📧 Email: {COLLEGE_EMAIL}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}"
        )

    if selected_id == "location_info":
        return (
            "📍 *Location*\n\n"
            f"{COLLEGE_NAME}\n"
            f"{COLLEGE_LOCATION}\n\n"
            f"🌐 Website:\n{COLLEGE_WEBSITE}"
        )

    return "🙂 Please type *hi* to open the menu again."


# =========================
# GEMINI FALLBACK
# =========================
def get_gemini_reply(user_message):
    if not model:
        return None

    prompt = f"""
You are a friendly WhatsApp admission assistant for {COLLEGE_NAME}.

Rules:
- Answer only using the college details given below.
- Keep the answer short, clear, and student-friendly.
- Use simple English.
- If the student types Tamil-English mixed language, reply naturally in simple style.
- Do not invent fees or departments not provided.
- If exact fee amount is not provided, say to contact admission office.
- UG courses are: IT, CSE, AIML, EEE, ECE, CIVIL, CHEMICAL, AIDS, CCE, CSBS.
- PG courses are: MBA, M.Tech, M.Sc, MA.

College details:
{COLLEGE_CONTEXT}

Student question:
{user_message}
"""

    try:
        response = model.generate_content(prompt)
        if response and hasattr(response, "text") and response.text:
            return response.text.strip()
        return None
    except Exception as e:
        print("Gemini Error:", e)
        return None


def get_reply(user_message):
    static_reply = get_static_reply(user_message)
    if static_reply:
        return static_reply

    gemini_reply = get_gemini_reply(user_message)
    if gemini_reply:
        return gemini_reply

    return (
        "🙂 Sorry, I can help only with V.S.B Engineering College details.\n\n"
        "Type *hi* to open the menu.\n\n"
        "You can ask about:\n"
        "• Courses\n"
        "• Fees\n"
        "• Admission\n"
        "• Contact\n"
        "• Location"
    )


# =========================
# ROUTES
# =========================
@app.route("/", methods=["GET"])
def home():
    return "VSB WhatsApp Bot is Live!", 200


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
    print("INCOMING:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            return "OK", 200

        message = value["messages"][0]
        from_number = message["from"]
        msg_type = message.get("type")

        print("MSG TYPE:", msg_type)

        if msg_type == "interactive":
            interactive = message["interactive"]
            interactive_type = interactive.get("type")

            if interactive_type == "list_reply":
                selected_id = interactive["list_reply"]["id"]
                reply = handle_menu_selection(selected_id)
                send_text(from_number, reply)
                return "OK", 200

        if msg_type == "text":
            user_text = message["text"]["body"]
            print(f"USER {from_number}: {user_text}")

            reply = get_reply(user_text)

            if reply == "SHOW_MENU":
                send_menu(from_number)
            else:
                send_text(from_number, reply)

    except Exception as e:
        print("Webhook Error:", e)

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
