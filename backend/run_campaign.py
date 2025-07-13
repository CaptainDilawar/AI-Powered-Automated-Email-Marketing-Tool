import subprocess
import sys
import os
import pandas as pd
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.analyze_replies import analyze_replies
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / user
def run_scraper(user):
    print("\n🕷️ [1/5] Running lead scraper...")
    result = subprocess.run([sys.executable, "backend/scraper.py", user])
    if result.returncode != 0:
        print("❌ Scraper failed.")
        sys.exit(1)
    print("✅ Scraping completed.")

def run_generate(user):
    print("\n🧠 [2/5] Generating emails...")
    result = subprocess.run([sys.executable, "backend/generate_emails.py", user])
    if result.returncode != 0:
        print("❌ Email generation failed.")
        sys.exit(1)
    print("✅ Emails generated.")

def run_send(user):
    print("\n📤 [3/5] Sending emails...")
    result = subprocess.run([sys.executable, "backend/send_emails.py", user])
    if result.returncode != 0:
        print("❌ Sending failed.")
        sys.exit(1)
    print("✅ Emails sent.")

def merge_opens(user):
    print("\n🔁 [4/5] Merging open tracking into final report...")
    sent_path = DATA_DIR/"personalized_emails_sent.csv"
    opens_path = DATA_DIR/"opens_log.csv"

    try:
        df_sent = pd.read_csv(sent_path)
    except FileNotFoundError:
        print(f"❌ {sent_path} not found. Skipping merge.")
        return

    try:
        df_opens = pd.read_csv(opens_path)
        opened_ids = set(df_opens['lead_id'].astype(int))
    except FileNotFoundError:
        print(f"⚠️ {opens_path} not found. Proceeding with all leads marked unopened.")
        opened_ids = set()

    if 'Lead ID' not in df_sent.columns:
        print("❌ 'Lead ID' column missing.")
        return

    df_sent['Opened'] = df_sent['Lead ID'].apply(lambda x: "Yes" if x in opened_ids else "No")
    df_sent.to_csv(sent_path, index=False)
    print("✅ Open status added to 'personalized_emails_sent.csv'")

def run_reply_analysis(user):
    print("\n📬 [5/5] Analyzing replies and classifying sentiments...")
    analyze_replies(user)

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python run_campaign.py <username>")
        sys.exit(1)

    user = sys.argv[1]
    os.environ["CURRENT_USER"] = user

    Path(f"data/{user}").mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 Starting full campaign for user: {user}\n")
    run_scraper(user)
    run_generate(user)
    run_send(user)
    merge_opens(user)
    run_reply_analysis(user)
    print(f"\n🎉 All done for user: {user}. Results ready in /data/{user}/")

if __name__ == "__main__":
    main()
