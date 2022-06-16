import warnings

from flask import flash, redirect, url_for, session
from flask_login import current_user, logout_user
from sqlalchemy.exc import SAWarning
from system import db
from system.services.sim_trading.client import client_config

warnings.simplefilter(action='ignore', category=SAWarning)


def logout_service():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    flash('Goodbye!', 'info')
    session.clear()
    client_config.done_pair_model = "pointer-events:none;color:grey;"
    return redirect(url_for('login'))