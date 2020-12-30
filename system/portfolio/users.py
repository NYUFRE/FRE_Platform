#################
#### imports ####
#################

from flask import render_template, url_for
from flask_mail import Message
from threading import Thread
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.exc import SQLAlchemyError
from system import app, mail, db
from system.portfolio.models import User


def add_admin_user():
    # drop all of the existing database tables
    ###db.drop_all()
    '''
    try:
        num_rows_deleted = User.query.delete()
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()

    # create the database and the database table
    db.create_all()
    '''

    try:
        admin_user = User(email='stangny@gmail.com', plaintext_password='123456', role='admin')
        db.session.add(admin_user)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()



def send_async_email(msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, text_body, html_body):
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    thr = Thread(target=send_async_email, args=[msg])
    thr.start()


# def send_email(subject, recipients, text_body, html_body):
#    msg = Message(subject, recipients=recipients)
#    msg.body = text_body
#    msg.html = html_body
#    mail.send(msg)


def send_confirmation_email(user_email):
    confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    confirm_url = url_for(
        'confirm_email',
        token=confirm_serializer.dumps(user_email, salt='email-confirmation-salt'),
        _external=True)

    html = render_template(
        'email_confirmation.html',
        confirm_url=confirm_url)

    send_email('Confirm Your Email Address', [user_email], 'confirm your email address', html)


def send_password_reset_email(user_email):
    password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    password_reset_url = url_for(
        'reset_with_token',
        token=password_reset_serializer.dumps(user_email, salt='password-reset-salt'),
        _external=True)

    html = render_template(
        'email_password_reset.html',
        password_reset_url=password_reset_url)

    send_email('Password Reset Requested', [user_email], 'Reset password email', html)
