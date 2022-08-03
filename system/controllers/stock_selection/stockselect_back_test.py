import warnings

from flask import flash, render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database

from system.services.stock_select.stock_select_back_test import extract_database_mkt, extract_database_rf_10yr, extract_database_stock_10yr, stock_select_back_test


def stockselect_back_test_service(global_param_dict):
    top_stocks_list = global_param_dict["top_stocks_list"]
    if len(top_stocks_list) == 0:
        flash('Please click on "select stock" before run the back test!')
        return render_template("stockselect_introduction.html")
    else:
        top_stocks = []
        res = top_stocks_list
        for i in range(len(res)):
            top_stocks.append(res[i][1])
        mkt_test = extract_database_mkt(database)
        stocks_10yr = extract_database_stock_10yr(database)
        rf = extract_database_rf_10yr(database)
        images_back_test = stock_select_back_test(top_stocks, mkt_test, stocks_10yr, rf)
        return render_template('stockselect_backtest.html', images_back_test=images_back_test)
