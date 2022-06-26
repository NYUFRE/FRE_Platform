import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def ei_introduction_service():
    return render_template("ei_introduction.html")