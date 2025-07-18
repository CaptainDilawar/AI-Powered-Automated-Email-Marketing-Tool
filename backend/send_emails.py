import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# --------- CLI Arguments ---------
if len(sys.argv) < 3:
    print("Usage: python send_emails.py <username> <campaign>")
    sys.exit(1)

user = sys.argv[1]
campaign = sys.argv[2]

data_path = Path(f"data/{user}/campaigns/{campaign}").resolve()
data_path.mkdir(parents=True, exist_ok=True)

# --------- Load SMTP credentials from .env ---------
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
REPLY_TO_EMAIL = os.getenv("REPLY_TO_EMAIL")

# --------- Load generated email content ---------
input_path = data_path / "generated_emails.csv"
df = pd.read_csv(input_path)
df['Delivery Status'] = ""

print(f"\n📤 Sending {len(df)} emails via SMTP...\n")

# --------- Setup SMTP server ---------
server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
server.starttls()
server.login(SMTP_USERNAME, SMTP_PASSWORD)

# --------- Send emails ---------
for i, row in df.iterrows():
    recipient = row.get("Email")
    subject = row.get("Email Subject")
    body_text = row.get("Generated Email")
    body_html = row.get("Email HTML")

    if not recipient or "@" not in recipient:
        df.at[i, 'Delivery Status'] = "Invalid Email"
        continue

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USERNAME
        msg["To"] = recipient
        msg["Reply-To"] = REPLY_TO_EMAIL

        part1 = MIMEText(body_text, "plain")
        part2 = MIMEText(body_html, "html")
        msg.attach(part1)
        msg.attach(part2)

        server.sendmail(SMTP_USERNAME, recipient, msg.as_string())
        df.at[i, 'Delivery Status'] = "Sent"
        print(f"✅ Sent to {recipient}")

    except Exception as e:
        df.at[i, 'Delivery Status'] = f"Failed: {e}"
        print(f"❌ Failed to {recipient} — {e}")

server.quit()

# --------- Save results ---------
output_path = data_path / "personalized_emails_sent.csv"
df.to_csv(output_path, index=False)
print(f"\n✅ All done. Delivery statuses saved to '{output_path}'")
