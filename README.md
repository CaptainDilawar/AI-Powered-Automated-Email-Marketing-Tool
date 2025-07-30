# AI Powered Automated Email Marketing Tool

## Railway Deployment Instructions

### 1. Prerequisites
- Push this repo to GitHub.
- Ensure all secrets (API keys, SMTP, IMAP, etc.) are set in Railway's environment variables (not in .env).

### 2. Multi-Service Setup
- This repo uses a Procfile to run two services:
  - `web`: Streamlit dashboard (`dashboard/Home.py`)
  - `scraper`: Flask/Selenium API (`backend/scraper.py`)

### 3. Deploy on Railway
- Go to https://railway.app and create a new project.
- Connect your GitHub repo.
- Railway will detect the Procfile and set up both services.
- Set all required environment variables in the Railway dashboard.
- After deployment, update the Streamlit dashboard's `FLASK_API_URL` to the public URL of the scraper service.

### 4. Chrome/Chromedriver
- Chrome and Chromedriver are auto-installed using `chromedriver-autoinstaller`.

### 5. Usage
- Access your Streamlit dashboard at the Railway web service URL.
- Scraping, campaign management, and email sending are all available from the dashboard.

---

For troubleshooting, see Railway docs or ask for help in the dashboard!
