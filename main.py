# Import packages
import yfinance as yf
import sqlite3
import schedule
import time
from datetime import datetime

# Initialise percentage loss
loss_percentage = 0.0

# Create table in sqlite
def create_table():
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ticker_info (
        ticker TEXT PRIMARY KEY NOT NULL,
        quantity INTEGER NOT NULL,
        currency TEXT NOT NULL,
        average_purchase_price FLOAT NOT NULL,
        stop_loss_price FLOAT,
        current_price FLOAT NOT NULL,
        update_time DATETIME
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transaction_info (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        transaction_type VARCHAR(10) NOT NULL,
        quantity_change INTEGER NOT NULL,
        currency TEXT NOT NULL,
        purchase_price FLOAT NOT NULL,
        update_time DATETIME,
        FOREIGN KEY (ticker) REFERENCES ticker_info(ticker)
    )
    ''') 
    conn.commit()
    conn.close()

# Import data of initial portfolio to database
def insert_transaction(data, quantity):
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO transaction_info (ticker, transaction_type, quantity_change, currency, purchase_price, update_time)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.info.get('symbol'),
        "long", 
        quantity,
        data.info.get('currency'), 
        data.info.get('currentPrice', 0),
        datetime.now()
    ))
    conn.commit()
    conn.close()
def insert_ticker_data(data, quantity):
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO ticker_info (ticker, quantity, currency, average_purchase_price, current_price, update_time)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.info.get('symbol'),
        quantity,
        data.info.get('currency'), 
        data.info.get('currentPrice', 0),
        data.info.get('currentPrice', 0),
        datetime.now()
    ))
    conn.commit()
    conn.close()
def fetch_price(ticker, quantity):
    data = yf.Ticker(ticker)
    if 'symbol' in data.info:
        insert_transaction(data, quantity)
        insert_ticker_data(data, quantity)
    else:
        print(f"No data found for {ticker}")
def initial_portfolio(input_tickers):
    global loss_percentage

    target_ticker = []
    
    ticker_list = input_tickers.split()
    for i in range(0, len(ticker_list), 2):
        ticker = ticker_list[i].strip().upper()
        quantity = int(ticker_list[i + 1]) if i + 1 < len(ticker_list) and ticker_list[i + 1].isdigit() else 0
        target_ticker.append((ticker, quantity))
    
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM ticker_info''')
    cursor.execute('''DELETE FROM transaction_info''')
    cursor.execute('''UPDATE sqlite_sequence SET seq=0 WHERE name="transaction_info" ''')
    conn.commit()
    conn.close()
    
    for ticker, quantity in target_ticker:
        if quantity > 0:
            fetch_price(ticker, quantity)
        else:
            print(f"The quantity of {ticker} should be greater than 0. Please try to add it again later.")
            view_ticker()
    
    print("\n")
    loss_percentage = input("Enter maximum percentage loss (1 to 100) of each ticker: ")
    loss_percentage = float(loss_percentage)
    calculate_stop_loss(loss_percentage)
    view_ticker()

# Update current price
def insert_update_price(data):
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE ticker_info
    SET current_price = ?, update_time = ?
    WHERE ticker = ?
    ''', (
        data.info.get('currentPrice', 0), 
        datetime.now(), 
        data.info.get('symbol')
    ))
    conn.commit()
    conn.close()
def fetch_update_price():
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT ticker FROM ticker_info''')
    portfolio_tickers = cursor.fetchall()
    conn.close()
    
    for ticker in portfolio_tickers:
        data = yf.Ticker(ticker[0])
        if 'symbol' in data.info:
            insert_update_price(data)
        else:
            print(f"No data found for {ticker[0]}")

# Update average purchase price
def average_purchase_price():
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE ticker_info
    SET average_purchase_price = (
        SELECT AVG(purchase_price) 
        FROM transaction_info
        WHERE transaction_info.ticker = ticker_info.ticker
        AND transaction_type = 'long'
    )
    ''')
    conn.commit()
    conn.close()

# Calculation (stop loss price)
def calculate_stop_loss(loss_percentage):
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE ticker_info SET stop_loss_price = average_purchase_price * ?''', ((1-loss_percentage/100),))
    conn.commit()
    conn.close()

