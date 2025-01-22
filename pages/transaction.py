from navigation import make_sidebar
import streamlit as st
from classes import Operation

st.set_page_config(
    page_title="Portfolio Tracker App",
    page_icon="📈",
)

make_sidebar()

st.title("💵 Transaction")

tab1, tab2 = st.tabs(["Make Transaction", "Transaction History"])

with tab1:
    st.subheader("Make Transaction")
    transaction_type = st.selectbox("Transaction Type:", ["Long", "Short"])
    ticker = st.text_input("Ticker:", placeholder="Enter ticker symbol (e.g. AAPL)").strip().upper()
    quantity = st.text_input("Quantity:", placeholder="Enter an integer").strip()

    if st.button("Execute"):
        Operation.add_transaction(st.session_state.login_username, transaction_type, ticker, quantity)

with tab2:
    st.subheader("Transaction History")
    Operation.view_history(st.session_state.login_username)