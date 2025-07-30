import subprocess
import sys
import os
from pathlib import Path
from analyze_replies import analyze_replies
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import SessionLocal
from database.models import Campaign, EmailContent

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

def run_reply_analysis(user, campaign):
    print("\n📬 [5/5] Analyzing replies and classifying sentiments...")
    analyze_replies(user, campaign)

def main():
    if len(sys.argv) < 3:
        print("[ERROR] Usage: python run_campaign.py <username> <campaign_name>")
        sys.exit(1)

    user = sys.argv[1]
    campaign = sys.argv[2]

    print(f"\n🚀 Starting full campaign for user: {user}, campaign: {campaign}\n")

    run_scraper(user, campaign)
    run_generate(user, campaign)
    run_send(user, campaign)
    # merge_opens(user, campaign)  # Removed, open tracking is now DB-only
    run_reply_analysis(user, campaign)

    print(f"\n🎉 All done for user: {user}, campaign: {campaign}. Check the database for results.")

if __name__ == "__main__":
    main()
