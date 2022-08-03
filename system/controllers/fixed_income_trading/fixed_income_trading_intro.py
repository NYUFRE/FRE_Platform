import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning
from system import database, eod_market_data


warnings.simplefilter(action='ignore', category=SAWarning)


def fixed_income_service():
    eod_market_data.populate_bond_list()
    database.create_table(['saved_bond', 'saved_bond_ptfl'])
    return render_template("fixed_income_trading.html")