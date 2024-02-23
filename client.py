from flask import Flask, request, render_template, url_for, redirect
import requests
import urllib.parse
import datetime
import random

app = Flask(__name__)

# HUB_AUTHKEY = '1234567890'
# HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = 'Crr-K3d-2N'
HUB_URL = 'https://temporary-server.de'

CHANNELS = None
LAST_CHANNEL_UPDATE = None


def update_channels():
    global CHANNELS, LAST_CHANNEL_UPDATE
    if CHANNELS and LAST_CHANNEL_UPDATE and (datetime.datetime.now() - LAST_CHANNEL_UPDATE).seconds < 60:
        return CHANNELS
    # fetch list of channels from server
    response = requests.get(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY})
    if response.status_code != 200:
        return "Error fetching channels: "+str(response.text), 400
    channels_response = response.json()
    if not 'channels' in channels_response:
        return "No channels in response", 400
    CHANNELS = channels_response['channels']
    LAST_CHANNEL_UPDATE = datetime.datetime.now()
    return CHANNELS


@app.route('/')
def home_page():
    # fetch list of channels from server
    return render_template("home.html", channels=update_channels())


@app.route('/show')
def show_channel():
    # fetch list of messages from channel
    show_channel = request.args.get('channel', None)
    if not show_channel:
        return "No channel specified", 400
    channel = None
    for c in update_channels():
        if c['endpoint'] == urllib.parse.unquote(show_channel):
            channel = c
            break
    if not channel:
        return "Channel not found", 404
    response = requests.get(channel['endpoint'], headers={'Authorization': 'authkey ' + channel['authkey']})
    if response.status_code != 200:
        return "Error fetching messages: "+str(response.text), 400
    messages = response.json()
    if channel['name'] == "Number Guessing":
        return render_template("channel.html", channel=channel, messages=messages)
    elif channel['name'] == "Hangman":
        return render_template("channel2.html", channel=channel, messages=messages)
    else:
        return render_template("channel.html", channel=channel, messages=messages)


@app.route('/post', methods=['POST'])
def post_message():
    global RANDOM_NUMBER, RANDOM_WORD, GUESSED_LETTERS, REMAINING_LIVES, WORDS
    post_channel = request.form['channel']
    if not post_channel:
        return "No channel specified", 400
    channel = None
    for c in update_channels():
        if c['endpoint'] == urllib.parse.unquote(post_channel):
            channel = c
            break
    if not channel:
        return "Channel not found", 404

    # Retrieve and validate the guessed number
    if 'number' in request.form: 
        try:
            guessed_number = int(request.form['number'])
        except ValueError:
            return "Number must be an integer", 400
        
        # Compare the guessed number to the random number
        if guessed_number == RANDOM_NUMBER:
            message = "Congratulations! You guessed the number! The number was " + str(RANDOM_NUMBER) + ". Do you want to play again? Just guess again!"
            message_timestamp = datetime.datetime.now().isoformat()
            response = requests.post(channel['endpoint'],
                                headers={'Authorization': 'authkey ' + channel['authkey']},
                                json={'guess': guessed_number, 'timestamp': message_timestamp, 'response': message})
            if response.status_code != 200:
                return "Error posting message: "+str(response.text), 400
            RANDOM_NUMBER = random.randint(0, 100)

        elif guessed_number < RANDOM_NUMBER:
            message = "The number is higher than "+ str(guessed_number) + ". Guess again!"
            message_timestamp = datetime.datetime.now().isoformat()
            response = requests.post(channel['endpoint'],
                                headers={'Authorization': 'authkey ' + channel['authkey']},
                                json={'guess': guessed_number, 'timestamp': message_timestamp, 'response': message})
            
            if response.status_code != 200:
                return "Error posting message: "+str(response.text), 400
        
        else:
            message = "The number is lower than "+ str(guessed_number) + ". Guess again!"
            message_timestamp = datetime.datetime.now().isoformat()
            response = requests.post(channel['endpoint'],
                                headers={'Authorization': 'authkey ' + channel['authkey']},
                                json={'guess': guessed_number, 'timestamp': message_timestamp, 'response': message})
            
            if response.status_code != 200:
                return "Error posting message: "+str(response.text), 400
    
    elif 'letter' in request.form:
        guessed_letter = request.form['letter']

        if len(guessed_letter) != 1:
            return "Please only guess single letters", 400
        
        if guessed_letter in GUESSED_LETTERS:
            return "You already guessed this letter. Try a different one.", 400
        
        if guessed_letter in RANDOM_WORD:
            GUESSED_LETTERS.append(guessed_letter)
            word = display_word(RANDOM_WORD, GUESSED_LETTERS)
            
            if "_ " not in word:
                message = "Congratulations you guessed the word! It was " + RANDOM_WORD + ". Do you want to play again? Just guess a new letter!"
                message_timestamp = datetime.datetime.now().isoformat()
                response = requests.post(channel['endpoint'],
                                    headers={'Authorization': 'authkey ' + channel['authkey']},
                                    json={'guess': guessed_letter, 'timestamp': message_timestamp, 'response': message, 'guesses': GUESSED_LETTERS, 'word': word, 'lives': REMAINING_LIVES})
            
                RANDOM_WORD = random.choice(WORDS)
                GUESSED_LETTERS = []
                REMAINING_LIVES = 6
            
            else:
                message = "The word does indeed include one or more " + str(guessed_letter) + "/s. Keep guessing!"
                message_timestamp = datetime.datetime.now().isoformat()
                response = requests.post(channel['endpoint'],
                                    headers={'Authorization': 'authkey ' + channel['authkey']},
                                    json={'guess': guessed_letter, 'timestamp': message_timestamp, 'response': message, 'guesses': GUESSED_LETTERS, 'word': word, 'lives': REMAINING_LIVES})
            
        if guessed_letter not in RANDOM_WORD:
            REMAINING_LIVES -= 1
            GUESSED_LETTERS.append(guessed_letter)
            word = display_word(RANDOM_WORD, GUESSED_LETTERS)
            
            if REMAINING_LIVES == 0:
                message = "Sadly you lost. The word was " + RANDOM_WORD + ". Guess a new letter to start again!"
                message_timestamp = datetime.datetime.now().isoformat()
                response = requests.post(channel['endpoint'],
                                    headers={'Authorization': 'authkey ' + channel['authkey']},
                                    json={'guess': guessed_letter, 'timestamp': message_timestamp, 'response': message, 'guesses': GUESSED_LETTERS, 'word': word, 'lives': REMAINING_LIVES})
                
                RANDOM_WORD = random.choice(WORDS)
                GUESSED_LETTERS = []
                REMAINING_LIVES = 6
            
            else:
                message = "The word does NOT include a " + str(guessed_letter) + ". Guess again!"
                message_timestamp = datetime.datetime.now().isoformat()
                response = requests.post(channel['endpoint'],
                                    headers={'Authorization': 'authkey ' + channel['authkey']},
                                    json={'guess': guessed_letter, 'timestamp': message_timestamp, 'response': message, 'guesses': GUESSED_LETTERS, 'word': word, 'lives': REMAINING_LIVES})      
    
    else:
        return "No input provided", 400

    # Redirect to show the result and allow for further guessing if necessary
    return redirect(url_for('show_channel')+'?channel='+urllib.parse.quote(post_channel))

