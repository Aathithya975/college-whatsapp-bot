from flask import Flask, request
import os
import requests
import logging
import time
import google.generativeai as genai  # ✅ Stable package

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ─────────────────────────────────────────────
# Environment Variables
# ─────────────────────────────────────────────
GEMINI_API_KEY     = os.environ.get("GROK_API_KEY")        # ✅ Matches Render env key
WHATSAPP_TOKEN     = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID    = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN       = os.environ.get("VERIFY_TOKEN", "college_bot_123")

# ─────────────────────────────────────────────
# College Info
# ─────────────────────────────────────────────
COLLEGE_NAME           = "V.S.B ENGINEERING COLLEGE"
COLLEGE_LOCATION       = "Karur"
COLLEGE_EMAIL          = "admission@vsbec.com"
COLLEGE_PHONE          = "9994496212"
COLLEGE_WEBSITE        = "https://vsbec.edu.in/"
COLLEGE_ADMISSION_LINK = "https://vsbec.edu.in/contact-us/"

UG_COURSES = ["IT", "CSE", "AIML", "EEE", "ECE", "CIVIL", "CHEMICAL", "AIDS", "CCE", "CSBS"]
PG_COURSES = ["MBA", "M.Tech", "M.Sc", "MA"]

ug_courses_text = "\n".join([f"• {c}" for c in UG_COURSES])
pg_courses_text = "\n".join([f"• {c}" for c in PG_COURSES])

COLLEGE_CONTEXT = f"""
College Name: {COLLEGE_NAME}
Location: {COLLEGE_LOCATION}
Email: {COLLEGE_EMAIL}
Phone: {COLLEGE_PHONE}
Website: {COLLEGE_WEBSITE}
UG Courses: {", ".join(UG_COURSES)}
PG Courses: {", ".join(PG_COURSES)}
Admission Info: {COLLEGE_ADMISSION_LINK}
"""

# ─────────────────────────────────────────────
# Gemini AI Setup
# ─────────────────────────────────────────────
gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("✅ Gemini AI initialised successfully.")
    except Exception as e:
        logger.error(f"Gemini setup error: {e}")

# ─────────────────────────────────────────────
# Simple In-Memory Rate Limiter
# ─────────────────────────────────────────────
_user_last_seen: dict = {}
RATE_LIMIT_SECONDS = 2

def _is_rate_limited(phone: str) -> bool:
    now = time.time()
    last = _user_last_seen.get(phone, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    _user_last_seen[phone] = now
    return False

# ─────────────────────────────────────────────
# WhatsApp API Helpers
# ─────────────────────────────────────────────
_WA_URL_TEMPLATE = "https://graph.facebook.com/v22.0/{phone_number_id}/messages"

def _wa_headers():
    return {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

def _post_to_whatsapp(payload: dict) -> None:
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.warning("Missing WHATSAPP_TOKEN or PHONE_NUMBER_ID — message not sent.")
        return
    url = _WA_URL_TEMPLATE.format(phone_number_id=PHONE_NUMBER_ID)
    try:
        resp = requests.post(url, headers=_wa_headers(), json=payload, timeout=20)
        if resp.status_code != 200:
            logger.error(f"WhatsApp API error {resp.status_code}: {resp.text}")
        else:
            logger.info(f"Message sent OK → {payload.get('to')}")
    except requests.exceptions.Timeout:
        logger.error("WhatsApp API request timed out.")
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")

def send_text(to: str, message: str) -> None:
    _post_to_whatsapp({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message[:4096]},
    })

def send_menu(to: str) -> None:
    _post_to_whatsapp({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🎓 VSB Engineering College Bot"},
            "body": {
                "text": (
                    "👋 Welcome to *V.S.B Engineering College* Assistant!\n\n"
                    "Please choose an option below:"
                )
            },
            "footer": {"text": "✨ Quick college help"},
            "action": {
                "button": "📋 Open Menu",
                "sections": [
                    {
                        "title": "📚 College Information",
                        "rows": [
                            {"id": "about_college",  "title": "🏫 About College",  "description": "View college basic details"},
                            {"id": "courses_info",   "title": "🎓 Courses",         "description": "UG and PG course details"},
                            {"id": "fees_info",      "title": "💰 Fees Details",    "description": "Merit, Management, Counselling, 7.5"},
                            {"id": "admission_info", "title": "📝 Admission Info",  "description": "Admission enquiry details"},
                            {"id": "contact_info",   "title": "📞 Contact",         "description": "Phone and email details"},
                            {"id": "location_info",  "title": "📍 Location",        "description": "College location and website"},
                        ],
                    }
                ],
            },
        },
    })

