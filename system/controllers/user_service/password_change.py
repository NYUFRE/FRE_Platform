import warnings

from flask import flash, redirect, url_for, render_template, request
from flask_login import current_user
from sqlalchemy.exc import SAWarning
from system import db, bcrypt
from system.services.portfolio.forms import PasswordForm

warnings.simplefilter(action='ignore', category=SAWarning)


def password_change_service():
    form = PasswordForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = current_user
            user._password = bcrypt.generate_password_hash(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Password has been updated!', 'success')
            return redirect(url_for('user_profile'))

    return render_template('password_change.html', form=form)