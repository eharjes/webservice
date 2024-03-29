## channel.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify
import json
import requests
import datetime

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'https://temporary-server.de'
HUB_AUTHKEY = 'Crr-K3d-2N' 
# HUB_URL = 'http://localhost:5555'
# HUB_AUTHKEY = '1234567890'
CHANNEL_AUTHKEY = '22334455'
CHANNEL_NAME = "Hangman"
CHANNEL_ENDPOINT = "http://vm455.rz.uni-osnabrueck.de/user064/channel2.wsgi" 
# CHANNEL_ENDPOINT = "http://localhost:5002"
CHANNEL_FILE = 'messages2.json'


@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
            "name": CHANNEL_NAME,
            "endpoint": CHANNEL_ENDPOINT, 
            "authkey": CHANNEL_AUTHKEY}))

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def post_number():
    if not check_authorization(request):
        return "Invalid authorization", 400
    data = request.json
    if 'guess' not in data:
        return "No number provided", 400

    # Convert number to integer
    try:
        letter = data['guess']
        response = data['response']
        guesses = data['guesses']
        word = data['word']
        lives = data['lives']
    except ValueError:
        return "Number must be an integer", 400
    # Add number to messages
    messages = read_messages()
    timestamp = datetime.datetime.now().isoformat()
    messages.append({'guess': letter, 'timestamp': timestamp, 'response': response, 'guesses': guesses, 'word': word, 'lives': lives})
    save_messages(messages)
    return "OK", 200

def read_messages():
    try:
        with open(CHANNEL_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

# Start development web server
if __name__ == '__main__':
    app.run(port=5002, debug=True)
