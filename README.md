
# 🤖 AI-Powered Automated Email Marketing Tool

This project is a full-stack, multi-user platform for running personalized cold email campaigns using AI. It features lead scraping, AI-generated emails, automated sending, open/reply tracking, and advanced analytics—all managed through a modern Streamlit dashboard.

---

## 📦 Features

- � Secure login and multi-user management
- 🛠️ Admin dashboard: view all users, campaign activity, and delete users/campaigns with all related data
- �🔍 Google-based lead scraping
- 🧠 AI-generated emails (Groq + LLaMA3)
- ✉️ Automated email sending (SMTP)
- 📬 Open tracking and reply sentiment analysis
- 📊 Real-time campaign analytics: leads, sent emails, open rates, replies
- � Interactive charts and live reply viewer
- 📂 Export campaign results as CSV, Excel, or PDF
- 🧑‍� User dashboard: manage sender profile, campaigns, and view results

---

## ⚙️ Project Structure

.
├── .streamlit/
|       |── config.toml
├── backend/
│   ├── scraper.py
│   ├── generate_emails.py
│   ├── send_emails.py
│   ├── analyze_replies.py
│   └── run_campaign.py
│
├── server/
│   └── open_tracker.py
│
├── dashboard/
│   |── Home.py  # Main Streamlit dashboard
|   |── pages
|        |──AdminDashboard.py
|        |──CreateCampaign.py
|        |──Register.py
|        └──SenderSettings.py
│
├── database/
│   ├── db.py
│   ├── models.py
│   ├── leads_crud.py
│   └── initialize_db.py
│
├── start_app.py
├── .env
├── app.db  # SQLite database
├── user_auth.py
└── static/
    └── pixel.png

---

## 🛠️ Setup Instructions

### 1. 📦 Install Python Dependencies

Install Python 3.10+ and dependencies:

```bash
pip install -r requirements.txt
```

Or manually install the important ones:

```bash
pip install streamlit selenium pandas flask imapclient pyzmail requests python-dotenv xlsxwriter reportlab sqlalchemy
```

### 2. 🔐 Environment Variables

Create a `.env` file in the root:

```
GROQ_API_KEY = "your_groq_api_key"
SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_USERNAME = "yourmail@gmail.com"
SMTP_PASSWORD = "your_smtp_password"
REPLY_TO_EMAIL = "yourmail@gmail.com"
IMAP_SERVER = "imap.gmail.com"
EMAIL = "yourmail@gmail.com"
EMAIL_PASSWORD = "your_google_app_password"
```

### 3. 👤 Register Users
Register Users from the Register Page


### 4. 🧑‍💼 Start App & Login

Start the app with:

```bash
python start_app.py
```

Launch the Streamlit dashboard at [http://localhost:8501](http://localhost:8501)

Start the tracker server if needed.

### 5. ⚙️ Configure Sender Profile

Once logged in, go to Sender Settings in the dashboard sidebar and save:

- Sender name
- Company name
- Email
- Website
- Phone number

### 6. 🎯 Create and Manage Campaigns

Use the dashboard to:

- Set your service
- Choose target industries, states, and platforms
- Scrape leads, generate emails, send campaigns, analyze replies
- View campaign analytics and export results

---

## 🚀 Workflow Overview

1. **Lead Scraping** from Google using advanced dorks
2. **Email Generation** using AI (Groq / LLaMA3)
3. **SMTP Sending** using sender config
4. **Open Tracking** and reply analysis
5. **Sentiment Classification** for replies
6. **Admin Controls** for user/campaign management
7. **Data Export** (CSV, Excel, PDF)

All campaign, sender, lead, email, open tracking, and reply analysis data is stored in the SQLite database (`app.db`). All data is managed through the dashboard and backend scripts.

---

## 🧯 Troubleshooting

- ❌ CAPTCHA blocking: Try using VPN or wait before rerunning
- ❌ Invalid SMTP login: Make sure `.env` has correct credentials
- ❌ No leads scraped: Change industries/platforms/locations

---

## 👨‍💻 Developed by

Muhammad Dilawar Akram


---

## 🛠️ Setup Instructions

### 1. 📦 Install Python Dependencies

Install Python 3.10+ and dependencies:

```bash
pip install -r requirements.txt

Or manually install the important ones:

pip install streamlit selenium pandas flask imapclient pyzmail requests python-dotenv xlsxwriter

2. 🔐 Environment Variables
Create a .env file in the root:
GROQ_API_KEY = "gsk-afafadfkdfdfsdfhsdjhsdfhsdjkhfkdhf" #Take it from https://console.groq.com/keys
#smtp brevo
SMTP_SERVER = "smtp-relay.brevo.com" # SMTP Credentials from brevo.com. Through this server emails will be sent

---

## ℹ️ Important Notes

- **Reply Handling:** All replies from campaign recipients will be received in the inbox specified by the `EMAIL` and `EMAIL_PASSWORD` values in your `.env` file. The `REPLY_TO_EMAIL` sets the reply address shown to recipients, but replies are fetched from the configured IMAP inbox.
- **User Registration:** Users should register via the Register page in the dashboard. Admins can manage users and campaigns from the Admin Dashboard.
- **Data Storage:** All campaign, sender, lead, email, open tracking, and reply analysis data is stored in the SQLite database (`app.db`). No CSV or JSON files are used for campaign or sender configuration or results.

---