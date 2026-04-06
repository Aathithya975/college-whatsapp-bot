# 📱College WhatsApp Bot

An automated WhatsApp chatbot for **V.S.B Engineering College, Karur** — built with Flask, WhatsApp Cloud API, and Google Gemini AI. Students and prospective applicants can query college information, courses, fees, and admission details directly through WhatsApp, with no additional app required.

---

## ✨ Features

- 🗂️ **Interactive Menu** — Tap-to-select list menu for quick navigation
- 🏫 **College Info** — About, location, website, and contact details
- 🎓 **Course Listings** — All UG and PG courses (IT, CSE, AIML, EEE, ECE, CIVIL, MBA, M.Tech, etc.)
- 💰 **Fee Categories** — Merit, Management, Counselling, and 7.5 fee info
- 📝 **Admission Enquiry** — Direct link to the official admission page
- 🤖 **Gemini AI Fallback** — Handles free-text questions using Google Gemini 1.5 Flash, grounded strictly in college data
- 🛡️ **Rate Limiting** — Built-in per-user cooldown (2 seconds) to prevent duplicate replies
- 🩺 **Health Endpoint** — `/health` route for uptime monitoring

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| WhatsApp API | Meta WhatsApp Cloud API (v22.0) |
| AI | Google Gemini 1.5 Flash (`google-generativeai`) |
| Server | Gunicorn |
| Deployment | Any platform supporting `PORT` env var (Render, Railway, etc.) |

---

## 📁 Project Structure

```
├── whatsapp.py        # Core bot logic — Flask app, webhook handling, Gemini AI, reply logic
├── whatsapp_bot.py    # Entry point — imports and runs the Flask app
├── requirements.txt   # Python dependencies
└── README.md
```

---

## ⚙️ Environment Variables

Set these before running:

| Variable | Description |
|---|---|
| `WHATSAPP_TOKEN` | Meta WhatsApp Cloud API bearer token |
| `PHONE_NUMBER_ID` | WhatsApp Phone Number ID from Meta Developer Console |
| `GEMINI_API_KEY` | Google Gemini API key (also checks `GOOGLE_API_KEY`) |
| `VERIFY_TOKEN` | Webhook verification token (default: `college_bot_123`) |
| `PORT` | Server port (default: `10000`) |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/vsb-whatsapp-bot.git
cd vsb-whatsapp-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

```bash
export WHATSAPP_TOKEN=your_token
export PHONE_NUMBER_ID=your_phone_number_id
export GEMINI_API_KEY=your_gemini_key
export VERIFY_TOKEN=college_bot_123
```

### 4. Run the server

```bash
# Development
python whatsapp_bot.py

# Production
gunicorn whatsapp:app
```

### 5. Configure Meta Webhook

In the [Meta Developer Console](https://developers.facebook.com/), set your webhook URL to:

```
https://your-domain.com/webhook
```

Use the same `VERIFY_TOKEN` value during webhook verification.

---

## 🤖 How It Works

1. User sends a message to the college's WhatsApp number.
2. Meta sends a POST request to `/webhook`.
3. The bot checks for a **greeting** → sends the interactive menu.
4. For **menu selections** (list replies) → returns the corresponding static info.
5. For **free-text queries** → checks keyword-based static replies first, then falls back to **Gemini AI** with a strict college-context prompt.
6. If nothing matches → sends a friendly fallback with a prompt to type `hi`.

---

## 💬 Supported Commands

| Input | Response |
|---|---|
| `hi`, `hello`, `hey`, `help`, `menu` | Shows interactive menu |
| `about`, `college` | College name, location, contact |
| `courses`, `ug`, `pg` | Full UG and PG course list |
| `cse`, `it`, `aiml`, `eee` … | Info for that specific course |
| `fees`, `merit`, `management` | Fee category details |
| `admission`, `apply` | Admission enquiry link |
| `contact`, `phone`, `email` | Contact details |
| `location`, `address`, `map` | College location |
| Any other question | Gemini AI answers using college context |

---

## 📋 API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/` or `/webhook` | Webhook verification |
| `POST` | `/` or `/webhook` | Receive incoming WhatsApp messages |
| `GET` | `/health` | Health check (Gemini + token status) |

---

## 📦 Requirements

```
flask
requests
google-generativeai
gunicorn
```

---

## 🏫 College Details (Hardcoded)

> **V.S.B Engineering College**, Karur
> 📞 9994496212 | 📧 admission@vsbec.com | 🌐 [vsbec.edu.in](https://vsbec.edu.in/)

**UG:** IT, CSE, AIML, EEE, ECE, CIVIL, CHEMICAL, AIDS, CCE, CSBS
**PG:** MBA, M.Tech, M.Sc, MA

---

## 📄 License

MIT License. Free to use and modify.
