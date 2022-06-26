import warnings

from flask import flash, redirect, url_for, render_template, request
from flask_login import login_user
from sqlalchemy.exc import IntegrityError, SAWarning
from system import db, User
from system.services.portfolio.forms import RegisterForm
from system.services.portfolio.users import send_confirmation_email

warnings.simplefilter(action='ignore', category=SAWarning)


def register_service():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                new_user = User(form.email.data, form.first_name.data, form.last_name.data, form.password.data)
                new_user.authenticated = True
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                send_confirmation_email(new_user.email)
                flash('Thanks for registering!  Please check your email to confirm your email address.', 'success')
                return redirect(url_for('login'))
            except IntegrityError:
                db.session.rollback()
                flash('ERROR! Email ({}) already exists.'.format(form.email.data), 'error')
    return render_template('register.html', form=form)