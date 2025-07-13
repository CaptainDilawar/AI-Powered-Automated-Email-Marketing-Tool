import pandas as pd
import streamlit_authenticator as stauth
from pathlib import Path

USER_DB = Path("users.csv")

def load_users():
    if not USER_DB.exists():
        return [], [], [], []
    df = pd.read_csv(USER_DB)
    usernames = df['username'].tolist()
    names = df['name'].tolist()
    passwords = df['password'].tolist()
    is_admin = df['is_admin'].tolist()
    return usernames, names, passwords, is_admin

def add_user(name, username, password, email, is_admin=False):
    new_user = {
        "name": name,
        "username": username,
        "password": stauth.Hasher([password]).generate()[0],
        "email": email,
        "is_admin": int(is_admin)
    }

    df = pd.DataFrame([new_user])
    file_exists = USER_DB.exists()

    # Append properly with correct line termination
    df.to_csv(USER_DB, mode='a', index=False, header=not file_exists, encoding='utf-8', lineterminator='\n')

def user_exists(username):
    if not USER_DB.exists():
        return False
    return username in pd.read_csv(USER_DB)['username'].values

def is_admin_user(username):
    if not USER_DB.exists():
        return False
    df = pd.read_csv(USER_DB)
    match = df[df['username'] == username]
    if not match.empty:
        value = str(match['is_admin'].values[0]).strip()
        return value in ("1", "True", "true")
    return False

def get_authenticator():
    usernames, names, passwords, _ = load_users()
    if not usernames or not names or not passwords:
        raise ValueError("User database is empty or malformed. Please register a user.")
    return stauth.Authenticate(
        names,
        usernames,
        passwords,
        "email_app",
        "abcdef",
        cookie_expiry_days=3
    )
