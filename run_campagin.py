import subprocess
import sys
import os
import pandas as pd

def run_scraper():
    print("\n🕷️ [1/4] Running lead scraper...")
    result = subprocess.run([sys.executable, "scraper.py"])
    if result.returncode != 0:
        print("❌ Scraper failed.")
        sys.exit(1)
    print("✅ Scraping completed.")

def run_generate():
    print("\n🧠 [2/4] Generating emails...")
    result = subprocess.run([sys.executable, "generate_emails.py"])
    if result.returncode != 0:
        print("❌ Email generation failed.")
        sys.exit(1)
    print("✅ Emails generated.")

def run_send():
    print("\n📤 [3/4] Sending emails...")
    result = subprocess.run([sys.executable, "send_emails.py"])
    if result.returncode != 0:
        print("❌ Sending failed.")
        sys.exit(1)
    print("✅ Emails sent.")

def merge_opens():
    print("\n🔁 [4/4] Merging open tracking into final report...")

    try:
        df_sent = pd.read_csv("personalized_emails_sent.csv")
        df_opens = pd.read_csv("opens_log.csv")
        opened_ids = set(df_opens['lead_id'].astype(int))
    except FileNotFoundError:
        opened_ids = set()

    if 'Lead ID' not in df_sent.columns:
        print("❌ 'Lead ID' column missing. Make sure it's included in generated emails.")
        sys.exit(1)

    df_sent['Opened'] = df_sent['Lead ID'].apply(lambda x: "Yes" if x in opened_ids else "No")
    df_sent.to_csv("personalized_emails_sent.csv", index=False)

    print("✅ Open status added to 'personalized_emails_sent.csv'")

def main():
    print("🚀 Launching Full AI Email Outreach Campaign...\n")
    run_scraper()
    run_generate()
    run_send()
    merge_opens()
    print("\n🎉 All steps completed successfully. Campaign report is ready!")

if __name__ == "__main__":
    main()
