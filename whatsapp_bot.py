from flask import Flask, request
import os
import requests
import logging
import time
import threading
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
GEMINI_API_KEY  = os.environ.get("GROK_API_KEY")
WHATSAPP_TOKEN  = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN    = os.environ.get("VERIFY_TOKEN", "college_bot_123")

# ─────────────────────────────────────────────
# College Constants
# ─────────────────────────────────────────────
COLLEGE_NAME           = "V.S.B ENGINEERING COLLEGE"
COLLEGE_LOCATION       = "Karur, Tamil Nadu"
COLLEGE_EMAIL          = "admission@vsbec.com"
COLLEGE_PHONE          = "9994496212"
COLLEGE_WEBSITE        = "https://vsbec.edu.in/"
COLLEGE_ADMISSION_LINK = "https://vsbec.edu.in/contact-us/"
COLLEGE_MAP_LINK       = "https://maps.app.goo.gl/vsbec"

UG_COURSES = ["IT", "CSE", "AIML", "EEE", "ECE", "CIVIL", "CHEMICAL", "AIDS", "CCE", "CSBS"]
PG_COURSES = ["MBA", "M.Tech", "M.Sc", "MA"]

ug_courses_text = "\n".join([f"• {c}" for c in UG_COURSES])
pg_courses_text = "\n".join([f"• {c}" for c in PG_COURSES])

# ─── Hostel Info ───────────────────────────────
HOSTEL_INFO = {
    "en": (
        "🏢 *Hostel Facilities*\n\n"
        "*Boys Hostel:*\n"
        "• Separate hostel block for boys\n"
        "• 24/7 security & CCTV\n"
        "• Wi-Fi enabled rooms\n"
        "• Hygienic mess with South Indian food\n"
        "• Indoor games & reading room\n\n"
        "*Girls Hostel:*\n"
        "• Separate secure block for girls\n"
        "• Warden available 24/7\n"
        "• Wi-Fi enabled rooms\n"
        "• Nutritious meals provided\n"
        "• Laundry & medical facilities\n\n"
        f"📞 Hostel Enquiry: {COLLEGE_PHONE}\n"
        f"📧 Email: {COLLEGE_EMAIL}"
    ),
    "ta": (
        "🏢 *விடுதி வசதிகள்*\n\n"
        "*ஆண்கள் விடுதி:*\n"
        "• தனி விடுதி கட்டிடம்\n"
        "• 24/7 பாதுகாப்பு & CCTV\n"
        "• Wi-Fi வசதி\n"
        "• சுத்தமான உணவகம் - தென்னிந்திய உணவு\n"
        "• உள்ளரங்க விளையாட்டு & வாசிப்பறை\n\n"
        "*பெண்கள் விடுதி:*\n"
        "• தனி பாதுகாப்பான கட்டிடம்\n"
        "• 24/7 வார்டன் கண்காணிப்பு\n"
        "• Wi-Fi வசதி\n"
        "• சத்தான உணவு வழங்கல்\n"
        "• சலவை & மருத்துவ வசதி\n\n"
        f"📞 விடுதி விசாரணை: {COLLEGE_PHONE}\n"
        f"📧 மின்னஞ்சல்: {COLLEGE_EMAIL}"
    ),
}

# ─── Transport Info ────────────────────────────
TRANSPORT_INFO = {
    "en": (
        "🚌 *Transport Facilities*\n\n"
        "• College buses available from major routes\n"
        "• Covers: Karur, Tiruchirappalli, Namakkal,\n"
        "  Salem, Erode, Coimbatore & nearby areas\n"
        "• AC & Non-AC buses available\n"
        "• GPS tracking on all buses\n"
        "• Nominal transport fee\n"
        "• Morning & evening trips daily\n\n"
        f"📞 Transport Enquiry: {COLLEGE_PHONE}\n"
        f"📧 Email: {COLLEGE_EMAIL}"
    ),
    "ta": (
        "🚌 *போக்குவரத்து வசதிகள்*\n\n"
        "• முக்கிய பாதைகளில் கல்லூரி பஸ் வசதி\n"
        "• கரூர், திருச்சி, நாமக்கல்,\n"
        "  சேலம், ஈரோடு, கோவை & அருகில் உள்ள பகுதிகள்\n"
        "• AC & Non-AC பஸ் வசதி\n"
        "• அனைத்து பஸ்களிலும் GPS கண்காணிப்பு\n"
        "• குறைந்த போக்குவரத்து கட்டணம்\n"
        "• தினமும் காலை & மாலை சேவை\n\n"
        f"📞 போக்குவரத்து விசாரணை: {COLLEGE_PHONE}\n"
        f"📧 மின்னஞ்சல்: {COLLEGE_EMAIL}"
    ),
}

