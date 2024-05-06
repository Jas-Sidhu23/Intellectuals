from flask import Flask, render_template, request, redirect, make_response, send_from_directory, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import os
from pymongo import MongoClient
from bcrypt import gensalt, hashpw
import secrets
from hashlib import sha256
from flask import jsonify
from bson import ObjectId
import logging
from datetime import datetime, timedelta
import threading
from html import escape as html_escape
from collections import defaultdict, deque

Database = MongoClient('mongo')
Project = Database['Project']
users_collection = Project['users']
auth_token_collection = Project['auth_token']
chat_collection = Project['chat']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
active_users = {}

REQUEST_LIMIT = 50
TIME_WINDOW = timedelta(seconds=10)
BLOCK_DURATION = timedelta(seconds=30)

request_counts = defaultdict(lambda: deque())
blocked_ips = {}


def get_client_ip():
    ip = request.headers.get('CF-Connecting-IP')
    if not ip:
        ip = request.headers.get('X-Forwarded-For').split(',')[0] if 'X-Forwarded-For' in request.headers else request.remote_addr
    return ip


def is_ip_blocked(ip):
    return ip in blocked_ips and datetime.now() < blocked_ips[ip]

@app.before_request
def rate_limit():
    ip = get_client_ip()
    now = datetime.now()

    if is_ip_blocked(ip):
        response = make_response("Too Many Requests", 429)
        response.headers["Retry-After"] = int(BLOCK_DURATION.total_seconds())
        return response

    request_log = request_counts[ip]

    while request_log and now - request_log[0] > TIME_WINDOW:
        request_log.popleft()

    request_log.append(now)

    if len(request_log) > REQUEST_LIMIT:
        blocked_ips[ip] = now + BLOCK_DURATION
        request_counts.pop(ip, None)
        response = make_response("Too Many Requests", 429)
        response.headers["Retry-After"] = int(BLOCK_DURATION.total_seconds())
        return response

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_active_time(user_id):
    user = auth_token_collection.find_one({"_id": user_id})
    if user and 'login_time' in user:
        login_time = user['login_time']
        if isinstance(login_time, str):
            login_time = datetime.strptime(login_time, '%Y-%m-%dT%H:%M:%S.%f')
        return (datetime.now() - login_time).total_seconds()
    return 0

def broadcast_active_times():
    while True:
        active_times = {username: calculate_active_time(user['_id']) for username, user in active_users.items()}
        socketio.emit('active_times', active_times)
        socketio.sleep(1)

@app.route('/logout')
def logout():
    cookie = request.cookies.get('auth_token')
    if cookie:
        user = auth_token_collection.find_one({'token': sha256(cookie.encode()).hexdigest()})
        if user:
            auth_token_collection.find_one_and_delete({'_id': user['_id']})
            active_users.pop(user['username'], None)
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
            msgs = [{'username': html_escape(msg['username']), 'message': html_escape(msg['message'])} for msg in messages]
            return make_response(render_template('landingpage.html', prompt='You are signed in as: ' + check['username'], msgs=msgs))
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
            login_time = datetime.now()
            auth_token_collection.insert_one({
                'username': username,
                'token': sha256(token.encode()).hexdigest(),
                'login_time': login_time
            })
            active_users[username] = {'_id': user['_id'], 'login_time': login_time}
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

@app.route('/get_username', methods=['POST'])
def get_username():
    token = request.json.get('token')
    user = auth_token_collection.find_one({'token': sha256(token.encode()).hexdigest()})
    if user:
        return jsonify({'username': user['username']})
    else:
        return jsonify({'error': 'Username not found'}), 404

@socketio.on('connect')
def handle_connect():
    token = request.args.get('token')
    if not token or token == "null":
        emit('error', {'error': 'Authentication failed'})
        return
    user = auth_token_collection.find_one({'token': sha256(token.encode()).hexdigest()})
    if user:
        join_room(user['username'])
        active_users[user['username']] = user
        emit('connection_response', {'message': 'Connected as ' + user['username']})
    else:
        emit('error', {'error': 'Authentication failed'})
        return

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('post_message')
def handle_post_message(data):
    token = request.args.get('token')
    if not token:
        emit('error', {'error': 'No token provided'})
        return

    user_info = auth_token_collection.find_one({'token': sha256(token.encode()).hexdigest()})
    if not user_info:
        emit('error', {'error': 'Authentication failed'})
        return

    username = user_info['username']
    message = html_escape(data['message'])
    image_data = data.get('image')
    
    if image_data:
        filename = secure_filename(image_data['filename'])
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(image_path, 'wb') as f:
            f.write(image_data['content'])
        chat_collection.insert_one({
            'username': username,
            'message': message,
            'replies': [],
            'image_path': f'images/{filename}'
        })
        emit('new_message', {'username': username, 'message': message, 'image_path': image_path}, broadcast=True)
    else:
        chat_collection.insert_one({
            'username': username,
            'message': message,
            'replies': [],
            'image_path': None
        })
        emit('new_message', {'username': username, 'message': message, 'image_path': None}, broadcast=True)

@socketio.on('send_reply')
def handle_send_reply(data):
    chat_id = data.get('chat_id')
    message = data.get('message')
    token = request.args.get('token')

    if not token:
        emit('error', {'error': 'No token provided'})
        return

    user_info = auth_token_collection.find_one({'token': sha256(token.encode()).hexdigest()})
    if not user_info:
        emit('error', {'error': 'Authentication failed'})
        return

    username = user_info['username']
    chat = chat_collection.find_one({'_id': ObjectId(chat_id)})

    if not chat:
        emit('error', {'error': 'Chat not found'})
        return

    replies = chat.get('replies', [])
    replies.append({'username': username, 'message': message})
    update_result = chat_collection.update_one({'_id': ObjectId(chat_id)}, {"$set": {'replies': replies}})

    if update_result.modified_count == 0:
        emit('error', {'error': 'Failed to update chat'})
        return

    emit('reply_posted', {'chat_id': chat_id, 'username': username, 'message': message, 'replies': replies}, broadcast=True)

if __name__ == '__main__':
    threading.Thread(target=broadcast_active_times).start()
    socketio.run(app, host="0.0.0.0", port=8080, allow_unsafe_werkzeug=True)
