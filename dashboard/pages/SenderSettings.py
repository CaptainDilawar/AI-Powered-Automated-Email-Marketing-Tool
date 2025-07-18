import streamlit as st
import json
from pathlib import Path
import os
import sys

# Extend path to access user_auth
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from user_auth import get_authenticator

# -------------------- Page Config --------------------
st.set_page_config(page_title="✉️ Sender Settings", layout="centered")

# -------------------- Authentication --------------------
authenticator = get_authenticator()
name, auth_status, username = authenticator.login("Login", "main")

if not auth_status:
    if auth_status is False:
        st.error("❌ Incorrect username or password")
    elif auth_status is None:
        st.warning("🔐 Please enter your credentials")
    st.stop()

st.sidebar.success(f"✅ Logged in as: {username}")
authenticator.logout("🚪 Logout", "sidebar")

# -------------------- Setup Sender Config Path --------------------
user_data_path = Path("data") / username
user_data_path.mkdir(parents=True, exist_ok=True)
sender_config_path = user_data_path / "sender_config.json"

# -------------------- Load Existing Config --------------------
def load_config():
    if sender_config_path.exists():
        with open(sender_config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

config = load_config()

# -------------------- Sender Settings Form --------------------
st.title("✉️ Customize Your Sender Identity")
st.markdown("Fill in the details below to personalize your email campaigns.")

with st.form("sender_form"):
    company_name = st.text_input("Company Name", value=config.get("company_name", ""))
    sender_name = st.text_input("Sender Name", value=config.get("sender_name", ""))
    sender_email = st.text_input("Sender Email", value=config.get("sender_email", ""))
    website = st.text_input("Website URL", value=config.get("website", ""))
    phone = st.text_input("Phone Number", value=config.get("phone", ""))
    submitted = st.form_submit_button("💾 Save Settings")

    if submitted:
        new_config = {
            "company_name": company_name.strip(),
            "sender_name": sender_name.strip(),
            "sender_email": sender_email.strip(),
            "website": website.strip(),
            "phone": phone.strip(),
        }
        with open(sender_config_path, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=4)
        st.success("✅ Sender settings saved successfully!")
        st.balloons()

# -------------------- Show Preview --------------------
if sender_config_path.exists():
    st.markdown("---")
    st.subheader("📋 Current Sender Identity")
    with open(sender_config_path, "r", encoding="utf-8") as f:
        st.json(json.load(f))
