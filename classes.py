import yfinance as yf
import numpy as np
import bcrypt
import re
import pandas as pd
import streamlit as st
import sqlite3
import plotly.graph_objs as go
import smtplib
import os

from datetime import datetime, timedelta
from currency_converter import CurrencyConverter
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
app_password = os.getenv('APP_PASSWORD')

# Set up SQLite database
class Setup:
    def create_tables():
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                username TEXT PRIMARY KEY UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notifications_enabled INTEGER DEFAULT 0,
                price_drop_threshold DECIMAL(10, 2),
                price_rise_threshold DECIMAL(10, 2)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticker (
                ticker TEXT PRIMARY KEY NOT NULL,
                company_name TEXT NOT NULL,
                currency TEXT NOT NULL,
                current_price DECIMAL(10, 2) NOT NULL,
                beta DECIMAL(10, 2),
                expected_return DECIMAL(10, 2),
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS "transaction" (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                ticker TEXT NOT NULL,
                transaction_type VARCHAR(10) NOT NULL CHECK(transaction_type IN ('long', 'short')),
                quantity_change INTEGER NOT NULL,
                currency TEXT NOT NULL,
                long_short_price DECIMAL(10, 2),
                long_short_price_hkd DECIMAL(10, 2),
                total_value_hkd DECIMAL(10, 2),
                transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES user(username) ON DELETE CASCADE,
                FOREIGN KEY (ticker) REFERENCES ticker(ticker) ON DELETE CASCADE
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            ticker TEXT NOT NULL,
            notification_type TEXT NOT NULL CHECK(notification_type IN ('price drop', 'price rise')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES user(username),
            FOREIGN KEY (ticker) REFERENCES ticker(ticker)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                username TEXT NOT NULL,
                ticker TEXT NOT NULL,
                total_quantity INTEGER NOT NULL,
                currency TEXT NOT NULL,
                current_price DECIMAL(10, 2) NOT NULL,
                current_price_hkd DECIMAL(10, 2),
                total_value_hkd DECIMAL(10, 2),
                beta DECIMAL(10, 2),
                expected_return DECIMAL(10, 2),
                weighting DECIMAL(10, 2),
                FOREIGN KEY (username) REFERENCES user(username),
                FOREIGN KEY (ticker) REFERENCES ticker(ticker),
                UNIQUE (username, ticker)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_value (
                username TEXT NOT NULL,
                portfolio_value DECIMAL(10, 2),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES user(username)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_return (
                username TEXT NOT NULL,
                portfolio_return DECIMAL(10, 2),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES user(username)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_comparison (
                username TEXT NOT NULL,
                ticker TEXT NOT NULL,
                last_long_price DECIMAL(10, 2),
                current_price DECIMAL(10, 2),
                notifications_enabled INTEGER,
                price_drop_threshold DECIMAL(10, 2),
                price_rise_threshold DECIMAL(10, 2),
                price_drop_threshold_value DECIMAL(10, 2),
                price_rise_threshold_value DECIMAL(10, 2),
                PRIMARY KEY (username, ticker),
                FOREIGN KEY (username) REFERENCES user(username),
                FOREIGN KEY (ticker) REFERENCES ticker(ticker)
            )
            ''')
            conn.commit()
        except Exception as e:
            st.error(f"Error creating tables: {e}")
        finally:
            conn.close()

# Calculation
class Calculation:
    def convert_to_hkd(amount, currency):
        if amount is None or currency == 'HKD':
            return amount
        
        c = CurrencyConverter()
        try:
            return c.convert(amount, currency, 'HKD')
        except Exception as e:
            st.error(f"Error converting {amount} {currency} to HKD: {e}")
            return None

    def expected_return(ticker, risk_free_rate, market_ticker='ACWI'):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        market_data = yf.download(market_ticker, start=start_date, end=end_date, progress=False)

        if market_data.empty:
            raise ValueError(f"No data found for market ticker: {market_ticker}")

        market_returns = market_data['Adj Close'].pct_change().dropna()

        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if stock_data.empty:
            raise ValueError(f"No data found for stock: {ticker}")

        stock_returns = stock_data['Adj Close'].pct_change().dropna()

        combined_returns = pd.concat([stock_returns, market_returns], axis=1).dropna()
        stock_returns_aligned = combined_returns.iloc[:, 0]
        market_returns_aligned = combined_returns.iloc[:, 1]

        covariance = np.cov(stock_returns_aligned, market_returns_aligned)[0][1]
        market_variance = np.var(market_returns_aligned)
        beta = covariance / market_variance if market_variance != 0 else np.nan

        expected_return = (risk_free_rate + beta * (market_returns.mean() - risk_free_rate)) * 100
        
        return expected_return, beta

    def portfolio_value(username):
        conn = sqlite3.connect('portfolio.db')
        try:
            cursor = conn.cursor()
            query = '''
                SELECT portfolio_value, updated_at
                FROM portfolio_value
                WHERE username = ?
                ORDER BY updated_at DESC
                LIMIT 1
            '''
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if result:
                portfolio_value, updated_at = result
                st.success(f"Current portfolio value (HKD): {portfolio_value:,.2f}")
                return portfolio_value, updated_at
            else:
                return None, None

        except Exception as e:
            st.error(f"An error occurred while fetching current portfolio value: {e}")
            return None, None
        finally:
            conn.close()

    def portfolio_beta(username):
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT username, SUM(beta * weighting /100) AS portfolio_beta
                FROM portfolio
                WHERE username = ?
                GROUP BY username
            ''', (username,))
            
            portfolio_beta = cursor.fetchone()
            
            if portfolio_beta:
                st.success(f"Portfolio beta: {portfolio_beta[1]:.2f}")
                return username, portfolio_beta
            else:
                return username, None
        
        except Exception as e:
            st.error(f"An error occurred: {e}")
        
        finally:
            conn.close()
        
    def expected_portfolio_return(username, market_ticker='ACWI'):
        risk_free_ticker = '^TNX'
        data = yf.download(risk_free_ticker, period='1d', interval='1m', progress=False)
        
        if data.empty:
            raise ValueError("Could not retrieve data for the 10-Year U.S. Treasury Yield.")
        
        risk_free_rate = data['Close'].iloc[-1] / 100

        with sqlite3.connect('portfolio.db') as conn:
            query = """
            SELECT ticker, weighting 
            FROM portfolio 
            WHERE username = ?
            """
            df_portfolio = pd.read_sql_query(query, conn, params=(username,))

            if not df_portfolio.empty:
                expected_returns = []
                betas = []

                for index, row in df_portfolio.iterrows():
                    ticker = row['ticker']
                    weight = row['weighting']

                    try:
                        exp_return, beta = Calculation.expected_return(ticker, risk_free_rate, market_ticker)
                        expected_returns.append(exp_return/100 * weight)
                        betas.append(beta)
                    except ValueError as e:
                        print(e)

                total_expected_return = sum(expected_returns)
                st.success(f"Expected annual portfolio return: {total_expected_return:.2f} %")
                return username, total_expected_return
                
            else:
                st.write("")
                return username, None

# Input validation functions
class Validation:
    def email(email):
        regex = r'^[a-z0-9]+(\.[a-z0-9]+)*[@]\w+[.]\w+$'
        return bool(re.match(regex, email))

    def username(username):
        return len(username) >= 1

    def password(password):
        return len(password) >= 1

# Insert data into database
class Database:
    def ticker(data):
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        
        try:
            # Fetch the current 10-Year U.S. Treasury Yield
            risk_free_ticker = '^TNX'
            rf_data = yf.download(risk_free_ticker, period='1d', interval='1m', progress=False)

            if rf_data.empty:
                raise ValueError("Could not retrieve data for the 10-Year U.S. Treasury Yield.")
            
            risk_free_rate = rf_data['Close'].iloc[-1] / 100  # Convert to decimal

            # Now call expected_return with the risk_free_rate
            expected_return, beta = Calculation.expected_return(data.info.get('symbol'), risk_free_rate)

            expected_return = round(expected_return, 2) if expected_return is not None else None

            cursor.execute('''
                INSERT OR REPLACE INTO ticker (ticker, company_name, currency, current_price, beta, expected_return, last_updated)
                VALUES (:ticker, :company_name, :currency, :current_price, :beta, :expected_return, :last_updated)
            ''', {
                'ticker': data.info.get('symbol'),
                'company_name': data.info.get('longName'),
                'currency': data.info.get('currency'),
                'current_price': data.info.get('currentPrice', 0),
                'beta': beta, 
                'expected_return': expected_return,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            conn.commit()
        except Exception as e:
            st.error(f"Error inserting/updating ticker: {e}")
        finally:
            conn.close()

    def transaction(username, data, quantity, transaction_type):
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        try:
            long_short_price_hkd = Calculation.convert_to_hkd(data.info.get('currentPrice', 0), data.info.get('currency'))
            total_value_hkd = quantity * long_short_price_hkd if long_short_price_hkd is not None else None
            
            long_short_price_hkd = round(long_short_price_hkd, 2) if long_short_price_hkd is not None else None
            total_value_hkd = round(total_value_hkd, 2) if total_value_hkd is not None else None

            cursor.execute('''
                INSERT INTO "transaction" (username, ticker, transaction_type, quantity_change, currency, long_short_price, long_short_price_hkd, total_value_hkd, transaction_date)
                VALUES (:username, :ticker, :transaction_type, :quantity_change, :currency, :long_short_price, :long_short_price_hkd, :total_value_hkd, :transaction_date)
            ''', {
                'username': username,
                'ticker': data.info.get('symbol'),
                'transaction_type': transaction_type, 
                'quantity_change': quantity,
                'currency': data.info.get('currency'), 
                'long_short_price': round(data.info.get('currentPrice', 0), 2),
                'long_short_price_hkd': long_short_price_hkd,
                'total_value_hkd': total_value_hkd,
                'transaction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            conn.commit()
        except Exception as e:
            st.error(f"Error inserting transaction: {e}")
        finally:
            conn.close()

    def portfolio():
        with sqlite3.connect('portfolio.db') as conn:
            cursor = conn.cursor()

            cursor.execute('DELETE FROM portfolio')

            cursor.execute('''
                SELECT username, ticker, SUM(quantity_change) as total_quantity
                FROM "transaction"
                GROUP BY username, ticker
            ''')
            results = cursor.fetchall()

            for username, ticker, total_quantity in results:
                if total_quantity != 0:
                    cursor.execute('''
                        SELECT currency, current_price, beta, expected_return FROM ticker WHERE ticker = ?
                    ''', (ticker,))
                    ticker_info = cursor.fetchone()

                    if ticker_info:
                        currency, current_price, beta, expected_return = ticker_info
                        current_price_hkd = Calculation.convert_to_hkd(current_price, currency)
                        
                        total_value_hkd = total_quantity * current_price_hkd if current_price_hkd is not None else None

                        current_price_hkd = round(current_price_hkd, 2) if current_price_hkd is not None else None
                        total_value_hkd = round(total_value_hkd, 2) if total_value_hkd is not None else None

                        cursor.execute('''
                            INSERT INTO portfolio (username, ticker, total_quantity, currency, current_price, current_price_hkd, total_value_hkd, beta, expected_return)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            username,
                            ticker,
                            total_quantity,
                            currency,
                            round(current_price, 2),
                            current_price_hkd,
                            total_value_hkd,
                            beta,
                            expected_return,
                        ))

            conn.commit()
      
    def portfolio_value():
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT username, SUM(total_value_hkd) as portfolio_value
                FROM portfolio
                GROUP BY username
            ''')
            results = cursor.fetchall()

            for username, portfolio_value in results:
                cursor.execute('''
                            INSERT INTO portfolio_value (username, portfolio_value, updated_at)
                            VALUES (?, ?, ?)
                        ''', (
                            username,
                            portfolio_value,
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        ))  

            conn.commit()
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            conn.close()      
    
    def portfolio_return():
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT username, SUM(expected_return * weighting) as portfolio_return
                FROM portfolio
                GROUP BY username
            ''')
            results = cursor.fetchall()

            for username, portfolio_return in results:
                cursor.execute('''
                            INSERT INTO portfolio_return (username, portfolio_return, updated_at)
                            VALUES (?, ?, ?)
                        ''', (
                            username,
                            portfolio_return,
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        ))  

            conn.commit()
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            conn.close()   
    
    def weighting():
        try:
            with sqlite3.connect('portfolio.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT username, total_value_hkd
                    FROM portfolio
                    WHERE total_value_hkd IS NOT NULL AND total_value_hkd > 0
                ''')
                rows = cursor.fetchall()

                cursor.execute('SELECT SUM(total_value_hkd) FROM portfolio WHERE total_value_hkd IS NOT NULL AND total_value_hkd > 0')
                grand_total = cursor.fetchone()[0]

                if grand_total is not None and grand_total > 0:
                    for username, total_value in rows:
                        weighting = round((total_value / grand_total) * 100, 2)

                        cursor.execute('''
                            UPDATE portfolio
                            SET weighting = ?
                            WHERE username = ? AND total_value_hkd = ?
                        ''', (weighting, username, total_value))

                    conn.commit()
                else:
                    print("Total grand value is zero or null, no updates performed.")
                    
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def user_preferences(username, notifications_enabled, price_drop_threshold, price_rise_threshold):
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
            UPDATE user
            SET notifications_enabled = ?,
                price_drop_threshold = ?,
                price_rise_threshold = ?
            WHERE username = ?
            ''', (int(notifications_enabled), price_drop_threshold, price_rise_threshold, username))
            conn.commit()
            st.success("Preferences saved successfully!")
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            conn.close()

    def price_comparison():
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        
        query = '''
        SELECT 
            u.username, 
            t.ticker, 
            t.long_short_price, 
            ti.current_price, 
            u.notifications_enabled, 
            u.price_drop_threshold, 
            u.price_rise_threshold
        FROM (
            SELECT 
                username, 
                ticker, 
                long_short_price, 
                ROW_NUMBER() OVER (PARTITION BY username, ticker ORDER BY transaction_date DESC) AS rn
            FROM 
                "transaction"
            WHERE 
                transaction_type = 'long'
        ) AS t
        INNER JOIN 
            user AS u ON t.username = u.username
        INNER JOIN 
            portfolio AS p ON t.ticker = p.ticker
        INNER JOIN 
            ticker AS ti ON t.ticker = ti.ticker
        WHERE 
            t.rn = 1;
        '''
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        insert_query = '''
        INSERT INTO price_comparison (username, ticker, last_long_price, current_price, notifications_enabled, price_drop_threshold, price_rise_threshold)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(username, ticker) DO UPDATE SET
            last_long_price = excluded.last_long_price,
            current_price = excluded.current_price,
            notifications_enabled = excluded.notifications_enabled,
            price_drop_threshold = excluded.price_drop_threshold,
            price_rise_threshold = excluded.price_rise_threshold;
        '''
        
        cursor.executemany(insert_query, results)
        conn.commit()
     
        conn.close()

    def notification(conn, username, ticker, notification_type):
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO notification (username, ticker, notification_type)
            VALUES (?, ?, ?)
        ''', (username, ticker, notification_type))
        
        conn.commit()

    def update_price():
        risk_free_ticker = '^TNX'
        data = yf.download(risk_free_ticker, period='1d', interval='1m', progress=False)
        
        if data.empty:
            raise ValueError("Could not retrieve data for the 10-Year U.S. Treasury Yield.")
        
        risk_free_rate = data['Close'].iloc[-1] / 100

        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()

        cursor.execute('SELECT ticker FROM ticker')
        existing_tickers = cursor.fetchall()

        for ticker_tuple in existing_tickers:
            ticker = ticker_tuple[0]
            data = yf.Ticker(ticker)

            expected_return_value, _ = Calculation.expected_return(ticker, risk_free_rate, market_ticker='ACWI')

            current_price = round(data.info.get('currentPrice', 0), 2)
            expected_return_value = round(expected_return_value, 2) if expected_return_value is not None else None

            cursor.execute('''
                UPDATE ticker 
                SET current_price = ?, expected_return = ?, last_updated = ?
                WHERE ticker = ?
            ''', (
                current_price,
                expected_return_value,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ticker
            ))

        conn.commit()
        conn.close()

# Main operations
class Operation:
    def register_user(username, email, password):
        if not (Validation.username(username) and Validation.email(email) and Validation.password(password)):
            st.error("Please ensure all fields are correctly filled.")
            return False
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM user WHERE username = ? OR email = ?', 
                           (username, email))
            if cursor.fetchone():
                st.error("Username or email already exists.")
                return False
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO user (username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                username,
                email,
                password_hash,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            conn.commit()
            st.success("Registered successfully! Please log in.")
            return True
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            return False
        finally:
            conn.close()

    def login(username, password):
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT username, password_hash FROM user WHERE username = ?', 
                           (username,))
            user = cursor.fetchone()
            if user is None:
                st.error("User not found.")
                return False, None
            stored_username, stored_password_hash = user
            if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash):
                st.success("Logged in successfully!")
                return True, stored_username
            else:
                st.error("Incorrect password.")
                return False, None
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return False, None
        finally:
            conn.close()

    def add_transaction(username, transaction_type, ticker, quantity):
        if not ticker or not quantity.isdigit() or int(quantity) <= 0:
            st.warning("Please enter a valid ticker and quantity greater than 0.")
            return

        quantity = int(quantity)
        target_ticker = [(ticker.strip().upper(), quantity)]

        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()

        for ticker, quantity in target_ticker:
            cursor.execute('''SELECT SUM(quantity_change) FROM "transaction" WHERE username=? AND ticker=? GROUP BY ticker''', 
                        (username, ticker))
            existing_quantity = cursor.fetchone()
            existing_quantity = existing_quantity[0] if existing_quantity else 0

            if transaction_type.lower() == "short" and quantity > existing_quantity:
                st.error(f"Cannot short {quantity} of {ticker}. Existing quantity is only {existing_quantity}.")
                continue

            if transaction_type.lower() == "short":
                quantity = -quantity

            data = yf.Ticker(ticker)
            if 'symbol' in data.info and 'currentPrice' in data.info:
                Database.transaction(username, data, quantity, transaction_type.lower())
                Database.ticker(data)
                Database.portfolio()
                Database.weighting()
                Database.portfolio_value()
                Database.portfolio_return()
                st.success(f"{transaction_type.capitalize()} {ticker} successfully with quantity {abs(quantity)}.")
            else:
                st.error(f"No data found for {ticker}.")
    
    def view_portfolio_details(username):
        with sqlite3.connect('portfolio.db') as conn:
            query = """
            SELECT ticker, total_quantity, currency, current_price, current_price_hkd, total_value_hkd
            FROM portfolio
            WHERE username = ?
            """
            df_portfolio = pd.read_sql_query(query, conn, params=(username,))

            if not df_portfolio.empty:
                df_portfolio.columns = ['Ticker', 'Quantity', 'Currency', 'Current Price', 'Current Price (HKD)', 'Total Value (HKD)']
                df_portfolio.index = df_portfolio.index + 1 
                st.dataframe(df_portfolio)
            else:
                st.write("No tickers in your portfolio.")

    def view_portfolio_returns(username):
        with sqlite3.connect('portfolio.db') as conn:
            query = """
            SELECT ticker, beta, expected_return, weighting 
            FROM portfolio 
            WHERE username = ?
            """
            df_returns = pd.read_sql_query(query, conn, params=(username,))

            if not df_returns.empty:
                df_returns.columns = ['Ticker', 'Beta', 'Expected Annual Return (%)', 'Weighting (%)']
                df_returns.index = df_returns.index + 1
                st.dataframe(df_returns)
            else:
                st.write("No expected return data available.")

    def portfolio_value_graph(username):
        conn = sqlite3.connect('portfolio.db')
        
        try:
            query = '''
                SELECT updated_at, portfolio_value
                FROM portfolio_value
                WHERE username = ?
                ORDER BY updated_at
            '''
            df = pd.read_sql_query(query, conn, params=(username,))

            if df.empty:
                return

            df['updated_at'] = pd.to_datetime(df['updated_at'])
            df.set_index('updated_at', inplace=True)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['portfolio_value'],
                mode='lines+markers',
                name='Portfolio Value',
                line=dict(color='royalblue', width=2),
                marker=dict(size=5)
            ))

            fig.update_layout(
                title={
                    'text': 'Portfolio Value Over Time',
                    'font': {'size': 18}, 
                    'x': 0.5, 
                    'xanchor': 'center'
                },
                xaxis_title='Date',
                yaxis_title='Portfolio Value (HKD)',
                template='plotly_white',
                xaxis=dict(showgrid=True),
                yaxis=dict(showgrid=True),
                hovermode='x unified'
            )

            st.plotly_chart(fig)

        except Exception as e:
            st.error(f"An error occurred while fetching data: {e}")
        
        finally:
            conn.close()

    def portfolio_return_graph(username):
        conn = sqlite3.connect('portfolio.db')
        
        try:
            query = '''
                SELECT updated_at, portfolio_return
                FROM portfolio_return
                WHERE username = ?
                ORDER BY updated_at
            '''
            df = pd.read_sql_query(query, conn, params=(username,))

            if df.empty:
                return

            df['updated_at'] = pd.to_datetime(df['updated_at'])
            df.set_index('updated_at', inplace=True)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['portfolio_return'],
                mode='lines+markers',
                name='Portfolio Return',
                line=dict(color='royalblue', width=2),
                marker=dict(size=5)
            ))

            fig.update_layout(
                title={
                    'text': 'Expected Annual Portfolio Return Over Time',
                    'font': {'size': 18}, 
                    'x': 0.5, 
                    'xanchor': 'center'
                },
                xaxis_title='Date',
                yaxis_title='Expected Annual Portfolio Return (%)',
                template='plotly_white',
                xaxis=dict(showgrid=True),
                yaxis=dict(showgrid=True),
                hovermode='x unified'
            )

            st.plotly_chart(fig)

        except Exception as e:
            st.error(f"An error occurred while fetching data: {e}")
        
        finally:
            conn.close()

    def view_history(username):
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT * FROM "transaction" WHERE username=?''', (username,))
            rows = cursor.fetchall()
            
            if rows:
                df = pd.DataFrame(rows, columns=[col[0] for col in cursor.description])
                df_filtered = df[['ticker', 'transaction_type', 'quantity_change', 'long_short_price_hkd', 'total_value_hkd', 'transaction_date']]
                df_filtered.columns = ['Ticker', 'Type', 'Quantity', 'Price (HKD)', 'Total value (HKD)', 'Transaction date']
                df_filtered.index = range(1, len(df_filtered) + 1)
                
                st.dataframe(df_filtered)
            else:
                st.write("No transaction records regarding your portfolio.")
        except Exception as e:
            st.error(f"Error fetching history: {e}")
        finally:
            conn.close()

    def candlestick(ticker, start_date, end_date):
        data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
    
        if data.empty:
            st.error("No data found for the specified ticker and date range.")
            return None
        
        ticker_info = yf.Ticker(ticker)
        currency = ticker_info.info.get('currency', 'USD')
        company_name = ticker_info.info.get('shortName')
        
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                                            open=data['Open'],
                                            high=data['High'],
                                            low=data['Low'],
                                            close=data['Close'])])
        fig.update_layout(
            title={
                'text': f'{ticker} ({company_name})',
                'font': {'size': 24}, 
                'x': 0.5, 
                'xanchor': 'center'
                },
                xaxis_title='Date',
                yaxis_title=f'Price ({currency})',
                xaxis_rangeslider_visible=False)
        
        return fig
    
    def company_information(ticker, choice, period):
        ticker_data = yf.Ticker(ticker)
        company_name = ticker_data.info.get('shortName')

        if choice == "Income Statement":
            if period == "Quarterly":
                st.subheader(f"**Quarterly Income Statement** for {ticker} ({company_name})")
                display_financials = ticker_data.quarterly_financials
            elif period == "Yearly":
                st.subheader(f"**Annual Income Statement** for {ticker} ({company_name})")
                display_financials = ticker_data.financials
            
            if display_financials.empty:
                st.write("No data available at the moment")
            else:
                st.write(display_financials)

        if choice == "Balance Sheet":
            if period == "Quarterly":
                st.subheader(f"**Quarterly Balance Sheet** for {ticker} ({company_name})")
                display_balancesheet = ticker_data.quarterly_balance_sheet
            elif period == "Yearly":
                st.subheader(f"**Annual Balance Sheet** for {ticker} ({company_name})")
                display_balancesheet = ticker_data.balance_sheet
            
            if display_balancesheet.empty:
                st.write("No data available at the moment")
            else:
                st.write(display_balancesheet)

        if choice == "Cashflow":
            if period == "Quarterly":
                st.subheader(f"**Quarterly Cashflow** for {ticker} ({company_name})")
                display_cashflow = ticker_data.quarterly_cashflow
            elif period == "Yearly":
                st.subheader(f"**Annual Cashflow** for {ticker} ({company_name})")
                display_cashflow = ticker_data.cashflow
            
            if display_cashflow.empty:
                st.write("No data available at the moment")
            else:
                st.write(display_cashflow)

    def fetch_user_preferences(username):
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT notifications_enabled, price_drop_threshold, price_rise_threshold 
            FROM user 
            WHERE username = ?
            ''', (username,)
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                "notifications_enabled": bool(result[0]),
                "price_drop_threshold": result[1],
                "price_rise_threshold": result[2]
            }
        return None

    def send_email(conn, username, ticker, condition):
        cursor = conn.cursor()
        
        cursor.execute('SELECT email FROM user WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if result:
            user_email = result[0] 
            notification_type = "price drop" if "dropped" in condition else "price rise"
            
            try:
                message = MIMEText(f"Alert for {ticker}: The price has {condition}.")
                message["From"] = "sender.test.pms@gmail.com"
                message["To"] = user_email
                message["Subject"] = f"Price Alert Notification for {ticker}"
            
                mail_server = smtplib.SMTP("smtp.gmail.com", 587)
                mail_server.starttls()
                mail_server.login("sender.test.pms@gmail.com", app_password)
                mail_server.send_message(message)
                mail_server.quit()

                print("Email sent successfully")
                
                Database.notification(conn, username, ticker, notification_type)

            except Exception as e:
                print("Error: ", e)
        else:
            print("No email found for the given username.")
            
    def check_price():
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT username, ticker, notifications_enabled, 
                    current_price,
                    last_long_price,
                    price_drop_threshold,
                    price_rise_threshold
                FROM price_comparison
            ''')
            
            results = cursor.fetchall()
            
            for result in results:
                username, ticker, notifications_enabled, current_price, last_long_price, price_drop_threshold, price_rise_threshold = result
                
                price_drop_threshold_value = last_long_price * (1 - price_drop_threshold / 100)
                price_rise_threshold_value = last_long_price * (1 + price_rise_threshold / 100)
                
                cursor.execute('''
                    UPDATE price_comparison
                    SET price_drop_threshold_value = ?, 
                        price_rise_threshold_value = ?
                    WHERE username = ? AND ticker = ?
                ''', (price_drop_threshold_value, price_rise_threshold_value, username, ticker))
                
                if notifications_enabled == 1:
                    if current_price < price_drop_threshold_value:
                        Operation.send_email(conn, username, ticker, "dropped below the threshold")
                        
                    elif current_price > price_rise_threshold_value:
                        Operation.send_email(conn, username, ticker, "rose above the threshold")
                        
            conn.commit()   
    
        except Exception as e:
            print("An error occurred:", e)
        
        finally:
            conn.close()