# ─────────────────────────────────────────────
# Static Reply Logic
# ─────────────────────────────────────────────
GREETINGS = {"hi", "hello", "hey", "hii", "menu", "start", "vanakkam", "வணக்கம்", "help"}

def get_static_reply(text: str):
    msg = text.lower().strip()

    if msg in GREETINGS:
        return "SHOW_MENU"

    if "about" in msg or "college" in msg:
        return (
            f"🏫 *{COLLEGE_NAME}*\n\n"
            f"📍 Location: {COLLEGE_LOCATION}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}\n"
            f"📧 Email: {COLLEGE_EMAIL}\n"
            f"📞 Phone: {COLLEGE_PHONE}"
        )

    if any(k in msg for k in ["course", "courses"]) or msg in ("ug", "pg"):
        return (
            "🎓 *Courses Available*\n\n"
            "*UG Courses:*\n"
            f"{ug_courses_text}\n\n"
            "*PG Courses:*\n"
            f"{pg_courses_text}\n\n"
            f"🌐 Website: {COLLEGE_WEBSITE}"
        )

    all_courses_lower = {c.lower(): c for c in UG_COURSES + PG_COURSES}
    if msg in all_courses_lower:
        course_upper = all_courses_lower[msg]
        return (
            f"🎓 *{course_upper} Course Information*\n\n"
            f"{course_upper} is offered at {COLLEGE_NAME}.\n\n"
            f"📞 For admission/department details:\n"
            f"Phone: {COLLEGE_PHONE}\n"
            f"Email: {COLLEGE_EMAIL}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}"
        )

    if any(k in msg for k in ["fee", "fees", "management", "merit", "counselling", "7.5"]):
        return (
            "💰 *Fee Categories Available*\n\n"
            "• Merit\n"
            "• Management\n"
            "• Counselling\n"
            "• 7.5 Fee\n\n"
            "📞 For exact fee details, contact the admission office:\n"
            f"Phone: {COLLEGE_PHONE}\n"
            f"Email: {COLLEGE_EMAIL}"
        )

    if any(k in msg for k in ["admission", "apply", "register"]):
        return (
            "📝 *Admission Information*\n\n"
            "For admission enquiry and support, use the official contact page:\n"
            f"{COLLEGE_ADMISSION_LINK}"
        )

    if any(k in msg for k in ["contact", "phone", "email", "mail"]):
        return (
            "📞 *Contact Details*\n\n"
            f"📱 Phone: {COLLEGE_PHONE}\n"
            f"📧 Email: {COLLEGE_EMAIL}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}"
        )

    if any(k in msg for k in ["location", "address", "where", "map"]):
        return (
            "📍 *College Location*\n\n"
            f"{COLLEGE_NAME}\n"
            f"{COLLEGE_LOCATION}\n\n"
            f"🌐 Website: {COLLEGE_WEBSITE}"
        )

    return None

# ─────────────────────────────────────────────
# Menu Selection Handler
# ─────────────────────────────────────────────
_MENU_REPLIES = {
    "about_college": (
        f"🏫 *{COLLEGE_NAME}*\n\n"
        f"📍 Location: {COLLEGE_LOCATION}\n"
        f"🌐 Website: {COLLEGE_WEBSITE}\n"
        f"📧 Email: {COLLEGE_EMAIL}\n"
        f"📞 Phone: {COLLEGE_PHONE}"
    ),
    "courses_info": (
        "🎓 *Courses Available*\n\n"
        f"*UG Courses:*\n{ug_courses_text}\n\n"
        f"*PG Courses:*\n{pg_courses_text}\n\n"
        f"🌐 Website: {COLLEGE_WEBSITE}"
    ),
    "fees_info": (
        "💰 *Fee Categories*\n\n"
        "• Merit\n• Management\n• Counselling\n• 7.5 Fee\n\n"
        "📞 For exact fee details, contact admission office:\n"
        f"Phone: {COLLEGE_PHONE}\nEmail: {COLLEGE_EMAIL}"
    ),
    "admission_info": (
        "📝 *Admission Info*\n\n"
        f"For admission enquiry, use the official page:\n{COLLEGE_ADMISSION_LINK}"
    ),
    "contact_info": (
        "📞 *Contact Details*\n\n"
        f"📱 Phone: {COLLEGE_PHONE}\n"
        f"📧 Email: {COLLEGE_EMAIL}\n"
        f"🌐 Website: {COLLEGE_WEBSITE}"
    ),
    "location_info": (
        "📍 *Location*\n\n"
        f"{COLLEGE_NAME}\n{COLLEGE_LOCATION}\n\n"
        f"🌐 Website: {COLLEGE_WEBSITE}"
    ),
}

