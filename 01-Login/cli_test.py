import webbrowser
from http.server import HTTPServer

import requests
from dotenv import load_dotenv, find_dotenv
from os import environ as env

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# Constants for API and localhost server
CLIENT_ID = env.get("AUTH0_CLIENT_ID")
CLIENT_SECRET = env.get("AUTH0_CLIENT_SECRET")
APP_SECRET_KEY = env.get("APP_SECRET_KEY")
AUTHORIZE_URL = f'https://{env.get("AUTH0_DOMAIN")}/authorize'  # Without trailing slash
TOKEN_URL = f'https://{env.get("AUTH0_DOMAIN")}/oauth/token'  # Without trailing slash
API_BASE_URL = f'https://{env.get("API_DOMAIN")}'  # Without trailing slash
SIM_API_BASE_URL = f'https://{env.get("SIM_API_DOMAIN")}'  # Without trailing slash
SCOPE = "openid offline_access profile MarketData"
PORT = 8080
REDIRECT_URI = f'http://localhost:{str(PORT)}'

def get_token_response():
    post_data = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': env.get("REFRESH_TOKEN"),
    }
    response = requests.post(TOKEN_URL, data=post_data)
    if response.status_code == 200:
        print(response.json())  # Print to console for demonstration

    return response


def run():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f'Serving on http://localhost:{str(PORT)}')
    webbrowser.open('http://localhost:8080')
    httpd.serve_forever()
