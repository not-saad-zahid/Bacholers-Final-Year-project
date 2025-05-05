import sqlite3

# Method 1: Basic connection and simple query
def read_database_basic(db_path):
    """
    Basic method to connect to an SQLite database and execute a simple query
    """
    # Establish a connection to the database
    conn = sqlite3.connect(db_path)
    
    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    try:
        # Get list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in the database:")
        for table in tables:
            print(table[0])
        
        # Example: Read all data from the first table
        if tables:
            first_table = tables[0][0]
            cursor.execute(f"SELECT * FROM {first_table}")
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            print(f"\nColumns in {first_table}:")
            print(column_names)
            
            print(f"\nData from {first_table}:")
            for row in rows:
                print(row)
    
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Always close the connection
        conn.close()

# Method 2: Pandas integration for more advanced data handling
def read_database_with_pandas(db_path):
    """
    Read SQLite database using pandas for more powerful data manipulation
    """
    import pandas as pd
    
    # Establish a connection to the database
    conn = sqlite3.connect(db_path)
    
    try:
        # Get list of tables
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
        print("Tables in the database:")
        print(tables)
        
        # If tables exist, read the first table into a DataFrame
        if not tables.empty:
            first_table = tables.iloc[0]['name']
            df = pd.read_sql_query(f"SELECT * FROM {first_table}", conn)
            print(f"\nDataFrame from {first_table}:")
            print(df)
            
            # Optional: Additional pandas operations
            print("\nDataFrame Info:")
            df.info()
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Close the connection
        conn.close()

def read_all_data_from_database(db_path):
    """
    Read all data from all tables in the SQLite database and display it.
    """
    # Establish a connection to the database
    conn = sqlite3.connect(db_path)
    
    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    try:
        # Get list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
        
        print("Tables in the database:")
        for table in tables:
            print(f"\nTable: {table[0]}")
            
            # Fetch all data from the current table
            cursor.execute(f"SELECT * FROM {table[0]}")
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            print(f"Columns: {column_names}")
            
            # Print rows
            if rows:
                print("Data:")
                for row in rows:
                    print(row)
            else:
                print("No data found in this table.")
    
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Always close the connection
        conn.close()

# Example usage
if __name__ == "__main__":
    # Replace 'your_database.db' with the path to your actual .db file
    db_path = 'timetable.db'
    
    print("Method 1: Basic SQLite Reading")
    read_database_basic(db_path)
    
    print("\n" + "="*50 + "\n")
    
    print("Method 2: Pandas SQLite Reading")
    read_database_with_pandas(db_path)
    
    print("\n" + "="*50 + "\n")
    
    print("Reading all data from the database:")
    read_all_data_from_database(db_path)
