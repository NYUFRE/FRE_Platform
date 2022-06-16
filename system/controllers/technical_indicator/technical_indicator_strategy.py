import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def technical_indicator_strategy_service():
    return render_template("technical_indicator_strategy.html")