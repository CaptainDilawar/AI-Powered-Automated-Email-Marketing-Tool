import pandas as pd
import requests
from tqdm import tqdm
import os
import json
from dotenv import load_dotenv
import csv
import sys
from pathlib import Path
import streamlit as st
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import SessionLocal
from database.models import Campaign, Lead, EmailContent, User

# --------- Get username ---------
if len(sys.argv) < 3:
    print("Usage: python generate_emails.py <username>")
    sys.exit(1)

user = sys.argv[1]
campaign = sys.argv[2]
# Folder creation removed; all data is stored in the database
# --------- Load API Key ---------
# env_path = Path(__file__).resolve().parent.parent / ".env"
# load_dotenv(dotenv_path=env_path)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# --------- Load Sender Info (User-specific) ---------
from database.models import SenderConfig, User

# --- Fetch sender config from DB ---
session = SessionLocal()
db_user = session.query(User).filter_by(username=user).first()
if not db_user:
    print(f"❌ User '{user}' not found.")
    sys.exit(1)

sender_config = session.query(SenderConfig).filter_by(user_id=db_user.id).first()
if not sender_config:
    print(f"❌ Sender config not found for user '{user}'. Please set it from the Sender Settings UI.")
    sys.exit(1)

SENDER_INFO = {
    "company_name": sender_config.company_name,
    "sender_name": sender_config.sender_name,
    "sender_email": sender_config.sender_email,
    "website": sender_config.website,
    "phone": sender_config.phone
}


# --------- Industry Role Mapping ---------
INDUSTRY_ROLES = {
    "Real Estate": "Real Estate Manager",
    "Clinic": "Clinic Manager",
    "Law Firm": "Legal Advisor",
    "Restaurant": "Restaurant Owner",
    "E-commerce": "E-commerce Owner",
    "Fitness": "Gym Owner",
    "Education": "School Administrator"
}

def create_prompt(row, service="Website Development"):
    # Sender details from user config
    company_name = SENDER_INFO["company_name"]
    sender_name = SENDER_INFO["sender_name"]
    sender_email = SENDER_INFO["sender_email"]
    website = SENDER_INFO["website"]
    phone = SENDER_INFO["phone"]

    # Lead details
    industry = row['Industry']
    state = row['State']
    platform = row['Platform Source']
    description = str(row.get('Profile Description', '') or '').strip()

    role_title = INDUSTRY_ROLES.get(industry, f"{industry} Professional")
    title_with_location = f"{role_title} in {state}"

    prompt = f"""
You are a professional email copywriter working for a digital agency called {company_name}. 

Your goal is to help generate leads for the agency by reaching out to potential clients for {service} services.

Generate:
1. A compelling subject line (less than 10 words)
2. A short, personalized outreach email.

Details:
- Recipient: {title_with_location}
- Industry: {industry}
- State: {state}
- Source Platform: {platform}
- Profile Description: "{description or 'N/A'}"

The email should:
- Mention they don't have a website
- Be personalized to their industry and location
- Be friendly, professional, and concise
- Start the email with: "Hi {title_with_location},"
- Include a call to action (e.g., "Can we connect for a quick chat?")
- End with this signature:

Best,  
{sender_name}  
{company_name}  
📧 {sender_email}  
🌐 {website}  
📞 {phone}

Return the output in this format:
Subject: [subject]  
Email:  
[email body]
"""
    return prompt.strip()

def generate_from_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a professional email copywriter."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }

    for attempt in range(3):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
            result = r.json()

            if "error" in result and "rate_limit_exceeded" in result.get("error", {}).get("code", ""):
                wait_time = 5 * (attempt + 1)
                print(f"⏳ Rate limit hit. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            if "choices" not in result or not result["choices"]:
                print("❌ Unexpected API response format:", result)
                return "ERROR", "ERROR"

            content = result["choices"][0]["message"]["content"].strip()

            subject = "N/A"
            body = content
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if line.lower().startswith("subject:"):
                    subject = line.replace("Subject:", "").strip()
                elif line.lower().startswith("email:"):
                    body = "\n".join(lines[i+1:]).strip()
                    break

            return subject, body

        except Exception as e:
            print(f"❌ Groq API error: {e}")
            time.sleep(3)

    return "ERROR", "ERROR"

def convert_to_html(text, lead_id):
    lines = text.strip().splitlines()
    html = "<p>" + "</p><p>".join(line.strip() for line in lines if line.strip()) + "</p>"
    tracking_pixel = f'<img src="http://localhost:5000/track_open?lead_id={lead_id}" width="1" height="1" alt="" style="display:none;">'
    return html + tracking_pixel

def main():
    session = SessionLocal()

    # --- Fetch user object first ---
    user_obj = session.query(User).filter_by(username=user).first()
    if not user_obj:
        print(f"❌ User '{user}' not found.")
        return

    # --- Fetch campaign using user_id ---
    campaign_obj = session.query(Campaign).filter_by(user_id=user_obj.id, name=campaign).first()
    if not campaign_obj:
        print(f"❌ Campaign '{campaign}' not found for user '{user}'")
        return

    leads = session.query(Lead).filter_by(campaign_id=campaign_obj.id).all()
    if not leads:
        print("⚠️ No leads found in database.")
        return

    print(f"\n📬 Generating emails using Groq API for {len(leads)} leads...\n")

    for lead in tqdm(leads):
        prompt = create_prompt({
            "Industry": lead.industry,
            "State": lead.state,
            "Platform Source": lead.platform_source,
            "Profile Description": lead.profile_description
        })
        subject, email = generate_from_groq(prompt)
        email_html = convert_to_html(email, lead_id=lead.id)

        print(f"\nLead ID: {lead.id}")
        print(f"Subject: {subject}")
        print(f"Email: {email[:100]}...")
        print(f"HTML: {email_html[:100]}...")

        # Save to DB
        email_content = EmailContent(
            lead_id=lead.id,
            campaign_id=campaign_obj.id,
            subject=subject,
            body=email,
            html=email_html
        )
        session.add(email_content)

    session.commit()
    session.close()
    print("\n✅ Emails saved to database.")


if __name__ == "__main__":
    main()
