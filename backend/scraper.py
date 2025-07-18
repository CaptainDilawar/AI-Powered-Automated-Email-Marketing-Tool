import pandas as pd
import re
import time
import os
import random
import sys
from pathlib import Path
from datetime import datetime
from itertools import product
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import requests
from bs4 import BeautifulSoup
import json
import logging

options = Options()
options.add_argument("--ignore-certificate-errors")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
service = Service(log_path=os.devnull)
logging.getLogger('selenium').setLevel(logging.CRITICAL)
driver = webdriver.Chrome(service=service, options=options)
# --------- Get CLI Arguments ---------
if len(sys.argv) < 3:
    print("Usage: python scraper.py <username> <campaign_name>")
    sys.exit(1)

user = sys.argv[1]
campaign = sys.argv[2]

user_path = Path(f"data/{user}").resolve()
campaign_path = user_path / "campaigns" / campaign
campaign_path.mkdir(parents=True, exist_ok=True)

# --------- Load Campaign Meta Info ---------
meta_path = campaign_path / "campaign_config.json"
if not meta_path.exists():
    print(f"❌ Campaign meta.json not found: {meta_path}")
    sys.exit(1)

with open(meta_path, "r", encoding="utf-8") as f:
    meta = json.load(f)

service = meta.get("service")
platforms = meta.get("platforms", [])
industries = meta.get("industries", [])
locations = meta.get("locations", [])

# --------- Load Sender Config from user root ---------
sender_config_path = user_path / "sender_config.json"
if not sender_config_path.exists():
    print(f"❌ sender_config.json not found at {sender_config_path}")
    sys.exit(1)

with open(sender_config_path, "r", encoding="utf-8") as f:
    sender_info = json.load(f)

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
    pattern = r"https?://[\w.-]+|www\.[\w.-]+"
    return bool(re.search(pattern, text))

def is_captcha_present(driver):
    try:
        return (
            driver.find_elements(By.CSS_SELECTOR, 'form#captcha-form') or
            driver.find_elements(By.CSS_SELECTOR, 'div#recaptcha') or
            'detected unusual traffic' in driver.page_source.lower()
        )
    except Exception:
        return False

def scrape_google(driver, combinations):
    leads = []
    email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"

    for platform, industry, location in combinations:
        site_domain = platform if '.' in platform else f"{platform}.com"
        for dork in DORK_PATTERNS:
            query = dork.format(site_domain=site_domain, industry=industry, location=location)
            print(f"🔍 Searching: {query}")
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
                    print("⚠️ CAPTCHA detected. Waiting for it to be solved...")

                    for _ in range(90):
                        time.sleep(1)
                        if not is_captcha_present(driver):
                            print("✅ CAPTCHA solved or bypassed.")
                            break
                        else:
                            print("⏳ Captcha still present after 90 seconds, skipping this query.")
                            continue
                results = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.tF2Cxc"))
                )

                for result in results:
                    try:
                        title = result.find_element(By.CSS_SELECTOR, "h3.LC20lb").text
                        link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        description = result.find_element(By.CSS_SELECTOR, "div.VwiC3b").text

                        profile_description = ""
                        try:
                            resp = requests.get(link, headers={"User-Agent": user_agent}, timeout=5)
                            if resp.status_code == 200:
                                soup = BeautifulSoup(resp.text, 'html.parser')
                                meta = soup.find('meta', attrs={'name': 'description'})
                                if meta:
                                    profile_description = meta.get("content", "")
                        except Exception:
                            pass

                        emails = re.findall(email_pattern, description)
                        if emails and not has_website(description):
                            leads.append({
                                "Name": title,
                                "Email": ", ".join(list(set(emails))),
                                "Platform Source": platform.capitalize(),
                                "Profile Link": link,
                                "Website": "No",
                                "State": location,
                                "Industry": industry,
                                "Profile Description": profile_description
                            })
                    except Exception:
                        continue

                time.sleep(1)

            except Exception as e:
                print(f"❌ Error: {e}")
                continue

    return leads

# --------- Main ---------
if __name__ == "__main__":
    try:
        driver_opts = webdriver.ChromeOptions()
        driver_opts.add_argument("--ignore-certificate-errors")
        driver_opts.add_argument("--disable-extensions")
        driver_opts.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=driver_opts)

        combinations = list(product(platforms, industries, locations))
        leads = scrape_google(driver, combinations)

        if leads:
            df = pd.DataFrame(leads)
            df.drop_duplicates(subset=["Email", "Name"], inplace=True)
            df.to_csv(campaign_path / "leads.csv", index=False)
            print(f"✅ Saved {len(df)} leads to {campaign_path / 'leads.csv'}")
        else:
            print("⚠️ No leads found.")

    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()