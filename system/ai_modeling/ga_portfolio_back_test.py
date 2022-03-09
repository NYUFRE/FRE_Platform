# -*- coding: utf-8 -*
# !/usr/bin/env python3

import sys

sys.path.append('../')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd 

import datetime as dt
from typing import Tuple

from system.ai_modeling.ga_portfolio import GAPortfolio, Stock, Trade
from system.ai_modeling.ga_portfolio_select import extract_spy, extract_us10y


class GABackTestResult:
    def __init__(self):
        self.bt_start_date = ""
        self.bt_end_date = ""
        self.portfolio_cum_rtn = {}
        self.spy_cum_rtn = {}


ga_back_test_result = GABackTestResult()


def ga_back_test(database, start, end) -> Tuple[GAPortfolio, Stock]:
    """
    Do backtest; Calculate cumulative return of best_portfolio and spy

    :param database: 
    :type database: 
    :return: best_portfolio, spy
    :rtype: Tuple[GAPortfolio, Stock]
    """    
    back_testing_start_date = start
    back_testing_end_date = end

    # Extract best portfolio's data from table best_portfolio
    best_portfolio_select = "SELECT symbol, sector, category_pct from best_portfolio;"
    best_portfolio_df = database.execute_sql_statement(best_portfolio_select)
    best_portfolio_symbols = list(best_portfolio_df['symbol'])

    # Extract stock price data from table stocks
    stock_select = f"""
        SELECT stocks.symbol, stocks.date, stocks.open, stocks.close, sp500.name, sp500_sectors.category_pct AS weight
        FROM stocks
            JOIN sp500
                ON stocks.symbol = sp500.symbol
            JOIN sp500_sectors
                ON sp500.sector = sp500_sectors.sector
        WHERE Date(date) BETWEEN Date('{back_testing_start_date}') AND Date('{back_testing_end_date}')
            AND open > 0 
            AND close > 0;
    """
    price_df = database.execute_sql_statement(stock_select)

    best_portfolio = GAPortfolio()
    best_portfolio.populate_portfolio_by_symbols(best_portfolio_symbols, price_df)  # Calculate returns
    
    spy = extract_spy(database, back_testing_start_date, back_testing_end_date, include_fundamental=False)
    spy.price_df['date'] = pd.to_datetime(spy.price_df['date'])
    spy.price_df.set_index('date', inplace=True)
    
    print("Back Test:")
    print("best portfolio cumulative return: %4.2f%%" % (best_portfolio.cumulative_return*100))
    print("spy cumulative return: %4.2f%%" % (spy.cumulative_return*100))
    return best_portfolio, spy


def ga_back_test_plot(database, start, end) -> None:
    best_portfolio, spy = ga_back_test(database, start, end)
    portfolio_ys = list(best_portfolio.portfolio_daily_cumulative_returns)
    spy_ys = list(spy.price_df['spy_daily_cumulative_return'])
    n = len(portfolio_ys)

    fig, ax = plt.subplots()
    line = np.zeros(n)
    t = range(n)
    ax.plot(t, portfolio_ys[0:n], 'ro')
    ax.plot(t, spy_ys[0:n], 'bd')
    ax.plot(t, line, 'b')
    plt.figtext(0.2, 0.8, "Red - Portfolio, Blue - SPY")
    plt.xlim(1, n)
    ax.set(xlabel="Date",
           ylabel="Cumulative Returns",
           title="Portfolio Back Test (" + start + " to " + end + ")",
           xlim=[0, n])

    ax.grid(True)
    fig.autofmt_xdate()

    plt.show()
