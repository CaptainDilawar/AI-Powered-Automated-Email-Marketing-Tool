# 🧠 AI-Powered Email Marketing Automation Tool  
### Built with Python, AI (Groq/OpenAI), and Problem Solving

---

## 🚀 Overview

This project is a fully automated, intelligent email marketing system built during our internship at **Dynamic Leo**. The tool streamlines the *entire cold email outreach pipeline* — from lead scraping to AI-personalized content generation, delivery, and open tracking.

It’s designed to solve one of the biggest problems in email marketing:
> “How do we scale outreach without sounding robotic?”

---

## ✅ Key Features

### 1. 🎯 Lead Scraping (Automated)
- Scrapes highly targeted professional leads based on industry, state, and platform.
- Extracts useful metadata: Name, Industry, State, Profile Description, Email, etc.
- Output file: `test_leads.csv`

### 2. ✍️ AI-Powered Email Generation
- Uses Groq (LLM) or OpenAI to generate:
  - Compelling subject lines
  - Hyper-personalized outreach messages
  - Professionally styled HTML versions
- Personalization includes:
  - Industry
  - Location
  - Tone of voice
- Output file: `personalized_emails_groq.csv`

### 3. 📧 Automated Email Delivery
- Sends emails using Python’s `smtplib` (SMTP).
- Delivers both plain text and HTML formats.
- Logs delivery status (`Sent`, `Failed`).
- Output file: `personalized_emails_sent.csv`

### 4. 👁️ Email Open Tracking
- Each email contains a unique tracking pixel.
- When opened, the server logs:
  - `Lead ID`
  - `Timestamp`
- Pixel tracking handled by a Flask server.
- Log file: `opens_log.csv`

### 5. 🔁 Merged Campaign Report
- Automatically merges open status into the final email report.
- Adds `Opened = Yes/No` column.
- Output: Enhanced `personalized_emails_sent.csv`

---

## 🛠 Technologies Used
- 🐍 Python
- 🌐 Flask (for tracking server)
- 🤖 Groq / OpenAI LLMs
- 📤 SMTP (Gmail-compatible)
- 🧠 Prompt engineering
- 🗂️ Pandas for CSV handling

---

## 🗃️ Folder Structure

```bash
project/
├── .env                       # API keys and SMTP credentials
├── sender_config.json         # Company/sender identity
├── scraper.py                 # Lead scraping logic
├── generate_emails.py         # AI personalization logic
├── send_emails.py             # SMTP-based delivery
├── open_tracker.py            # Flask server for pixel tracking
├── run_campaign.py            # Master orchestrator
├── pixel.png                  # 1x1 transparent tracking pixel
├── test_leads.csv             # Scraped leads
├── personalized_emails_groq.csv     # Generated emails
├── personalized_emails_sent.csv     # Final email log (with open status)
└── opens_log.csv              # Logs opens from pixel hits
