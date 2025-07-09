import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

# Load SMTP credentials
load_dotenv()
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Load the leads + email content
df = pd.read_csv("personalized_emails_groq.csv")

# Track status
df['Delivery Status'] = ""

print(f"\n📤 Sending {len(df)} emails via SMTP...\n")

# Set up SMTP connection
server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
server.starttls()
server.login(SMTP_USERNAME, SMTP_PASSWORD)

for i, row in df.iterrows():
    recipient = row.get("Email")
    subject = row.get("Email Subject")
    body_text = row.get("Generated Email")
    body_html = row.get("Email HTML")

    if not recipient or "@" not in recipient:
        df.at[i, 'Delivery Status'] = "Invalid Email"
        continue

    try:
        # Compose the email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USERNAME
        msg["To"] = recipient

        part1 = MIMEText(body_text, "plain")
        part2 = MIMEText(body_html, "html")
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        server.sendmail(SMTP_USERNAME, recipient, msg.as_string())
        df.at[i, 'Delivery Status'] = "Sent"
        print(f"✅ Sent to {recipient}")

    except Exception as e:
        df.at[i, 'Delivery Status'] = f"Failed: {e}"
        print(f"❌ Failed to {recipient} — {e}")

server.quit()

# Save with delivery status
df.to_csv("personalized_emails_sent.csv", index=False)
print("\n✅ All done. Delivery statuses saved to 'personalized_emails_sent.csv'")
