from flask import Flask, render_template, request, redirect, make_response, send_from_directory, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import os
from pymongo import MongoClient
from bcrypt import gensalt, hashpw
import secrets
from hashlib import sha256
from bson import ObjectId
import logging

# Database configuration
Database = MongoClient('mongo')
Project = Database['Project']
users_collection = Project['users']
auth_token_collection = Project['auth_token']
chat_collection = Project['chat']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/logout')
def logout():
    cookie = request.cookies.get('auth_token')
    if cookie:
        auth_token_collection.find_one_and_delete({'token': sha256(cookie.encode()).hexdigest()})
    response = make_response(redirect('/landingpage'))
    response.set_cookie('auth_token', "", max_age=0)
    return response

@app.route('/')
def index():
    return make_response(render_template('index.html'))

@app.route('/landingpage')
def landingpage():
    cookie = request.cookies.get('auth_token')
    messages = chat_collection.find({})
    if cookie:
        check = auth_token_collection.find_one({'token': sha256(cookie.encode()).hexdigest()})
        if check:
            return make_response(render_template('landingpage.html', prompt='You are signed in as: ' + check['username'], msgs=messages))
    return make_response(render_template('landingpage.html', prompt='You are not signed in! To make or interact with posts please sign in', msgs=messages))

@app.route('/<path:filename>')
def send_file(filename):
    return make_response(send_from_directory('static', filename))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return make_response(render_template('signin.html'))
    username = request.form.get('username')
    password = request.form.get('password')
    if username and password:
        user = users_collection.find_one({'username': username})
        if user and hashpw(password.encode(), user['salt']) == user['password']:
            token = secrets.token_hex()
            auth_token_collection.delete_one({'username': username})
            auth_token_collection.insert_one({'username': username, 'token': sha256(token.encode()).hexdigest()})
            response = make_response(redirect('/landingpage'))
            response.set_cookie('auth_token', token, max_age=3600, httponly=False)
            return response
    return make_response(render_template('signin.html'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return make_response(render_template('signup.html'))
    username = request.form.get('username')
    password = request.form.get('password1')
    password1 = request.form.get('password2')
    if username and password and password1 and password == password1:
        if not users_collection.find_one({'username': username}):
            salt = gensalt()
            password_hashed = hashpw(password.encode(), salt)
            users_collection.insert_one({'username': username, 'password': password_hashed, 'salt': salt})
            return redirect('/signin')
    return make_response(render_template('signup.html'))

@socketio.on('connect')
def handle_connect():
    token = request.args.get('token')
    logging.info(f"Attempting to connect with token: {token}")
    if not token or token == "null":
        logging.error("No valid token provided, disconnecting.")
        emit('error', {'error': 'Authentication failed'})
        disconnect()
    else:
        user = auth_token_collection.find_one({'token': sha256(token.encode()).hexdigest()})
        if user:
            join_room(user['username'])
            emit('connection_response', {'message': 'Connected as ' + user['username']})
            logging.info("User connected successfully.")
        else:
            logging.error("Invalid token, disconnecting.")
            emit('error', {'error': 'Authentication failed'})
            disconnect()

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('post_message')
def handle_post_message(data):
    username = data['username']
    message = data['message']
    image_data = data.get('image')
    
    if image_data:
        # Handle the case where image data is provided
        filename = secure_filename(image_data['filename'])
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(image_path, 'wb') as f:
            f.write(image_data['content'])
        chat_collection.insert_one({
            'username': username,
            'message': message,
            'replies': [],
            'image_path': image_path
        })
        emit('new_message', {'username': username, 'message': message, 'image_path': image_path}, broadcast=True)
    else:
        # Handle the case where no image is provided
        chat_collection.insert_one({
            'username': username,
            'message': message,
            'replies': [],
            'image_path': None
        })
        emit('new_message', {'username': username, 'message': message, 'image_path': None}, broadcast=True)

@socketio.on('send_reply')
def handle_send_reply(data):
    chat_id = data['chat_id']
    message = data['message']
    username = data['username']
    chat = chat_collection.find_one({'_id': ObjectId(chat_id)})
    if chat:
        replies = chat.get('replies', [])
        replies.append({'username': username, 'message': message})
        chat_collection.update_one({'_id': ObjectId(chat_id)}, {"$set": {'replies': replies}})
        emit('reply_posted', {'chat_id': chat_id, 'replies': replies}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=8080, allow_unsafe_werkzeug=True)
