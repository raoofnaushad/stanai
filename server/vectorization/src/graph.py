import os
import requests
from src import db_utils as DU
from src import utils as U
from datetime import datetime


def list_files_in_shared_folder(access_token, item_id=None, shared_folder_url=None):
    if item_id:
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/children"
    else:
        share_id = U.encode_sharing_url(shared_folder_url)  # Use the function from earlier
        url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/children"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['value']
    else:
        raise Exception(f"Failed to list files: {response.json()}")


def download_files_and_folders(access_token, shared_items, local_download_path, base_shared_folder_url=None):
    for item in shared_items:
        local_item_path = os.path.join(local_download_path, item['name'])

        if 'folder' in item:
            U.create_directory_if_not_exists(local_item_path)
            folder_contents = list_files_in_shared_folder(access_token, item_id=item['id'])
            download_files_and_folders(access_token, folder_contents, local_item_path)
        elif item['name'].lower().endswith(('.pdf', '.docx')):
            download_url = item['@microsoft.graph.downloadUrl']
            # print(f"Downloading {item['name']} to {local_item_path}")
            try:
                if 'folder' not in item and should_download(item):
                    U.download_file(download_url, local_item_path)
                    file_hash = U.generate_file_hash(local_item_path)
                    file_type = item['name'].split('.')[-1]
                    parent_name = U.extract_parent_name(local_item_path)
                    created_time = datetime.strptime(item['createdDateTime'], "%Y-%m-%dT%H:%M:%SZ")
                    downloaded_time = datetime.now()
                    last_modified = datetime.strptime(item['lastModifiedDateTime'], "%Y-%m-%dT%H:%M:%SZ")
                    
                    DU.insert_file_download_details(file_type, item['name'], parent_name, created_time, downloaded_time, last_modified, file_hash)
                    print(f"Downloaded {item['name']} to {local_item_path}")

            except Exception as e:
                print(f"Failed to download {item['name']}: {e}")


def should_download(item):
    latest_last_downloaded_time, file_hashes = DU.get_file_details(item['name'])
    
    if latest_last_downloaded_time is None:
        return True

    # Check if latest_last_downloaded_time is already a datetime object
    if isinstance(latest_last_downloaded_time, datetime):
        latest_downloaded_time = latest_last_downloaded_time
    else:
        # Convert the latest downloaded_time string to a datetime object
        latest_downloaded_time = datetime.strptime(latest_last_downloaded_time, "%Y-%m-%d %H:%M:%S")
    
    last_modified_time = datetime.strptime(item['lastModifiedDateTime'], "%Y-%m-%dT%H:%M:%SZ")

    if last_modified_time <= latest_downloaded_time:
        return False
    
    download_url = item['@microsoft.graph.downloadUrl']
    temp_file_path = 'temp_file_for_hash_check'
    U.download_file(download_url, temp_file_path)
    new_file_hash = U.generate_file_hash(temp_file_path)
    os.remove(temp_file_path)

    if new_file_hash in file_hashes:
        return False
    
    return True



