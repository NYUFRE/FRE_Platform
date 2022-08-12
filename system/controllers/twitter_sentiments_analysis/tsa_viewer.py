import warnings

from flask import render_template, request, flash
from sqlalchemy.exc import SAWarning
from system.services.twitter_sentiment_analysis.tsa_service import tsa_res

warnings.simplefilter(action='ignore', category=SAWarning)

def tsa_viewer_service():

    spot_ = 0.0
    pdlist_curve1 = ['MSFT', 'LikesCount']
    pdlist_curve2 = ['MSFT', 'LikesCount']

    if request.method == "POST":
        spot_input = request.form.get('spot')
        spot_ = int(spot_input) + 1
        tsa_res.demo_deg = spot_
        return render_template("tsa_viewer.html", spot = spot_, pdlist_curve1 = pdlist_curve1, pdlist_curve2 = pdlist_curve2)
    else:
        return render_template("tsa_viewer.html", spot = spot_, pdlist_curve1 = pdlist_curve1, pdlist_curve2 = pdlist_curve2)
