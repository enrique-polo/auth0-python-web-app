import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request
from cache_functions import LocalCache

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

cache = LocalCache()

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid offline_access profile MarketData ReadAccount Trade Crypto Matrix OptionSpreads",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
    authorize_url=f'https://{env.get("AUTH0_DOMAIN")}/authorize',
)


def get(url, **kwargs):
    process_token()
    return oauth.auth0.get(url, **kwargs)


def process_token():
    if oauth.auth0.token is not None:
        token = oauth.auth0.token
    elif session.get('user', None) is not None:
        token = session.get('user', None)
        oauth.oauth2_client_cls.token = token
    else:
        token = cache.get('enrique.polo', None)
        oauth.oauth2_client_cls.token = token
        session["user"] = oauth.oauth2_client_cls.token
    if cache.get('enrique.polo', None) != token:
        cache.set('enrique.polo', token)


# Controllers API
@app.route("/", methods=["GET", "POST"])
def home():
    if 'code' in request.args:
        token = oauth.auth0.authorize_access_token()
        session["user"] = token
        return redirect("/")

    process_token()
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )

@app.route("/bars")
def bars():
    process_token()
    symbol = 'MSFT'
    interval = '15'
    unit = 'Minute'
    barsback = '100'
    query = f'{symbol}?interval={interval}&unit={unit}&barsback={barsback}'
    response = get(f'https://{env.get("API_DOMAIN")}/v3/marketdata/barcharts/{query}')
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(response.json(), indent=4),
    )

@app.route("/login")
def login():
    request = oauth.auth0.authorize_redirect(
        redirect_uri=url_for('home', _external=True),
        audience=f'https://{env.get("API_DOMAIN")}'
    )
    return request


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

if __name__ == "__main__":
    app.run(host="localhost", load_dotenv=True)