# ─── Placements Info ───────────────────────────
PLACEMENTS_INFO = {
    "en": (
        "🏆 *Placements & Achievements*\n\n"
        "*🌟 Star Performers (Product-Based):*\n"
        "• IT Dept — 47 LPA 🥇 (Atlassian)\n"
        "• IT Dept — 45 LPA (Walmart Global Tech)\n"
        "• IT Dept — 40 LPA (Flipkart)\n"
        "• CSE Dept — 45 LPA (Nutanix)\n"
        "• CSE Dept — 40 LPA (Chargebee)\n\n"
        "*🏢 Product-Based Companies:*\n"
        "• Zoho, Freshworks, Chargebee\n"
        "• Flipkart, Walmart Global Tech\n"
        "• Atlassian, Nutanix, Postman\n"
        "• PhonePe, Razorpay, Groww\n"
        "• Swiggy, Meesho, BrowserStack\n"
        "• Dunzo, Sharechat, Darwinbox\n\n"
        "*🏢 Service-Based Companies:*\n"
        "• TCS, Infosys, Wipro, Cognizant\n"
        "• HCL, Tech Mahindra, Capgemini\n"
        "• Accenture, LTIMindtree, Hexaware\n\n"
        "*📊 Placement Stats:*\n"
        "• ✅ 90%+ overall placement\n"
        "• 🥇 Highest: 47 LPA\n"
        "• 📈 Average: 6.5 LPA\n"
        "• 👥 500+ placed per year\n\n"
        "*🎖️ Accreditations:*\n"
        "• NAAC Accredited\n"
        "• NBA Accredited departments\n"
        "• Anna University rank holders\n\n"
        f"🌐 {COLLEGE_WEBSITE}"
    ),
    "ta": (
        "🏆 *வேலைவாய்ப்பு & சாதனைகள்*\n\n"
        "*🌟 சிறந்த சம்பள சாதனைகள் (Product நிறுவனங்கள்):*\n"
        "• IT துறை — 47 LPA 🥇 (Atlassian)\n"
        "• IT துறை — 45 LPA (Walmart Global Tech)\n"
        "• IT துறை — 40 LPA (Flipkart)\n"
        "• CSE துறை — 45 LPA (Nutanix)\n"
        "• CSE துறை — 40 LPA (Chargebee)\n\n"
        "*🏢 Product நிறுவனங்கள்:*\n"
        "• Zoho, Freshworks, Chargebee\n"
        "• Flipkart, Walmart Global Tech\n"
        "• Atlassian, Nutanix, Postman\n"
        "• PhonePe, Razorpay, Groww\n"
        "• Swiggy, Meesho, BrowserStack\n"
        "• Dunzo, Sharechat, Darwinbox\n\n"
        "*🏢 Service நிறுவனங்கள்:*\n"
        "• TCS, Infosys, Wipro, Cognizant\n"
        "• HCL, Tech Mahindra, Capgemini\n"
        "• Accenture, LTIMindtree, Hexaware\n\n"
        "*📊 வேலைவாய்ப்பு புள்ளிவிவரங்கள்:*\n"
        "• ✅ 90%+ வேலைவாய்ப்பு\n"
        "• 🥇 அதிகபட்சம்: 47 LPA\n"
        "• 📈 சராசரி: 6.5 LPA\n"
        "• 👥 ஆண்டுதோறும் 500+ மாணவர்களுக்கு வேலை\n\n"
        "*🎖️ அங்கீகாரங்கள்:*\n"
        "• NAAC அங்கீகரிக்கப்பட்டது\n"
        "• NBA அங்கீகரிக்கப்பட்ட துறைகள்\n"
        "• அண்ணா பல்கலைக்கழக rank holders\n\n"
        f"🌐 {COLLEGE_WEBSITE}"
    ),
}

