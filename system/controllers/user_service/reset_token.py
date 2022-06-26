import warnings

from flask import flash, redirect, url_for, render_template
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.exc import IntegrityError, SAWarning
from system import app, db, bcrypt, User
from system.services.portfolio.forms import PasswordForm

warnings.simplefilter(action='ignore', category=SAWarning)


def reset_token_service(token):
    try:
        password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))

    form = PasswordForm()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=email).first_or_404()
        except IntegrityError:
            flash('Invalid email address!', 'error')
            return redirect(url_for('login'))

        user._password = bcrypt.generate_password_hash(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password_with_token.html', form=form, token=token)