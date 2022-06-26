import warnings
from datetime import datetime
from flask import flash, redirect, url_for, session
from flask_login import login_user
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.exc import SAWarning
from system import app, db, database
from system.services.portfolio.users import User
from system.services.sim_trading.client import client_config

warnings.simplefilter(action='ignore', category=SAWarning)


def confirm_email_service(token):
    try:
        confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = confirm_serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
    except:
        flash('The confirmation link is invalid or has expired.', 'error')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()

    if user.email_confirmed:
        flash('Account already confirmed. Please login.', 'info')
    else:
        user.email_confirmed = True
        user.email_confirmed_on = datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('Thank you for confirming your email address!')

        login_user(user)
        user = database.get_user(email, '')
        session["user_id"] = user["user_id"]
        client_config.client_id = user['first_name']

    return redirect(url_for('index'))