# FRE_Platform/portfolio/forms.py

from system import db
from system import bcrypt
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method 
from datetime import datetime


class User(db.Model):
 
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    _password = db.Column(db.Binary(60), nullable=False)
    authenticated = db.Column(db.Boolean, default=False)
    email_confirmed = db.Column(db.Boolean, nullable=True, default=False)
    email_confirmed_on = db.Column(db.DateTime, nullable=True)
    registered_on = db.Column(db.DateTime, nullable=True)
    last_logged_in = db.Column(db.DateTime, nullable=True)
    current_logged_in = db.Column(db.DateTime, nullable=True)
    cash = db.Column(db.Numeric, nullable=False, default='10000.00')
    role = db.Column(db.String, default='user')
 
    def __init__(self, email, first_name, last_name, plaintext_password, role='user', cash='10000.00'):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self._password = bcrypt.generate_password_hash(plaintext_password)
        self.authenticated = False
        self.email_confirmed = False
        self.email_confirmed_on = None
        self.registered_on = datetime.now()
        self.last_logged_in = None
        self.current_logged_in = datetime.now()
        self.cash = cash
        self.role = role	

    @hybrid_property
    def password(self):
        return self._password
 
    @password.setter
    def set_password(self, plaintext_password):
        self._password = bcrypt.generate_password_hash(plaintext_password)
 
    @hybrid_method
    def is_correct_password(self, plaintext_password):
        return bcrypt.check_password_hash(self.password, plaintext_password)

    @property
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated
 
    @property
    def is_active(self):
        """Always True, as all users are active."""
        return True
 
    @property
    def is_anonymous(self):
        """Always False, as anonymous users aren't supported."""
        return False
 
    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        """Requires use of Python 3"""
        return str(self.user_id)
 
    def __repr__(self):
        return '<User {0}>'.format(self.user_id)

