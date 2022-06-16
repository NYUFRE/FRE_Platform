import warnings

from flask import flash, render_template
from sqlalchemy.exc import SAWarning

from system.services.stock_select.stock_select import extract_database_stock_10yr, extract_database_rf_10yr, \
    extract_database_sector, build_model_predict_select

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database


def stockselect_build_service():
    try:
        stocks_10yr = extract_database_stock_10yr(database)
        rf = extract_database_rf_10yr(database)
        sector = extract_database_sector(database)
        global top_stocks_list
        top_stocks_list = build_model_predict_select(stocks_10yr, rf, sector)
        length = len(top_stocks_list)

        return render_template('stockselect_build.html', length=length, top_stocks=top_stocks_list)

    except ValueError:
        flash('Error! There is something wrong about the database, unable to select stocks, please contact IT!')
        return render_template("stockselect_introduction.html")