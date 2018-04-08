#from google.appengine.ext import vendor
#vendor.add('lib')
from flask import Flask, request, jsonify, make_response
#needed for front and backend to work together
from flask_cors import CORS
import flask
import flask_login
import os
import json
import sys
import os
#import MySQLdb
import logging
# from app import db
from app import app,db
from model import User, Envelope, Image, History
from sqlalchemy import func
from hashlib import md5
from itsdangerous import URLSafeTimedSerializer


logging.getLogger('flask_cors').level = logging.DEBUG
CORS(app)

app.secret_key = 'snapsend_rocks'
login_serializer = URLSafeTimedSerializer(app.secret_key)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

#Our mock database.

class User_Class(flask_login.UserMixin):
  def __init__(self, userid, password):
    self.id = userid
    self.password = password


  def get_auth_token(self):
    #Encode a secure token for cookie
    data = [str(self.id), self.password]
    return login_serializer.dumps(data)


  @staticmethod
  def get(email):
        # Static method to search the database and see if userid exists.  If it 
        # does exist then return a User Object.  If not then return None as 
        # required by Flask-Login. 
        #For this example the USERS database is our Users table

    try:
      user_tuple=User.query.filter_by(email=email).first()
      return User_Class(user_tuple.email,user_tuple.password)
    except:
      return None


def hash_envid(envid):
	target = md5(str(envid).encode('utf-8')).hexdigest()[0:10].upper()
	return target

def hash_pass(password):
    #Return the md5 hash of the password+salt
    salted_password = password + app.secret_key
    return md5(salted_password).hexdigest()[0:50]


@login_manager.request_loader
def load_token(token):
    """
    Flask-Login token_loader callback. 
    The token_loader function asks this function to take the token that was 
    stored on the users computer process it to check if its valid and then 
    return a User Object if its valid or None if its not valid.
    """
 
    #The Token itself was generated by User.get_auth_token.  So it is up to 
    #us to known the format of the token data itself.  
 
    #The Token was encrypted using itsdangerous.URLSafeTimedSerializer which 
    #allows us to have a max_age on the token itself.  When the cookie is stored
    #on the users computer it also has a exipry date, but could be changed by
    #the user, so this feature allows us to enforce the exipry date of the token
    #server side and not rely on the users cookie to exipre. 

    # max_age = app.config["REMEMBER_COOKIE_DURATION"].total_seconds()
 
    #Decrypt the Security Token, data = [username, hashpass]
    data = login_serializer.loads(token)
 
    #Find the User
    user = User_Class.get(data[0])
    # print("inside token function")
    # print()
 
    #Check Password and return user or None
    if user and data[1].lower().strip() == user.password.lower().strip():
        return user
    return None



@login_manager.user_loader
def load_user(email):
    """
    Flask-Login user_loader callback.
    The user_loader function asks this function to get a User Object or return 
    None based on the userid.
    The userid was stored in the session environment by Flask-Login.  
    user_loader stores the returned User object in current_user during every 
    flask request. 
    """
    return User_Class.get(email)




@login_manager.request_loader
def request_loader(request):
  email = request.form.get('email')
  if email not in users:
      return

  user = User()
  user.id = email

  user.is_authenticated = request.form['password'] == users[email]['password']
  return user



@app.route('/login', methods=['POST'])
def login():
  if request.method == 'POST':
    loaded_r = request.get_json()
    r = json.dumps(loaded_r)
    loaded_r = json.loads(r)

    email = loaded_r['email']
    pwd = loaded_r['password']
    new_pwd = hash_pass(pwd)

    user_tuple=User.query.filter_by(email=email).first()
    curr_pwd = user_tuple.password

    if new_pwd.lower().strip() == curr_pwd.lower().strip():
      user = User_Class(email,new_pwd)
      flask_login.login_user(user)
      some_token = user.get_auth_token()
      user_tuple.token = some_token
      db.session.commit()
      
      loaded_r = {
                  "token" : some_token
                  }
      return return_success(loaded_r,True)
    else:

      loaded_r = {"error" : "Possible incorrect password"}
      return return_success(loaded_r,False)


@app.route('/signup', methods=['POST'])
def signup():
  if request.method == 'POST':
    loaded_r = request.get_json()
    r = json.dumps(loaded_r)
    loaded_r = json.loads(r)

    curr_email = loaded_r['email']
    pwd1 = loaded_r['password1']
    pwd2 = loaded_r['password2']
    user_name = loaded_r['username']
    profile_picture = loaded_r['profilepic'] 
    print profile_picture

    try:
      hashed_pwd = hash_pass(pwd1)
      user_obj = User_Class(curr_email,hashed_pwd)
      flask_login.login_user(user_obj)
      some_token = user_obj.get_auth_token()
      new_user = User(user_name, curr_email, hashed_pwd, some_token, profile_picture)
    
      db.session.add(new_user)
      db.session.commit()

      loaded_r = {
                  "token" : some_token 
                  }
      return return_success(loaded_r,True)


    except:
      loaded_r = {
                  "error" : "Signup failed"
                  }

      return return_success(loaded_r,False)

#       #return flask.redirect(flask.url_for('signup'))
#     #return flask.redirect(flask.url_for('protected'))


@app.route('/protected')
@flask_login.login_required
def protected():
  return 'Logged in as: ' + flask_login.current_user.id


