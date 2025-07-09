import pandas as pd
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import time
from itertools import product
from tqdm import tqdm
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
]

SLEEP_BETWEEN_SEARCHES = 2  # seconds
ERROR_LOG_FILE = 'scraper_errors.log'

DORK_PATTERNS = [
    'site:{site_domain} "{industry}" "{location}" "@gmail.com"',
    'site:{site_domain} "{industry}" "{location}" intext:email',
    'site:{site_domain} "{industry}" "{location}" contact',
    'site:{site_domain} "{industry}" "{location}" "contact us"',
    'site:{site_domain} "{industry}" "{location}" inurl:contact',
    'site:{site_domain} "{industry}" "{location}" intitle:contact',
    'site:{site_domain} "{industry}" "{location}" "@yahoo.com"',
    'site:{site_domain} "{industry}" "{location}" "@outlook.com"',
]

def get_user_inputs():
    """Gets all the necessary inputs from the user AND CORRECTLY SPLITS THEM."""
    service = input("Enter the service you want to sell (e.g., website development): ")
    industries_str = input("Enter target industries (comma separated, e.g., real estate,insurance,lawyer): ")
    locations_str = input("Enter target states/locations (comma separated, e.g., California,Texas,Florida): ")
    platforms_str = input("Enter platforms to target (comma separated, e.g., yelp,instagram,linkedin,google): ")

    industry_list = [i.strip() for i in industries_str.split(",") if i.strip()]
    location_list = [l.strip() for l in locations_str.split(",") if l.strip()]
    platform_list = [p.strip().lower() for p in platforms_str.split(",") if p.strip()]

    print("\n--- Verifying Inputs After Splitting ---")
    print(f"Platforms list: {platform_list}")
    print(f"Industries list: {industry_list}")
    print(f"Locations list: {location_list}")
    print("----------------------------------------\n")
    
    return service, platform_list, industry_list, location_list

def has_website(text):
    """Checks if a given text string contains a URL pattern."""
    website_pattern = r"https?://[\w.-]+|www\.[\w.-]+"
    return bool(re.search(website_pattern, text))

def is_captcha_present(driver):
    """Detects if a Google CAPTCHA is present on the page."""
    try:
        # Check for common Google CAPTCHA elements or text
        if (
            driver.find_elements(By.CSS_SELECTOR, 'form#captcha-form') or
            driver.find_elements(By.CSS_SELECTOR, 'div#recaptcha') or
            'detected unusual traffic' in driver.page_source.lower() or
            'our systems have detected unusual traffic' in driver.page_source.lower()
        ):
            return True
    except Exception:
        pass
    return False