def handle_menu_selection(selected_id: str) -> str:
    return _MENU_REPLIES.get(
        selected_id,
        "🙂 Please type *hi* to open the menu again."
    )

# ─────────────────────────────────────────────
# Gemini AI Reply
# ─────────────────────────────────────────────
def get_gemini_reply(user_message: str):
    if not gemini_model:
        return None

    prompt = (
        f"You are a friendly WhatsApp admission assistant for {COLLEGE_NAME}.\n\n"
        "Rules:\n"
        "- Answer ONLY using the college details provided below.\n"
        "- Keep responses short, clear, and WhatsApp-friendly.\n"
        "- Do NOT invent fee amounts or any details not listed.\n"
        "- If you cannot answer from the given details, say: "
        f"'Please contact us at {COLLEGE_PHONE} or {COLLEGE_EMAIL}.'\n\n"
        f"College details:\n{COLLEGE_CONTEXT}\n\n"
        f"Student question: {user_message}"
    )

    try:
        response = gemini_model.generate_content(prompt)
        text = response.text.strip() if response and hasattr(response, "text") else None
        if text:
            logger.info("Gemini reply generated successfully.")
            return text
    except Exception as e:
        logger.error(f"Gemini Error: {e}")

    return None

# ─────────────────────────────────────────────
# Unified Reply Resolver
# ─────────────────────────────────────────────
FALLBACK_MSG = (
    "🙂 Sorry, I can only help with *V.S.B Engineering College* details.\n\n"
    "Type *hi* to open the menu."
)

def get_reply(user_message: str) -> str:
    static = get_static_reply(user_message)
    if static:
        return static

    gemini = get_gemini_reply(user_message)
    if gemini:
        return gemini

    return FALLBACK_MSG

# ─────────────────────────────────────────────
# Flask Routes
# ─────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return "VSB WhatsApp Bot is Live! 🎓", 200

@app.route("/health", methods=["GET"])
def health():
    return {
        "status": "ok",
        "gemini": gemini_model is not None,
        "whatsapp_token_set": bool(WHATSAPP_TOKEN),
    }, 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully.")
        return challenge, 200
    logger.warning("Webhook verification failed.")
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json(silent=True)
    if not data:
        return "OK", 200

    logger.info(f"INCOMING: {data}")

    try:
        entry   = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value   = changes.get("value", {})

        if "statuses" in value and "messages" not in value:
            return "OK", 200

        if "messages" not in value:
            return "OK", 200

        message     = value["messages"][0]
        from_number = message["from"]
        msg_type    = message.get("type")

        if _is_rate_limited(from_number):
            logger.info(f"Rate-limited duplicate from {from_number}, skipping.")
            return "OK", 200

        if msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "list_reply":
                selected_id = interactive["list_reply"]["id"]
                reply = handle_menu_selection(selected_id)
                send_text(from_number, reply)
            return "OK", 200

        if msg_type == "text":
            user_text = message["text"]["body"].strip()
            logger.info(f"MSG from {from_number}: {user_text}")
            reply = get_reply(user_text)

            if reply == "SHOW_MENU":
                send_menu(from_number)
            else:
                send_text(from_number, reply)
            return "OK", 200

        logger.info(f"Unsupported message type '{msg_type}' from {from_number}.")
        send_text(
            from_number,
            "🙂 I can only understand text messages for now.\nType *hi* to open the menu."
        )

    except (KeyError, IndexError) as e:
        logger.error(f"Webhook parsing error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected webhook error: {e}")

    return "OK", 200

# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
