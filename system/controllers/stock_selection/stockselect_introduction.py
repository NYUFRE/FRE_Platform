import warnings

from flask import flash, render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def stockselect_introduction_service():
    flash("When you click 'select stock', the model will run to select stocks, which will take over 2 hours, please wait...")
    return render_template("stockselect_introduction.html")