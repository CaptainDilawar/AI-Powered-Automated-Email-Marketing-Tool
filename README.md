# 🤖 AI-Powered Automated Email Marketing Tool

This is a full-stack solution for running personalized cold email campaigns using AI. It scrapes leads from Google, generates emails using LLMs, sends them, tracks opens, and analyzes replies — all from a graphical interface powered by Streamlit.

---

## 📦 Features

- 🔍 Google-based lead scraping
- 🧠 AI-generated emails (Groq + LLaMA3)
- ✉️ Auto email sending (SMTP)
- 📬 Open tracking & sentiment classification
- 🧑‍💼 Multi-user dashboard (login & campaign selection)
- 📊 Visual reporting via Streamlit UI

---

## ⚙️ Project Structure

.
├── backend/
│ ├── scraper.py
│ ├── generate_emails.py
│ ├── send_emails.py
│ ├── analyze_replies.py
│ └── run_campaign.py
│
├── server/
│ └── open_tracker.py
│
├── dashboard/
│ └── Home.py
│
├── start_app.py
├── .env
├── users.csv
└── data/
└── <username>/
├── sender_config.json
└── campaigns/
└── <campaign_name>/
├── campaign_config.json
├── leads.csv
├── personalized_emails_sent.csv
├── reply_analysis.csv
└── opens_log.csv


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
SMTP_PORT = 587
SMTP_USERNAME = "yourmail@gmail.com"
SMTP_PASSWORD ="yoursmtp-password"
REPLY_TO_EMAIL = "yourmail@gmail.com" #Mail on which you want to get replies from the campagins
# IMAP settings for Gmail
IMAP_SERVER= "imap.gmail.com" #server through which you will recieve replies
EMAIL="yourmail@gmail.com" 
EMAIL_PASSWORD="askeliwiosnvbhis" # A 16 digits password from google. Take it from myaccounts.google.com

3. 👤 Register Users
Edit users.csv with your details:
Credentials with which you login first
name,username,password,name,email,is_admin
Admin User,admin,$2b$12$1eFSjVY/lRyickUChfRp2egMoea9wvNlNDK0QcRvVmYwAGhbN25nm,admin@localhost,1 #Hashed Password

4. 🧑‍💼 Start App & Login
Start the app with:

python start_app.py
It will ask for your username.

Start the tracker server.

Launch the Streamlit dashboard at http://localhost:8501

5. ⚙️ Configure Sender Profile
Once logged in, go to Sender Settings in the dashboard sidebar and save:

Sender name

Company name

Email

Website

Phone number

Saved at:

data/<username>/sender_config.json
6. 🎯 Create a Campaign
Use the Campaign Manager tab:

Set your service

Choose target industries, states, and platforms

Campaign saved to:

data/<username>/campaigns/<campaign_name>/campaign_config.json

🚀 Campaign Workflow
Each campaign goes through the following automated stages:

Lead Scraping from Google using advanced dorks

Email Generation using AI (Groq / LLaMA3)

SMTP Sending using the sender config

Open Tracking merged into final report

Reply Analysis with sentiment classification

All results are saved in the campaign folder.

🧠 CAPTCHA Handling
If Google CAPTCHA appears, the script waits for 45 seconds to let you solve it. No need to press Enter manually.

📁 Key Output Files
File	Description
leads.csv	All scraped leads
personalized_emails_sent.csv	Emails that were generated and sent
reply_analysis.csv	Replies with classified sentiment
opens_log.csv	Open tracking log

🧯 Troubleshooting
❌ CAPTCHA blocking: Try using VPN or wait before rerunning

❌ Invalid SMTP login: Make sure .env has correct credentials

❌ No leads scraped: Change industries/platforms/locations

👨‍💻 Developed by
DynamicLeo