import psycopg2

# Database connection parameters
db_params = {
    'host': '34.93.11.95',
    'port': '5432',
    'database': 'postgres',
    'user': 'ltai',
    'password': 'msdthala2019'
}

def get_db_connection():
    return psycopg2.connect(**db_params)

# create_table_query = """
# CREATE TABLE IF NOT EXISTS requests (
#     request_id VARCHAR(255) PRIMARY KEY,
#     role_or_gop VARCHAR(255),
#     user_email VARCHAR(255),
#     manager_email VARCHAR(255),
#     status VARCHAR(50)
# );
# """

# try:
#     # Connect to the PostgreSQL database
#     conn = get_db_connection()
#     cur = conn.cursor()
    
#     # Execute the create table query
#     cur.execute(create_table_query)
    
#     # Commit changes
#     conn.commit()
    
#     print("Table created successfully.")
    
#     # Close the cursor and connection
#     cur.close()
#     conn.close()

# except Exception as e:
#     print(f"Error: {e}")

# try:
#     conn = get_db_connection()
#     cur = conn.cursor()
    
#     # Execute the delete statement
#     cur.execute('DELETE FROM requests')
    
#     # Commit the transaction
#     conn.commit()
    
# except Exception as e:
#     print(f"An error occurred: {e}")
#     # Optionally, roll back the transaction if something went wrong
#     conn.rollback()
    
# finally:
#     # Close the cursor and connection in the finally block to ensure they are always closed
#     cur.close()
#     conn.close()