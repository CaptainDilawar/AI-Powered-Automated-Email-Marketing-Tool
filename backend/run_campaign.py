import subprocess
import sys
import os
import pandas as pd
from pathlib import Path
from analyze_replies import analyze_replies

def run_scraper(user, campaign):
    print("\n🕷️ [1/5] Running lead scraper...")
    result = subprocess.run([sys.executable, "backend/scraper.py", user, campaign])
    if result.returncode != 0:
        print("❌ Scraper failed.")
        sys.exit(1)
    print("✅ Scraping completed.")

def run_generate(user, campaign):
    print("\n🧠 [2/5] Generating emails...")
    result = subprocess.run([sys.executable, "backend/generate_emails.py", user, campaign])
    if result.returncode != 0:
        print("❌ Email generation failed.")
        sys.exit(1)
    print("✅ Emails generated.")

def run_send(user, campaign):
    print("\n📤 [3/5] Sending emails...")
    result = subprocess.run([sys.executable, "backend/send_emails.py", user, campaign])
    if result.returncode != 0:
        print("❌ Sending failed.")
        sys.exit(1)
    print("✅ Emails sent.")

def merge_opens(user, campaign):
    print("\n🔁 [4/5] Merging open tracking into final report...")
    base = Path(f"data/{user}/campaigns/{campaign}")
    sent_path = base / "personalized_emails_sent.csv"
    opens_path = base / "opens_log.csv"

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

def run_reply_analysis(user, campaign):
    print("\n📬 [5/5] Analyzing replies and classifying sentiments...")
    analyze_replies(user, campaign)

def main():
    if len(sys.argv) < 3:
        print("❌ Usage: python run_campaign.py <username> <campaign_name>")
        sys.exit(1)

    user = sys.argv[1]
    campaign = sys.argv[2]
    os.environ["CURRENT_USER"] = user
    os.environ["CURRENT_CAMPAIGN"] = campaign

    campaign_dir = Path(f"data/{user}/campaigns/{campaign}")
    campaign_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 Starting full campaign for user: {user}, campaign: {campaign}\n")
    run_scraper(user, campaign)
    run_generate(user, campaign)
    run_send(user, campaign)
    merge_opens(user, campaign)
    run_reply_analysis(user, campaign)
    print(f"\n🎉 All done for user: {user}, campaign: {campaign}. Results ready in /data/{user}/campaigns/{campaign}/")

if __name__ == "__main__":
    main()
