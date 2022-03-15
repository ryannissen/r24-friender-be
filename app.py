from flask import Flask, request, jsonify
import os
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     os.environ['DATABASE_URL'].replace("postgres://", "postgresql://"))
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///r24_friender'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'secret'

connect_db(app)
db.create_all()

@app.route('/signup', methods=["POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB
    """

    username = request.json["username"]
    password = request.json["password"]
    email = request.json["email"]
    firstname = request.json["firstname"]
    lastname = request.json["lastname"]

    try:
        user = User.signup(
            username=username,
            password=password,
            email=email,
            firstname=firstname,
            lastname=lastname,
        )
        print(user)
        db.session.commit()

    except IntegrityError:
        return "Username or email already exist"

    serialized = user.serialize()

    """Serialize/Jsonify our return object"""
    return (jsonify(user=serialized), 201)

@app.route('/login', methods=["POST"])
def login():
    """Handle user login."""

    username = request.json["username"]
    password = request.json["password"]

    user = User.authenticate(username, password)

    if user:
        serialized = user.serialize()
        return (jsonify(user=serialized), 200)

    else:
        return "Incorrect username/password"

