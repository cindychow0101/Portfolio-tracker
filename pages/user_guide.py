from navigation import make_sidebar
import streamlit as st

# Set up the page configuration
st.set_page_config(
    page_title="Portfolio Tracker App",
    page_icon="📈",
)

make_sidebar()

# Main title of the app
st.title("📘 User Guide")

# Section for Overview
st.header("❄ Overview")
st.write("""
This powerful application is designed to help you **manage** and **analyze** your investment portfolio with ease.
""")
st.write("")

# Quick Navigation
st.write("### 📑 Quick Navigation")
st.markdown(""" ➤ [Key Features](#a135a1cd)""")
st.markdown(""" ➤ [How to Use](#274c55a8)""")
st.markdown(""" ➤ [Formulas Used](#5fb61b15)""")
st.markdown(""" ➤ [Data Source](#bcd57316)""")
st.markdown(""" ➤ [Troubleshooting Tips](#e2c8ba2)""")
st.markdown(""" ➤ [Additional Resources](#e2c8ba2)""")
st.write("")

# Section for Key Features
st.subheader("🌟 Key Features")
st.write("✧ **Portfolio Management:** Get a clear overview of your investments and track transactions effortlessly.")
st.write("✧ **Market Analysis:** Use interactive charts and access financial statements to enhance your decision-making.")
st.write("✧ **Customized Notifications:** Set up email alerts to stay updated on important changes.")
st.write("")

# Section for How to Use
st.subheader("🛠️ How to Use")

st.write("### 1. Portfolio Overview")
st.write("""
✧ Navigate to the **Portfolio Overview** section in the sidebar. 
  Here, you can view a comprehensive overview of your investments, including performance metrics.
""")

st.write("### 2. Transaction")
st.write("""
✧ Go to the **Transaction** section in the sidebar. 
  Here, you can buy or sell tickers as desired. 
  Additionally, you can review a detailed history of all your investment activities.
""")

st.write("### 3. Information Search")
st.write("""
✧ Navigate to the **Information Search** section in the sidebar to visually analyze market trends and access detailed reports.
  You can use the interactive features to zoom in and out on specific timeframes.
  Moreover, you can filter by company or period to find the information you need.
""")

st.write("### 4. Notification Preference")
st.write("""
✧ Navigate to the **Notification Preference** in the sidebar. 
  Here, you can customize your notification preferences. 
  Choose whether to enable email notifications, set price thresholds, and save your settings.
""")
st.write("")

st.subheader("📊 Formulas Used")
st.write("### 1. Expected Annual Return of a Stock")
st.latex(r'''
   \text{Expected Return} = \left( r_f + \beta \times (E(R_m) - r_f) \right) \times 100
''')
st.write("- Where:")
st.write("- **rf** = Risk-free rate")
st.markdown("- **β** = Beta of the stock")
st.write("- **E(Rm)** = Expected return of the market")

st.write("### 2. Beta Calculation")
st.latex(r'''
   \beta = \frac{\text{Covariance}(\text{Stock Returns}, \text{Market Returns})}{\text{Variance}(\text{Market Returns})}
''')
st.write("- Where:")
st.write("- Covariance measures how the stock and market returns move together.")
st.write("- Variance measures the dispersion of market returns.")

st.write("### 3. Expected Annual Portfolio Return")
st.latex(r'''
   \text{Total Expected Return} = \sum \left( \frac{E(R_i)}{100} \times w_i \right)
''')
st.write("- Where:")
st.write("- **E(Ri)** = Expected return of asset **i**")
st.write("- **wi** = Weighting of asset **i** in the portfolio")
st.write("")

# Section for Data Source
st.subheader("🗄️ Data Source")
st.write("""
The data used in this application is primarily sourced from **Yahoo Finance** through the `yfinance` library. 
This includes stock prices, historical data, and financial statements to support your investment analysis.
""")
st.write("")

# Section for Troubleshooting Tips
st.subheader("⚙️ Troubleshooting Tips")
st.write("""
- **Data Not Loading:** Ensure you have a stable internet connection.
- **Error Messages:** If you encounter an error, try refreshing the page or checking your data input.
- **Contact Support:** Reach out to support@example.com for assistance.
""")
st.write("")

# Section for Additional Resources
st.subheader("🔗 Additional Resources")
st.write("""
- [How to Start Investing in Stocks in 2024](https://www.investopedia.com/articles/basics/06/invest1000.asp)
- [Glossary of Investment Terms](https://am.jpmorgan.com/us/en/asset-management/adv/resources/glossary-of-investment-terms/)
""")