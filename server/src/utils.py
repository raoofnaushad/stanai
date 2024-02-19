import json
from src import config as C

import os
import logging
from logging.handlers import RotatingFileHandler

def get_logger():
    # Create a logs directory if it does not exist
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Set up logging
    file_handler = RotatingFileHandler('logs/farpointoi.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)

    app_logger = logging.getLogger('farpointoi')
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(file_handler)
    app_logger.info('Application startup')

    return app_logger

logger = get_logger()

def load_json_file(file_path):
    """
    Load a JSON file and return its contents.
    Args:
        file_path (str): Path to the JSON file.
    Returns:
        dict: Contents of the JSON file.
    """
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"An error occurred while loading JSON file: {e}", exc_info=True)
        return None

def generate_prompt(prompt_keys, interview_details):
    """
    Generate a prompt by combining text values from prompts.json and replacing placeholders with values from interview_details.
    Args:
        prompt_keys (list): List of keys to retrieve prompts for.
        interview_details (dict): Dictionary containing interview details for placeholder replacement.
    Returns:
        str: Concatenated and formatted prompt.
    """
    # Load prompts data from JSON file
    prompts_data = load_json_file(C.PROMPTS_JSON_PATH)

    if not prompts_data:
        return "Error: Unable to load prompts data."

    combined_prompt = ""
    for key in prompt_keys:
        if key in prompts_data:
            # Format the prompt by replacing placeholders with interview details
            prompt = prompts_data[key].format(**interview_details)
            combined_prompt += prompt + "\n\n"

    return combined_prompt.strip()



