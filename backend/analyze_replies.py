import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from imapclient import IMAPClient
import pyzmail
import sys
import streamlit as st

# Add root path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import SessionLocal
from database.models import Campaign, EmailContent, Lead, User

# --------- Load Environment Variables ---------
# load_dotenv(Path(__file__).resolve().parent.parent / ".env")
# EMAIL = os.getenv("EMAIL")
# EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
EMAIL = st.secrets["EMAIL"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
IMAP_SERVER = st.secrets.get("IMAP_SERVER", "imap.gmail.com")

# --------- Sentiment Classifier ---------
def classify_reply_text(reply_text):
    prompt = f"""You are a sales assistant. Classify the following email reply into one of the following categories:
- Positive (interested or wants to connect)
- Neutral (asks for more info or ambiguous)
- Negative (not interested, unsubscribe, or rejection)

Reply:
{reply_text}

Just return: Positive, Neutral, or Negative.
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a professional email assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 100
    }

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        r.raise_for_status()
        result = r.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Error classifying reply: {e}")
        return "Unknown"


# --------- Analyze Replies ---------
def analyze_replies(username, campaign_name):
    session = SessionLocal()

    # Fetch user object
    user_obj = session.query(User).filter_by(username=username).first()
    if not user_obj:
        print(f"❌ User '{username}' not found.")
        return

    # Fetch campaign
    campaign_obj = session.query(Campaign).filter_by(user_id=user_obj.id, name=campaign_name).first()
    if not campaign_obj:
        print(f"❌ Campaign '{campaign_name}' not found for user '{username}'")
        return

    # Fetch related email content
    email_records = session.query(EmailContent).filter_by(campaign_id=campaign_obj.id).all()
    if not email_records:
        print(f"⚠️ No emails found for campaign '{campaign_name}'")
        return

    # Map recipient emails to their records
    lead_map = {}
    for email in email_records:
        lead = session.query(Lead).filter_by(id=email.lead_id).first()
        if lead and lead.email:
            lead_map[lead.email.lower()] = (email, lead)

    if not lead_map:
        print("⚠️ No leads with valid email addresses found.")
        return


    # Connect to IMAP
    with IMAPClient(IMAP_SERVER) as client:
        client.login(EMAIL, EMAIL_PASSWORD)
        client.select_folder('INBOX', readonly=False)

        all_uids = set()
        for addr in lead_map.keys():
            try:
                uids = client.search(['FROM', addr])
                all_uids.update(uids)
            except Exception as e:
                print(f"IMAP search failed for sender {addr}: {e}", flush=True)

        for uid in all_uids:
            raw = client.fetch([uid], ['BODY[]', 'ENVELOPE'])
            msg = pyzmail.PyzMessage.factory(raw[uid][b'BODY[]'])
            envelope = raw[uid][b'ENVELOPE']
            sender_email = envelope.from_[0].mailbox.decode() + '@' + envelope.from_[0].host.decode()

            email_entry = lead_map.get(sender_email.lower())
            if not email_entry:
                print(f"⚠️ Reply from unknown sender: {sender_email}")
                continue

            email_record, _ = email_entry

            if msg.text_part:
                try:
                    reply_text = msg.text_part.get_payload().decode(msg.text_part.charset)
                    sentiment = classify_reply_text(reply_text)
                    email_record.reply_text = reply_text
                    email_record.reply_sentiment = sentiment
                    print(f"✅ Reply from {sender_email} → {sentiment}")
                except Exception as e:
                    print(f"⚠️ Error decoding reply from {sender_email}: {e}")

    session.commit()
    session.close()
    print("\n✅ Replies analyzed and saved to DB.")


# --------- CLI Entry Point ---------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python analyze_replies.py <username> <campaign>")
        sys.exit(1)

    username = sys.argv[1]
    campaign = sys.argv[2]
    analyze_replies(username, campaign)
