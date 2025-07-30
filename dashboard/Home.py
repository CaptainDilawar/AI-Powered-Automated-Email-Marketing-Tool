import streamlit as st
import subprocess
import pandas as pd
import os
import sys
from pathlib import Path
from io import BytesIO
from xlsxwriter import Workbook
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import text

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from user_auth import get_authenticator, is_admin_user
from database.db import SessionLocal
from database.models import User, Campaign, Lead, SenderConfig, EmailContent

st.set_page_config(page_title="📬 AI Automated Email Marketing Tool", layout="wide")

authenticator = get_authenticator()
name, auth_status, username = authenticator.login("Login", "main")

if not auth_status:
    if auth_status is False:
        st.error("❌ Incorrect username or password.")
    elif auth_status is None:
        st.warning("🔐 Please enter your credentials")
    st.stop()



# Sidebar navigation logic
if not auth_status:
    st.sidebar.title("Navigation")
    st.sidebar.page_link("pages/CreateCampaign.py", label="Create Campaign")
    st.sidebar.page_link("pages/Register.py", label="Register")
    st.sidebar.page_link("pages/SenderSettings.py", label="Sender Settings")
else:
    st.sidebar.success(f"✅ Logged in as: {username}")
    authenticator.logout("🚪 Logout", "sidebar")
    # Only show AdminDashboard if admin
    if is_admin_user(username):
        st.sidebar.page_link("pages/AdminDashboard.py", label="Admin Dashboard")
    st.sidebar.page_link("pages/CreateCampaign.py", label="Create Campaign")
    st.sidebar.page_link("pages/SenderSettings.py", label="Sender Settings")

import database.db as db_mod
db = SessionLocal()
user = db.query(User).filter_by(username=username).first()
if not user:
    st.error("❌ User not found in database.")
    st.stop()

admin = is_admin_user(username)

# -------------------- Admin Dashboard --------------------
if admin:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛠️ Admin Dashboard")
    st.title("🛠️ Admin Dashboard")
    users = db.execute(text("SELECT username, name, email, is_admin FROM users")).fetchall()
    if users:
        df_users = pd.DataFrame(users, columns=["username", "name", "email", "is_admin"])
        st.subheader("👤 Registered Users")
        st.dataframe(df_users, use_container_width=True)

        st.subheader("📂 User Campaign Activity")
        for user_row in df_users["username"]:
            u = db.query(User).filter_by(username=user_row).first()
            if u:
                campaign_count = db.query(Campaign).filter_by(user_id=u.id).count()
                total_emails = db.query(Lead).join(Campaign).filter(Campaign.user_id == u.id).count()
                display_name = u.name if u.name else u.username
                st.markdown(f"**📂 {display_name}** — {total_emails} emails sent across {campaign_count} campaigns")

        # --- Admin: Delete User Functionality ---
        st.subheader("🗑️ Delete a User")
        user_to_delete = st.selectbox("Select a user to delete", df_users["username"].tolist(), key="delete_user_select")
        if st.button("Delete Selected User", key="delete_user_btn"):
            with st.spinner(f"Deleting user '{user_to_delete}' and all related data..."):
                del_user = db.query(User).filter_by(username=user_to_delete).first()
                if del_user:
                    # Delete all campaigns, leads, sender config, and email content for this user
                    campaigns = db.query(Campaign).filter_by(user_id=del_user.id).all()
                    for campaign in campaigns:
                        leads = db.query(Lead).filter_by(campaign_id=campaign.id).all()
                        for lead in leads:
                            db.query(EmailContent).filter_by(lead_id=lead.id).delete()
                        db.query(Lead).filter_by(campaign_id=campaign.id).delete()
                        db.query(EmailContent).filter_by(campaign_id=campaign.id).delete()
                        db.query(Campaign).filter_by(id=campaign.id).delete()
                    db.query(SenderConfig).filter_by(user_id=del_user.id).delete()
                    db.delete(del_user)
                    db.commit()
                    st.success(f"✅ User '{user_to_delete}' and all related data deleted!")
                    st.rerun()
                else:
                    st.error(f"❌ User '{user_to_delete}' not found.")
    else:
        st.warning("No users registered yet.")
    # Removed st.stop() so admin can see campaign dashboard too

# -------------------- Campaign Actions --------------------

st.title(f"📬 AI Email Campaign Dashboard — Welcome {name}")
# Add Refresh Button
if st.button("🔄 Refresh Dashboard"):
    st.rerun()

# Sender Settings
st.subheader("📇 Your Sender Settings")
sender = db.query(SenderConfig).filter_by(user_id=user.id).first()
if sender:
    st.markdown(f"""
**Sender Name:** {sender.sender_name}  
**Company:** {sender.company_name}  
**Email:** {sender.sender_email}  
**Website:** {sender.website}  
**Phone:** {sender.phone}  
""")
    st.info("✏️ You can update these in the **Sender Settings** page.")
