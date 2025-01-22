from navigation import make_sidebar
import streamlit as st
from classes import Calculation, Operation

st.set_page_config(
    page_title="Portfolio Tracker App",
    page_icon="📈",
)

make_sidebar()

if 'refresh' not in st.session_state:
    st.session_state.refresh = 0

def refresh_state():
    st.session_state.refresh += 1

col1, col2 = st.columns([3, 1])

with col1:
    st.title("📄 Portfolio Overview")

with col2:
    st.write("")
    st.button('Refresh', on_click=refresh_state)

tab1, tab2 = st.tabs(["Details", "Expected Returns"])

with tab1:
    st.subheader("Details")
    Operation.view_portfolio_details(st.session_state.login_username)
    Calculation.portfolio_value(st.session_state.login_username)
    Operation.portfolio_value_graph(st.session_state.login_username)

with tab2:
    st.subheader("Expected Returns")
    Operation.view_portfolio_returns(st.session_state.login_username)
    Calculation.expected_portfolio_return(st.session_state.login_username)
    Calculation.portfolio_beta(st.session_state.login_username)
    Operation.portfolio_return_graph(st.session_state.login_username)