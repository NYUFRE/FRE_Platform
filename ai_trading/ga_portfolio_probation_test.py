# -*- coding: utf-8 -*
# !/usr/bin/env python3

import sys

sys.path.append('../')

import datetime as dt
import holidays

from market_data.fre_market_data import EODMarketData
from database.fre_database import FREDatabase
from ai_trading.ga_portfolio import *

database = FREDatabase()
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

#TODO Need to modify, don't return previous working day if current date is a working day
def previous_working_day(check_day_, holidays=holidays.US()):
    offset = max(1, (check_day_.weekday() + 6) % 7 - 3)
    most_recent = check_day_ - dt.timedelta(offset)
    if most_recent not in holidays:
        return most_recent
    else:
        return previous_working_day(most_recent, holidays)

probation_testing_start_date = (dt.date(2020, 6, 30) + dt.timedelta(days=1)).strftime('%Y-%m-%d')
# probation_testing_end_date = previous_working_day(dt.datetime.today()).strftime('%Y-%m-%d')
probation_testing_end_date = previous_working_day(dt.date(2020, 8, 1)).strftime('%Y-%m-%d')

best_portfolio = GAPortfolio()

best_portfolio_select = "SELECT symbol, sector, category_pct from best_portfolio;"
print(best_portfolio_select)
stock_df = database.execute_sql_statement(best_portfolio_select)
for index, stock_row in stock_df.iterrows():
    stock = Stock()
    stock.symbol = stock_row['symbol']
    stock.sector = stock_row['sector']
    stock.category_pct = stock_row['category_pct']
    stock_select = "SELECT * FROM stocks WHERE strftime(\'%Y-%m-%d\', date) " \
                   "BETWEEN \"" + probation_testing_start_date + "\" AND \"" + probation_testing_end_date + \
                   "\" AND open > 0 AND close > 0 AND symbol = \'" + stock.symbol + "\';"
    print(stock_select)
    price_df = database.execute_sql_statement(stock_select)
    if price_df.empty:
        exit("probation testing price_df is empty")
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

conn = database.engine.connect()

for i in range(len(best_portfolio.stocks)):
    open_date = probation_testing_start_date
    close_date = probation_testing_end_date
    open_price = best_portfolio.stocks[i].trades[probation_testing_start_date].adjusted_close
    close_price = best_portfolio.stocks[i].trades[probation_testing_end_date].adjusted_close
    shares = int(fund * best_portfolio.stocks[i].category_pct/open_price)
    profit_loss = (close_price - open_price) * shares
    best_portfolio.stocks[i].probation_test_trade.open_date = open_date
    best_portfolio.stocks[i].probation_test_trade.close_date = close_date
    best_portfolio.stocks[i].probation_test_trade.open_price = open_price
    best_portfolio.stocks[i].probation_test_trade.close_price = close_price
    best_portfolio.stocks[i].probation_test_trade.shares = shares
    best_portfolio.stocks[i].probation_test_trade.profit_loss = profit_loss

    update_stmt = "UPDATE best_portfolio SET open_date = \"" + str(open_date) + "\", open_price = " + str(open_price) + ", close_date = \"" + \
                  str(close_date) + "\", close_price = " + str(close_price) + ", shares = " + str(shares) + ", profit_loss = " + str(round(profit_loss, 2)) + \
                  " WHERE symbol = \"" + best_portfolio.stocks[i].symbol + "\";"
    print(update_stmt)
    conn.execute(update_stmt)

best_portfolio.calculate_profit_loss()


spy = Stock()
spy.symbol = 'SPY'

# make SPY captical in spy table
spy_select = "SELECT * FROM spy WHERE strftime(\'%Y-%m-%d\', date) " \
            "BETWEEN \"" + probation_testing_start_date + "\" AND \"" + probation_testing_end_date + \
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

spy.probation_test_trade.open_date = probation_testing_start_date
spy.probation_test_trade.close_date = probation_testing_end_date
spy.probation_test_trade.open_price = spy.trades[probation_testing_start_date].open
spy.probation_test_trade.close_price = spy.trades[probation_testing_end_date].close
spy.probation_test_trade.shares = int(fund / spy.probation_test_trade.open_price)
spy.probation_test_trade.profit_loss = (spy.probation_test_trade.close_price - spy.probation_test_trade.open_price) * \
                                       spy.probation_test_trade.shares

print("Probabtion Test:")
print("best portfolio return: %4.2f%%" % (float(best_portfolio.profit_loss / fund) * 100))
print("spy return: %4.2f%%" % (float(spy.probation_test_trade.profit_loss / fund) * 100))
