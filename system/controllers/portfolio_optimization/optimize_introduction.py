import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def optimize_introduction_service():
    return render_template("optimize_introduction.html")