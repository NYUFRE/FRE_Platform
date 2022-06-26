import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def pair_ai_introduction_service():
    return render_template("pair_ai_introduction.html")