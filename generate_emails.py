import pandas as pd
import requests
from tqdm import tqdm
import os
import json
from dotenv import load_dotenv
import csv

# Load API key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Load sender info
with open("sender_config.json", "r", encoding="utf-8") as f:
    SENDER_INFO = json.load(f)

# Basic mapping of industries to professional titles
INDUSTRY_ROLES = {
    "Real Estate": "Real Estate Manager",
    "Clinic": "Clinic Manager",
    "Law Firm": "Legal Advisor",
    "Restaurant": "Restaurant Owner",
    "E-commerce": "E-commerce Owner",
    "Fitness": "Gym Owner",
    "Education": "School Administrator"
    # Add more mappings as needed
}

DEBUG_PRINT = False

def create_prompt(row, service="Website Development"):
    # Sender details from config
    company_name = SENDER_INFO["company_name"]
    sender_name = SENDER_INFO["sender_name"]
    sender_email = SENDER_INFO["sender_email"]
    website = SENDER_INFO["website"]
    phone = SENDER_INFO["phone"]

    # Lead details
    industry = row['Industry']
    state = row['State']
    platform = row['Platform Source']
    description = str(row.get('Profile Description', '') or '').strip()

    # Create professional role + location
    role_title = INDUSTRY_ROLES.get(industry, f"{industry} Professional")
    title_with_location = f"{role_title} in {state}"

    prompt = f"""
You are a professional email copywriter working for a digital agency called {company_name}. 

Your goal is to help generate leads for the agency by reaching out to potential clients for {service} services.

Generate:
1. A compelling subject line (less than 10 words)
2. A short, personalized outreach email.

Details:
- Recipient: {title_with_location}
- Industry: {industry}
- State: {state}
- Source Platform: {platform}
- Profile Description: "{description or 'N/A'}"

The email should:
- Mention they don’t have a website
- Be personalized to their industry and location
- Be friendly, professional, and concise
- Start the email with: "Hi {title_with_location},"
- Include a call to action (e.g., "Can we connect for a quick chat?")
- End with this signature:

Best,  
{sender_name}  
{company_name}  
📧 {sender_email}  
🌐 {website}  
📞 {phone}

Return the output in this format:
Subject: [subject]  
Email:  
[email body]
"""
    return prompt.strip()


def generate_from_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a professional email copywriter."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        result = r.json()

        if "choices" not in result or not result["choices"]:
            print("❌ Unexpected API response format:", result)
            return "ERROR", "ERROR"

        content = result["choices"][0]["message"]["content"].strip()

        if DEBUG_PRINT:
            print("---- RAW RESPONSE ----")
            print(content)
            print("----------------------\n")

        # Extract subject and body
        subject = "N/A"
        body = content
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.lower().startswith("subject:"):
                subject = line.replace("Subject:", "").strip()
            elif line.lower().startswith("email:"):
                body = "\n".join(lines[i+1:]).strip()
                break

        return subject, body

    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return "ERROR", "ERROR"

def convert_to_html(text):
    lines = text.strip().splitlines()
    html = "<p>" + "</p><p>".join(line.strip() for line in lines if line.strip()) + "</p>"
    return html

def main():
    input_file = "test_leads.csv"
    output_file = "personalized_emails_groq.csv"

    df = pd.read_csv(input_file)
    df['Email Subject'] = ""
    df['Generated Email'] = ""
    df['Email HTML'] = ""

    print(f"\n📬 Generating personalized emails using Groq API for {len(df)} leads...\n")

    for i in tqdm(df.index):
        prompt = create_prompt(df.loc[i])
        subject, email = generate_from_groq(prompt)
        email_html = convert_to_html(email)

        print(f"\n Lead {i+1}")
        print(f"Subject: {subject}")
        print(f"Email: {email[:100]}...")  # Preview
        print(f"HTML: {email_html[:100]}...")  # Preview

        df.at[i, 'Email Subject'] = subject
        df.at[i, 'Generated Email'] = email
        df.at[i, 'Email HTML'] = email_html

    df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL, lineterminator='\n', encoding='utf-8')
    print(f"\n✅ Emails and HTML saved to: '{output_file}'")

if __name__ == "__main__":
    main()
