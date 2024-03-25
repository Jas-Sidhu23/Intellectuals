from flask import Flask, render_template,request,make_response,send_from_directory,redirect

from pymongo import MongoClient
from bcrypt import gensalt,hashpw
import secrets
from hashlib import sha256
from bson import ObjectId

#Database = MongoClient('localhost')
Database = MongoClient('mongo')
Project = Database['Project']
users_collection = Project['users']
auth_token_collection = Project['auth_token']
chat_collection = Project['chat']

app = Flask(__name__)

@app.route('/')
def index():
    response = make_response(render_template('index.html'),200)
    response.headers["X-Content-Type-Options"] ='nosniff'
    return response

@app.route('/landingpage')
def landingpage():
    cookie = request.cookies.get('auth_token',None)
    messages = chat_collection.find({})
    if cookie!=None:
        check = auth_token_collection.find_one({'token':sha256(cookie.encode()).hexdigest()})
    else:
        check = None
    if(cookie == None or check == None):
        response = make_response(render_template('landingpage.html',prompt='You are not signed in! To make or interact with posts please sign in',msgs=messages),200)
        response.headers["X-Content-Type-Options"] ='nosniff'
        return response
    else:
        response = make_response(render_template('landingpage.html',prompt='You are signed in as: '+check['username'],msgs=messages),200)
        response.headers["X-Content-Type-Options"] ='nosniff'
        return response

@app.route('/<path:filename>')
def send_file(filename):
    response = make_response(send_from_directory('static',filename))
    response.headers["X-Content-Type-Options"] ='nosniff'
    return response

@app.route('/signin',methods=['GET','POST'])
def signin():
    if request.method == 'GET':
        response = make_response(render_template('signin.html'),200)
        response.headers["X-Content-Type-Options"] ='nosniff'
        return response
    else:
        username = request.form.get('username',None)
        password = request.form.get('password',None)
        print(username)
        print(password)
        if username == None or password == None:
            response = make_response(render_template('signin.html'),200)
            response.headers["X-Content-Type-Options"] ='nosniff'
            return response
        else:
            user = users_collection.find_one({'username':username})
            if user !=None:
                password_hashed = hashpw(password.encode(),user['salt'])
                if password_hashed == user['password']:
                    token = secrets.token_hex()
                    auth_token_collection.delete_one({'username':username})
                    auth_token_collection.insert_one({'username':username,'token':sha256(token.encode()).hexdigest()})
                    response = make_response(redirect('/landingpage'))
                    response.set_cookie('auth_token',token,max_age=3600,httponly=True)
                    return response
                else:
                    response = make_response(render_template('signin.html'),200)
                    response.headers["X-Content-Type-Options"] ='nosniff'
                    return response
            else:
                response = make_response(render_template('signin.html'),200)
                response.headers["X-Content-Type-Options"] ='nosniff'
                return response

@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method == 'GET':
        response = make_response(render_template('signup.html'),200)
        response.headers["X-Content-Type-Options"] ='nosniff'
        return response
    else:
        username = request.form.get('username',None)
        password = request.form.get('password1',None)
        password1 = request.form.get('password2',None)
        if username == None or password == None or password1 == None:
            response = make_response(render_template('signup.html'),200)
            response.headers["X-Content-Type-Options"] ='nosniff'
            return response
        elif password1 != password:
            response = make_response(render_template('signup.html'),200)
            response.headers["X-Content-Type-Options"] ='nosniff'
            return response
        else:
            user = users_collection.find_one({'username':username})
            if user != None:
                response = make_response(render_template('signup.html'),200)
                response.headers["X-Content-Type-Options"] ='nosniff'
                return response
            else:
                salt = gensalt()
                password_hashed = hashpw(password.encode(),salt)
                users_collection.insert_one({'username':username,'password':password_hashed,'salt':salt})
                return redirect('/signin')

@app.route('/message',methods=['POST'])
def message():
    message = request.form.get('message')
    title = request.form.get('title')
    cookie = request.cookies.get('auth_token',None)
    if cookie!=None:
        check = auth_token_collection.find_one({'token':sha256(cookie.encode()).hexdigest()})
    else:
        check = None
    if cookie == None or check == None or message == None:
        response = make_response(redirect('/landingpage'))
        return response
    else:
        chat_collection.insert_one({'username':check['username'],'message':message,'replys':[],'title':title})
        response = make_response(redirect('/landingpage'))
        return response

@app.route('/reply',methods=['POST'])
def reply():
    message = request.form.get('message')
    id = request.form.get('msg_id')
    cookie = request.cookies.get('auth_token',None)
    if cookie!=None:
        check = auth_token_collection.find_one({'token':sha256(cookie.encode()).hexdigest()})
    else:
        check = None
    if cookie == None or check == None or message == None:
        response = make_response(redirect('/landingpage'))
        return response
    else:
        chat = chat_collection.find_one({'_id':ObjectId(id)})
        if chat !=None:
            replys = chat['replys']
            replys.append({'username':check['username'],'message':message})
            chat_collection.update_one({'_id':ObjectId(id)},{"$set":{'replys':replys}})
            response = make_response(redirect('/landingpage'))
            return response
        else:
            response = make_response(redirect('/landingpage'))
            return response

app.run(host="0.0.0.0",port=8080)