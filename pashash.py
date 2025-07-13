import streamlit_authenticator as stauth

passwords = ["Dilawar"]
hashed_passwords = stauth.Hasher(passwords).generate()
print(hashed_passwords[0])
