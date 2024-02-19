import requests


def refresh_access_token(client_id, client_secret, refresh_token, tenant_id):
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "scope": "https://graph.microsoft.com/.default"
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        response_data = response.json()
        new_access_token = response_data.get('access_token')
        # Refresh token can also be updated in this step, as new one may be returned
        new_refresh_token = response_data.get('refresh_token', refresh_token)  # Fallback to old if not provided
        return new_access_token, new_refresh_token
    else:
        raise Exception(f"Failed to refresh access token: {response.text}")

    
def get_tokens_from_code(client_id, client_secret, authorization_code, redirect_uri, tenant_id):
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": authorization_code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "scope": "https://graph.microsoft.com/.default"
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()  # This will return both access_token and refresh_token
    else:
        raise Exception("Failed to get tokens")

