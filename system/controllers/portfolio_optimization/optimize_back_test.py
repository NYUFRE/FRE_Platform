import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

from system.services.model_optimization.opt_back_test import opt_back_testing
from system.services.model_optimization.optimization import get_ticker

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database, eod_market_data


def optimize_back_test_service():
    tickers = get_ticker()
    cum_return = opt_back_testing(database, eod_market_data, tickers)
    return render_template('optimize_back_test.html', cum_return=cum_return)