@app.route('/logout', methods=['POST'])
def logout():
  loaded_r = request.get_json()
  r = json.dumps(loaded_r)
  loaded_r = json.loads(r)
  tkn = loaded_r['token']
  loaded_usr = load_token(tkn)

  loaded_r = {}

  if(loaded_usr):
    email = loaded_usr.id
    user_tuple=User.query.filter_by(email=email).first()

    user_tuple.token = None
    db.session.commit()
    flask_login.logout_user()
    return return_success(loaded_r,True)
  
  else:
    return return_success(loaded_r,False)



@login_manager.unauthorized_handler
def unauthorized_handler():
  loaded_r = {"error":"Unauthorized User"}
  payload = json.dumps(loaded_r)
  response = make_response(payload)
  response.headers['Content-Type'] = 'text/json'
  return response



@app.route('/helloworld')
def index():
  return "Hello, World"



@app.route('/envelope', methods=['POST'])
def postenvelope():
  loaded_r = request.get_json()
  # r = json.dumps(loaded_r)
  # loaded_r = json.loads(r)
  env_name = loaded_r['envelopeName']
  rec_name = loaded_r['recipientName']
  sender_name = loaded_r['senderName']
  all_images = loaded_r['images']
  token = loaded_r['token']

  j= db.session.query(func.max(Envelope.envelopeID)).scalar()
  h = hash_envid(j+1)
  if token == "":
    newenvelope = Envelope(env_name,sender_name,rec_name,h)
    newenvelope.eowner = None
    db.session.add(newenvelope)
    db.session.commit()

  else:
    result = db.session.query(User).filter(User.token==token).first()
    newenvelope = Envelope(env_name,sender_name,rec_name,h)
    newenvelope.eowner = result.userID
    db.session.add(newenvelope)
    db.session.commit()
  
  try:
    for i in range(len(all_images)):
      curr_dict = all_images[i]
      b = curr_dict['url']
      c = curr_dict['filename']
      image = Image(str(j+1),b,c)
      db.session.add(image)
      db.session.commit()

  except Exception as e:
    raise e
  #loaded_r['envelopeID'] = j
  
  #j= db.session.query(func.max(Envelope.envelopeID)).scalar()
  #result = db.session.query(Envelope).filter(Envelope.envelopeID==j).first()
  loaded_r['handle'] = h
  return return_success(loaded_r,True)
  


@app.route('/envelope/<handle>', methods=['GET'])
def getenvelope(handle):
  # loaded_r = {"handle": handle}
  # r = json.dumps(loaded_r)
  # loaded_r = json.loads(r)
  # handle = loaded_r['handle']
  result = db.session.query(Envelope).filter(Envelope.handle==handle).first()
  envid = result.envelopeID
  imgres = db.session.query(Image).filter(Image.inenvID==envid).all()
  payload = ""
  env_out = {}
  try:
  	env_out = {
  	    "handle": handle,
  	    "envelopeName": result.ename,
  	    "recipientName": result.recipient,
  	    "senderName": result.sender
  	    
  	}

  	img_arr = []
  	img_out = {}

  	for imgs in imgres:
  	  img_out = {"imageId": imgs.imageID, "url": imgs.imagelink, "filename": imgs.filename}
  	  img_arr.append(img_out)
  	  img_out = {}

  	payload = env_out
  	payload["images"] = img_arr

  	
  	return return_success(payload,True)

  except Exception as e:
  	raise e

#@flask_login.login_required
@app.route('/profile/<token>',methods=['GET'])
def profile(token):
  pay = ""
  payload ={}
  result1 = db.session.query(User).filter(User.token==token).first()
  payload = {"uname":result1.uname,"profilepic":result1.profilepic,"email":result1.email}
  
  result2 = db.session.query(Envelope).filter(Envelope.eowner==result1.userID).all()
  envelopes = []
  envs = {}

  for env in result2:
    envs = {"handle":env.handle,"sender":env.sender,"recipient":env.recipient, "ename":env.ename}
    result3 = db.session.query(Image).filter(Image.inenvID==env.envelopeID).all()
    img_out = {}
    img_arr = []
    for img in result3:
      img_out = {"imageId": img.imageID, "url": img.imagelink, "filename": img.filename}
      img_arr.append(img_out)
      img_out = {}
    envs["images"] = img_arr
    
    result4 = db.session.query(History).filter(History.envelopeID==env.envelopeID).all()
    hist_out = {}
    hist_arr =[]
    for hist in result4:

      hist_out={"act_type":hist.act_type,"dnum":hist.dnum,"actiondate":hist.actiondate}
      hist_arr.append(hist_out)
      hist_out={}
    envs["history"] = hist_arr
    
    envelopes.append(envs)
    envs = {}

  payload["envelope"]=envelopes
  
  return return_success(payload,True)


@app.route('/history',methods=['POST'])
def history():
  loaded_r = request.get_json()
  r = json.dumps(loaded_r)
  loaded_r = json.loads(r)
  token = loaded_r['token']
  handle = loaded_r['handle']
  action = loaded_r['action']
  dnum = loaded_r['dnum']

  result1 = db.session.query(User).filter(User.token==token).first()

  result = db.session.query(Envelope).filter(Envelope.handle==handle).first()
  envid = result.envelopeID
  history = History(envid,action,result1.userID,dnum)
  db.session.add(history)
  db.session.commit()
  
  response = return_success({},True)
  response.headers['Content-Type'] = 'text/json'
  response.headers['Access-Control-Allow-Origin'] = '*'
  return response

def return_success(loaded_r,j):
  loaded_r['success'] = j
  payload = json.dumps(loaded_r)
  response = make_response(payload)
  return response
