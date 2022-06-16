import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def hf_trading_service():
    return render_template("hf_trading.html")