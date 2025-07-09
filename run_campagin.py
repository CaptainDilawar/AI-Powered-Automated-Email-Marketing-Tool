import subprocess
import sys
import os

def run_scraper():
    print("\n🕷️ [1/3] Running lead scraper...")
    result = subprocess.run([sys.executable, "scraper.py"])
    if result.returncode != 0:
        print("❌ Scraper failed.")
        sys.exit(1)
    print("✅ Scraping completed. Leads saved to 'test_leads.csv'.")

def run_generate():
    print("\n🧠 [2/3] Generating emails...")
    result = subprocess.run([sys.executable, "generate_emails.py"])
    if result.returncode != 0:
        print("❌ Email generation failed.")
        sys.exit(1)
    print("✅ Emails generated in 'personalized_emails_groq.csv'.")

def run_send():
    print("\n📤 [3/3] Sending emails...")
    result = subprocess.run([sys.executable, "send_emails.py"])
    if result.returncode != 0:
        print("❌ Email sending failed.")
        sys.exit(1)
    print("✅ Emails sent. Logged in 'personalized_emails_sent.csv'.")

def main():
    print("\n🚀 Launching Full AI Email Outreach Campaign...\n")
    run_scraper()
    run_generate()
    run_send()
    print("\n🎉 All steps completed successfully.")

if __name__ == "__main__":
    main()
