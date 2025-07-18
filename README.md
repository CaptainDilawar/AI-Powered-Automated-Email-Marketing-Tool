# AI-Powered-Automated-Email-Marketing-Tool
AI powered automated marketing tool for agencies.
# 🤖 AI-Powered Automated Email Marketing Tool

This is a full-stack solution for running personalized cold email campaigns using AI. It scrapes leads from Google, generates emails using GPT-based models, sends emails via SMTP, tracks opens and replies, and provides a web-based dashboard (built with Streamlit) for monitoring campaign performance.

---

## 📦 Features

- 🔍 Lead scraping with Google dorking
- 🧠 Email generation using AI (Groq + LLaMA3)
- ✉️ Automated SMTP email sending
- 📬 Open tracking and reply analysis
- 🧾 Sentiment classification of replies
- 🧑‍💼 Admin and user roles with authentication
- 📊 Streamlit-based campaign dashboard

---

## ⚙️ Project Structure

├── backend/
│ ├── scraper.py # Google scraper with CAPTCHA handling
│ ├── generate_emails.py # Email generation using AI
│ ├── send_emails.py # SMTP-based email sending
│ ├── analyze_replies.py # Fetch replies + classify with Groq
│ └── run_campaign.py # Runs full 5-step pipeline
│
├── dashboard/
│ └── Home.py # Streamlit dashboard for campaign results
│
├── server/
│ └── open_tracker.py # Flask-based open tracking server
│
├── users.csv # User registry (username, password, admin role)
├── start_app.py # Starts server + Streamlit dashboard
├── .env # Environment credentials
└── data/
└── <username>/
├── sender_config.json # Sender info (email, company, etc.)
└── campaigns/
└── <campaign_name>/
├── campaign_config.json
├── leads.csv
├── personalized_emails_sent.csv
├── reply_analysis.csv
└── opens_log.csv

yaml
Copy
Edit

---

## 🛠️ Setup Instructions

### 1. 🐍 Python Environment

Install Python 3.10+ and required packages:

```bash
pip install -r requirements.txt
Example packages you'll need:

txt
Copy
Edit
streamlit
selenium
pandas
imapclient
pyzmail
flask
requests
python-dotenv
xlsxwriter
2. 🔐 Configure .env
Create a .env file in the root with:

env
Copy
Edit
SMTP_USERNAME=youremail@gmail.com
SMTP_PASSWORD=yourapppassword
IMAP_SERVER=imap.gmail.com
GROQ_API_KEY=your_groq_api_key
💡 For Gmail, enable IMAP and create an App Password if 2FA is enabled.

3. 👤 Add User
Edit users.csv:

csv
Copy
Edit
username,password,name,email,is_admin
dilawar123,securepass,Dilawar,dilawar@example.com,True
4. 📨 Setup Sender Configuration
Run the app once and go to Sender Settings in the sidebar to configure:

json
Copy
Edit
{
  "sender_name": "Dilawar",
  "company_name": "WebGrow Solutions",
  "sender_email": "dilawar@example.com",
  "website": "https://webgrow.io",
  "phone": "+123456789"
}
This will be saved in:

Edit
data/<username>/sender_config.json
5. 🎯 Create a Campaign
Go to the Streamlit dashboard and create a campaign by choosing:

Service (e.g., Website Design)

Platforms (e.g., yelp, linkedin)

Target Industries (e.g., Real Estate, Clinics)

Locations (e.g., California, Texas)

A campaign_config.json will be saved in:

php-template
Copy
Edit
data/<username>/campaigns/<campaign_name>/
🚀 Run the Application
bash
Copy
Edit
python start_app.py
This will:

Start the open tracker server

Ask for your username

Run the full 5-step pipeline:

Scraper

AI Email Generator

SMTP Sender

Open Tracker Merge

Reply Analyzer

Launch the Streamlit dashboard on http://localhost:8501

✅ Full Workflow
Scraping: Uses Google dorks to find leads with emails

Email Generation: GPT-based AI generates personalized emails

Sending: Emails are sent using your configured SMTP account

Open Tracking: A pixel-based tracker logs when leads open your email

Reply Classification: Replies are pulled via IMAP and classified as Positive / Neutral / Negative

🧪 CAPTCHA Handling
If CAPTCHA is triggered on Google, the scraper will pause for 45 seconds

You can solve it manually, and the script will resume scraping automatically

📁 Output Files
Each campaign will include:

leads.csv: Scraped leads

personalized_emails_sent.csv: Final sent logs

reply_analysis.csv: Replies + sentiment

opens_log.csv: Leads who opened the email

🔐 Admin Dashboard
Admins can view:

All registered users

Total campaigns and emails sent by each user

🧯 Troubleshooting
CAPTCHA loops: Use residential proxies or rotate user agents

Invalid credentials: Check your SMTP / IMAP login details

No leads scraped: Adjust dork patterns or keywords

📌 Author
Built by DynamicLeo 🚀

