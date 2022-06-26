import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def ai_modeling_service():
    return render_template("ai_modeling.html")