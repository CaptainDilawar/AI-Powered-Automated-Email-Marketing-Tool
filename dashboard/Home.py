import streamlit as st
import subprocess
import pandas as pd
import os
from pathlib import Path
import sys
import json
import shutil
from io import BytesIO
from xlsxwriter import Workbook
import reportlab
import base64

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from user_auth import get_authenticator, is_admin_user

st.set_page_config(page_title="📬 AI Email Dashboard", layout="wide")
authenticator = get_authenticator()
name, auth_status, username = authenticator.login("Login", "main")

if not auth_status:
    st.warning("🔐 Please enter your credentials")
    st.stop()

st.sidebar.success(f"✅ Logged in as: {username}")
authenticator.logout("🚪 Logout", "sidebar")

admin = is_admin_user(username)
user_base_path = Path(f"data/{username}")
campaigns_dir = user_base_path / "campaigns"
campaigns_dir.mkdir(parents=True, exist_ok=True)

# -------------------- Admin Dashboard --------------------
if admin:
    st.title("🛠️ Admin Dashboard")
    users_file = Path("users.csv")
    if users_file.exists():
        df_users = pd.read_csv(users_file)
        st.subheader("👤 Registered Users")
        st.dataframe(df_users[["username", "name", "email", "is_admin"]], use_container_width=True)

        st.subheader("📂 User Campaign Folders")
        user_dirs = sorted([f.name for f in Path("data/").glob("*") if f.is_dir()])
        for user_dir in user_dirs:
            user_campaign_dir = Path(f"data/{user_dir}/campaigns")
            campaigns = list(user_campaign_dir.glob("*/personalized_emails_sent.csv"))
            total = sum(pd.read_csv(c).shape[0] for c in campaigns)
            st.markdown(f"**🗂️ {user_dir}** — {total} emails sent across {len(campaigns)} campaigns")
    else:
        st.warning("No users registered yet.")
    st.stop()

# -------------------- Campaign Actions --------------------
st.title(f"📬 AI Email Campaign Dashboard — Welcome {name}")
sender_config_path = Path(f"data/{username}/sender_config.json")

st.subheader("📇 Your Sender Settings")

if sender_config_path.exists():
    with open(sender_config_path, "r", encoding="utf-8") as f:
        sender_info = json.load(f)

    st.markdown(f"""
**Sender Name:** {sender_info.get("sender_name", "N/A")}  
**Company:** {sender_info.get("company_name", "N/A")}  
**Email:** {sender_info.get("sender_email", "N/A")}  
**Website:** {sender_info.get("website", "N/A")}  
**Phone:** {sender_info.get("phone", "N/A")}  
""")
    st.info("✏️ You can update these in the **Sender Settings** page.")
else:
    st.warning("⚠️ Sender settings not found. Please go to the **Sender Settings** page to configure.")

# -------------------- Campaign Selector --------------------
campaigns = sorted([f.name for f in campaigns_dir.iterdir() if f.is_dir()])
if not campaigns:
    st.info("📂 No campaigns found. Run a campaign to get started.")
    st.stop()

selected_campaign = st.sidebar.selectbox("📂 Select a Campaign", campaigns)
campaign_path = campaigns_dir / selected_campaign
sent_log_path = campaign_path / "personalized_emails_sent.csv"

st.sidebar.markdown("### ⚙️ Campaign Actions")
if selected_campaign:
    if st.sidebar.button("1️⃣ Run Full Campaign"):
        with st.spinner("Running full campaign..."):
            subprocess.run(["python", "backend/run_campaign.py", username, selected_campaign])
        st.success("✅ Campaign completed!")

    if st.sidebar.button("2️⃣ Re-analyze Replies"):
        with st.spinner("Analyzing replies..."):
            subprocess.run(["python", "backend/analyze_replies.py", username, selected_campaign])
        st.success("✅ Reply analysis updated!")

    if st.sidebar.button("3️⃣ Start Tracker Server"):
        subprocess.Popen(["python", "server/open_tracker.py"])
        st.success("📡 Open tracker started on port 5000")
else:
    st.sidebar.warning("⚠️ No campaign selected.")

# Meta Info
meta_path = campaign_path / "meta.json"
if meta_path.exists():
    meta = json.load(open(meta_path))
    st.markdown(f"**🛠 Service**: {meta.get('service')} &nbsp;&nbsp; | &nbsp;&nbsp; **🗓 Date**: {meta.get('date')}")

# Delete Button
with st.expander("🗑️ Danger Zone: Delete This Campaign"):
    if st.button("⚠️ Delete Campaign"):
        shutil.rmtree(campaign_path)
        st.warning(f"Campaign '{selected_campaign}' deleted.")
        st.experimental_rerun()

# -------------------- Campaign Results --------------------
if sent_log_path.exists():
    df = pd.read_csv(sent_log_path)
    st.subheader("📊 Campaign Summary")

    total_leads = len(df)
    total_sent = df["Delivery Status"].eq("Sent").sum() if "Delivery Status" in df.columns else total_leads
    total_opened = df["Opened"].eq("Yes").sum() if "Opened" in df.columns else 0
    replies = df["Reply Text"].notna().sum() if "Reply Text" in df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Leads", total_leads)
    col2.metric("Emails Sent", total_sent)
    col3.metric("Emails Opened", total_opened)
    col4.metric("Replies", replies)

    # Filters
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

    # Export Buttons
    st.download_button("📥 Download CSV", data=filtered_df.to_csv(index=False), file_name=f"{selected_campaign}.csv", mime="text/csv")

    towrite = BytesIO()
    with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="Report")
    towrite.seek(0)
    st.download_button("📊 Export as Excel", data=towrite.read(), file_name=f"{selected_campaign}.xlsx")

    # Optional PDF button
if st.button("📄 Export to PDF (Stable)"):
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet

        from io import BytesIO
        buffer = BytesIO()

        selected_columns = [
            "Name", "Email", "Platform Source", "State", "Industry",
            "Email Subject", "Reply Sentiment", "Opened"
        ]
        data = filtered_df[selected_columns].fillna("").values.tolist()
        headers = selected_columns
        data.insert(0, headers)

        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        style = getSampleStyleSheet()

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#333333")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))

        story = [Paragraph(f"Campaign Report: {selected_campaign}", style["Title"]), table]
        doc.build(story)

        buffer.seek(0)
        st.download_button(
            label="📄 Download Campaign Report PDF",
            data=buffer,
            file_name=f"{selected_campaign}_summary.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"PDF generation failed: {e}")


    # Charts
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
    st.info("No campaign data found.")
