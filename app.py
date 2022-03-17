from flask import Flask, request, jsonify
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User
from flask_cors import CORS

"""Boto3 imports"""
from botocore.exceptions import ClientError
import boto3
import os
import logging

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


@app.route('/profile', methods=["PATCH"])
def update():
    """Handles updating user from profile and adds image to s3 bucket"""
    
    username = request.form["username"]
    password = request.form["password"]
    email = request.form["email"]
    firstname = request.form["firstname"]
    lastname = request.form["lastname"]
    location = request.form["location"]
    hobbies = request.form["hobbies"]
    interests = request.form["interests"]
    friendradius = request.form["friendradius"]

    image_file = request.files["image_url"]

    bucket_name = "r24practicebucket"
    region = "us-west-1"
    object_key = f"{username}-profile-image"

    upload_file(image_file, bucket_name, object_key)

    image_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_key}"

    """Request.files --> Pull image --> Send image to S3 --> Pull URL from that S3 instance --> image_url = s3_url for database"""

    try:
        user = User.authenticate(username, password)
    except IntegrityError:
        print("USER AUTH FAILED")

    if user:
        try:
            updateduser = User.update(
                username,
                firstname,
                lastname,
                email,
                location,
                hobbies,
                interests,
                friendradius,
                image_url)
            
            serialized = updateduser.serialize()
            return (jsonify(user=serialized), 200)
            
        except IntegrityError:
            print("UPDATE USER FAILED")

    else:
        return "Could not update user"


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_fileobj(file_name, bucket, object_name)
        print("RESPONSE FROM S3", response)
    except ClientError as e:
        logging.error(e)
        return False
    return True