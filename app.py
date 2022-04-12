from flask import Flask, request, jsonify
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Likes, Dislikes
from flask_cors import CORS
import os

"""Boto3 imports"""
from botocore.exceptions import ClientError
import boto3
import logging

database_url = os.environ['DATABASE_URL']
database_url = database_url.replace('postgres://', 'postgresql://')

app = Flask(__name__)
CORS(app)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     os.environ['DATABASE_URL'].replace("postgres://", "postgresql://"))


app.config['SQLALCHEMY_DATABASE_URI'] = database_url
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
    
    """CR - Backend - Better to be explicit instead of destructure. Could be used by other people/bad actors"""
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

    bucket_name = os.environ.get('BUCKET_NAME')
    region = os.environ.get('REGION')
    object_key = f"{username}-profile-image"

    upload_file(image_file, bucket_name, object_key)

    #Look at getting presigned URL
    image_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_key}"

    """Request.files --> Pull image --> Send image to S3 --> Pull URL from that S3 instance --> image_url = s3_url for database"""

    #Move to top of function. Should be authorizing user first. Return error/unauth/etc.
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

@app.route('/cards', methods=["GET"])
def get_all_users():
    """Gets all users from database"""

    allUsers = User.getAllUsers()

    serializedUsers = [user.serialize() for user in allUsers]

    serialized = {"users": serializedUsers}

    return (jsonify(serialized), 200)

@app.route('/like', methods=["POST"])
def like_user():
    """CurrentUser likes current card user"""

    user_swiping=request.json["user_swiping"]
    user_being_liked=request.json["user_being_liked"]

    Likes.liking(user_swiping, user_being_liked)

    db.session.commit()

    return "Friend Liked"

@app.route('/dislike', methods=["POST"])
def dislike_user():
    """CurrentUser dislikes current card user"""
    
    user_swiping=request.json["user_swiping"]
    user_being_disliked=request.json["user_being_disliked"]

    Dislikes.disliking(user_swiping, user_being_disliked)

    db.session.commit()

    return "Friend Disliked"

@app.route('/alllikes/<user>', methods=['GET'])
def get_all_likes(user):
    """Get all likes for current user"""

    print("Got to alllikes/user in python app.py")
    allLikes = Likes.getAllLikes(user)

    serializedLikes = [like.serialize() for like in allLikes]
    # serialized = {"likes": serializedLikes}

    return (jsonify(serializedLikes), 200)

@app.route('/alldislikes/<user>', methods=['GET'])
def get_all_dislikes(user):
    """Get all dislikes for current user"""

    allDislikes = Dislikes.getAllDislikes(user)

    serializedDislikes = [dislike.serialize() for dislike in allDislikes]
    # serialized = {"dislikes": serializedDislikes}

    return (jsonify(serializedDislikes), 200)

#Move function to another file
def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False

    CR - First parameter should probably be 'file'
    """

    # If S3 object_name was not specified, use file_name
    # CR commented out during CR, probably not needed.
    # if object_name is None:
    #     object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_fileobj(file_name, bucket, object_name)
        print("RESPONSE FROM S3", response)
    except ClientError as e:
        #CR See if this is logging anywhere. Verify what its doing.
        logging.error(e)
        return False
    return True