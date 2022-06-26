import warnings

from flask import flash, redirect, url_for, render_template
from sqlalchemy.exc import SAWarning

from system import User
from system.services.portfolio.forms import EmailForm
from system.services.portfolio.users import send_password_reset_email

warnings.simplefilter(action='ignore', category=SAWarning)


def reset_service():
    form = EmailForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first_or_404()
        except:
            flash('Invalid email address!', 'error')
            return render_template('password_reset_email.html', form=form)

        if user.email_confirmed:
            send_password_reset_email(user.email)
            flash('Please check your email for a password reset link.', 'success')
        else:
            flash('Your email address must be confirmed before attempting a password reset.', 'error')
        return redirect(url_for('login'))

    return render_template('password_reset_email.html', form=form)