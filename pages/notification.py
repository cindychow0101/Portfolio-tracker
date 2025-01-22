from navigation import make_sidebar
import streamlit as st
from classes import Database, Operation

st.set_page_config(
    page_title="Portfolio Tracker App",
    page_icon="📈",
)

make_sidebar()

st.title("🔔 Notification")

user_data = Operation.fetch_user_preferences(st.session_state.login_username)

if user_data:
    notifications_enabled = st.checkbox("Enable Email Notifications", user_data.get('notifications_enabled', False))
    
    price_drop_threshold = st.number_input(
        "Price Drop Threshold (%)", 
        min_value=0.0, 
        max_value=100.0, 
        value=float(user_data.get('price_drop_threshold', 5.0) or 5.0),
        step=0.5)
    
    price_rise_threshold = st.number_input(
        "Price Rise Threshold (%)", 
        min_value=0.0, 
        max_value=100.0, 
        value=float(user_data.get('price_rise_threshold', 5.0) or 5.0),
        step=0.5)

    if st.button("Save"):
        Database.user_preferences(st.session_state.login_username, notifications_enabled, price_drop_threshold, price_rise_threshold)
        user_data = Operation.fetch_user_preferences(st.session_state.login_username)

    st.write("")
    st.subheader("Current Settings")
    st.write("Notifications Enabled:", user_data.get('notifications_enabled', False))
    st.write("Price Drop Threshold (%):", user_data.get('price_drop_threshold', 5.0))
    st.write("Price Rise Threshold (%):", user_data.get('price_rise_threshold', 5.0))
else:
    st.error("User not found.")