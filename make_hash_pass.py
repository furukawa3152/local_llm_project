import streamlit_authenticator as stauth

hashed_passwords = stauth.Hasher(['password123', 'mypassword']).hashes
print(hashed_passwords)
