import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import SessionLocal
from database.models import Campaign, EmailContent, Lead, User, SenderConfig

# --------- CLI Arguments ---------
if len(sys.argv) < 3:
    print("Usage: python send_emails.py <username> <campaign>")
    sys.exit(1)

username = sys.argv[1]
campaign_name = sys.argv[2]

# --------- Load SMTP credentials from .env ---------
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# --------- DB Setup ---------
session = SessionLocal()

# Get user object
user = session.query(User).filter_by(username=username).first()
if not user:
    print(f"❌ User '{username}' not found in database.")
    sys.exit(1)

# Get sender config from DB
sender_config = session.query(SenderConfig).filter_by(user_id=user.id).first()
if not sender_config:
    print(f"❌ Sender config not found in database for user '{username}'")
    sys.exit(1)

# Set reply-to (fallback to SMTP username if empty)
reply_to_email = sender_config.sender_email or SMTP_USERNAME

# Get campaign
campaign_obj = session.query(Campaign).filter_by(user_id=user.id, name=campaign_name).first()
if not campaign_obj:
    print(f"❌ Campaign '{campaign_name}' not found for user '{username}'")
    sys.exit(1)

emails = session.query(EmailContent).filter_by(campaign_id=campaign_obj.id).all()
if not emails:
    print("⚠️ No emails found in DB to send.")
    sys.exit(1)

print(f"\n📤 Sending {len(emails)} emails via SMTP...\n")

# --------- Setup SMTP server ---------
server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
server.starttls()
server.login(SMTP_USERNAME, SMTP_PASSWORD)

# --------- Send Emails ---------

for email in emails:
    lead = session.query(Lead).filter_by(id=email.lead_id).first()
    recipient = lead.email.strip().lower() if lead and lead.email else None

    if not recipient or "@" not in recipient:
        email.delivery_status = "Invalid Email"
        if lead:
            lead.delivery_status = "Invalid Email"
        continue

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = email.subject
        msg["From"] = SMTP_USERNAME
        msg["To"] = recipient
        msg["Reply-To"] = reply_to_email

        msg.attach(MIMEText(email.body, "plain"))
        msg.attach(MIMEText(email.html, "html"))

        server.sendmail(SMTP_USERNAME, recipient, msg.as_string())

        email.delivery_status = "Sent"
        if lead:
            lead.delivery_status = "Sent"
        print(f"✅ Sent to {recipient}")

    except Exception as e:
        email.delivery_status = f"Failed: {str(e)}"
        if lead:
            lead.delivery_status = f"Failed: {str(e)}"
        print(f"❌ Failed to {recipient} — {e}")

# --------- Save all updates ---------
session.commit()
session.close()
server.quit()

print("\n✅ All done. Email statuses saved to the database.")
