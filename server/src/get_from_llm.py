from openai import OpenAI

from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import threading
import os

from src import utils as U
from src import db_utils as DU
from src import config as C

logger = U.get_logger()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def generate_key_notes(request):
    # Generate transcript and interview details
    transcript = DU.generate_latest_transcript_given_id(request["_id"])
    # transcript = DU.generatetranscript_given_id(request["_id"])

    if not transcript:
        raise Exception("No new transcript found")
    
    interview_details = DU.get_interview_details(request["_id"])

    # Generate general and keynotes prompts
    general_prompt = U.generate_prompt(["farpoint_general", "client_general", "meeting_general"], 
                                       interview_details)
    keynotes_prompt = U.generate_prompt(["key_notes_prompt"], 
                                       interview_details)
    
    # Append the transcript to the keynotes prompt
    keynotes_prompt += "\n" + str(transcript)

    # Read and update completion.json file
    with open(C.COMPLETION_JSON_PATH, "r") as file:
        final_keynotes_prompt = json.load(file)
    
    # Update the content based on the role
    for prompt in final_keynotes_prompt['key_notes_prompt']:
        if prompt['role'] == 'system':
            prompt['content'] = general_prompt
        elif prompt['role'] == 'user':
            prompt['content'] = keynotes_prompt


    # Write the updated completion_json to a file
    with open(C.KEYNOTES_PROMPT_JSON_PATH, "w") as file:
        json.dump(final_keynotes_prompt, file, indent=4)

    # Generate completion using the updated prompts
    completion = client.chat.completions.create(
        model=C.OPENAI_MODEL,
        messages=final_keynotes_prompt['key_notes_prompt']
    )

    # Extract keynotes from the completion
    keynotes = completion.choices[0].message.content

    # Remove the phrase if it exists at the start of the string and strip whitespace
    if keynotes.startswith(C.PHRASE_TO_REMOVE):
        keynotes = keynotes[len(C.PHRASE_TO_REMOVE):].strip()

    # Write/append the questions to the text file
    with open(C.KEYNOTES_PATH, 'a') as file:
        file.write(keynotes + "\n\n")  # Adding an extra newline for separation between entries

    # Write keynotes to the PostgreSQL database
    res = DU.write_key_notes_to_postgres(request["_id"], keynotes)

    return keynotes


def get_meeting_summary(data, transcript):

    
    interview_details = DU.get_interview_details(data["_id"])

    # Generate general and keynotes prompts
    general_prompt = U.generate_prompt(["farpoint_general", "client_general", "meeting_general"], 
                                       interview_details)
    summary_prompt = U.generate_prompt(["transcript_summary_prompt"], 
                                       interview_details)
    
    # Append the transcript to the keynotes prompt
    summary_prompt += "\n" + str(transcript)

    # Read and update completion.json file
    with open(C.COMPLETION_JSON_PATH, "r") as file:
        final_summary_prompt = json.load(file)
    
    # Update the content based on the role
    for prompt in final_summary_prompt['transcript_summary_prompt']:
        if prompt['role'] == 'system':
            prompt['content'] = general_prompt
        elif prompt['role'] == 'user':
            prompt['content'] = summary_prompt


    # Write the updated completion_json to a file
    with open(C.SUMMARY_PROMPT_JSON_PATH, "w") as file:
        json.dump(final_summary_prompt, file, indent=4)

    # Generate completion using the updated prompts
    completion = client.chat.completions.create(
        model=C.OPENAI_MODEL,
        messages=final_summary_prompt['transcript_summary_prompt']
    )

    # Extract keynotes from the completion
    meeting_summary = completion.choices[0].message.content

    return meeting_summary



