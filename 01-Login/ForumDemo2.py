#!/usr/bin/env python

########################################################################
# Title: ForumDemo2.py
# Date: 2019-03-13
#
# This file is designed to demonstrate the TradeStation web API using
# python, a localhost server, and javascript. API values should be set
# in the constants section below. When this file is run, an HTTP server
# is started on the port specified in the constants section. As an
# example, if the port specified is 8080, use:
#
#   http://localhost:8080
#
# The python requests module is used to issue a POST request to obtain
# an access token. On the localhost page, javascript and the jQuery
# library are used to make GET and POST requests.
#
########################################################################

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import re
import requests  # Module not included in standard python libarary
import urllib
import webbrowser
from os import environ as env
from dotenv import find_dotenv, load_dotenv

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

# HTML to serve on root path /
# This page contains a link to the API sign in page
# Note: { and } are required to be escaped as {{ and }}, respectively


def generate_root_page():
    return f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
    <script>
    $(function() {{
        $('#main-div').fadeIn(2000);
    }});
    </script>
    <title>API Test</title>
    <style>
        #main-div {{
            position: absolute;
            display: none;
            top: 0;
            left: 0;
            height: 100%;
            width: 100%;
        }}
        #text-wrapper {{
            display: flex;
            height: 100%;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        #text-block {{
            margin-bottom: 4rem;
            text-align: center;
        }}
        #title-text {{
            font-size: 6rem;
            font-family: Verdana;
            border-top: 1px solid black;
            border-bottom: 1px solid black;
        }}
        #login-link {{
            margin-top: 2rem;
            font-family: Verdana;
            font-size: 1.25rem;
        }}
    </style>
</head>
<body>
    <div id="main-div">
        <div id="text-wrapper">
            <div id='text-block'>
                <div id="title-text">WEB API</div>
                <div id="login-link"><a href="{get_access_url()}">Sign in to TradeStation Account</a></div>
            </div>
        </div>
    </div>
</body>
</html>
""".encode('utf-8')

# HTML to serve when path is invalid


def generate_404_page():
    return "<!DOCTYPE html><html><body><pre>404 - Page not found.</pre></html>".encode("utf-8")

# HTML to serve when path contains case insensitive "code="
# Javascript + jQuery are used on the page to handle GET and POST requests
# Note: { and } are required to be escaped as {{ and }}, respectively


def generate_main_page(user_access_code):

    # Use access code in localhost URL to get token response
    response = get_token_response(user_access_code)

    # Handle non-200 response
    # This could be the result of an invalid or expired access code
    if response.status_code != 200:
        return f"""<!DOCTYPE html><html><body><pre>{response.text}</pre><br>
 <div id="login-link"><a href="http://localhost:{str(PORT)}">Home</a></div>
 </html>""".encode('utf-8')

    data = response.json()

    return f"""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
<style>
    #main-wrapper {{
        width: 80%;
        margin: 0% 10%;
    }}
    #templatesLabel {{
        font-family: monospace;
        font-weight: bold;
    }}
    #tokenExpiration {{
        float: right;
        font-family: monospace;
    }}
    #apiRefreshButton {{
        float: right;
    }}
    pre {{
        white-space: pre-wrap;
        border: 1px solid black;
        padding: 2em;
        word-wrap: break-word;
    }}
    #apiGetURL {{
        width: 100%; 
        margin: .5rem 0rem;
        border: 1px solid black;
        box-sizing: border-box;
        padding: 0.5rem;
    }}
    .bold-red {{
        font-weight: bold;
        color: red;
    }}
</style>
<script>

