import requests
import os
from dotenv import load_dotenv
from datetime import datetime

from src import auth
from src import graph
from src import utils as U
from src import config as C
from src import db_utils as DU

load_dotenv()  # Load the environment variables from the .env file

def get_the_latest_files(client_id, client_secret, tenant_id, redirect_uri, shared_folder_url, local_download_path, auth_code_file='auth_code.txt'):
   
    # Step 1: Retrieve refresh token from environment variable
    try: 
        refresh_token = os.environ['REFRESH_TOKEN']
    except:
        refresh_token = None

    access_token = None

    # Step 2: Check if refresh token is available
    if refresh_token:
        try:
            # Step 3: Use refresh token to obtain access token
            access_token, new_refresh_token = auth.refresh_access_token(client_id, client_secret, refresh_token, tenant_id)
            # Update the refresh token environment variable if a new refresh token was obtained
            if new_refresh_token != refresh_token:
                os.environ['REFRESH_TOKEN'] = refresh_token
                U.update_env_file('REFRESH_TOKEN', refresh_token)
        except Exception as e:
            print(f"Error refreshing access token with refresh token: {e}")
            return
    else:
        # Use the authorization code to get tokens if refresh_token environment variable is not set
        try:
            authorization_code = U.read_auth_code_from_file(auth_code_file)
            if not authorization_code:
                print("Failed to read authorization code.")
                return
            
            tokens = auth.get_tokens_from_code(client_id, client_secret, authorization_code, redirect_uri, tenant_id)
            access_token = tokens.get('access_token')
            refresh_token = tokens.get('refresh_token')
            
            # Save the new refresh token in the environment variable
            os.environ['REFRESH_TOKEN'] = refresh_token
            U.update_env_file('REFRESH_TOKEN', refresh_token)

        except Exception as e:
            print(f"Error exchanging authorization code for tokens: {e}")
            return
    
    if not access_token:
        print("Failed to obtain access token.")
        return

    # Step 4: Download files from the shared folder
    try:
        shared_items = graph.list_files_in_shared_folder(access_token, shared_folder_url=shared_folder_url)
        graph.download_files_and_folders(access_token, shared_items, local_download_path, base_shared_folder_url=shared_folder_url)
    except Exception as e:
        print(f"Error processing shared folder: {e}")


if __name__ == '__main__':
    client_id = os.environ['MS_CLIENT_ID']
    client_secret = os.environ['MS_CLIENT_SECRET']
    tenant_id = os.environ['MS_TENANT_ID']
    redirect_uri = os.environ['MS_REDIRECT_URI']
    shared_folder_url = os.environ['MS_SHARED_FOLDER_URL']

    local_download_path = './files'
    U.create_directory_if_not_exists(local_download_path)

    get_the_latest_files(client_id, client_secret, tenant_id, redirect_uri, shared_folder_url, local_download_path)