def generate_questions(request):

    # Generate transcript and interview details
    transcript = DU.generatetranscript_given_id(request["_id"])    
    interview_details = DU.get_interview_details(request["_id"])

    # Generate general and keynotes prompts
    general_prompt = U.generate_prompt(["farpoint_general", "client_general", "meeting_general"], 
                                       interview_details)
    questions_prompt = U.generate_prompt(["recommended_questions_prompt"], 
                                       interview_details)
    
    # Append the transcript to the keynotes prompt
    questions_prompt += "\n" + transcript

    # Read and update completion.json file
    with open(C.COMPLETION_JSON_PATH, "r") as file:
        final_questions_prompt = json.load(file)

    # Update the content based on the role
    for prompt in final_questions_prompt['recommended_questions_prompt']:
        if prompt['role'] == 'system':
            prompt['content'] = general_prompt
        elif prompt['role'] == 'user':
            prompt['content'] = questions_prompt

    # Write the updated completion_json to a file
    with open(C.QUESTIONS_PROMPT_JSON_PATH, "w") as file:   
        json.dump(final_questions_prompt, file, indent=4)

    # Generate completion using the updated prompts
    completion = client.chat.completions.create(
        model=C.OPENAI_MODEL,
        messages=final_questions_prompt['recommended_questions_prompt']
    )

    # Extract questions from the completion
    questions = completion.choices[0].message.content
    questions = '\n'.join(line for line in questions.split('\n') if not line.strip().startswith('```'))

    # Write/append the questions to the text file
    with open(C.QUESTIONS_PATH, 'a') as file:
        file.write(questions + "\n\n")  # Adding an extra newline for separation between entries

    try:
        questions_json = json.loads(questions)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding the JSON format:: {e}", exc_info=True)
        
    # print(f"Similarity Checked questions: {questions_json}")
    all_questions = DU.processing_questions_to_postgres(request["_id"], questions_json)
    return all_questions


def get_question_answer(questions, interview_id):
    # Generate transcript and interview details
    transcript = DU.generatetranscript_given_id(interview_id)    
    interview_details = DU.get_interview_details(interview_id)

    # Generate general and keynotes prompts
    general_prompt = U.generate_prompt(["farpoint_general", "client_general", "meeting_general"], 
                                       interview_details)
    
    answered_questions_prompt = U.load_json_file(C.PROMPTS_JSON_PATH)["answered_questions_prompt"]
    # answered_questions_prompt = U.generate_prompt(["answered_questions_prompt"], 
    #                                    interview_details)
    
    # Format each question as '<id>: <question>' and join them with a newline
    formatted_questions = "\n".join(f"{item['id']}: {item['question']}" for item in questions)

    # Append the formatted questions to the prompt
    answered_questions_prompt += "\n" + formatted_questions

    # Append the transcript to the prompt
    answered_questions_prompt += "\n Please find the transcripts of the meeting below:\n" +  transcript
    # Read and update completion.json file
    with open(C.COMPLETION_JSON_PATH, "r") as file:
        final_answered_questions_prompt = json.load(file)

    # Update the content based on the role
    for prompt in final_answered_questions_prompt['answered_questions_prompt']:
        if prompt['role'] == 'system':
            prompt['content'] = general_prompt
        elif prompt['role'] == 'user':
            prompt['content'] = answered_questions_prompt


    # Write the updated completion_json to a file
    with open(C.ANS_QUESTIONS_PROMPT_JSON_PATH, "w") as file:
        json.dump(final_answered_questions_prompt, file, indent=4)

    # Generate completion using the updated prompts
    completion = client.chat.completions.create(
        model=C.OPENAI_MODEL,
        messages=final_answered_questions_prompt['answered_questions_prompt']
    )

    questions_answers = completion.choices[0].message.content
    questions_answers = '\n'.join(line for line in questions_answers.split('\n') if not line.strip().startswith('```'))

    # Write/append the questions to the text file
    with open(C.ANSWERED_QUESTIONS_PATH, 'a') as file:
        file.write(questions_answers + "\n\n")  # Adding an extra newline for separation between entries

    try:
        questions_answers_json = json.loads(questions_answers)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding the JSON format:: {e}", exc_info=True)

    return questions_answers_json




def get_embedding(text, model="text-embedding-ada-002"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding


def get_similarity(embedding1, embedding2, model="text-embedding-ada-002"):

    # Reshaping the embeddings to 2D arrays for sklearn compatibility
    embedding1 = np.array(embedding1).reshape(1, -1)
    embedding2 = np.array(embedding2).reshape(1, -1)

    # Calculating cosine similarity
    similarity_score = cosine_similarity(embedding1, embedding2)[0][0]
    return similarity_score
