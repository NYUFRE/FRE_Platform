# -*- coding: utf-8 -*
# !/usr/bin/env python3

import sys

sys.path.append('../')

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import numpy as np

import io

import datetime as dt

from market_data.fre_market_data import EODMarketData
from database.fre_database import FREDatabase
from ai_trading.ga_portfolio import *

#database = FREDatabase()
#eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

back_testing_start_date = dt.date(2020, 1, 1).strftime('%Y-%m-%d')
back_testing_end_date = dt.date(2020, 6, 30).strftime('%Y-%m-%d')

best_portfolio = GAPortfolio()

spy = Stock()
spy.symbol = 'SPY'

def ga_back_test():
    best_portfolio_select = "SELECT symbol, sector, category_pct from best_portfolio;"
    print(best_portfolio_select)
    stock_df = database.execute_sql_statement(best_portfolio_select)
    for index, stock_row in stock_df.iterrows():
        stock = Stock()
        stock.symbol = stock_row['symbol']
        stock.sector = stock_row['sector']
        stock.category_pct = stock_row['category_pct']
        stock_select = "SELECT * FROM stocks WHERE strftime(\'%Y-%m-%d\', date) " \
                        "BETWEEN \"" + back_testing_start_date + "\" AND \"" + back_testing_end_date + \
                       "\" AND open > 0 AND close > 0 AND symbol = \'" + stock.symbol + "\';"
        print(stock_select)
        price_df = database.execute_sql_statement(stock_select)
        if price_df.empty:
            exit("back testing price_df is empty")
        for index, trade_row in price_df.iterrows():
            trade = Trade()
            trade.date = trade_row['date']
            trade.open = trade_row['open']
            trade.high = trade_row['high']
            trade.low = trade_row['low']
            trade.close = trade_row['close']
            trade.adjusted_close = trade_row['adjusted_close']
            trade.volume = trade_row['volume']
            stock.add_trade(trade)

        stock.calculate_daily_return()
        best_portfolio.stocks.append(stock)

    best_portfolio.calculate_portfolio_daily_return()
    #est_portfolio.calculate_cumulative_return(back_testing_start_date, back_testing_end_date)
    best_portfolio.calculate_daily_cumulative_return(back_testing_start_date, back_testing_end_date)

    # make SPY captical in spy table
    spy_select = "SELECT * FROM spy WHERE strftime(\'%Y-%m-%d\', date) " \
                "BETWEEN \"" + back_testing_start_date + "\" AND \"" + back_testing_end_date + \
                "\" AND open > 0 AND close > 0 AND symbol = 'spy';"
    print(spy_select)
    price_df = database.execute_sql_statement(spy_select)

    for index, row in price_df.iterrows():
        trade = Trade()
        trade.date = row['date']
        trade.open = row['open']
        trade.high = row['high']
        trade.low = row['low']
        trade.close = row['close']
        trade.adjusted_close = row['adjusted_close']
        trade.volume = row['volume']
        spy.add_trade(trade)

    spy.calculate_daily_return()
    spy.calculate_daily_cumulative_return(back_testing_start_date, back_testing_end_date)

    print("Back Test:")
    print("best portfolio cumulative return: %4.2f%%" % (best_portfolio.cumulative_return*100))
    print("spy cumulative return: %4.2f%%" % (spy.cumulative_return*100))

def ga_back_test_plot():
    portfolio_ys = list(best_portfolio.portfolio_daily_cumulative_returns.values())
    spy_ys = list(spy.daily_cumulative_returns.values())
    n = len(best_portfolio.portfolio_daily_cumulative_returns.keys())
    #xs = list(best_portfolio.portfolio_daily_cumulative_returns.keys())
    '''
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Portfolio Back Test Cumulative Daily Return")
    axis.set_xlabel("Date")
    axis.grid(True)
    
    axis.plot(xs, portfolio_ys)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    #response = make_response(output.getvalue())
    #response.mimetype = 'image/png'
    #return response
    '''
    fig, ax = plt.subplots()
    line = np.zeros(n)
    t = range(n)
    ax.plot(t, portfolio_ys[0:n], 'ro')
    ax.plot(t, spy_ys[0:n], 'bd')
    ax.plot(t, line, 'b')
    #ax.plot(xs, portfolio_ys[0:n], 'ro')
    #ax.plot(xs, spy_ys[0:n], 'bd')
    #ax.plot(xs, line, 'b')
    plt.figtext(0.2, 0.8, "Red - Portfolio, Blue - SPY")
    #plt.xlim("2020-01-01", "2020-06-30")
    plt.xlim(1, n)
    ax.set(xlabel="Date",
           ylabel="Cumulative Returns",
           title="Portfolio Back Test (2020-01-01 to 2020-06-30)",
           xlim=[0, n])

    #date_from = DateFormatter('%Y-%m-%d')
    #ax.xaxis.set_major_formatter(date_from)
    #ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=3))
    ax.grid(True)
    fig.autofmt_xdate()

    plt.show()

    '''
    line = np.zeros(n)
    plt.plot(xs, ys[0:n], 'ro')
    #plt.plot(t, ret2[0:n], 'bd')
    plt.plot(xs, line, 'b')
    plt.figtext(0.4, 0.8, "Red for Google, Blue for S&P500")
    plt.xlim(1, n)
    plt.ylim(-0.10, 0.10)
    plt.title("Comparison between stock and market returns")
    plt.xlabel("Day")
    plt.ylabel("Returns")
    plt.show()
    '''