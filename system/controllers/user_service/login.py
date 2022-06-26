import warnings
from datetime import datetime

from flask import flash, redirect, url_for, render_template, session, request
from flask_login import login_user
from sqlalchemy.exc import SAWarning
from system import db, database, User
from system.services.portfolio.forms import LoginForm
from system.services.sim_trading.client import client_config

warnings.simplefilter(action='ignore', category=SAWarning)


def login_service():
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None and user.is_correct_password(form.password.data):
                user.authenticated = True
                user.last_logged_in = user.current_logged_in
                user.current_logged_in = datetime.now()
                db.session.add(user)
                db.session.commit()
                login_user(user)
                user = database.get_user(request.form.get("email"), '')
                session["user_id"] = user["user_id"]
                client_config.client_id = user['first_name']
                return redirect(url_for('index'))
            else:
                flash('ERROR! Incorrect login credentials.', 'error')
    return render_template('login.html', form=form)