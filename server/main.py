import requests
from flask import Flask, request, jsonify, redirect, session, url_for
from flask import session
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity, create_refresh_token
from datetime import timedelta
import json
from dotenv import load_dotenv
import os

import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from src import config as C
from src import db_utils as DU
from src import utils as U
from src import get_from_llm as llm
from src import create_tables
from src import rag
from vectorization import vectorize_interview as vectorize
# from rag import rag


app = Flask(__name__)
CORS(app, supports_credentials=True)

load_dotenv()  # Load the environment variables from the .env file

# Initialize JWTManager
app.config['JWT_SECRET_KEY'] = os.environ['AUTH_SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=3) 
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)  

jwt = JWTManager(app)

GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
GOOGLE_SECRET_KEY = os.environ['GOOGLE_SECRET_KEY']
app.secret_key = os.environ['AUTH_SECRET_KEY']

# # This OAuth 2.0 access scope allows for read-only access to the user's calendar
# SCOPES = ['openid',
#           'https://www.googleapis.com/auth/calendar.readonly',
#           'https://www.googleapis.com/auth/userinfo.email',
#           'https://www.googleapis.com/auth/userinfo.profile']

# API_SERVICE_NAME = 'calendar'
# API_VERSION = 'v3'

@app.route('/', methods=['GET'])
def hello_world():
    return "Hello, FarpointOI Backend!!"



@app.route('/google_login', methods=['POST'])
def login():
    auth_code = request.get_json()['code']
    data = {
        'code': auth_code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_SECRET_KEY,
        'redirect_uri': 'postmessage',
        'grant_type': 'authorization_code'
    }

    response = requests.post('https://oauth2.googleapis.com/token', data=data).json()
    

    headers = {
        'Authorization': f'Bearer {response["access_token"]}'
    }
    user_info = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers).json()

    # Instead of storing in session, store the access token in the database
    # Here, store_user_access_token is a placeholder for your actual database function
    DU.store_user_access_token(user_email=user_info['email'], access_token=response['access_token'])

    jwt_token = create_access_token(identity=user_info['email'])
    refresh_token = create_refresh_token(identity=user_info['email'])
    return jsonify(user=user_info, access_token=jwt_token, refresh_token=refresh_token), 200


