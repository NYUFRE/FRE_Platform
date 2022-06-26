import warnings

from flask import render_template, request
from sqlalchemy.exc import SAWarning

from system.controllers.simulated_trading.sim_auto_trading import sim_auto_trading_service

warnings.simplefilter(action='ignore', category=SAWarning)


def sim_choose_strat_service():
    if request.method == "POST":
        strategy = request.form.get('strategy')
        return sim_auto_trading_service(strategy)
        # return redirect(url_for("sim_auto_trading"),strategy)

        # TODO warning takes 30 minutes , also warning server not up
    else:
        return render_template("sim_choose_strat.html")