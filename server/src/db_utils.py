import psycopg2
from psycopg2 import sql

from datetime import datetime
from dotenv import load_dotenv
import os

from src import get_from_llm as llm
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


def insert_data_to_postgres(data, table_name='interviewboard'):
    '''
    This function is used to insert data into the PostGresDB
    Args:
        data ([dictionary]): [dictionary containing the data to be inserted]
    Returns:
        [insert_id]: [Returns the last inserted id]
    '''
    conn = get_db_connection()
    cur = conn.cursor()

    # Assuming 'data' is a dictionary that contains the data you want to insert
    # Adapt the following SQL command based on your specific table structure
    columns = data.keys()
    values = [data[column] for column in columns]
    insert_query = f'INSERT INTO {table_name} (' + ', '.join(columns) + ') VALUES (%s)' % ', '.join(['%s'] * len(values))
    cur.execute(insert_query, values)
    conn.commit()

    # Retrieve the last inserted id
    cur.execute('SELECT LASTVAL()')
    insert_id = cur.fetchone()[0]

    cur.close()
    conn.close()
    return insert_id


def get_summary_and_finish_interview(data, table_name='interviewboard'):
    '''
    This function is used to generate a meeting summary, mark an interview as finished, 
    and update the PostGresDB with the summary and the latest meeting summary.
    Args:
        data (dictionary): Dictionary containing the '_id' of the interview.
        table_name (str): Name of the table where the interview record is stored.
    '''
    if '_id' not in data:
        print("Error: '_id' not provided in data")
        return

    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch all transcript data
        cur.execute("""
            SELECT transcript FROM interviewtranscription
            WHERE interview_id = %s
        """, (data['_id'],))
        
        transcripts = cur.fetchall()
        all_transcript = '\n'.join([t[0] for t in transcripts if t[0]])

        # Get meeting summary using a hypothetical llm.get_meeting_summary function
        meeting_summary = llm.get_meeting_summary(data, all_transcript)

        # Prepare the update query for interviewboard to also update latest_meeting_summary
        update_query = f"""
            UPDATE {table_name}
            SET finished = TRUE, finish_time = %s, meeting_summary = %s, latest_meeting_summary = %s
            WHERE id = %s
        """
        finish_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        interview_id = data['_id']

        # Execute the update query
        cur.execute(update_query, (finish_time, meeting_summary, meeting_summary, interview_id))
        conn.commit()

        logger.info(f"Interview with ID {interview_id} marked as finished and summary updated.")
    
    except Exception as e:
        logger.error(f"An error occurred in get_summary_and_finish_interview: {e}", exc_info=True)
        raise e

    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
        
        return interview_id


