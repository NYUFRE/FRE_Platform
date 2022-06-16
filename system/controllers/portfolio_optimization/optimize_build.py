import warnings

from flask import flash, render_template
from sqlalchemy.exc import SAWarning

from system.services.model_optimization.optimization import find_optimal_min_constraint, find_optimal_max_constraint, \
    find_optimal_vol, find_optimal_sharpe, extract_database_rf, extract_database_stock, get_ticker, \
    create_database_table

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database, eod_market_data


def optimize_build_service():
    try:
        create_database_table(database, eod_market_data)
        tickers = get_ticker()
        length = len(tickers)
        stocks = extract_database_stock(database)
        print(stocks)
        rf = extract_database_rf(database)
        max_sharpe = find_optimal_sharpe(stocks, rf)
        min_vol = find_optimal_vol(stocks, rf)
        max_const = find_optimal_max_constraint(stocks, rf)
        min_const = find_optimal_min_constraint(stocks, rf)
        return render_template('optimize_build.html', max_sharpe=max_sharpe, min_vol=min_vol, max_const=max_const,
                               min_const=min_const, length=length, tickers=tickers)
    except ValueError:
        flash('Error! Portfolio has poor data quality, unable to optimize, please change the portfolio and try again!')
        return render_template("optimize_introduction.html")