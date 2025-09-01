from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv
import os
import requests

# Load environment variables from .env file
load_dotenv()

# Replace with your actual Yoti credentials from the .env file
YOTI_CLIENT_SDK_ID = os.getenv("YOTI_CLIENT_SDK_ID")
YOTI_BEARER_TOKEN = os.getenv("YOTI_BEARER_TOKEN")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start-avs', methods=['POST'])
def start_avs_workflow():
    try:
        headers = {
            "Authorization": f"Bearer {YOTI_BEARER_TOKEN}",
            "Content-Type": "application/json",
            "Yoti-SDK-Id": YOTI_CLIENT_SDK_ID
        }

        # Debug print statement to verify headers
        print("Headers being sent:", headers)

        payload = {
            "type": "OVER",
            "age_estimation": {
                "allowed": True,
                "threshold": 18,
                "level": "PASSIVE"
            },
            "digital_id": {
                "allowed": True,
                "threshold": 18,
                "level": "NONE"
            },
            "doc_scan": {
                "allowed": True,
                "threshold": 18,
                "authenticity": "AUTO",
                "level": "PASSIVE"
            },
            "credit_card": {
                "allowed": False,
                "threshold": 18,
                "level": "NONE"
            },
            "mobile": {
                "allowed": False,
                "threshold": 18,
                "level": "NONE"
            },
            "ttl": 900,
            "reference_id": "over_18_example",
            "callback": {
                "auto": True,
                "url": "https://127.0.0.1:5000/yoti-callback"
            },
            
            "synchronous_checks": True
        }

        response = requests.post("https://age.yoti.com/api/v1/sessions", json=payload, headers=headers)
        response.raise_for_status() # A good practice to check for HTTP errors
        print("Response from Yoti:", response.json()) # Debug print to see the response
        session_id = response.json().get('id')
        if not session_id:
            return "Error: Session ID not found in Yoti response.", 500
        if response.status_code == 200:
            yoti_redirect_url = f"https://age.yoti.com?sessionId={session_id}&sdkId={YOTI_CLIENT_SDK_ID}"
            print(f"--> Attempting to redirect user to: {yoti_redirect_url}")
            return redirect(yoti_redirect_url)
        else:
            return f"Error: {response.status_code}, {response.text}", 500
    except requests.exceptions.HTTPError as e:
        return f"HTTP Error creating session: {e.response.status_code}, {e.response.text}", 500    
    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route('/yoti-callback')
def yoti_callback():
    try:
        # Get the session id from the URL after Yoti redirects the user
        session_id = request.args.get('sessionId')
        if not session_id:
            return "Error: sessionId not found in callback URL.", 400

        headers = {
            "Authorization": f"Bearer {YOTI_BEARER_TOKEN}",
            "Content-Type": "application/json",
            "Yoti-SDK-Id": YOTI_CLIENT_SDK_ID
        }

        response = requests.get(f"https://age.yoti.com/api/v1/sessions/{session_id}/result", headers=headers)

        if response.status_code == 200:
            age_verification_result = response.json()
            print("Age Verification Result:", age_verification_result)
            if age_verification_result.get('status') == 'COMPLETE':
                return render_template('success.html')
            else:
                print(age_verification_result.get('status'))
                status = age_verification_result.get('status')
                return f"Age verification was not successful. The final status was: '{status}'.", 400
        else:
            return f"Error: {response.status_code}, {response.text}", 500
    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route('/success')
def success_page():
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)

