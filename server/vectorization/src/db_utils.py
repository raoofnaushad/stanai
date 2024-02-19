import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv() # Load the environment variables from the .env file

def get_db_connection():
    '''
    This function is used to connect to the PostGresDB
    Returns:
        connection: Returns the connection object
    '''
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        port=os.getenv('POSTGRES_PORT')
    )
    return conn


def insert_file_download_details(file_type, file_name, parent_name, created_time, downloaded_time, last_modified, file_hash):
    sql = """
    INSERT INTO file_downloads (file_type, file_name, parent_name, created_time, downloaded_time, last_modified, file_hash)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, (file_type, file_name, parent_name, created_time, downloaded_time, last_modified, file_hash))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Failed to insert file download details: {e}")
    finally:
        if conn is not None:
            conn.close()



def get_file_details(file_name):
    sql = """
    SELECT downloaded_time, file_hash FROM file_downloads
    WHERE file_name = %s
    ORDER BY downloaded_time DESC;
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, (file_name,))
        results = cur.fetchall()
        cur.close()

        # If no records found, return None for last_downloaded_time and an empty list for file_hashes
        if not results:
            return None, []

        # The latest last_downloaded_time is the first element in the results due to ORDER BY DESC
        latest_last_downloaded_time = results[0][0]

        # Collect all distinct file_hash values
        file_hashes = list(set([file_hash for _, file_hash in results]))

        return latest_last_downloaded_time, file_hashes

    except Exception as e:
        print(f"Failed to get file details: {e}")
        return None, []  # Return None and empty list in case of an error
    finally:
        if conn:
            conn.close()






## --------------------------------------------- File Creation -----------------------------------------------------------


def create_file_download_details_table():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if the table exists
        cur.execute(sql.SQL("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = %s);"), ['file_downloads'])
        exists = cur.fetchone()[0]

        if not exists:
            cur.execute("""
                CREATE TABLE file_downloads (
                    id SERIAL PRIMARY KEY,
                    file_type VARCHAR(10),
                    file_name VARCHAR(255),
                    parent_name VARCHAR(255),
                    created_time TIMESTAMP WITHOUT TIME ZONE,
                    downloaded_time TIMESTAMP WITHOUT TIME ZONE,
                    last_modified TIMESTAMP WITHOUT TIME ZONE,
                    file_hash VARCHAR(64)
                );
            """)

            conn.commit()
            print("Table 'file_downloads' created successfully.")
        else:
            print("Table 'file_downloads' already exists.")

    except Exception as e:
        print(f"An error occurred in create_file_download_details_table: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


create_file_download_details_table()