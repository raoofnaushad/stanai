from flask import Flask, request, redirect
from dotenv import load_dotenv
import urllib.parse
import os

load_dotenv()  # Load the environment variables from the .env file

app = Flask(__name__)

MS_CLIENT_ID = os.environ['MS_CLIENT_ID']
MS_TENANT_ID = os.environ['MS_TENANT_ID']
MS_REDIRECT_URI = os.environ['MS_REDIRECT_URI']
MS_SCOPE = os.environ['MS_SCOPE']

AUTH_CODE_FILE='auth_code.txt'


@app.route('/')
def home():
    # Construct the authorization URL
    auth_url = (
        f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/authorize?"
        f"client_id={MS_CLIENT_ID}&response_type=code&redirect_uri={urllib.parse.quote(MS_REDIRECT_URI)}&"
        f"response_mode=query&scope={urllib.parse.quote(MS_SCOPE)}&state=12345"
    )
    # Redirect the user to the Microsoft login page
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Extract the authorization code from the query string
    code = request.args.get('code', '')
    
    if code:
        # Write the authorization code to a file
        with open(AUTH_CODE_FILE, 'w') as file:
            file.write(code)
        return 'Authorization code received and stored.'
    else:
        return 'Authorization code not found in the request.'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
