import schedule
import time
from classes import Database, Operation

def job():
    Database.update_price()
    Database.portfolio()
    Database.weighting()
    Database.portfolio_value()
    Database.portfolio_return()
    Database.price_comparison()
    Operation.check_price()
    print("Successfully fetched and updated portfolio data.")

def fetch_schedule():
    print("\nTo track your portfolio:")
    interval = input("Enter the interval in minutes (default is 1): ")

    if interval.strip() == "":
        interval = 1.0
    else:
        try:
            interval = float(interval)
            if interval <= 0:
                raise ValueError("Interval must be greater than 0.")
        except ValueError:
            print("Invalid input. Using default interval of 1 minute.")
            interval = 1.0

    schedule.every(interval).minutes.do(job)

    print(f"Scheduler started. Fetching ticker data every {interval} minute(s).")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Scheduler stopped.")

if __name__ == "__main__":
    fetch_schedule()