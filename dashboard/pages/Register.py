import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from pathlib import Path
from user_auth import add_user, user_exists

st.set_page_config(page_title="📝 Register", layout="centered")
st.title("📝 Create Your Account")

# Navigation: Back to login
if st.button("🔙 Back to Login"):
    # Only works when app is launched from Home.py at root
    st.switch_page("Home.py")

with st.form("register"):
    name = st.text_input("Full Name")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")
    submit = st.form_submit_button("Register")

    import re
    def is_strong_password(pw):
        # At least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
        return (
            len(pw) >= 8 and
            re.search(r"[A-Z]", pw) and
            re.search(r"[a-z]", pw) and
            re.search(r"[0-9]", pw) and
            re.search(r"[^A-Za-z0-9]", pw)
        )

    def is_valid_email(em):
        return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", em)

    if submit:
        if not name or not username or not email or not password:
            st.warning("⚠️ Please fill out all fields.")
        elif not is_valid_email(email):
            st.error("❌ Please enter a valid email address.")
        elif user_exists(username):
            st.error("❌ Username already exists.")
        elif password != confirm:
            st.error("❌ Passwords do not match.")
        elif not is_strong_password(password):
            st.warning("🔐 Password must be at least 8 characters and include uppercase, lowercase, number, and special character.")
        else:
            add_user(name, username, password, email)
            st.success("✅ Registered successfully! You can now log in.")
            st.balloons()