else:
    st.warning("⚠️ Sender settings not found. Please go to the **Sender Settings** page to configure.")

# Campaigns
campaigns = db.query(Campaign).filter_by(user_id=user.id).all()
if not campaigns:
    st.info("📂 No campaigns found. Run a campaign to get started.")
    st.stop()

campaign_names = [c.name for c in campaigns]
selected_campaign = st.sidebar.selectbox("📂 Select a Campaign", campaign_names)

campaign_obj = db.query(Campaign).filter_by(user_id=user.id, name=selected_campaign).first()
st.sidebar.markdown("### ⚙️ Campaign Actions")
if selected_campaign:
    
    if st.sidebar.button("🔍 Scrape Leads"):
        with st.spinner("Scraping leads for this campaign..."):
            subprocess.run(["python", "backend/scraper.py", username, selected_campaign])
        st.success("✅ Leads scraped and saved to database!")
    if st.sidebar.button("✉️ Generate and Send Emails"):
        with st.spinner("Generating and sending emails for this campaign..."):
            subprocess.run(["python", "backend/generate_emails.py", username, selected_campaign])
            subprocess.run(["python", "backend/send_emails.py", username, selected_campaign])
        st.success("✅ Emails generated and sent!")
    # Full campaign, re-analyze, and tracker server buttons remain unchanged
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


if campaign_obj:
    st.markdown(f"**🛠 Service**: {campaign_obj.service} &nbsp;&nbsp; | &nbsp;&nbsp; **🗓 Date**: {campaign_obj.date_created.strftime('%Y-%m-%d')}")

    # Delete Campaign Button
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Delete This Campaign"):
        with st.spinner("Deleting campaign and all related data..."):
            leads = db.query(Lead).filter_by(campaign_id=campaign_obj.id).all()
            for lead in leads:
                db.query(EmailContent).filter_by(lead_id=lead.id).delete()
            db.query(Lead).filter_by(campaign_id=campaign_obj.id).delete()
            db.query(Campaign).filter_by(id=campaign_obj.id).delete()
            db.commit()
        st.success(f"✅ Campaign '{selected_campaign}' deleted!")
        st.rerun()

    # Show dashboard sections based on available data
    leads_exist = db.query(Lead).filter_by(campaign_id=campaign_obj.id).count() > 0
    emails_exist = db.query(EmailContent).filter_by(campaign_id=campaign_obj.id).count() > 0
    sent_exist = db.query(Lead).filter_by(campaign_id=campaign_obj.id, delivery_status="Sent").count() > 0

    dashboard_mode = st.sidebar.radio("Show Data For", ["Leads", "Generated Emails", "Sent Emails", "All"], index=3)

    # Query results based on mode (always fetch fresh from DB)
    data = []
    if dashboard_mode == "Leads":
        results = db.query(Lead).filter_by(campaign_id=campaign_obj.id).all()
        for lead in results:
            data.append({
                "name": lead.name,
                "email": lead.email,
                "profile_link": lead.profile_link,
                "state": lead.state,
                "profile_description": lead.profile_description,
                "delivery_status": lead.delivery_status,
                "reply_text": lead.reply_text,
                "reply_sentiment": lead.reply_sentiment,
                "opened": "Yes" if lead.opened else "No",
                "campaign_id": lead.campaign_id,
                "platform_source": lead.platform_source,
                "industry": lead.industry,
                "email_subject": lead.email_subject,
            })
    elif dashboard_mode == "Generated Emails":
        results = db.query(Lead, EmailContent).outerjoin(EmailContent, EmailContent.lead_id == Lead.id).filter(Lead.campaign_id == campaign_obj.id).all()
        for lead, email in results:
            data.append({
                "name": lead.name,
                "email": lead.email,
                "profile_link": lead.profile_link,
                "state": lead.state,
                "profile_description": lead.profile_description,
                "generated_email": email.body if email else None,
                "delivery_status": lead.delivery_status,
                "reply_text": lead.reply_text,
                "reply_sentiment": lead.reply_sentiment,
                "opened": "Yes" if lead.opened else "No",
                "campaign_id": lead.campaign_id,
                "platform_source": lead.platform_source,
                "industry": lead.industry,
                "email_subject": lead.email_subject or (email.subject if email else None),
            })
    elif dashboard_mode == "Sent Emails":
        results = db.query(Lead, EmailContent).join(EmailContent, EmailContent.lead_id == Lead.id).filter(Lead.campaign_id == campaign_obj.id, Lead.delivery_status == "Sent").all()
        for lead, email in results:
            if email:
                data.append({
                    "name": lead.name,
                    "email": lead.email,
                    "profile_link": lead.profile_link,
                    "state": lead.state,
                    "profile_description": lead.profile_description,
                    "generated_email": email.body,
                    "delivery_status": lead.delivery_status,
                    "reply_text": lead.reply_text,
                    "reply_sentiment": lead.reply_sentiment,
                    "opened": "Yes" if lead.opened else "No",
                    "campaign_id": lead.campaign_id,
                    "platform_source": lead.platform_source,
                    "industry": lead.industry,
                    "email_subject": lead.email_subject or email.subject,
                })
    else:
        results = db.query(Lead, EmailContent).outerjoin(EmailContent, EmailContent.lead_id == Lead.id).filter(Lead.campaign_id == campaign_obj.id).all()
        for lead, email in results:
            data.append({
                "name": lead.name,
                "email": lead.email,
                "profile_link": lead.profile_link,
                "state": lead.state,
                "profile_description": lead.profile_description,
                "generated_email": email.body if email else None,
                "delivery_status": lead.delivery_status,
                "reply_text": lead.reply_text,
                "reply_sentiment": lead.reply_sentiment,
                "opened": "Yes" if lead.opened else "No",
                "campaign_id": lead.campaign_id,
                "platform_source": lead.platform_source,
                "industry": lead.industry,
                "email_subject": lead.email_subject or (email.subject if email else None),
            })
    # st.write("[DEBUG] Raw leads data from DB:", data)
    df = pd.DataFrame(data)
    # if df.empty:
        # st.info("No data available for this mode yet.")


