import streamlit as st
import subprocess
import pandas as pd
import os
from pathlib import Path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from user_auth import get_authenticator, is_admin_user

# -------------------- Page Config --------------------
st.set_page_config(page_title="📬 AI Email Dashboard", layout="wide")

# -------------------- Authentication --------------------
authenticator = get_authenticator()
name, auth_status, username = authenticator.login("Login", "main")

if not auth_status:
    if auth_status is False:
        st.error("❌ Incorrect username or password")
    elif auth_status is None:
        st.warning("🔐 Please enter your credentials")
    st.stop()

# -------------------- Authenticated --------------------
st.sidebar.success(f"✅ Logged in as: {username}")
authenticator.logout("🚪 Logout", "sidebar")

admin = is_admin_user(username)
user_data_path = f"data/{username}"
Path(user_data_path).mkdir(parents=True, exist_ok=True)

# -------------------- Admin Dashboard --------------------
if admin:
    st.title("🛠️ Admin Dashboard")
    st.write("Welcome, Admin. You can manage user data and view campaign metrics.")

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
        st.warning("No users registered yet.")
    st.stop()  # 👈 Stop here to prevent access to user tools

# -------------------- User Campaign Tools --------------------
st.title(f"📬 AI Email Campaign Dashboard — Welcome {name}")

st.sidebar.markdown("### ⚙️ Campaign Actions")
if st.sidebar.button("1️⃣ Run Full Campaign"):
    with st.spinner("Running full campaign..."):
        subprocess.run(["python", "backend/run_campaign.py", username])
    st.success("✅ Campaign completed!")

if st.sidebar.button("2️⃣ Re-analyze Replies"):
    with st.spinner("Analyzing replies..."):
        subprocess.run(["python", "backend/analyze_replies.py", username])
    st.success("✅ Reply analysis updated!")

if st.sidebar.button("3️⃣ Start Tracker Server"):
    subprocess.Popen(["python", "server/open_tracker.py"])
    st.success("📡 Open tracker started on port 5000")

# -------------------- Campaign Report --------------------
sent_log_path = f"{user_data_path}/personalized_emails_sent.csv"
if os.path.exists(sent_log_path):
    df = pd.read_csv(sent_log_path)
    st.subheader("📊 Campaign Results")

    col1, col2 = st.columns(2)
    with col1:
        sentiment_filter = st.selectbox("Filter by Reply Sentiment", ["All", "Positive", "Neutral", "Negative"])
    with col2:
        opened_filter = st.selectbox("Filter by Opened Status", ["All", "Yes", "No"])

    filtered_df = df.copy()
    if sentiment_filter != "All" and "Reply Sentiment" in df.columns:
        filtered_df = filtered_df[filtered_df["Reply Sentiment"] == sentiment_filter]

    if opened_filter != "All" and "Opened" in df.columns:
        filtered_df = filtered_df[filtered_df["Opened"] == opened_filter]

    st.dataframe(filtered_df, use_container_width=True)

    st.download_button(
        label="📥 Download Filtered Results",
        data=filtered_df.to_csv(index=False),
        file_name="campaign_results_filtered.csv",
        mime="text/csv"
    )

    if "Reply Sentiment" in df.columns:
        st.subheader("📈 Sentiment Distribution")
        st.bar_chart(df["Reply Sentiment"].value_counts())

    if "Opened" in df.columns:
        st.subheader("📈 Open Rate")
        st.bar_chart(df["Opened"].value_counts())

    if "Reply Text" in df.columns:
        st.subheader("📬 Live Reply Viewer")
        replies = df[df["Reply Text"].notna()][["Email", "Reply Sentiment"]]
        if not replies.empty:
            selected_email = st.selectbox("Select a reply to view", replies["Email"].tolist())
            reply_text = df[df["Email"] == selected_email]["Reply Text"].values[0]
            st.code(reply_text, language="text")
        else:
            st.info("No replies yet.")
else:
    st.info("No campaign data found. Run a campaign to generate results.")