def display_word(word, guessed_letters):
    display = ""
    for letter in word:
        if letter in guessed_letters:
            display += letter
        else:
            display += "_ "
    return display

# Start development web server
if __name__ == '__main__':
    RANDOM_NUMBER = random.randint(0, 100)
    WORDS = ["python",
            "hangman",
            "programming",
            "developer",
            "javascript",
            "computer",
            "science",
            "algorithm",
            "coding",
            "software",
            "challenge",
            "intelligence",
            "function",
            "variable",
            "iteration",
            "database",
            "interface",
            "keyboard",
            "monitor",
            "memory",
            "network",
            "router",
            "algorithm",
            "analytics",
            "application",
            "authentication",
            "authorization",
            "cloud",
            "debugging",
            "encryption",
            "framework",
            "integration",
            "optimization",
            "parameter",
            "repository",
            "syntax",
            "template",
            "version",
            "virtualization",
            "website",
            "authentication",
            "bootstrap",
            "cryptography",
            "deployment",
            "efficiency",
            "framework",
            "graphics",
            "hackathon",
            "interface",
            "javascript",
            "knowledge",
            "linux",
            "middleware",
            "networking",
            "opensource",
            "performance",
            "query",
            "recursion",
            "scripting",
            "template",
            "unittest",
            "validation",
            "webpage",
            "workspace",
            "xamarin",
            "youtube",
            "zeppelin",
            "aardvark",
            "barracuda",
            "caterpillar",
            "dolphin",
            "elephant",
            "flamingo",
            "gorilla",
            "hedgehog",
            "iguana",
            "jaguar",
            "kangaroo",
            "leopard",
            "mongoose",
            "narwhal",
            "ocelot",
            "penguin",
            "quokka",
            "raccoon",
            "salamander",
            "toucan",
            "umbrella",
            "vampire",
            "whale",
            "xylophone",
            "yogurt",
            "zeppelin"]
    RANDOM_WORD = random.choice(WORDS)
    GUESSED_LETTERS = []
    REMAINING_LIVES = 6
    app.run(port=5005, debug=True)
