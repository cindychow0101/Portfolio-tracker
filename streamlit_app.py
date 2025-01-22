import streamlit as st
from time import sleep
from navigation import make_sidebar
from classes import Setup, Operation

st.set_page_config(
    page_title="Portfolio Tracker App",
    page_icon="📈",
)

Setup.create_tables()

make_sidebar()

st.title("Welcome to your portfolio tracker!")

choice = st.selectbox("Choose an option", ("Register", "Log in"), key="main_choice")

if choice == "Register":
    st.subheader("Register")
    username = st.text_input("Enter a unique username")
    email = st.text_input("Enter an email")
    password = st.text_input("Enter a password", type="password")

    if st.button("Confirm"):
        Operation.register_user(username, email, password)

elif choice == "Log in":
    st.subheader("Log into Your Account")
    username = st.text_input("Username (For demo: `test`)")
    password = st.text_input("Password (For demo: `test`)", type="password")

    if st.button("Log in", type="primary"):
        success, user_info = Operation.login(username, password)
        if success:
            st.session_state.login_username = username
            st.session_state.logged_in = True
            sleep(0.5)
            st.switch_page("pages/user_guide.py")
        else:
            st.error("Incorrect username or password")

# streamlit run streamlit_app.py