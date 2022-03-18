"""SQLAlchemy models for Friender."""

from datetime import datetime
from flask import jsonify

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    firstname = db.Column(
        db.Text,
        nullable=False,
    )

    lastname = db.Column(
        db.Text,
        nullable=False,
    )

    location = db.Column(
        db.Text,
    )

    image_url = db.Column(
        db.Text,
        default="./public/6525a08f1df98a2e3a545fe2ace4be47.jpeg",
    )

    hobbies = db.Column(
        db.Text,
    )

    interests = db.Column(
        db.Text,
    )

    friendradius = db.Column(
        db.Integer,
    )

    @classmethod
    def signup(cls, username, email, password, firstname, lastname ):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            firstname=firstname,
            lastname=lastname,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

    @classmethod
    def update(cls, username, firstname, lastname, email, location, hobbies, interests, friendradius, image_url):
        """Updates current user"""

        user = cls.query.filter_by(username=username).first()

        if user:
            user.firstname = firstname
            user.lastname = lastname
            user.email = email
            user.location = location
            user.hobbies = hobbies
            user.interests = interests
            user.friendradius = friendradius
            user.image_url = image_url

            db.session.commit()
            return user

    def serialize(self):
        """Serialize to dictionary"""

        return {
            "username": self.username,
            "email": self.email,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "location": self.location or "",
            "hobbies": self.hobbies or "",
            "interests": self.interests or "",
            "friendradius": self.friendradius or 0,
            "image_url": self.image_url,
        }

    @classmethod
    def getAllUsers(cls):
        """Gets all users"""

        users = cls.query.all()

        return users

class Likes(db.Model):
    """Liked users"""

    __tablename__ = 'likes'

    user_swiping = db.Column(
        db.Text,
        db.ForeignKey('users.username', ondelete="cascade"),
        primary_key=True,
    )

    user_being_liked = db.Column(
        db.Text,
        db.ForeignKey('users.username', ondelete="cascade"),
        primary_key=True,
    )

    @classmethod
    def liking(cls, user_swiping, user_being_liked):
        newLike = Likes(user_swiping, user_being_liked)
        db.session.add(newLike)

class Dislikes(db.Model):
    """Disliked users"""

    __tablename__ = 'dislikes'

    user_swiping = db.Column(
        db.Text,
        db.ForeignKey('users.username', ondelete="cascade"),
        primary_key=True,
    )

    user_being_disliked = db.Column(
        db.Text,
        db.ForeignKey('users.username', ondelete="cascade"),
        primary_key=True,
    )

    @classmethod
    def disliking(cls, user_swiping, user_being_disliked):
        newDislike = Dislikes(user_swiping, user_being_disliked)
        db.session.add(newDislike)


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
