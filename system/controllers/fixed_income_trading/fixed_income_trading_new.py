import time
import warnings


from flask import flash, redirect, url_for, render_template, session, request
from sqlalchemy.exc import SAWarning

from system import database, iex_market_data, eod_market_data
from system.services.VaR.VaR_Calculator import VaR
from system.services.utility.helpers import usd

warnings.simplefilter(action='ignore', category=SAWarning)


def fixed_income_trading_new_service():
    sug_bonds_list = []
    if request.method == "POST":
        keyword = request.form.get('symbol').upper()
        month = request.form.get('month')
        year = request.form.get('year')
        if not keyword:
            flash('ERROR! Bond name can not be blank.', 'error')
            return render_template("fixed_income_trading_new.html", res=sug_bonds_list)

        sug_bonds_list = database.get_bonds_suggest(keyword, month, year)
        if(len(sug_bonds_list)>0):
            return render_template("fixed_income_trading_new.html", res=sug_bonds_list)
        else:
            flash('ERROR! Bond not found.', 'error')
            return render_template("fixed_income_trading_new.html", res=sug_bonds_list)
    return render_template("fixed_income_trading_new.html", res=sug_bonds_list)