def add_transcription_to_table(data):
    """
    Add transcription data to 'interviewTranscription' table in PostgreSQL database.

    Args:
        data (dict): Dictionary containing the transcription data.

    Returns:
        int: ID of the inserted record.
    """
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()

        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Extract relevant data from input
        interview_id = data.get("_id", None)
        transcription_data = data.get("transcription", {})

        if not interview_id:
            raise ValueError("Input data must contain an '_id' field.")

        # Insert data into 'interviewTranscription' table
        cur.execute("""
            INSERT INTO interviewTranscription 
            (start, duration, transcript, confidence, speaker, channel, interview_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            transcription_data.get("start", 0.0),
            transcription_data.get("duration", 0.0),
            transcription_data.get("transcript", ""),
            transcription_data.get("confidence", 0.0),
            transcription_data.get("speaker", -1),
            transcription_data.get("channel", -1),
            interview_id
        ))

        # Commit changes
        conn.commit()

        # Retrieve the last inserted id
        cur.execute('SELECT LASTVAL()')
        insert_id = cur.fetchone()[0]

        # logger.info(f"Transcription data added successfully. Inserted record ID: {insert_id}")

    except Exception as e:
        logger.error(f"An error occurred in add_transcription_to_table: {e}", exc_info=True)
        raise e
    
    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return insert_id


def get_last_10_finished_interviews():
    """
    Retrieve the last 10 finished interviews from the database.
    Returns:
        List[Dict]: A list of dictionaries, each containing details of an interview.
    """
    result = []
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()
        cur = conn.cursor()

        # Prepare and execute the query
        query = """
            SELECT id, company_name, name, interview_description, date, start_time, meeting_summary
            FROM interviewBoard
            WHERE finished = TRUE
            ORDER BY finish_time DESC
            LIMIT 10
        """
        cur.execute(query)

        # Fetch the results
        rows = cur.fetchall()
        for row in rows:
            interview_dict = {
                "id": row[0],
                "company": row[1],
                "attendees": row[2],
                "description": row[3],
                "date": row[4].isoformat() if row[4] else None,  # Converts date to string
                "startTime": row[5],
                "meeting_summary": row[6]
            }
            result.append(interview_dict)

    except Exception as e:
        logger.error(f"An error occurred in get_last_10_finished_interviews: {e}", exc_info=True)

    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return result


def generatetranscript_given_id(interview_id):
    """
    Retrieve interview transcripts from the database ,
    concatenate them, and then mark them as added to notes.
    Args:
        interview_id (int): The ID of the interview.
    Returns:
        str: Concatenated transcripts.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query to retrieve transcripts for the given interview_id where added_to_notes is False
        cur.execute("SELECT transcript FROM interviewTranscription WHERE interview_id = %s", (interview_id,))

        # Fetch all matching rows
        transcripts = cur.fetchall()

        # Concatenate the transcripts
        concatenated_transcripts = "\n".join([transcript[0] for transcript in transcripts])

        return concatenated_transcripts

    except Exception as e:
        logger.error(f"An error occurred in generatetranscript_given_id: {e}", exc_info=True)
        return ""
    
    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def generate_latest_transcript_given_id(interview_id):
    """
    Retrieve interview transcripts from the database where added_to_notes is False,
    concatenate them, and then mark them as added to notes.
    Args:
        interview_id (int): The ID of the interview.
    Returns:
        str: Concatenated transcripts.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query to retrieve transcripts for the given interview_id where added_to_notes is False
        cur.execute("SELECT transcript FROM interviewTranscription WHERE interview_id = %s AND added_to_notes = False", (interview_id,))

        # Fetch all matching rows
        transcripts = cur.fetchall()

        # Concatenate the transcripts
        concatenated_transcripts = "\n".join([transcript[0] for transcript in transcripts])

        if transcripts:
            # Update the added_to_notes column to True for all fetched transcripts
            cur.execute("UPDATE interviewTranscription SET added_to_notes = True WHERE interview_id = %s AND added_to_notes = False", (interview_id,))
            conn.commit()

        return concatenated_transcripts

    except Exception as e:
        logger.error(f"An error occurred in generate_latest_transcript_given_id: {e}", exc_info=True)
        return ""
    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def get_interview_details(_id):
    """
    Retrieve interview details from the database for a given interview ID, including the meeting summary.
    Args:
        _id (int): The ID of the interview.
    Returns:
        dict: Interview details in JSON format, including the meeting summary.
    """
    conn = None
    cur = None
    try:
        # Connect to the PostgreSQL database
        conn = get_db_connection()
        cur = conn.cursor()

        # Updated query to retrieve interview details along with meeting_summary
        cur.execute("""
            SELECT name, title, company_name, company_website, job_description, 
                   company_description, interview_description, date, start_time, finish_time, meeting_summary, latest_meeting_summary
            FROM interviewBoard
            WHERE id = %s
        """, (_id,))

        # Fetch the interview details
        result = cur.fetchone()

        if result:
            # Construct the JSON object with the added meeting_summary
            details = {
                "nameofclient": result[2],  # Assuming company_name is the name of the client
                "clientwebsite": result[3],
                "company_description": result[5],
                "name": result[0],
                "title": result[1],
                "date": result[7].isoformat() if result[7] else None,  # Converting date to string
                "jobdescription": result[4],
                "interview_description": result[6],
                "meeting_summary": result[10],
                "latest_meeting_summary": result[11]
            }
            return details
        else:
            logger.info("No details found for the given interview ID.")
            return {}

    except Exception as e:
        logger.error(f"An error occurred in get_interview_details: {e}", exc_info=True)
        return {}
    finally:
        # Close the cursor and connection to free resources
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def update_meeting_summary(meeting_id, new_summary):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # SQL query to update the meeting summary for a given meeting ID
        cur.execute("""
            UPDATE interviewBoard
            SET latest_meeting_summary = %s
            WHERE id = %s
        """, (new_summary, meeting_id))

        # Commit the changes to the database
        conn.commit()

        return "Meeting summary updated successfully"
    except Exception as e:
        # Ideally, you'd want more granular error handling here
        logger.error(f"An error occurred while updating meeting summary: {e}", exc_info=True)
        return "Error updating meeting summary"
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def add_interview_question(meeting_id, question):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # SQL query to insert the new question
        cur.execute("""
            INSERT INTO interviewQuestions (interview_id, question, answered)
            VALUES (%s, %s, %s)
        """, (meeting_id, question, False))

        # Commit the changes to the database
        conn.commit()

        return "Interview question added successfully"
    except Exception as e:
        logger.error(f"An error occurred while adding interview question: {e}", exc_info=True)
        return f"Error: {str(e)}"
    

def dislike_interview_question_logic(meeting_id, question_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # SQL query to update the valid column to 0
        cur.execute("""
            UPDATE interviewQuestions
            SET valid = 0
            WHERE interview_id = %s AND id = %s
        """, (meeting_id, question_id))

        # Commit the changes to the database
        conn.commit()

        if cur.rowcount == 0:
            return "No question found with the given ID."

        return "Interview question disliked successfully."
    except Exception as e:
        logger.error(f"An error occurred while disliking the interview question: {e}", exc_info=True)
        return f"Error: {str(e)}"
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def write_key_notes_to_postgres(interview_id, keynotes):
    """
    Write keynotes and their embedding vector to the 'interviewKeynotes' table in the PostgreSQL database.
    Args:
        interview_id (int): The ID of the interview.
        keynotes (str): Keynotes text to be written to the database.
    """
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()

        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Get the embedding for the keynotes
        embedding_vector = llm.get_embedding(keynotes)

        # Insert keynotes and their embedding into the 'interviewKeynotes' table
        cur.execute("""
            INSERT INTO interviewKeynotes (interview_id, keynotes, embedding_vector)
            VALUES (%s, %s, %s)
        """, (interview_id, keynotes, embedding_vector))

        # Commit changes
        conn.commit()
        logger.info("Keynotes and their embedding vector successfully written to the database.")

    except Exception as e:
        logger.error(f"An error occurred in write_key_notes_to_postgres: {e}", exc_info=True)

    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


### Function for question generation ------------------------------------------------------------------------

def write_unique_questions(interview_id, questions_json, conn):
    cur = conn.cursor()

    # Retrieve existing questions and their embeddings
    cur.execute("SELECT id, embedding_vector FROM interviewQuestions WHERE interview_id = %s", (interview_id,))
    existing_questions = cur.fetchall()

    # Iterate over each new question
    for _, new_question in questions_json.items():
        new_embedding = llm.get_embedding(new_question)

        # Check similarity with existing questions
        is_unique = True
        for _, existing_embedding in existing_questions:
            if llm.get_similarity(new_embedding, existing_embedding) >= C.QUESTION_SIMILARITY_THRESHOLD:
                is_unique = False
                break

        # If the new question is unique, add it to the database
        if is_unique:
            cur.execute("""
                INSERT INTO interviewQuestions (interview_id, question, embedding_vector)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (interview_id, new_question, new_embedding))
            new_q_id = cur.fetchone()[0]

    conn.commit()
    return None


