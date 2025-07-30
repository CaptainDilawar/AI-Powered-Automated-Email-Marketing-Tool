import streamlit_authenticator as stauth
from database.db import SessionLocal
from database.models import User
import bcrypt


def get_all_users():
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    return users


def get_authenticator():
    users = get_all_users()

    if not users:
        raise ValueError("User database is empty. Please register a user.")

    names = [user.name for user in users]
    usernames = [user.username for user in users]
    passwords = [user.password_hash for user in users]  # Pre-hashed passwords

    return stauth.Authenticate(
        names,
        usernames,
        passwords,
        "email_app",  # cookie name
        "abcdef",     # secret key
        cookie_expiry_days=3
    )


def user_exists(username):
    session = SessionLocal()
    user = session.query(User).filter(User.username == username).first()
    session.close()
    return bool(user)


def is_admin_user(username):
    session = SessionLocal()
    user = session.query(User).filter(User.username == username).first()
    session.close()
    return bool(user and user.is_admin)


def add_user(name, username, password, email, is_admin=False):
    if user_exists(username):
        return False

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_user = User(
        name=name,
        username=username,
        password_hash=hashed_pw,
        email=email,
        is_admin=is_admin
    )
    session = SessionLocal()
    session.add(new_user)
    session.commit()
    session.close()
    return True
