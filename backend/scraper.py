print("=== Scraper started ===", flush=True)
import sys
import os
import time
import random
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from itertools import product
import logging
# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import SessionLocal
from database.models import User, Campaign, Lead

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

def is_captcha_present(page):
    return page.query_selector('form#captcha-form') is not None or \
           page.query_selector('div#recaptcha') is not None or \
           "detected unusual traffic" in page.content().lower()

def scrape_google(combinations):
    """
    Initializes a headless Playwright browser, scrapes Google for leads,
    and returns a list of leads.
    """
    leads = []
    email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Always headless for server compatibility
        page = browser.new_page(user_agent=random.choice(USER_AGENTS))

        for platform, industry, location in combinations:
            site_domain = platform if '.' in platform else f"{platform}.com"
            for dork in DORK_PATTERNS:
                query = dork.format(site_domain=site_domain, industry=industry, location=location)
                print(f"[SEARCH] {query}")
                try:
                    page.goto("https://www.google.com", wait_until='networkidle', timeout=15000)
                    
                    search_box = page.locator('[name="q"]')
                    search_box.fill(query)
                    search_box.press("Enter")
                    
                    page.wait_for_load_state('networkidle', timeout=10000)

                    if is_captcha_present(page):
                        print("[CAPTCHA] CAPTCHA detected. Skipping query.")
                        continue

                    results = page.locator("div.tF2Cxc").all()

                    for result in results:
                        try:
                            title_element = result.locator("h3.LC20lb")
                            link_element = result.locator("a")
                            description_element = result.locator("div.VwiC3b")

                            title = title_element.inner_text() if title_element else ""
                            link = link_element.get_attribute("href") if link_element else ""
                            description = description_element.inner_text() if description_element else ""

                            print(f"Result title: {title}")
                            print(f"Result description: {description}")
                            print(f"Result link: {link}")

                            profile_description = ""
                            emails = set(re.findall(email_pattern, description))
                            print(f"Emails found in description: {emails}")

                            if link:
                                try:
                                    # Use requests for fetching linked pages to avoid browser overhead
                                    resp = requests.get(link, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=8)
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
                    
                    time.sleep(random.uniform(2, 5)) # Random delay between searches

                except PlaywrightTimeoutError:
                    print(f"[TIMEOUT] Timed out searching for: {query}")
                    continue
                except Exception as e:
                    print(f"[ERROR] {e}")
                    continue

        browser.close()
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

        campaign_obj.status = "Scraping"
        session.commit()

        platforms = campaign_obj.platforms.split(",") if hasattr(campaign_obj, "platforms") and campaign_obj.platforms else ["linkedin"]
        industries = campaign_obj.industries.split(",") if hasattr(campaign_obj, "industries") and campaign_obj.industries else ["tech"]
        locations = campaign_obj.locations.split(",") if hasattr(campaign_obj, "locations") and campaign_obj.locations else ["usa"]

        combinations = list(product(platforms, industries, locations))
        leads_data = scrape_google(combinations)

        if leads_data:
            existing_emails = {lead.email for lead in session.query(Lead.email).filter(Lead.campaign_id == campaign_obj.id).all()}
            new_leads_added = 0
            for lead_dict in leads_data:
                if lead_dict["email"] not in existing_emails:
                    new_lead = Lead(**lead_dict, campaign_id=campaign_obj.id)
                    session.add(new_lead)
                    existing_emails.add(new_lead.email)
                    new_leads_added += 1
            
            if new_leads_added > 0:
                session.commit()
                campaign_obj.status = "Idle"
                print(f"[SCRAPER TASK] SUCCESS: Saved {new_leads_added} new leads for campaign '{campaign_name}'.")
            else:
                campaign_obj.status = "Idle"
                print(f"[SCRAPER TASK] INFO: Scraped {len(leads_data)} leads, but all were duplicates.")
        else:
            campaign_obj.status = "Idle"
            print(f"[SCRAPER TASK] INFO: No new leads found for campaign '{campaign_name}'.")
        
        session.commit()
    except Exception as e:
        if campaign_obj:
            campaign_obj.status = "Failed: Scraping error"
            session.commit()
        print(f"[SCRAPER TASK] ERROR for campaign '{campaign_name}': {e}")
        session.rollback()
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