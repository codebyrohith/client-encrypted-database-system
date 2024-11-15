import pyodbc

# Database connection function
def get_db_connection():
    server = 'ROHITH\SQLEXPRESS'  
    database = 'ClientEncryptedDB' 

    # Connection string for Windows Authentication
    connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"Trusted_Connection=yes"
)
    try:
        # Establish the connection
        conn = pyodbc.connect(connection_string)
        print("Database connection successful")
        return conn
    
    except pyodbc.Error as e:
        print("Error in connection:", e)
        return None



