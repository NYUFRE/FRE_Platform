import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def sim_model_info_service():
    return render_template("sim_model_info.html")