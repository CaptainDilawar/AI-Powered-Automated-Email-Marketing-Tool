import pandas as pd
from imapclient import IMAPClient
import pyzmail
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables once
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")

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

def analyze_replies(user, campaign):
    base_path = Path(__file__).resolve().parent.parent
    campaign_path = base_path / "data" / user / "campaigns" / campaign
    campaign_path.mkdir(parents=True, exist_ok=True)

    sent_log = campaign_path / "personalized_emails_sent.csv"
    reply_log = campaign_path / "reply_analysis.csv"

    if not sent_log.exists():
        print(f"❌ Sent email log not found: {sent_log}")
        return

    df = pd.read_csv(sent_log)
    df['Reply Text'] = ''
    df['Reply Sentiment'] = ''

    known_recipients = df['Email'].dropna().unique().tolist()
    if not known_recipients:
        print("⚠️ No recipient emails found in sent log.")
        return

    with IMAPClient(IMAP_SERVER) as client:
        client.login(EMAIL, EMAIL_PASSWORD)
        client.select_folder('INBOX', readonly=False)

        search_query = ['OR'] * (len(known_recipients) - 1)
        for email in known_recipients:
            search_query.append('FROM')
            search_query.append(email)

        try:
            messages = client.search(search_query)
        except Exception as e:
            print(f"❌ IMAP search failed: {e}")
            return

        for uid in messages:
            raw = client.fetch([uid], ['BODY[]', 'ENVELOPE'])
            msg = pyzmail.PyzMessage.factory(raw[uid][b'BODY[]'])
            envelope = raw[uid][b'ENVELOPE']
            sender_email = envelope.from_[0].mailbox.decode() + '@' + envelope.from_[0].host.decode()

            if msg.text_part:
                try:
                    reply_text = msg.text_part.get_payload().decode(msg.text_part.charset)
                    sentiment = classify_reply_text(reply_text)

                    match = df[df['Email'] == sender_email]
                    if not match.empty:
                        idx = match.index[0]
                        df.at[idx, 'Reply Text'] = reply_text
                        df.at[idx, 'Reply Sentiment'] = sentiment
                        print(f"✅ Reply from {sender_email} → {sentiment}")
                    else:
                        print(f"⚠️ Reply from unknown sender: {sender_email}")
                except Exception as e:
                    print(f"⚠️ Error decoding reply from {sender_email}: {e}")

    df.to_csv(sent_log, index=False)
    df.to_csv(reply_log, index=False)
    print("\n✅ Replies analyzed and saved.")

# ---- CLI Entry Point ----
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python analyze_replies.py <username> <campaign>")
        sys.exit(1)

    user = sys.argv[1]
    campaign = sys.argv[2]
    analyze_replies(user, campaign)