$(function() {{

    var accessToken = "{data['access_token']}";
    var secondsTilExpiration = {str(data['expires_in'])};
    var xmlhttp = new XMLHttpRequest()
    var streamUpdateCounter = 0; 

    function decrementRefreshButton() {{

        secondsTilExpiration -= 1;

        if ( secondsTilExpiration <= 0 && $("#tokenExpiration").hasClass("bold-red") == false ) {{
            $("#tokenExpiration").addClass("bold-red");
        }} else if ( secondsTilExpiration > 0 && $("#tokenExpiration").hasClass("bold-red") ) {{
            $("#tokenExpiration").removeClass("bold-red");
        }}

        $("#tokenExpiration").html(`Token Expiration ≈ ${{secondsTilExpiration}}s`);

    }}
    
    refershButtonInterval = setInterval(decrementRefreshButton, 1000);

    $("#apiRequestResponse").html("<b>API Response:</b><br><br>{data}")
    
    // Handle partial stream chunk for snapshot
            
    function streamUpdate(oEvent) {{

            streamUpdateCounter += 1;
            if (streamUpdateCounter == 1) {{
                $("#apiRequestResponse").html("<b>API Response:</b><br><br><span id='snapshot-data'><span>");
            }}

            let responseText = oEvent.currentTarget.responseText;
            $("#apiRequestResponse #snapshot-data").append(responseText);

    }}

    // Handle request button
    // Populate API Response textbox with response
    $("#apiRequestButton").on("click", e => {{

        e.preventDefault();
        $("#apiRequestResponse").html("<b>API Response:</b><br><br><span style='color:blue'>Awaiting response...</span>")
        xmlhttp.abort();
        let url = $("#apiGetURL").val();

        // Check if request is a snapshot stream 
        if ( url.toLowerCase().includes("stream/quote/snapshots/") ) {{

            // Reset number of stream updates to 0 
            streamUpdateCounter = 0; 
        
            xmlhttp.open('GET', url, true);
            xmlhttp.send();

            // Handle stream chunks with progress event listener streamUpdate
            xmlhttp.addEventListener("progress", streamUpdate);
            return false;
        
        }}

        // If not snapshot stream use jQuery get method

        $.get( url, data => {{
            $("#apiRequestResponse").html("<b>API Response:</b><br><br>" + JSON.stringify(data, null, 4) ); 
        }}).fail( err => {{
            try {{
                $("#apiRequestResponse").html("<b>API Response:</b><br><br>" + err.responseText ); 
            }} catch (err) {{
                $("#apiRequestResponse").html("<b>API Response:</b><br><br>" + "Request Failed" ); 
            }}
        }});
        return false;
    }});

    // Handle enter key in API request input textbox by sending #apiRequestButton click event
    $("#apiGetURL").keyup( e => {{
        if(e.keyCode == 13){{
            $("#apiRequestButton").click();
        }}
    }});

    // Handle templte selection, both click and change events
    // Update URL in input textbox with selected template
    $("#apiTemplates").on("click change", function() {{
        $("#apiGetURL").val( $(this).val() + `access_token=${{accessToken}}`)
    }});

    // Handle Refresh Token button click
    $("#apiRefreshButton").on( "click", e => {{

        e.preventDefault();

        xmlhttp.abort();
    
        $("#apiRequestResponse").html("<b>API Response:</b><br><br><span style='color:blue'>Awaiting response...</span>")

        var settings = {{
            "async": true,
            "url": "{API_BASE_URL}/security/authorize",
            "method": "POST",
            "headers": {{
                "Content-Type": "application/x-www-form-urlencoded"
            }},
            "data": {{
                "response_type": "token",
                "grant_type": "refresh_token",
                "client_id": "{CLIENT_ID}",
                "redirect_uri": "{REDIRECT_URI}",
                "client_secret": "{CLIENT_SECRET}",
                "refresh_token": "{data['refresh_token']}"
            }}
        }}

        // Submit POST request using resfresh token to obtain new access token
        $.ajax(settings).done( function(response) {{

            $("#apiRequestResponse").html( "<b>API Response:</b><br><br>" + JSON.stringify(response, null, 4) ); 
            let oldAccessToken = accessToken;

            // Reset expiration countdown
            if (response.hasOwnProperty('expires_in')) {{
                secondsTilExpiration = response["expires_in"];
            }}

            if (response.hasOwnProperty('access_token')) {{

                accessToken = response["access_token"];

                // Attempt to replace access_token query param in URL textbox with with new access_token
                try {{
                    let requestText = $("#apiGetURL").val(); 
                    let oldTextRegex = new RegExp(`access_token=${{oldAccessToken}}`, "i");
                    let newText = `access_token=${{accessToken}}`
                    newRequestText = requestText.replace( oldTextRegex, newText );
                    $("#apiGetURL").val(newRequestText);
                }} 
                catch(err) {{
                    // Do nothing, unsuccessful replacement
                }}

            }} else {{
                accessToken =  "N/A"
            }}

            $("#apiAccessToken").html( `<b>Access Token:</b><br><br>${{accessToken}}` );

        }}); 

        return false;
        
    }});

}});
</script>
</head>
<body>
<div id="main-wrapper">
<span id='templatesLabel'>Templates: </Span><select id="apiTemplates">
    <option value="{API_BASE_URL}/users/{data['userid']}/accounts?">Get Accounts</Option>
    <option value="{API_BASE_URL}/data/symbollists?">Get All Symbol Lists</Option>
    <option value="{API_BASE_URL}/data/symbollists/SP500/symbols?">Get Symbols in Symbol List</Option>
    <option value="{API_BASE_URL}/data/quote/AAPL?">Get Quote for AAPL</Option>
    <option value="{API_BASE_URL}/data/quote/AMZN?">Get Quote for AMZN</Option>
    <option value="{API_BASE_URL}/data/quote/FB?">Get Quote for FB</Option>
    <option value="{API_BASE_URL}/data/quote/NFLX?">Get Quote for NFLX</Option>
    <option value="{API_BASE_URL}/data/quote/TSLA?">Get Quote for TSLA</Option>
    <option value="{API_BASE_URL}/stream/quote/snapshots/AMZN?">Get Snapshot Stream for AMZN</Option>
    <option value="{API_BASE_URL}/stream/quote/snapshots/@ES?">Get Snapshot Stream for @ES</Option>
    <option value="{API_BASE_URL}/stream/quote/snapshots/@NQ?">Get Snapshot Stream for @NQ</Option>
    <option value="{API_BASE_URL}/stream/quote/snapshots/TSLA?">Get Snapshot Stream for TSLA</Option>
    <option value="{API_BASE_URL}/data/symbols/suggest/Alcoa?">Search for Symbols</Option>
    <option value="{API_BASE_URL}/stream/barchart/AMZN/5/Minute/2-18-2019/2-20-2019?">Stream BarChart - Date Range</option>
    <option value="{API_BASE_URL}/stream/barchart/AMZN/5/Minute?SessionTemplate=USEQPreAndPost&daysBack=1&lastDate=12-01-2016&">Stream BarChart - Days Back</option>
