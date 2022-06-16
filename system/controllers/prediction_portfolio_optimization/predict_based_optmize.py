import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def predict_based_optimize_service():
    return render_template("Predict_based_optmize.html")