@app.route('/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify({'access_token': new_token})


@app.route("/userinfo", methods=["GET"])
@jwt_required()     
def get_userinfo():
    try:
        # Access the identity of the current user with get_jwt_identity
        current_user = get_jwt_identity()
        jwt_token = request.cookies.get('access_token_cookie')
        return jsonify({"message": "User information retrieved successfully", "user": current_user}), 200
    except Exception as ex:
        print(ex)
        return jsonify({"message": "Error occurred while retrieving user information", "error": str(ex)}), 500



@app.route('/interview/add', methods=['POST'])
@jwt_required()
def start_interview():
    try:
        data = request.json
        insert_id = DU.insert_data_to_postgres(data=data, table_name='interviewboard')
        return jsonify({"message": "Data added successfully", "_id": insert_id}), 201
    except Exception as ex:
        return jsonify({"message": "Error occurred while adding data", "error": str(ex)}), 500
    

@app.route('/interview/clientinfo', methods=['POST'])
@jwt_required()
def get_company_details():
    try:
        company_name = request.json['company']

        # Open and read the JSON file
        with open(C.PROMPTS_JSON_PATH, 'r') as file:
            data = json.load(file)

        # Access and modify the content of 'get_client_details'
        if 'get_client_details' in data:
            # Replace {companyname} with the actual company name
            prompt_with_company = data['get_client_details'].replace("{companyname}", company_name)
            
            # Use the updated prompt
            res = rag.query_index(prompt_with_company)
            return jsonify({"message": "Company details retrieved successfully", "details": str(res)}), 200
        else:
            return jsonify({"message": "'get_client_details' key not found"}), 404

    except FileNotFoundError:
        return jsonify({"message": "File not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"message": "Error decoding JSON from the file"}), 500
    except Exception as ex:
        return jsonify({"message": "An error occurred", "error": str(ex)}), 500

@app.route('/interview/finish', methods=['POST'])
@jwt_required()
def finish_interview():
    try:
        data = request.json
        interview_id = DU.get_summary_and_finish_interview(data=data, table_name='interviewboard')
        index = vectorize.to_vectorize_interview(data['_id'])
        return jsonify({"message": "Interview finished & vectorized successfully", "_id": interview_id}), 201
    except Exception as ex:
        return jsonify({"message": "Error in finishing & vectorizing interview", "error": str(ex)}), 500


@app.route('/interview/update', methods=['POST'])
@jwt_required()
def update_data():
    try:
        data = request.json
        insert_id = DU.add_transcription_to_table(data)
        return jsonify({"message": "Transcription added successfully", "transcript_id": insert_id}), 201
    except Exception as ex:
        return jsonify({"message": "Error occurred while adding transcript", "error": str(ex)}), 500
    
    
@app.route('/interview/get_notes', methods=['POST'])
@jwt_required()
def get_key_notes():
    try:
        data = request.json
        result = llm.generate_key_notes(data)
        return jsonify({"message": "Keynotes generated Successfully", "keynotes": result}), 200
    except Exception as ex:
        return jsonify({"message": "Error occurred while generating keynotes", "error": str(ex)}), 500

@app.route('/interview/get_interview_details/<meeting_id>', methods=['GET'])
@jwt_required()
def get_interview_details(meeting_id):
    try:
        # Here you would have logic to fetch the interview details based on the meeting_id
        # For instance, querying your database
        details = DU.get_interview_details(meeting_id)
        mapped_details = {
            "attendees": details['name'],  
            "date": details["date"], 
            "interviewType": details["interview_description"], 
            "companyName": details["nameofclient"],
            "meeting_summary" : details["latest_meeting_summary"]
        }
        # Assume result is a dictionary with the interview details
        return jsonify({"message": "Interview details fetched successfully", "interviewDetails": mapped_details}), 200
    except Exception as ex:
        return jsonify({"message": "Error occurred while fetching interview details", "error": str(ex)}), 500
    

@app.route('/interview/update_meeting_notes/<meeting_id>', methods=['POST'])
@jwt_required()
def update_meeting_notes(meeting_id):
    try:
        # Extract the new meeting summary from the request body
        new_summary = request.json.get('meetingSummary')
        if not new_summary:
            return jsonify({"message": "No meeting summary provided"}), 400

        # Call the update function
        success_message = DU.update_meeting_summary(meeting_id, new_summary)
        return jsonify({"message": success_message}), 200
    except Exception as ex:
        return jsonify({"message": "Error occurred while updating meeting notes", "error": str(ex)}), 500
    

@app.route('/interview/get_interview_questions/<meeting_id>', methods=['GET'])
@jwt_required()
def get_interview_questions(meeting_id):
    try:
        # Fetch questions for the meeting_id from a mock database or real database
        # questions = questions_database.get("1", [])
        questions = DU.get_all_questions(meeting_id)
        # Assume result is a dictionary with the interview details
        return jsonify({"message": "Interview Questions fetched successfully", "questions": questions}), 200
    except Exception as ex:
        return jsonify({"message": "Error occurred while fetching interview questions", "error": str(ex)}), 500
    

@app.route('/interview/add_interview_questions/<meeting_id>', methods=['POST'])
@jwt_required()
def add_interview_questions(meeting_id):
    try:
        # Extract the new question from the request body
        question_data = request.json
        new_question = question_data.get('question')
        if not new_question:
            return jsonify({"message": "No question provided"}), 400

        # Call the function to add the question to the database
        success_message = DU.add_interview_question(meeting_id, new_question)
        return jsonify({"message": success_message}), 200
    except Exception as ex:
        return jsonify({"message": "Error occurred while adding interview question", "error": str(ex)}), 500
    

@app.route('/interview/dislike_question/<meeting_id>/<question_id>', methods=['PATCH'])
@jwt_required()
def dislike_interview_question(meeting_id, question_id):
    try:
        # Call the function to dislike the question in the database
        success_message = DU.dislike_interview_question_logic(meeting_id, question_id)
        return jsonify({"message": success_message}), 200
    except Exception as ex:
        return jsonify({"message": "Error occurred while disliking the interview question", "error": str(ex)}), 500
    

@app.route('/board/previous_interviews', methods=['GET'])
@jwt_required()
def retrieving_prev_interviews():
    try:
        result = DU.get_last_10_finished_interviews()
        return jsonify({"message": "Retrieved Previous Interviews Succesfully", "previousInterviews": result}), 200
    except Exception as ex:
        return jsonify({"message": "Error retrieving previous interviews", "error": str(ex)}), 500
 

@app.route('/interview/get_questions', methods=['POST'])
@jwt_required()
def get_questions_from_trans():
    try:
        data = request.json
        result = llm.generate_questions(data)
        return jsonify({"message": "Generated Questions Succesfully", "questions": result}), 200
    except Exception as ex:
        return jsonify({"message": "Error occurred while generating questions", "error": str(ex)}), 500
    

@app.route('/farpointbot/bot_response', methods=['POST'])
@jwt_required()
def generating_bot_response():
    try:
        data = request.json
        result = rag.query_response(data['user_input'])
        # result = 'Response From Bot'
        return jsonify({"message": "Generated Bot Response Succesfully", "bot_response": str(result)}), 200
    except Exception as ex:
        return jsonify({"message": "Error generating response from FarpointBOT", "error": str(ex)}), 500
    

@app.route('/board/get_calendar_events', methods=['GET'])
@jwt_required()
def get_calendar_events():
    try:
        current_user = get_jwt_identity()
        
        # Retrieve the user's access token from the database
        user_access_token = DU.retrieve_user_access_token(current_user)
        if not user_access_token:
            return jsonify({"error": "Access token not available"}), 401

        service = build('calendar', 'v3', credentials=Credentials(token=user_access_token))

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=12, singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])

        return jsonify({"message": "Calendar Events Retrieved Successfully", "events": events}), 200
    except Exception as ex:
        return jsonify({"message": "Error Getting Calendar Events", "error": str(ex)}), 500
    


