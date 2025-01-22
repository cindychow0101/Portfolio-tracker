import streamlit as st
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages

def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("Couldn't get script context")

    pages = get_pages("")

    return pages[ctx.page_script_hash]["page_name"]

def make_sidebar():
    with st.sidebar:
        if st.session_state.get("logged_in", False):
            st.title("📈 Protfolio Tracker")
            
            st.page_link("pages/user_guide.py", label="User Guide", icon="📘")
            st.page_link("pages/portfolio.py", label="Portfolio Overview", icon="📄")
            st.page_link("pages/transaction.py", label="Transaction", icon="💵") 
            st.page_link("pages/information.py", label="Information Search", icon="🔍")
            st.page_link("pages/notification.py", label="Notification Preference", icon="🔔")

            st.write("")

            if st.button("Log out"):
                logout()

        elif get_current_page_name() != "streamlit_app":
            st.switch_page("streamlit_app.py")

def logout():
    st.session_state.logged_in = False
    st.info("Logged out successfully!")
    sleep(0.5)
    st.switch_page("streamlit_app.py")