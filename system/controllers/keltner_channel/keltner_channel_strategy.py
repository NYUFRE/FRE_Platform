import warnings

from flask import flash, render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def keltner_channel_strategy_service():
    flash("When you click 'Build Model', it will take about 20 minutes to run, please be patient...")
    return render_template("keltner_channel_strategy.html")