import sqlite3

def clear_tables_except_user():
    # Connect to the SQLite database
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    
    # Retrieve the list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # Loop through the tables and delete data from those not named 'user'
    for table_name in tables:
        table = table_name[0]
        if table != 'user':
            cursor.execute(f"DELETE FROM \"{table}\";")
            print(f"Cleared data from table: {table}")
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

# Usage
clear_tables_except_user()