import time
import warnings

from flask import flash, redirect, url_for, render_template, session, request
from sqlalchemy.exc import SAWarning

from system import database, iex_market_data
from system.services.VaR.VaR_Calculator import VaR
from system.services.utility.helpers import usd

warnings.simplefilter(action='ignore', category=SAWarning)


def fixed_income_build_ptfl_service():
    uid = session['user_id']
    saved_bond = database.get_saved_bonds(uid)
    return render_template("fixed_income_ptfl.html", res=saved_bond)