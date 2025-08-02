print("=== Scraper started ===", flush=True)
import sys
import os
import json
import time
import random
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from itertools import product
import logging

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import SessionLocal
from database.models import User, Campaign, SenderConfig, Lead

# --------- Constants ---------
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

DORK_PATTERNS = [
    'site:{site_domain} "{industry}" "{location}" "@gmail.com"',
    'site:{site_domain} "{industry}" "{location}" intext:email',
    'site:{site_domain} "{industry}" "{location}" contact',
    'site:{site_domain} "{industry}" "{location}" "contact us"',
    'site:{site_domain} "{industry}" "{location}" inurl:contact',
    'site:{site_domain} "{industry}" "{location}" intitle:contact',
    'site:{site_domain} "{industry}" "{location}" "@yahoo.com"',
    'site:{site_domain} "{industry}" "{location}" "@outlook.com"'
]

# --------- Utility Functions ---------
def has_website(text):
    return bool(re.search(r"https?://[\w.-]+|www\.[\w.-]+", text))

def is_captcha_present(driver):
    try:
        return (
            driver.find_elements(By.CSS_SELECTOR, 'form#captcha-form') or
            driver.find_elements(By.CSS_SELECTOR, 'div#recaptcha') or
            'detected unusual traffic' in driver.page_source.lower()
        )
    except Exception:
        return False

def scrape_google(combinations):
    """
    Initializes a headless Selenium driver, scrapes Google for leads based on combinations,
    and returns a list of leads. The driver is managed entirely within this function.
    """
    # Setup browser inside the function for thread safety and server environment
    options = Options()
    # The "--headless" argument is commented out to make the browser window visible for solving CAPTCHAs.
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    service = Service(log_path=os.devnull)
    logging.getLogger('selenium').setLevel(logging.CRITICAL)

    try:
        driver = webdriver.Chrome(service=service, options=options)
    except WebDriverException as e:
        print(f"❌ Failed to start WebDriver: {e}. Ensure chromedriver is installed and in your PATH.")
        return []

    leads = []
    email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"
    for platform, industry, location in combinations:
        site_domain = platform if '.' in platform else f"{platform}.com"
        for dork in DORK_PATTERNS:
            query = dork.format(site_domain=site_domain, industry=industry, location=location)
            print(f"[SEARCH] {query}")
            try:
                user_agent = random.choice(USER_AGENTS)
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})

                driver.get("https://www.google.com")
                search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "q")))
                search_box.clear()
                search_box.send_keys(query)
                search_box.send_keys(Keys.RETURN)
                time.sleep(2)

                if is_captcha_present(driver):
                    print("[CAPTCHA] CAPTCHA detected. Waiting for it to be solved...")
                    for _ in range(90):
                        time.sleep(1)
                        if not is_captcha_present(driver):
                            print("[CAPTCHA] CAPTCHA solved or bypassed.")
                            break
                    else:
                        print("[CAPTCHA] Skipping query due to CAPTCHA.")
                        continue

                results = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.tF2Cxc"))
                )

                for result in results:
                    try:
                        title = result.find_element(By.CSS_SELECTOR, "h3.LC20lb").text
                        link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        description = result.find_element(By.CSS_SELECTOR, "div.VwiC3b").text

                        print(f"Result title: {title}")
                        print(f"Result description: {description}")
                        print(f"Result link: {link}")

                        profile_description = ""
                        emails = set(re.findall(email_pattern, description))
                        print(f"Emails found in description: {emails}")
                        try:
                            resp = requests.get(link, headers={"User-Agent": user_agent}, timeout=5)
                            if resp.status_code == 200:
                                soup = BeautifulSoup(resp.text, 'html.parser')
                                meta = soup.find('meta', attrs={'name': 'description'})
                                if meta:
                                    profile_description = meta.get("content", "")
                                page_emails = set(re.findall(email_pattern, resp.text))
                                print(f"Emails found in linked page: {page_emails}")
                                emails.update(page_emails)
                        except Exception as e:
                            print(f"Error fetching/parsing linked page: {e}")
                            pass

                        if emails:
                            print(f"Adding lead(s) with emails: {emails}")
                            for email in emails:
                                leads.append({
                                    "name": title,
                                    "email": email.strip(),
                                    "platform_source": platform.capitalize(),
                                    "profile_link": link,
                                    "website": "Yes" if has_website(description) else "No",
                                    "state": location,
                                    "industry": industry,
                                    "profile_description": profile_description
                                })
                        else:
                            print("No emails found for this result.")
                    except Exception as e:
                        print(f"Error parsing result: {e}")
                        continue

                time.sleep(1)
            except Exception as e:
                print(f"[ERROR] {e}")
                continue

    driver.quit()
    print(f"Total leads found: {len(leads)}")
    return leads

