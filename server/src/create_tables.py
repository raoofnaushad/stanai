import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

from src import config as C
from src import utils as U

load_dotenv() # Load the environment variables from the .env file
logger = U.get_logger()

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


## -------------------- Creating Tables for PostGres -------------------------------------

def create_interviewboard_table():
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()

        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Check if the table exists
        cur.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = 'interviewboard');")
        exists = cur.fetchone()[0]

        if not exists:
            # Create table if it does not exist
            cur.execute("""
                    CREATE TABLE interviewBoard (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        title VARCHAR(100),
                        company_name VARCHAR(100),
                        company_website VARCHAR(255),
                        job_description TEXT,
                        company_description TEXT,
                        interview_description TEXT,
                        date DATE,
                        start_time TEXT,
                        finish_time TEXT,
                        finished BOOLEAN,
                        meeting_summary TEXT,
                        latest_meeting_summary TEXT
                    );
                """)

            # Commit changes
            conn.commit()
            print("Table 'interviewBoard' created successfully.")
        else:
            print("Table 'interviewBoard' already exists.")

    except Exception as e:
        logger.error(f"An error occurred in create_interviewboard_table: {e}", exc_info=True)

    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def create_transcription_table():
    """
    Create 'interviewTranscription' table in PostgreSQL database if it does not exist.
    """
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()

        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Check if the 'interviewTranscription' table exists
        cur.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = 'interviewTranscription');")
        exists = cur.fetchone()[0]

        if not exists:
            # Create 'interviewTranscription' table if it does not exist
            cur.execute("""
                CREATE TABLE interviewTranscription (
                    id SERIAL PRIMARY KEY,
                    interview_id INTEGER REFERENCES interviewBoard(id),
                    start NUMERIC,
                    duration NUMERIC,
                    transcript TEXT,
                    confidence NUMERIC,
                    speaker INTEGER,
                    channel INTEGER,
                    added_to_notes BOOLEAN DEFAULT FALSE
                );
            """)
            
            # Commit changes
            conn.commit()
            print("Table 'interviewTranscription' created successfully.")
        else:
            print("Table 'interviewTranscription' already exists.")

    except Exception as e:
        logger.error(f"An error occurred in create_transcription_table: {e}", exc_info=True)

    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def create_interviewkeynotes_table():
    """
    Create 'interviewKeynotes' table in PostgreSQL database if it does not exist,
    with an additional column for embedding vectors.
    """
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()

        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Check if the 'interviewKeynotes' table exists
        cur.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = 'interviewKeynotes');")
        exists = cur.fetchone()[0]

        if not exists:
            # Create 'interviewKeynotes' table if it does not exist
            cur.execute("""
                CREATE TABLE interviewKeynotes (
                    id SERIAL PRIMARY KEY,
                    interview_id INTEGER REFERENCES interviewBoard(id),
                    keynotes TEXT,
                    embedding_vector FLOAT[] DEFAULT '{}'
                );
            """)
            
            # Commit changes
            conn.commit()
            print("Table 'interviewKeynotes' created successfully with an embedding_vector column.")
        else:
            print("Table 'interviewKeynotes' already exists.")

    except Exception as e:
        logger.error(f"An error occurred in create_interviewkeynotes_table: {e}", exc_info=True)

    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def create_interviewquestions_table():
    """
    Create 'interviewQuestions' table in PostgreSQL database if it does not exist,
    with additional columns for the embedding vector (empty by default), answer (string, empty by default),
    and a 'valid' integer column with a default value of 1.
    """
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()

        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Check if the 'interviewQuestions' table exists
        cur.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = 'interviewQuestions');")
        exists = cur.fetchone()[0]

        if not exists:
            # Create 'interviewQuestions' table if it does not exist
            cur.execute("""
                CREATE TABLE interviewQuestions (
                    id SERIAL PRIMARY KEY,
                    interview_id INTEGER REFERENCES interviewBoard(id),
                    question TEXT,
                    answered BOOLEAN DEFAULT FALSE,
                    answer TEXT DEFAULT '',
                    embedding_vector FLOAT[] DEFAULT '{}',
                    valid INTEGER DEFAULT 1
                );
            """)
            
            # Commit changes
            conn.commit()
            print("Table 'interviewQuestions' created successfully with an 'answer' column and a 'valid' column.")
        else:
            print("Table 'interviewQuestions' already exists.")

    except Exception as e:
        logger.error(f"An error occurred in create_interviewquestions_table: {e}", exc_info=True)

    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def create_oiusers_table():
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()

        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Check if the table exists
        cur.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = 'oiusers');")
        exists = cur.fetchone()[0]

        if not exists:
            # Create table if it does not exist
            cur.execute("""
                    CREATE TABLE oiusers (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) DEFAULT NULL,
                        emailid VARCHAR(100) UNIQUE NOT NULL,
                        role VARCHAR(100) DEFAULT NULL,
                        team VARCHAR(100) DEFAULT NULL,
                        access_token TEXT DEFAULT NULL
                    );
                """)

            # Commit changes
            conn.commit()
            print("Table 'oiusers' created successfully.")
        else:
            print("Table 'oiusers' already exists.")

    except Exception as e:
        # Handle exceptions and log errors
        logger.error(f"An error occurred in create_oiusers_table: {e}", exc_info=True)

    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


# Call the functions to create tables
create_interviewboard_table()
create_transcription_table()
create_interviewkeynotes_table()
create_interviewquestions_table()
create_oiusers_table()