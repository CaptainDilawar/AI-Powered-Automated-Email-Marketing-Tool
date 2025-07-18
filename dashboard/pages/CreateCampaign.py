import streamlit as st
import json
from pathlib import Path
import os

# -------------------- Page Setup --------------------
st.set_page_config(page_title="🎯 Create Campaign", layout="centered")
st.title("🎯 Create a New Campaign")

# -------------------- Get Logged-in User --------------------
# Use Streamlit session state from the login
if "username" not in st.session_state:
    st.error("❌ You must be logged in to access this page.")
    st.stop()

username = st.session_state["username"]
user_campaign_dir = Path(f"data/{username}/campaigns")
user_campaign_dir.mkdir(parents=True, exist_ok=True)

# -------------------- Campaign Creation Form --------------------
with st.form("create_campaign"):
    campaign_name = st.text_input("Campaign Name (no spaces)", max_chars=30)

    service = st.text_input("Service You're Offering", value="Website Development")

    industries = st.multiselect(
        "Select Target Industries",
        ["Real Estate", "Clinic", "Law Firm", "Restaurant", "E-commerce", "Fitness", "Education"]
    )

    locations = st.text_input("Target Locations (comma-separated)", value="California, Texas, Florida")
    platforms = st.multiselect(
        "Platforms to Target",
        ["instagram", "yelp", "linkedin", "google"]
    )

    submitted = st.form_submit_button("📦 Save Campaign")

# -------------------- Save Campaign --------------------
if submitted:
    if not campaign_name:
        st.warning("⚠️ Please enter a campaign name.")
    elif not industries or not platforms:
        st.warning("⚠️ Select at least one industry and one platform.")
    else:
        clean_name = campaign_name.strip().replace(" ", "_").lower()
        campaign_path = user_campaign_dir / clean_name
        campaign_path.mkdir(parents=True, exist_ok=True)

        config = {
            "campaign_name": clean_name,
            "service": service,
            "industries": industries,
            "locations": [loc.strip() for loc in locations.split(",") if loc.strip()],
            "platforms": platforms
        }

        with open(campaign_path / "campaign_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        st.success(f"✅ Campaign '{clean_name}' saved!")
        st.balloons()