COLLEGE_CONTEXT = f"""
College Name: {COLLEGE_NAME}
Location: {COLLEGE_LOCATION}
Email: {COLLEGE_EMAIL}
Phone: {COLLEGE_PHONE}
Website: {COLLEGE_WEBSITE}
UG Courses: {", ".join(UG_COURSES)}
PG Courses: {", ".join(PG_COURSES)}
Admission Info: {COLLEGE_ADMISSION_LINK}
Hostel: Boys and Girls hostel available with Wi-Fi, mess, security.
Transport: College buses from Karur, Trichy, Namakkal, Salem, Erode, Coimbatore.
Placements: 90%+ placement. Highest: 47 LPA (IT-Atlassian), 45 LPA (IT-Walmart, CSE-Nutanix), 40 LPA (IT-Flipkart, CSE-Chargebee). Product companies: Zoho, Freshworks, PhonePe, Razorpay, Groww, Swiggy, Meesho. Average: 6.5 LPA.
Accreditation: NAAC accredited, NBA accredited departments.
"""

# ─────────────────────────────────────────────
# Language Detection
# ─────────────────────────────────────────────
TAMIL_UNICODE_RANGE = range(0x0B80, 0x0BFF + 1)

def detect_language(text: str) -> str:
    for char in text:
        if ord(char) in TAMIL_UNICODE_RANGE:
            return "ta"
    return "en"

user_language: dict = {}

def get_lang(phone: str) -> str:
    return user_language.get(phone, "en")

def set_lang(phone: str, lang: str) -> None:
    user_language[phone] = lang

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
# Rate Limiter & Deduplication
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
# Auto Follow-up Store
# ─────────────────────────────────────────────
_follow_up_timers: dict = {}
FOLLOW_UP_DELAY = 300  # 5 minutes

FOLLOW_UP_MSG = {
    "en": (
        "👋 *Still have questions?*\n\n"
        "We're here to help you! 😊\n\n"
        "📞 Call us: *9994496212*\n"
        "📧 Email: *admission@vsbec.com*\n"
        f"🌐 Website: {COLLEGE_WEBSITE}\n\n"
        "Type *hi* to open the menu again."
    ),
    "ta": (
        "👋 *இன்னும் கேள்விகள் இருக்கா?*\n\n"
        "நாங்கள் உதவ இங்கே இருக்கிறோம்! 😊\n\n"
        f"📞 அழைக்கவும்: *{COLLEGE_PHONE}*\n"
        f"📧 மின்னஞ்சல்: *{COLLEGE_EMAIL}*\n"
        f"🌐 இணையதளம்: {COLLEGE_WEBSITE}\n\n"
        "*வணக்கம்* என்று தட்டச்சு செய்யவும்."
    ),
}

def _send_follow_up(phone: str, lang: str) -> None:
    logger.info(f"Sending follow-up to {phone}")
    send_text(phone, FOLLOW_UP_MSG.get(lang, FOLLOW_UP_MSG["en"]))

def schedule_follow_up(phone: str, lang: str) -> None:
    if phone in _follow_up_timers:
        _follow_up_timers[phone].cancel()
    t = threading.Timer(FOLLOW_UP_DELAY, _send_follow_up, args=[phone, lang])
    t.daemon = True
    t.start()
    _follow_up_timers[phone] = t

def cancel_follow_up(phone: str) -> None:
    if phone in _follow_up_timers:
        _follow_up_timers[phone].cancel()
        del _follow_up_timers[phone]

# ─────────────────────────────────────────────
# WhatsApp API Helpers
# ─────────────────────────────────────────────
_WA_URL = "https://graph.facebook.com/v22.0/{pid}/messages"

def _wa_headers():
    return {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

def _post_wa(payload: dict) -> None:
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.warning("Missing WHATSAPP_TOKEN or PHONE_NUMBER_ID — message not sent.")
        return
    url = _WA_URL.format(pid=PHONE_NUMBER_ID)
    try:
        resp = requests.post(url, headers=_wa_headers(), json=payload, timeout=20)
        if resp.status_code != 200:
            logger.error(f"WA API error {resp.status_code}: {resp.text}")
        else:
            logger.info(f"Sent to {payload.get('to')} ✓")
    except requests.exceptions.Timeout:
        logger.error("WA request timed out.")
    except Exception as e:
        logger.error(f"WA send error: {e}")

def send_text(to: str, message: str) -> None:
    _post_wa({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message[:4096]},
    })

def mark_read(msg_id: str) -> None:
    _post_wa({
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": msg_id,
    })