# Stop loss warning
def stop_loss_warning():
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT ticker, current_price, stop_loss_price
    FROM ticker_info
    WHERE current_price < stop_loss_price
    ''')
    results = cursor.fetchall()
    if results:
        for ticker, current_price, stop_loss_price in results:
            print(f"Warning: For {ticker}, current price {current_price} is below stop loss price {stop_loss_price}!")
        adjustment()
    else:
        print("No tickers fall below the stop loss price.")
    conn.close()

# Update quantity of ticker
def insert_new_transaction(data, quantity, transaction_type):
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO transaction_info (ticker, transaction_type, quantity_change, currency, purchase_price, update_time)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.info.get('symbol'),
        transaction_type, 
        quantity,
        data.info.get('currency'), 
        data.info.get('currentPrice', 0),
        datetime.now()
    ))
    conn.commit()
    conn.close()
def insert_update_quantity(data):
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE ticker_info
    SET quantity = (
        SELECT SUM(quantity_change) 
        FROM transaction_info 
        WHERE ticker = ?
    )
    WHERE ticker = ?
    ''', (
        data.info.get('symbol'), 
        data.info.get('symbol')
    ))
    conn.commit()
    conn.close()
def update_quantity(ticker, transaction_type, quantity):
    data = yf.Ticker(ticker)
    if 'symbol' in data.info:
        with sqlite3.connect('ticker.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT quantity FROM ticker_info WHERE ticker=?', (ticker,))
            existing_quantity = cursor.fetchone()

            if existing_quantity is not None:
                existing_quantity = existing_quantity[0]
                
                if transaction_type == "2": 
                    if quantity < 0:
                        print(f"Short quantity cannot be negative: {quantity}")
                        return
                    if quantity > existing_quantity:
                        print(f"Cannot short {quantity} of {ticker}. Available quantity is {existing_quantity}.")
                        return

                    quantity = -quantity

                insert_new_transaction(data, quantity, "long" if transaction_type == "1" else "short")
                insert_update_quantity(data)
                
                average_purchase_price()
                print(f"Updated quantity of {ticker} successfully.")
            else:
                print(f"No data found for {ticker}.")
    else:
        print(f"No data found for {ticker}.")

# Update percentage loss
def update_loss_rate():
    global loss_percentage
    loss_percentage = input("Enter maximum percentage loss (1 to 100) of each ticker: ")
    loss_percentage = float(loss_percentage)
    calculate_stop_loss(loss_percentage)
    print("Updated maximum percentage loss successfully.")
    print(f"New maximum percentage loss: {int(loss_percentage)}%")

# Add new ticker(s)
def fetch_new_ticker(new_ticker):
    for ticker, quantity in new_ticker:
        data = yf.Ticker(ticker)
        if 'symbol' in data.info:
            insert_transaction(data, quantity)
            insert_ticker_data(data, quantity)
            print("Added ticker(s) successfully.")
        else:
            print(f"No data found for {ticker}")
def add_ticker(input_new_tickers):
    global loss_percentage
    new_ticker = []

    ticker_list = input_new_tickers.split()
    for i in range(0, len(ticker_list), 2):
        ticker = ticker_list[i].strip().upper()
        quantity = int(ticker_list[i + 1]) if i + 1 < len(ticker_list) and ticker_list[i + 1].isdigit() else 0
        new_ticker.append((ticker, quantity))

    for ticker, quantity in new_ticker:
        if quantity > 0:
            fetch_new_ticker(new_ticker)
        else:
            print(f"The quantity of {ticker} should be greater than 0. Please try to add it again later.")
            view_ticker()

    calculate_stop_loss(loss_percentage)
    average_purchase_price()

