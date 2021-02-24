# -*- coding: utf-8 -*
# !/usr/bin/env python3

import sys

sys.path.append('../')

import datetime as dt
import holidays
from system.ai_modeling.ga_portfolio import GAPortfolio, Stock, Trade
from system.ai_modeling.ga_portfolio_select import extract_spy, extract_us10y
from typing import Tuple

fund = 1000000

#database = FREDatabase()
#eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

#TODO Need to modify, don't return previous working day if current date is a working day
def previous_working_day(check_day_, holidays=holidays.US()):
    offset = max(1, (check_day_.weekday() + 6) % 7 - 3)
    most_recent = check_day_ - dt.timedelta(offset)
    if most_recent not in holidays:
        return most_recent
    else:
        return previous_working_day(most_recent, holidays)

probation_testing_start_date = (dt.date(2020, 6, 30) + dt.timedelta(days=1)).strftime('%Y-%m-%d')
probation_testing_end_date = (dt.date(2021, 2, 19)).strftime('%Y-%m-%d')
# probation_testing_end_date = previous_working_day(dt.date(2020, 8, 1)).strftime('%Y-%m-%d')

def ga_probation_test(database) -> Tuple[GAPortfolio, float, int]:
    """
    description:
        Do probation test from 2020-07-01 till today
    ---------------------------
    return:
        best_portfolio, spy_profit_loss, fund: Tuple[GAPortfolio, float, int]
    """
    # Extract best portfolio's data from table best_portfolio
    best_portfolio_select = "SELECT symbol, sector, category_pct from best_portfolio;"
    best_portfolio_df = database.execute_sql_statement(best_portfolio_select)
    best_portfolio_symbols = list(best_portfolio_df['symbol'])

    # Extract stock price data from table stocks
    stock_select = "SELECT stocks.symbol, stocks.date, stocks.open, stocks.close, sp500.name, sp500_sectors.category_pct AS weight\
                    FROM stocks, sp500, sp500_sectors\
                    WHERE stocks.symbol = sp500.symbol\
                    AND sp500.sector = sp500_sectors.sector\
                    AND strftime(\'%Y-%m-%d\', date) BETWEEN \"" + probation_testing_start_date + "\" AND \"" + \
                    probation_testing_end_date + "\" AND open > 0 AND close > 0;"
    price_df = database.execute_sql_statement(stock_select)

    best_portfolio = GAPortfolio()
    best_portfolio.populate_portfolio_by_symbols(best_portfolio_symbols, price_df)  # Calculate returns

    # Update table best_portfolio
    conn = database.engine.connect()
    for symbol in best_portfolio_symbols:
        open_date = probation_testing_start_date
        close_date = probation_testing_end_date
        # open_price = best_portfolio.stocks[i].trades[probation_testing_start_date].adjusted_close
        # close_price = best_portfolio.stocks[i].trades[probation_testing_end_date].adjusted_close
        df_slice = best_portfolio.price_df[best_portfolio.price_df.symbol == symbol]
        open_price = df_slice['open'].iloc[0]
        close_price = df_slice['close'].iloc[-1]
        shares = int(fund * best_portfolio.price_df[best_portfolio.price_df.symbol == symbol]['weight'].iloc[0] / open_price)
        profit_loss = (close_price - open_price) * shares
        best_portfolio.profit_loss += profit_loss

        update_stmt = "UPDATE best_portfolio SET open_date = \"" + str(open_date) + "\", open_price = " + str(open_price) + ", close_date = \"" + \
                      str(close_date) + "\", close_price = " + str(close_price) + ", shares = " + str(shares) + ", profit_loss = " + str(round(profit_loss, 2)) + \
                      " WHERE symbol = \"" + symbol + "\";"
        print(update_stmt)
        conn.execute(update_stmt)

    # make SPY captical in spy table
    spy_select = "SELECT date, open, close FROM spy WHERE strftime(\'%Y-%m-%d\', date) " \
                "BETWEEN \"" + probation_testing_start_date + "\" AND \"" + probation_testing_end_date + \
                "\" AND open > 0 AND close > 0 AND symbol = 'spy';"
    spy_df = database.execute_sql_statement(spy_select)

    spy_open_price = spy_df.open.iloc[0]
    spy_close_price = spy_df.close.iloc[-1]
    spy_shares = int(fund / spy_open_price)
    spy_profit_loss = (spy_close_price - spy_open_price) * spy_shares

    print("Probabtion Test:")
    print("best portfolio return: %4.2f%%" % (float(best_portfolio.profit_loss / fund) * 100))
    print("spy return: %4.2f%%" % (float(spy_profit_loss / fund) * 100))

    return best_portfolio, spy_profit_loss, fund
