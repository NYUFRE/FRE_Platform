import warnings

from flask import render_template, session
from sqlalchemy.exc import SAWarning
from system import database

warnings.simplefilter(action='ignore', category=SAWarning)


def history_service():
    uid = session["user_id"]
    # Extract transaction record from transactions table
    transactions = database.get_transaction(uid)
    length = len(transactions['symbol'])
    return render_template("history.html", length=length, dict=transactions)