def scrape_google(driver, combinations):
    """
    Scrapes Google using multiple dork patterns for each combination.
    Shows a progress bar, randomizes user-agent, and logs errors to a file.
    """
    leads = []
    email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
    total_combinations = len(combinations)
    current_combo_number = 0
    with open(ERROR_LOG_FILE, 'a') as error_log:
        for platform, industry, location in tqdm(combinations, desc='Scraping', unit='search'):
            current_combo_number += 1
            print(f"\n--- [STARTING TASK {current_combo_number}/{total_combinations}] ---")
            # Randomize user-agent
            user_agent = random.choice(USER_AGENTS)
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
            site_domain = platform if '.' in platform else f'{platform}.com'
            for dork in DORK_PATTERNS:
                query = dork.format(site_domain=site_domain, industry=industry, location=location)
                print(f"Executing DORK search query: '{query}'")
                try:
                    driver.get("https://www.google.com")
                    search_box = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "q"))
                    )
                    search_box.clear()
                    search_box.send_keys(query)
                    search_box.send_keys(Keys.RETURN)
                    time.sleep(2)
                    # CAPTCHA detection and handling
                    if is_captcha_present(driver):
                        print("\n[CAPTCHA DETECTED] Pausing for 20 seconds. Please solve the CAPTCHA in the browser window.")
                        error_log.write(f"[CAPTCHA] Detected for Platform: {platform}, Industry: {industry}, State: {location}, Dork: {dork}\n")
                        time.sleep(20)
                        print("Resuming scraping...")
                    if current_combo_number == 1 and dork == DORK_PATTERNS[0]:
                        print("\n" + "="*50)
                        print(">>> ACTION REQUIRED FOR FIRST SEARCH <<<")
                        input(">>> Solve any CAPTCHA, then press Enter here to start the script... <<<")
                        print("="*50 + "\n...Starting automatic scraping...")
                    else:
                        time.sleep(SLEEP_BETWEEN_SEARCHES)
                    result_container_selector = "div.tF2Cxc"
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, result_container_selector))
                    )
                    results = driver.find_elements(By.CSS_SELECTOR, result_container_selector)
                    print(f"Scraping {len(results)} results from the page.")
                    for result in results:
                        try:
                            title = result.find_element(By.CSS_SELECTOR, "h3.LC20lb").text
                            link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                            description_div = result.find_element(By.CSS_SELECTOR, "div.VwiC3b")
                            description_text = description_div.text
                            # Try to fetch the profile page and extract meta description
                            profile_description = ""
                            try:
                                import requests
                                from bs4 import BeautifulSoup
                                headers = {"User-Agent": user_agent}
                                resp = requests.get(link, headers=headers, timeout=8)
                                if resp.status_code == 200:
                                    soup = BeautifulSoup(resp.text, 'html.parser')
                                    # Try meta description first
                                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                                    if meta_desc and meta_desc.get('content'):
                                        profile_description = meta_desc['content']
                                    else:
                                        # Fallback: get first paragraph or some text
                                        p = soup.find('p')
                                        if p:
                                            profile_description = p.get_text(strip=True)
                                else:
                                    profile_description = ""
                            except Exception as e:
                                profile_description = ""
                                error_log.write(f"[PROFILE DESC ERROR] {e}\n")
                            emails = re.findall(email_pattern, description_text)
                            website_found = has_website(description_text)
                            if emails and not website_found:
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
                                print(f"  [LEAD FOUND] Name: {title} | Email: {', '.join(list(set(emails)))}")
                        except Exception as e:
                            error_log.write(f"[RESULT ERROR] {e}\n")
                            continue
                except TimeoutException:
                    print("No valid search results found on this page (or CAPTCHA re-appeared).")
                    error_log.write(f"[TIMEOUT] Platform: {platform}, Industry: {industry}, State: {location}, Dork: {dork}\n")
                    continue
                except Exception as e:
                    print(f"An unexpected error occurred during this task. Skipping. Error: {e}")
                    error_log.write(f"[TASK ERROR] {e}\n")
                    continue
            print(f"--- [FINISHED TASK {current_combo_number}/{total_combinations}] ---")
    return leads

# --- Main Logic ---
if __name__ == "__main__":
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=options)

        service, platforms, industries, locations = get_user_inputs()
        all_combinations = list(product(platforms, industries, locations))
        
        if not all_combinations:
            print("No combinations to search.")
        else:
            print(f"Created a to-do list of {len(all_combinations)} individual searches.")
            all_leads = scrape_google(driver, all_combinations)
            
            if all_leads:
                df = pd.DataFrame(all_leads)
                df.drop_duplicates(subset=["Email", "Name"], inplace=True)
                # filename = f"leads_{service.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filename = "test_leads.csv"
                df.to_csv(filename, index=False)
                print(f"\nSUCCESS: All tasks finished. {len(df)} unique leads saved to {filename}")
            else:
                print("\nScraping finished, but no leads were found matching the criteria.")
            
    except Exception as e:
        print(f"\nAn unexpected error occurred in the main script: {e}")
    finally:
        if driver:
            print("Closing the browser.")
            driver.quit()