import streamlit as st
import pandas as pd
import os
from pathlib import Path
import sys

# Allow import from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from user_auth import get_authenticator, is_admin_user

st.set_page_config(page_title="🛠️ Admin Dashboard", layout="wide")

# --- Authenticate first ---
authenticator = get_authenticator()
name, auth_status, username = authenticator.login("Admin Login", "main")

if not auth_status:
    if auth_status is False:
        st.error("❌ Incorrect username or password.")
    elif auth_status is None:
        st.warning("🔐 Please log in to access this page.")
    st.stop()

# --- Check admin role ---
if not is_admin_user(username):
    st.error("🚫 You do not have access to this page.")
    st.stop()

st.sidebar.success(f"✅ Logged in as admin: {username}")
authenticator.logout("🚪 Logout", "sidebar")

# --- Admin dashboard content ---
st.title("🛠️ Admin Dashboard")

users_file = Path("users.csv")
if users_file.exists():
    df_users = pd.read_csv(users_file)
    st.subheader("👤 Registered Users")
    st.dataframe(df_users[["username", "name", "email", "is_admin"]], use_container_width=True)

    st.subheader("📂 User Campaign Folders")
    user_dirs = sorted([f.name for f in Path("data/").glob("*") if f.is_dir()])
    for user_dir in user_dirs:
        campaign_file = Path(f"data/{user_dir}/personalized_emails_sent.csv")
        if campaign_file.exists():
            df = pd.read_csv(campaign_file)
            st.markdown(f"**🗂️ {user_dir}** — {len(df)} emails sent")
        else:
            st.markdown(f"**🗂️ {user_dir}** — ⚠️ No campaign yet")
else:
    st.warning("⚠️ No users registered yet.")