def get_answered_questions(interview_id, conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT id, question, answered FROM interviewQuestions
        WHERE interview_id = %s and answered = false
        ORDER BY id DESC
    """, (interview_id,))

    questions = [{"id": row[0], "question": row[1], "answered": row[2]} for row in cur.fetchall()]
    questions_with_answers = llm.get_question_answer(questions, interview_id)
    return questions_with_answers


def update_answered_questions(answered_questions, conn):
    """
    Update the 'answered' and 'answer' columns in the 'interviewQuestions' table based on the provided data.
    Args:
        answered_questions (list): List of dictionaries with question details.
        conn: Connection to the PostgreSQL database.
    """
    cur = None
    try:
        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Update each question in the database
        for question in answered_questions:
            update_query = """
                UPDATE interviewQuestions
                SET answered = %s, answer = %s
                WHERE id = %s
            """
            # Extract the values from the question dictionary
            q_id = question["id"]
            is_answered = question["is_answered"]
            answer = question["answer"]

            # Execute the update query
            cur.execute(update_query, (is_answered, answer, q_id))

        # Commit the changes
        conn.commit()
        logger.info("Questions successfully updated in the database.")

    except Exception as e:
        logger.error(f"An error occurred in update_answered_questions: {e}", exc_info=True)

    finally:
        # Close the cursor
        if cur is not None:
            cur.close()

def get_all_questions(interview_id, conn=None):
    """
    Retrieve all questions for a given interview ID from the 'interviewQuestions' table,
    sorted by answered status and then by newest first.
    Args:
        interview_id (int): The ID of the interview.
        conn: Connection to the PostgreSQL database.
    Returns:
        list: A list of dictionaries, each containing question details.
    """
    questions = []
    cur = None

    try:
        if conn is None:
            conn = get_db_connection()
        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Execute the SELECT query with ORDER BY clause
        cur.execute("""
            SELECT id, question, answered, answer, valid
            FROM interviewQuestions
            WHERE interview_id = %s
            ORDER BY answered, id DESC
        """, (interview_id,))

        # Fetch all rows from the query result
        rows = cur.fetchall()

        # Format each row into a dictionary
        for row in rows:
            question_dict = {
                "id": row[0],
                "question": row[1],
                "answered": row[2],
                "answer": row[3],
                "valid" : row[4]
            }
            questions.append(question_dict)

    except Exception as e:
        logger.error(f"An error occurred in get_all_questions: {e}", exc_info=True)

    finally:
        # Close the cursor
        if cur is not None:
            cur.close()

    return questions

def processing_questions_to_postgres(interview_id, questions_json):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        logger.info("Writing unique questions")
        write_unique_questions(interview_id, questions_json, conn)
        logger.info("Get the answer of questions")
        answered_questions = get_answered_questions(interview_id, conn)
        logger.info("Update answered questions")
        update_answered_questions(answered_questions, conn)
        logger.info("All Questions successfully updated in the database.")
        all_questions = get_all_questions(interview_id, conn)
    except Exception as e:
        logger.error(f"An error occurred processing_questions_to_postgres: {e}", exc_info=True)
        all_questions = get_all_questions(interview_id, conn)
        return all_questions
    finally:
        if conn is not None:
            conn.close()
    return all_questions


def get_all_keynotes(interview_id):
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()
        cur = conn.cursor()

        # Retrieve all keynotes for this interview_id
        cur.execute("""
            SELECT keynotes FROM interviewKeynotes
            WHERE interview_id = %s
        """, (interview_id,))

        # Fetch all keynotes and flatten the list
        keynotes = [row[0] for row in cur.fetchall()]

    except Exception as e:
        logger.error(f"An error occurred in get_all_keynotes: {e}", exc_info=True)


    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return keynotes



## Functions for user authentication:

def store_user_access_token(user_email, access_token):
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()

        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Check if user exists
        cur.execute("SELECT id FROM oiusers WHERE emailid = %s;", (user_email,))
        user_id = cur.fetchone()

        if user_id:
            # Update the existing user's access token
            cur.execute("UPDATE oiusers SET access_token = %s WHERE emailid = %s;", (access_token, user_email))
        else:
            # Insert a new user with the given email and access token
            cur.execute("INSERT INTO oiusers (name, emailid, role, team, access_token) VALUES (NULL, %s, NULL, NULL, %s);", (user_email, access_token))

        # Commit changes
        conn.commit()

    except Exception as e:
        logger.error(f"Error in store_user_access_token: {e}", exc_info=True)

    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def retrieve_user_access_token(user_email):
    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = get_db_connection()

        # Open a cursor to perform database operations
        cur = conn.cursor()

        # Retrieve access token for the given email
        cur.execute("SELECT access_token FROM oiusers WHERE emailid = %s;", (user_email,))
        result = cur.fetchone()
        return result[0] if result else None

    except Exception as e:
        logger.error(f"Error in retrieve_user_access_token: {e}", exc_info=True)
        return None

    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()


