# Portfolio management system

## Overview
This system is a personal porfolio management tool that allows users to track their ticker(i.e. stock) investments. It enables users to add transactions, update quantities of tickers, and track the current prices of tickers. 

## Features
- **Add Transactions:** Record new ticker purchases and sales.
- **Update Quantities:** Modify the quantities of tickers in your portfolio.
- **Database Storage:** Use SQLite for persistent storage of transactions and ticker information.
- **Real-Time Data:** Fetch ticker data using the `yfinance` library.

## Database Scheme
![Schema](/images/schema.png)

## Initialize a portfolio
- **Description:** Initializes the portfolio based on user input for ticker symbols and their respective quantities.
- **Parameters:**
  - `ticker`: The stock symbol of the new ticker(s) you want to add (e.g., 'GOOGL').
  - `quantity`: The number of shares of new ticker(s).
  - `loss_percentage`: The maximum percentage loss before an alert is triggered.
- **Examples:**
![Initialize](/images/initial.png)

## Functions
After initialising, there are serveral functions you can use to manage your portfolio. All changes will be shown in the SQLite database.
![Functions](/images/functions.png)

### 1. Update Quantity of a Ticker / Maximum Percentage Loss
- **Description:** This function allows you to modify the number of shares held for a specific ticker in your portfolio. Additionally, you can set a maximum percentage loss, which serves as a stop-loss trigger, helping to manage risk by alerting you when the stock price falls below a certain threshold.
- **Parameters:**
  - `ticker`: The stock symbol (e.g., 'AAPL').
  - `transaction_type`: Long or short
  - `quantity`: The number of shares to long or short.
  - `loss_percentage`: The maximum percentage loss before an alert is triggered.
- **Example:**
![Update](/images/update.png)

### 2. Add New Ticker(s)
- **Description:** This function is used to introduce new tickers into your portfolio. It fetches the latest market data for the specified ticker and initializes its records in the database, ensuring that you can start tracking it immediately.
- **Parameters:**
  - `ticker`: The stock symbol of the new ticker(s) you want to add (e.g., 'GOOGL').
  - `quantity`: The number of shares of new ticker(s).
- **Example:**
![Add](/images/add.png)

### 3. Delete Existing Ticker
- **Description:** This function removes a specified ticker from your portfolio, along with all its associated transaction records. This is useful for cleaning up your portfolio when you no longer wish to track a specific stock.
- **Parameters:**
  - `ticker`: The stock symbol of the ticker to be deleted (e.g., 'TSLA').
- **Example:**
![Delete](/images/delete.png)

### 4. View Current Portfolio / Transaction Records
- **Description:** This function retrieves and displays the current state of your portfolio, including all tickers and their respective quantities. It also provides access to transaction records, giving you insights into your buying and selling activities.
- **Example:**
![view](/images/view.png)

### 5. Start Tracking Your Portfolio
- **Description:** This function initiates the tracking process for your portfolio, enabling you to monitor real-time price changes and receive notifications when exceeding your maximum percentage loss. 
  - It is non-stop if you don't stop the system.
- **Parameters:**
  - `interval`: The frequency of updates (in minutes).
- **Example:**
![Track](/images/track.png)

### Example outcome of database:
![Ticker](/images/ticker.png)
![Transaction](/images/transaction.png)