# Delete existing ticker
def delete_ticker(ticker):
    data = yf.Ticker(ticker)
    
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    
    cursor.execute('''SELECT quantity FROM ticker_info WHERE ticker=?''', (ticker,))
    quantity = cursor.fetchone()

    if quantity:
        quantity_value = int(quantity[0]) * (-1)

        cursor.execute('''
        INSERT INTO transaction_info (ticker, transaction_type, quantity_change, currency, purchase_price, update_time)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.info.get('symbol'),
            "short", 
            quantity_value,
            data.info.get('currency'), 
            data.info.get('currentPrice', 0),
            datetime.now()
        ))
        
        cursor.execute('''DELETE FROM ticker_info WHERE ticker = ?''', (ticker,))
        conn.commit()
        conn.close()
        average_purchase_price()
        print(f"Deleted (shorted) {ticker} from your portfolio successfully.")
    
    else:
        print(f"No data found for {ticker}")
        conn.close() 

# View portfolio
def view_ticker():
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ticker_info')
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("\nYour current portofolio:")
        for row in rows:
            print(f"{row[0]} ({row[1]})")
    else:
        print("No ticker found in your portfolio.")

# View transaction history
def view_transaction():
    conn = sqlite3.connect('ticker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transaction_info')
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("\nYour transaction records:")
        for row in rows:
            print(row)
    else:
        print("No transaction records found.")

# Update operation
def update_operation():
    print("\nChoose one from the following:")
    print("1. Update quantity of a ticker")
    print("2. Update maxmimum percentage loss")

    choice = input("Choose an option: ")

    if choice == '1':
        ticker = input("Enter a ticker (e.g. 0700.HK) that you want to long/short: ").strip().upper()
        transaction_type = input("Enter 1 (i.e. long) or 2 (i.e. short): ").strip()
        quantity = int(input("Enter quantity which you want to long/short: "))
        update_quantity(ticker, transaction_type, quantity)

    elif choice == '2':
        update_loss_rate()

    else:
        print("Invalid option.")

# View operation
def view_operation():
    print("\nChoose one from the following:")
    print("1. View current portfolio")
    print("2. View transaction records")

    choice = input("Choose an option: ")

    if choice == '1':
        view_ticker()

    elif choice == '2':
        view_transaction()

    else:
        print("Invalid option.")

# Menu for operations (Update, Add, Delete, View)
def operations():
    while True:
        print("\nChoose one from the following:")
        print("1. Update quantity of a ticker/ maxmimum percentage loss")
        print("2. Add new ticker(s)")
        print("3. Delete existing ticker")
        print("4. View current portfolio/ transaction records")
        print("5. Start tracking your portfolio")

        choice = input("Choose an option: ")

        if choice == '1':
            update_operation()
        elif choice == '2':
            input_new_tickers = input("Enter new ticker(s) to your portfolio (Example: 0700.HK 10 MSFT 5): ")
            add_ticker(input_new_tickers)
        elif choice == '3':
            ticker = input("Enter ticker you want to delete: ").strip().upper()
            delete_ticker(ticker)
        elif choice == '4':
            view_operation()
        elif choice == '5':
            break
        else:
            print("Invalid option.")
        
        time.sleep(5)

# Choose to make adjustment or not
def adjustment():
    print("\nDo you want to manage your current portfolio?")
    print("1. Yes")
    print("2. No")

    choice = input("Choose an option: ")

    if choice == '1':
        operations()
    elif choice == '2':
        pass
    else:
        print("Invalid option.")

# Scheduler for fetching current price
def job():
    fetch_update_price()
    stop_loss_warning()
def scheduler():
    print("\nTo track your portfolio:")
    interval = input("Enter the interval in minutes (default is 1): ")
    interval = int(interval) if interval.isdigit() else 1

    schedule.every(interval).minutes.do(job)

    print(f"Scheduler started. Fetching ticker data every {interval} minute(s).")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Scheduler stopped.")

# Get started
def get_started():
    print('\nWelcome to the personal portfolio management system!')
    print("\nHave you inserted your portfolio in this system?")
    print("1. Yes")
    print("2. No")

    choice = input("Choose an option: ")

    if choice == '1':
        view_ticker()
        adjustment()
    elif choice == '2':
        print("\nPlease initialize your portfolio.")
        input_tickers = input("Enter your portfolio (Example: 0700.HK 10 MSFT 5): ")
        initial_portfolio(input_tickers)
        adjustment()
    else:
        print("Invalid option.")

# Main menu
def main():
    create_table()
    get_started()
    scheduler()
    
if __name__ == "__main__":
    main()