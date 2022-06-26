import warnings
from flask import abort, redirect, url_for, render_template
from flask_login import current_user
from sqlalchemy.exc import SAWarning
from system.services.portfolio.users import User

warnings.simplefilter(action='ignore', category=SAWarning)


def admin_view_users_service():
    if current_user.role != 'admin':
        abort(403)
    else:
        users = User.query.order_by(User.id).all()
        return render_template('admin_view_users.html', users=users)
    return redirect(url_for('user_profile'))