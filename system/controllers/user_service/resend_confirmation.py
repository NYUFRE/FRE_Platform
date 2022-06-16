import warnings

from flask import flash, redirect, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError, SAWarning

from system.services.portfolio.users import send_confirmation_email

warnings.simplefilter(action='ignore', category=SAWarning)


def resend_confirmation_service():
    try:
        send_confirmation_email(current_user.email)
        flash('Email sent to confirm your email address.  Please check your email!', 'success')
    except IntegrityError:
        flash('Error!  Unable to send email to confirm your email address.', 'error')

    return redirect(url_for('user_profile'))