def send_call_button(to: str, lang: str) -> None:
    """Send a CTA button to directly call the college."""
    body = (
        "📞 *Need more help?*\nCall our admission team directly!"
        if lang == "en" else
        "📞 *கூடுதல் உதவி வேண்டுமா?*\nசேர்க்கை குழுவை நேரடியாக அழைக்கவும்!"
    )
    _post_wa({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "body": {"text": body},
            "action": {
                "name": "cta_url",
                "parameters": {
                    "display_text": "📞 Call Admission Office" if lang == "en" else "📞 அலுவலகத்தை அழைக்கவும்",
                    "url": f"tel:{COLLEGE_PHONE}",
                },
            },
        },
    })

def send_menu(to: str, lang: str = "en") -> None:
    welcome = (
        "👋 Welcome to *V.S.B Engineering College* Assistant!\n\nPlease choose an option below:\n\n_💡 Type *tamil* for Tamil | *english* for English_"
        if lang == "en" else
        "👋 *V.S.B பொறியியல் கல்லூரி* உதவியாளருக்கு வரவேற்கிறோம்!\n\nகீழே ஒரு விருப்பத்தை தேர்ந்தெடுக்கவும்:\n\n_💡 *english* என்று தட்டச்சு செய்தால் ஆங்கிலத்திற்கு மாறலாம்_"
    )
    header  = "🎓 VSB Engineering College Bot" if lang == "en" else "🎓 VSB பொறியியல் கல்லூரி Bot"
    footer  = "✨ Powered by VSBEC AI" if lang == "en" else "✨ VSBEC AI மூலம்"
    button  = "📋 Open Menu" if lang == "en" else "📋 பட்டியல் திற"

    rows_en = [
        {"id": "about_college",   "title": "🏫 About College",      "description": "Basic college details"},
        {"id": "courses_info",    "title": "🎓 Courses",             "description": "UG and PG courses"},
        {"id": "fees_info",       "title": "💰 Fees Details",        "description": "Merit, Management, Counselling"},
        {"id": "hostel_info",     "title": "🏢 Hostel",              "description": "Boys & Girls hostel facilities"},
        {"id": "transport_info",  "title": "🚌 Transport",           "description": "Bus routes & facilities"},
        {"id": "placements_info", "title": "🏆 Placements",          "description": "Top recruiters & packages"},
        {"id": "admission_info",  "title": "📝 Admission",           "description": "How to apply & enquiry"},
        {"id": "contact_info",    "title": "📞 Contact",             "description": "Phone and email"},
        {"id": "location_info",   "title": "📍 Location",            "description": "Address & map"},
    ]
    rows_ta = [
        {"id": "about_college",   "title": "🏫 கல்லூரி பற்றி",      "description": "அடிப்படை விவரங்கள்"},
        {"id": "courses_info",    "title": "🎓 படிப்புகள்",          "description": "UG மற்றும் PG படிப்புகள்"},
        {"id": "fees_info",       "title": "💰 கட்டண விவரம்",        "description": "மெரிட், மேனேஜ்மெண்ட்"},
        {"id": "hostel_info",     "title": "🏢 விடுதி",              "description": "ஆண்கள் & பெண்கள் விடுதி"},
        {"id": "transport_info",  "title": "🚌 போக்குவரத்து",        "description": "பஸ் பாதைகள் & வசதிகள்"},
        {"id": "placements_info", "title": "🏆 வேலைவாய்ப்பு",       "description": "முன்னணி நிறுவனங்கள் & சம்பளம்"},
        {"id": "admission_info",  "title": "📝 சேர்க்கை",           "description": "விண்ணப்பிப்பது எப்படி"},
        {"id": "contact_info",    "title": "📞 தொடர்பு",             "description": "தொலைபேசி மற்றும் மின்னஞ்சல்"},
        {"id": "location_info",   "title": "📍 இருப்பிடம்",          "description": "முகவரி & வரைபடம்"},
    ]

    _post_wa({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body":   {"text": welcome},
            "footer": {"text": footer},
            "action": {
                "button": button,
                "sections": [{
                    "title": "📚 College Information" if lang == "en" else "📚 கல்லூரி தகவல்",
                    "rows": rows_en if lang == "en" else rows_ta,
                }],
            },
        },
    })