# -------------------- Campaign Results --------------------
if campaign_obj:

    # Always show available data for each mode, even if some steps are incomplete
    if df.empty:
        st.info("No data available for this mode yet.")
        # Don't stop, allow dashboard to show summary and export buttons (empty)

    df = df.drop_duplicates(subset=["email"])  # Remove duplicate leads by email

    st.subheader("📊 Campaign Summary")
    total_leads = len(df)
    total_sent = df["delivery_status"].eq("Sent").sum() if (not df.empty and "delivery_status" in df.columns) else 0
    total_opened = df["opened"].eq("Yes").sum() if (not df.empty and "opened" in df.columns) else 0
    replies = df["reply_text"].notna().sum() if (not df.empty and "reply_text" in df.columns) else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Leads", total_leads)
    col2.metric("Emails Sent", total_sent)
    col3.metric("Emails Opened", total_opened)
    col4.metric("Replies", replies)

    # Filters
    st.subheader("📊 Campaign Results")
    col1, col2 = st.columns(2)
    with col1:
        sentiment_filter = st.selectbox("Filter by Reply Sentiment", ["All", "Positive", "Neutral", "Negative"], key="sentiment_filter_main")
    with col2:
        opened_filter = st.selectbox("Filter by Opened Status", ["All", "Yes", "No"], key="opened_filter_main")

    filtered_df = df.copy()
    if sentiment_filter != "All":
        filtered_df = filtered_df[filtered_df["reply_sentiment"] == sentiment_filter]
    if opened_filter != "All":
        filtered_df = filtered_df[filtered_df["opened"] == opened_filter]

    st.dataframe(filtered_df, use_container_width=True)

    # Export Buttons
    st.download_button("📅 Download CSV", data=filtered_df.to_csv(index=False), file_name=f"{selected_campaign}.csv", mime="text/csv", key=f"download_csv_{dashboard_mode}")

    with BytesIO() as towrite:
        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
            filtered_df.to_excel(writer, index=False, sheet_name="Report")
        towrite.seek(0)
        st.download_button("📊 Export as Excel", data=towrite.read(), file_name=f"{selected_campaign}.xlsx", key=f"download_excel_{dashboard_mode}")

    # PDF Export
    if st.button("📄 Export to PDF (Stable)", key=f"export_pdf_{dashboard_mode}"):
        try:
            buffer = BytesIO()
            selected_columns = ["name", "email", "platform_source", "state", "industry", "email_subject", "reply_sentiment", "opened"]
            data = filtered_df[selected_columns].fillna("").values.tolist()
            data.insert(0, selected_columns)

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
    if "reply_sentiment" in df.columns and not df["reply_sentiment"].isnull().all():
        st.subheader("📈 Sentiment Distribution")
        st.bar_chart(df["reply_sentiment"].value_counts())

    if "opened" in df.columns and not df["opened"].isnull().all():
        st.subheader("📈 Open Rate")
        st.bar_chart(df["opened"].value_counts())

    if "reply_text" in df.columns:
        st.subheader("📬 Live Reply Viewer")
        replies = df[df["reply_text"].notna()][["email", "reply_sentiment"]]
        if not replies.empty:
            selected_email = st.selectbox("Select a reply to view", replies["email"].tolist())
            reply_text = df[df["email"] == selected_email]["reply_text"].values[0]
            st.code(reply_text, language="text")
        else:
            st.info("No replies yet.")


# -------------------- Campaign Results (for All mode) --------------------


## Removed duplicate results table and export buttons

# Close DB session
db.close()
