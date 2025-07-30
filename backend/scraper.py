
# --- Flask API ---

import chromedriver_autoinstaller
chromedriver_autoinstaller.install()
from flask import Flask, request, jsonify

app = Flask(__name__)

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
]

def has_website(text):
    import re
    return bool(re.search(r"https?://[\w.-]+|www\.[\w.-]+", text))

def is_captcha_present(driver):
    try:
        from selenium.webdriver.common.by import By
        return (
            driver.find_elements(By.CSS_SELECTOR, 'form#captcha-form') or
            driver.find_elements(By.CSS_SELECTOR, 'div#recaptcha') or
            'detected unusual traffic' in driver.page_source.lower()
        )
    except Exception:
        return False

def scrape_leads(username, campaign_name):
    import sys, os, random, time, re, requests
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException
    from itertools import product
    import logging
    import tempfile

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from database.db import SessionLocal
    from database.models import User, Campaign

    options = Options()
    options.add_argument("--ignore-certificate-errors")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    temp_profile = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_profile}")
    service = Service(log_path=os.devnull)
    logging.getLogger('selenium').setLevel(logging.CRITICAL)
    driver = webdriver.Chrome(service=service, options=options)

    session = SessionLocal()
    try:
        user_obj = session.query(User).filter_by(username=username).first()
        if not user_obj:
            return {"error": f"User '{username}' not found in DB."}, 404
        campaign_obj = session.query(Campaign).filter_by(user_id=user_obj.id, name=campaign_name).first()
        if not campaign_obj:
            return {"error": f"Campaign '{campaign_name}' not found for user '{username}'."}, 404

        platforms = campaign_obj.platforms.split(",") if hasattr(campaign_obj, "platforms") else ["linkedin"]
        industries = campaign_obj.industries.split(",") if hasattr(campaign_obj, "industries") else ["tech"]
        locations = campaign_obj.locations.split(",") if hasattr(campaign_obj, "locations") else ["usa"]
        combinations = list(product(platforms, industries, locations))

        # --- Scraping logic ---
        leads = []
        email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"
        for platform, industry, location in combinations:
            site_domain = platform if '.' in platform else f"{platform}.com"
            for dork in DORK_PATTERNS:
                query = dork.format(site_domain=site_domain, industry=industry, location=location)
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
                        for _ in range(90):
                            time.sleep(1)
                            if not is_captcha_present(driver):
                                break
                        else:
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
                            emails = set(re.findall(email_pattern, description))
                            try:
                                resp = requests.get(link, headers={"User-Agent": user_agent}, timeout=5)
                                if resp.status_code == 200:
                                    soup = BeautifulSoup(resp.text, 'html.parser')
                                    meta = soup.find('meta', attrs={'name': 'description'})
                                    if meta:
                                        profile_description = meta.get("content", "")
                                    page_emails = set(re.findall(email_pattern, resp.text))
                                    emails.update(page_emails)
                            except Exception:
                                pass
                            if emails:
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
                        except Exception:
                            continue
                    time.sleep(1)
                except Exception:
                    continue
        return {"leads": leads}, 200
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        driver.quit()
        session.close()

@app.route("/scrape", methods=["POST"])
def scrape_endpoint():
    data = request.get_json()
    username = data.get("username")
    campaign_name = data.get("campaign_name")
    if not username or not campaign_name:
        return jsonify({"error": "Missing username or campaign_name"}), 400
    result, status = scrape_leads(username, campaign_name)
    return jsonify(result), status

if __name__ == "__main__":
    app.run(debug=True)