# ─────────────────────────────────────────────
# Static Reply Content
# ─────────────────────────────────────────────
def _about(lang):
    if lang == "ta":
        return (f"🏫 *{COLLEGE_NAME}*\n\n"
                f"📍 இருப்பிடம்: {COLLEGE_LOCATION}\n"
                f"🌐 இணையதளம்: {COLLEGE_WEBSITE}\n"
                f"📧 மின்னஞ்சல்: {COLLEGE_EMAIL}\n"
                f"📞 தொலைபேசி: {COLLEGE_PHONE}")
    return (f"🏫 *{COLLEGE_NAME}*\n\n"
            f"📍 Location: {COLLEGE_LOCATION}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}\n"
            f"📧 Email: {COLLEGE_EMAIL}\n"
            f"📞 Phone: {COLLEGE_PHONE}")

def _courses(lang):
    if lang == "ta":
        return (f"🎓 *கிடைக்கும் படிப்புகள்*\n\n"
                f"*UG படிப்புகள்:*\n{ug_courses_text}\n\n"
                f"*PG படிப்புகள்:*\n{pg_courses_text}\n\n"
                f"🌐 {COLLEGE_WEBSITE}")
    return (f"🎓 *Courses Available*\n\n"
            f"*UG Courses:*\n{ug_courses_text}\n\n"
            f"*PG Courses:*\n{pg_courses_text}\n\n"
            f"🌐 {COLLEGE_WEBSITE}")

def _fees(lang):
    if lang == "ta":
        return ("💰 *கட்டண வகைகள்*\n\n"
                "• மெரிட்\n• மேனேஜ்மெண்ட்\n• கவுன்சலிங்\n• 7.5 ஒதுக்கீடு\n\n"
                f"📞 விவரங்களுக்கு: {COLLEGE_PHONE}\n"
                f"📧 மின்னஞ்சல்: {COLLEGE_EMAIL}")
    return ("💰 *Fee Categories*\n\n"
            "• Merit\n• Management\n• Counselling\n• 7.5 Quota\n\n"
            f"📞 For exact fee details: {COLLEGE_PHONE}\n"
            f"📧 Email: {COLLEGE_EMAIL}")

def _admission(lang):
    if lang == "ta":
        return (f"📝 *சேர்க்கை தகவல்*\n\n"
                f"அதிகாரப்பூர்வ தொடர்பு பக்கம்:\n👉 {COLLEGE_ADMISSION_LINK}")
    return (f"📝 *Admission Information*\n\n"
            f"Apply through our official contact page:\n👉 {COLLEGE_ADMISSION_LINK}")

def _contact(lang):
    if lang == "ta":
        return (f"📞 *தொடர்பு விவரங்கள்*\n\n"
                f"📱 தொலைபேசி: {COLLEGE_PHONE}\n"
                f"📧 மின்னஞ்சல்: {COLLEGE_EMAIL}\n"
                f"🌐 இணையதளம்: {COLLEGE_WEBSITE}")
    return (f"📞 *Contact Details*\n\n"
            f"📱 Phone: {COLLEGE_PHONE}\n"
            f"📧 Email: {COLLEGE_EMAIL}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}")

def _location(lang):
    if lang == "ta":
        return (f"📍 *கல்லூரி இருப்பிடம்*\n\n"
                f"{COLLEGE_NAME}\n{COLLEGE_LOCATION}\n\n"
                f"🗺️ Google Maps: {COLLEGE_MAP_LINK}\n"
                f"🌐 இணையதளம்: {COLLEGE_WEBSITE}")
    return (f"📍 *College Location*\n\n"
            f"{COLLEGE_NAME}\n{COLLEGE_LOCATION}\n\n"
            f"🗺️ Google Maps: {COLLEGE_MAP_LINK}\n"
            f"🌐 Website: {COLLEGE_WEBSITE}")

# ─────────────────────────────────────────────
# Menu Selection Handler
# ─────────────────────────────────────────────
MENU_MAP = {
    "about_college":   _about,
    "courses_info":    _courses,
    "fees_info":       _fees,
    "hostel_info":     lambda lang: HOSTEL_INFO.get(lang, HOSTEL_INFO["en"]),
    "transport_info":  lambda lang: TRANSPORT_INFO.get(lang, TRANSPORT_INFO["en"]),
    "placements_info": lambda lang: PLACEMENTS_INFO.get(lang, PLACEMENTS_INFO["en"]),
    "admission_info":  _admission,
    "contact_info":    _contact,
    "location_info":   _location,
}

