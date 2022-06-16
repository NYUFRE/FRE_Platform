import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def ap_introduction_service():
    return render_template("ap_introduction.html")