</select>
<span id='tokenExpiration'></span>
<input id='apiGetURL' value="{API_BASE_URL}/users/{data['userid']}/accounts?access_token={data['access_token']}"><br>
<button id="apiRequestButton" title="Submit API Request">Request</button><button id="apiRefreshButton" title="Generate New Access Token">Refresh Token</button>
<pre id='apiRequestResponse'></pre>
<pre id='apiAccessToken'>
<b>Access Token:</b> 

{data['access_token']}
</pre>
<pre id='apiRefreshToken'>
<b>Refresh Token:</b> 

{data['refresh_token']}
</pre>
</div><!-- ends main wrapper -->
</body>
</html>
""".encode('utf-8')

# This method obtains the initial API sign in URL, which grants an access code


def get_access_url():

    query_string = urllib.parse.urlencode({
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'audience': API_BASE_URL,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'state': APP_SECRET_KEY
    })

    access_url = f'{AUTHORIZE_URL}/authorize/?{query_string}'

    print(access_url)

    return access_url

 # This method accepts an access code string and sends a POST request
 # using the requests module in order to obtain a response


def get_token_response(access_code):

    post_data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': access_code,
        'redirect_uri': REDIRECT_URI,
    }

    # headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(TOKEN_URL, data=post_data)

    if response.status_code == 200:
        print(response.json())  # Print to console for demonstration

    return response

# This class handles localhost requests


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        # Serve root page with sign in link
        if self.path == '/':

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_response = generate_root_page()
            self.wfile.write(html_response)

            return

        # Check if query path contains case insensitive "code="
        code_match = re.search(r'code=([^&]+)', self.path, re.I)

        if code_match:

            user_access_code = code_match[1]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_response = generate_main_page(user_access_code)
            self.wfile.write(html_response)

            return

        # Send 404 error if path is none of the above
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html_response = generate_404_page()
        self.wfile.write(html_response)

        return

# This method starts the localhost server


def run():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f'Serving on http://localhost:{str(PORT)}')
    webbrowser.open('http://localhost:8080')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