def handle_menu_selection(selected_id: str, lang: str) -> str:
    fn = MENU_MAP.get(selected_id)
    if fn:
        return fn(lang)
    return ("🙂 Please type *hi* to open the menu."
            if lang == "en" else
            "🙂 *வணக்கம்* என்று தட்டச்சு செய்யவும்.")

# ─────────────────────────────────────────────
# Static Reply Logic
# ─────────────────────────────────────────────
GREETINGS      = {"hi", "hello", "hey", "hii", "menu", "start", "help", "hai", "வணக்கம்", "vanakkam"}
SWITCH_TAMIL   = {"tamil", "தமிழ்", "tamizh", "ta"}
SWITCH_ENGLISH = {"english", "eng", "en"}

def get_static_reply(text: str, lang: str):
    msg = text.lower().strip()

    if msg in SWITCH_TAMIL:   return "SWITCH_TA"
    if msg in SWITCH_ENGLISH: return "SWITCH_EN"
    if msg in GREETINGS:      return "SHOW_MENU"

    if any(w in msg for w in ("about", "college", "vsbec", "கல்லூரி", "பற்றி")):
        return _about(lang)
    if any(w in msg for w in ("course", "courses", "branch", "படிப்பு")) or msg in ("ug", "pg"):
        return _courses(lang)

    # Individual course
    all_lower = {c.lower(): c for c in UG_COURSES + PG_COURSES}
    if msg in all_lower:
        course = all_lower[msg]
        if lang == "ta":
            return (f"🎓 *{course} படிப்பு*\n\n{course} படிப்பு {COLLEGE_NAME} இல் உள்ளது.\n\n"
                    f"📞 {COLLEGE_PHONE}\n📧 {COLLEGE_EMAIL}\n🌐 {COLLEGE_WEBSITE}")
        return (f"🎓 *{course} Course*\n\n{course} is offered at {COLLEGE_NAME}.\n\n"
                f"📞 {COLLEGE_PHONE}\n📧 {COLLEGE_EMAIL}\n🌐 {COLLEGE_WEBSITE}")

    if any(w in msg for w in ("fee", "fees", "merit", "management", "counselling", "7.5", "கட்டணம்")):
        return _fees(lang)
    if any(w in msg for w in ("hostel", "accommodation", "room", "mess", "விடுதி", "தங்கும்")):
        return HOSTEL_INFO.get(lang, HOSTEL_INFO["en"])
    if any(w in msg for w in ("transport", "bus", "route", "travel", "பஸ்", "போக்குவரத்து")):
        return TRANSPORT_INFO.get(lang, TRANSPORT_INFO["en"])
    if any(w in msg for w in ("placement", "job", "salary", "package", "recruit", "வேலை", "சம்பளம்")):
        return PLACEMENTS_INFO.get(lang, PLACEMENTS_INFO["en"])
    if any(w in msg for w in ("admission", "apply", "register", "சேர்க்கை", "விண்ணப்பம்")):
        return _admission(lang)
    if any(w in msg for w in ("contact", "phone", "email", "mail", "தொடர்பு", "தொலைபேசி")):
        return _contact(lang)
    if any(w in msg for w in ("location", "address", "where", "map", "இருப்பிடம்", "எங்கே")):
        return _location(lang)

    return None

# ─────────────────────────────────────────────
# Gemini AI Reply
# ─────────────────────────────────────────────
GEMINI_PROMPT = {
    "en": (
        f"You are a friendly WhatsApp admission assistant for {COLLEGE_NAME}.\n"
        "Rules:\n"
        "- Answer ONLY using the college details below.\n"
        "- Keep responses short and WhatsApp-friendly (use *bold*).\n"
        "- Do NOT invent fee amounts or unverified details.\n"
        f"- If unsure, say: 'Please contact {COLLEGE_PHONE} or {COLLEGE_EMAIL}.'\n\n"
        f"College details:\n{COLLEGE_CONTEXT}"
    ),
    "ta": (
        f"நீங்கள் {COLLEGE_NAME} க்கான WhatsApp சேர்க்கை உதவியாளர்.\n"
        "விதிகள்:\n"
        "- கீழே உள்ள கல்லூரி விவரங்களை மட்டுமே பயன்படுத்தவும்.\n"
        "- பதில்கள் தமிழில் சுருக்கமாக இருக்கட்டும்.\n"
        "- கண்டுபிடிக்காத விவரங்களை சொல்லாதீர்கள்.\n"
        f"- தெரியாவிட்டால்: '{COLLEGE_PHONE} அல்லது {COLLEGE_EMAIL} தொடர்பு கொள்ளவும்.'\n\n"
        f"கல்லூரி விவரங்கள்:\n{COLLEGE_CONTEXT}"
    ),
}

