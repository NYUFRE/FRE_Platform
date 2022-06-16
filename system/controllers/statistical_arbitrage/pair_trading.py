import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

from system.services.sim_trading.client import client_config

warnings.simplefilter(action='ignore', category=SAWarning)


def pair_trading_service():
    return render_template("pair_trading.html", done_pair_trade_model=client_config.done_pair_model)