def run_scraper_for_campaign(username: str, campaign_name: str):
    """
    A self-contained function to be called as a background task.
    It handles DB connection, fetching campaign details, running the scraper,
    and saving the results.
    """
    session = SessionLocal()
    campaign_obj = None
    try:
        print(f"[SCRAPER TASK] Starting for user '{username}', campaign '{campaign_name}'")
        user_obj = session.query(User).filter_by(username=username).first()
        if not user_obj:
            raise Exception(f"[ERROR] User '{username}' not found in DB.")

        campaign_obj = session.query(Campaign).filter_by(user_id=user_obj.id, name=campaign_name).first()
        if not campaign_obj:
            raise Exception(f"[ERROR] Campaign '{campaign_name}' not found for user '{username}'.")

        # Set status after confirming campaign exists
        campaign_obj.status = "Scraping"
        session.commit()

        platforms = campaign_obj.platforms.split(",") if hasattr(campaign_obj, "platforms") else ["linkedin"]
        industries = campaign_obj.industries.split(",") if hasattr(campaign_obj, "industries") else ["tech"]
        locations = campaign_obj.locations.split(",") if hasattr(campaign_obj, "locations") else ["usa"]

        combinations = list(product(platforms, industries, locations))

        leads_data = scrape_google(combinations)

        if leads_data:
            # Check for existing emails in this campaign to avoid duplicates
            existing_emails = {
                lead.email for lead in session.query(Lead.email)
                .filter(Lead.campaign_id == campaign_obj.id)
                .all()
            }

            new_leads_added = 0
            for lead_dict in leads_data:
                if lead_dict["email"] not in existing_emails:
                    new_lead = Lead(
                        name=lead_dict["name"],
                        email=lead_dict["email"],
                        platform_source=lead_dict["platform_source"],
                        profile_link=lead_dict["profile_link"],
                        state=lead_dict["state"],
                        industry=lead_dict["industry"],
                        profile_description=lead_dict["profile_description"],
                        campaign_id=campaign_obj.id
                    )
                    session.add(new_lead)
                    existing_emails.add(new_lead.email)  # Add to set to prevent duplicates in same run
                    new_leads_added += 1

            if new_leads_added > 0:
                session.commit()
                campaign_obj.status = "Idle"
                print(f"[SCRAPER TASK] SUCCESS: Saved {new_leads_added} new leads for campaign '{campaign_name}'.")
            else:
                campaign_obj.status = "Idle"
                print(f"[SCRAPER TASK] INFO: Scraped {len(leads_data)} leads, but all were duplicates of existing ones.")
        else:
            campaign_obj.status = "Idle"
            print(f"[SCRAPER TASK] INFO: No new leads found for campaign '{campaign_name}'.")
        session.commit()
    except Exception as e:
        if campaign_obj:
            campaign_obj.status = f"Failed: Scraping error"
            session.commit()
        print(f"[SCRAPER TASK] ERROR for campaign '{campaign_name}': {e}")
        session.rollback()  # Rollback changes on error
    finally:
        session.close()

# --------- Main (for direct CLI execution) ---------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scraper.py <username> <campaign_name>")
        sys.exit(1)

    username_cli = sys.argv[1]
    campaign_name_cli = sys.argv[2]
    run_scraper_for_campaign(username_cli, campaign_name_cli)