def get_gemini_reply(user_message: str, lang: str):
    if not gemini_model:
        return None
    try:
        full_prompt = GEMINI_PROMPT.get(lang, GEMINI_PROMPT["en"]) + f"\n\nStudent question: {user_message}"
        response = gemini_model.generate_content(full_prompt)
        text = response.text.strip() if response and hasattr(response, "text") else None
        if text:
            logger.info("Gemini reply generated ✓")
        return text
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return None

# ─────────────────────────────────────────────
# Master Reply Dispatcher
# ─────────────────────────────────────────────
def get_reply(user_message: str, lang: str) -> str:
    static = get_static_reply(user_message, lang)
    if static:
        return static
    gemini = get_gemini_reply(user_message, lang)
    if gemini:
        return gemini
    if lang == "ta":
        return ("🙂 மன்னிக்கவும், VSB கல்லூரி தொடர்பான கேள்விகளுக்கு மட்டுமே உதவ முடியும்.\n\n"
                "*வணக்கம்* என்று தட்டச்சு செய்யவும்.")
    return ("🙂 Sorry, I can only help with *V.S.B Engineering College* queries.\n\n"
            "Type *hi* to open the menu.")

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
        "whatsapp_configured": bool(WHATSAPP_TOKEN and PHONE_NUMBER_ID),
    }, 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified ✅")
        return challenge, 200
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
        msg_id      = message.get("id", "")
        msg_type    = message.get("type")

        if _is_rate_limited(from_number):
            logger.info(f"Rate-limited {from_number}, skipping.")
            return "OK", 200

        if msg_id:
            mark_read(msg_id)

        lang = get_lang(from_number)

        # ── Interactive list reply ─────────────────────
        if msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "list_reply":
                selected_id = interactive["list_reply"]["id"]
                reply = handle_menu_selection(selected_id, lang)
                send_text(from_number, reply)
                # Send call button after hostel/placement/admission info
                if selected_id in ("hostel_info", "placements_info", "admission_info", "fees_info"):
                    time.sleep(1)
                    send_call_button(from_number, lang)
                schedule_follow_up(from_number, lang)
            return "OK", 200

        # ── Text message ───────────────────────────────
        if msg_type == "text":
            user_text = message["text"]["body"].strip()
            logger.info(f"MSG [{lang}] from {from_number}: {user_text}")

            detected = detect_language(user_text)
            if detected != lang:
                set_lang(from_number, detected)
                lang = detected

            reply = get_reply(user_text, lang)

            if reply == "SHOW_MENU":
                cancel_follow_up(from_number)
                send_menu(from_number, lang)

            elif reply == "SWITCH_TA":
                set_lang(from_number, "ta")
                send_text(from_number,
                          "✅ மொழி *தமிழ்* ஆக மாற்றப்பட்டது.\n*வணக்கம்* என்று தட்டச்சு செய்யவும்.")

            elif reply == "SWITCH_EN":
                set_lang(from_number, "en")
                send_text(from_number,
                          "✅ Language switched to *English*.\nType *hi* to open the menu.")

            else:
                send_text(from_number, reply)
                schedule_follow_up(from_number, lang)

            return "OK", 200

        # ── Unsupported type ───────────────────────────
        msg = ("🙂 I can only process text messages.\nType *hi* for the menu."
               if lang == "en" else
               "🙂 உரை செய்திகளை மட்டுமே புரிந்துகொள்ள முடியும்.\n*வணக்கம்* என்று தட்டச்சு செய்யவும்.")
        send_text(from_number, msg)

    except (KeyError, IndexError) as e:
        logger.error(f"Parsing error: {e}")
    except Exception as e:
        logger.exception(f"Webhook error: {e}")

    return "OK", 200

# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting VSB Bot on port {port}")
    app.run(host="0.0.0.0", port=port)
