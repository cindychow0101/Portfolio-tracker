from navigation import make_sidebar
import streamlit as st
from classes import Operation
from dateutil.relativedelta import relativedelta
from datetime import datetime

st.set_page_config(
    page_title="Portfolio Tracker App",
    page_icon="📈",
)

make_sidebar()

st.subheader("Information Search")
if 'ticker' not in st.session_state:
    st.session_state.ticker = 'AAPL'
ticker = st.text_input(
    'Enter Ticker:', 
    value=st.session_state.ticker,
    label_visibility="collapsed", 
    placeholder="Enter ticker symbol"
).strip().upper()
if ticker:
    st.session_state.ticker = ticker 

tab1, tab2 = st.tabs(["Candlestick Chart", "Financial Statement"])

with tab1:
    st.header('Candlestick Chart')

    end_date = datetime.now()
    default_start_date = end_date - relativedelta(years=1)

    start_date = st.date_input('Start date:', default_start_date.date())
    end_date = st.date_input('End date:', end_date.date())

    fig = Operation.candlestick(st.session_state.ticker, start_date, end_date)

    if fig is None:
        st.error(f"No data found for ticker: {st.session_state.ticker}")
    else:
        st.plotly_chart(fig)
      
with tab2:  
    st.header("Financial Statement")

    options = [
        "Income Statement",
        "Balance Sheet",
        "Cashflow",
        ]
    choice = st.selectbox('View information:', options)
    period = st.selectbox('Select period:', ["Quarterly", "Yearly"])

    Operation.company_information(st.session_state.ticker, choice, period)