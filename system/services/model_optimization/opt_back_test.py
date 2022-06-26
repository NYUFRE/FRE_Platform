import sys
import pandas as pd
import datetime as dt

from system.services.model_optimization.optimization import get_weights

sys.path.append('../../')

methods = ["max", "min", "max_const", "min_const"]
results = []
start_date = dt.date(2020, 6, 1).strftime('%Y-%m-%d')
end_date = dt.date(2021, 6, 1).strftime('%Y-%m-%d')


def opt_back_testing(database, eod_market_data, tickers):
    """
    Do back test from 2020-06-01 to 2021-06-01
    Extract SPY price data as market benchmark
    Extract the portfolio price data from database
    Calculate the cumulative daily return for SPY and the portfolio
    """
    back_test_start_date = dt.date(2021, 1, 1).strftime('%Y-%m-%d')
    back_test_end_date = dt.date(2021, 7, 1).strftime('%Y-%m-%d')
    database.create_table(["stocks_price_current"])
    database.clear_table(["stocks_price_current"])
    eod_market_data.populate_stock_data(tickers, "stocks_price_current", back_test_start_date, back_test_end_date, 'US')
    cum_ret = []

    spy_select = f"""
                           SELECT date, open, close, adjusted_close
                           FROM spy
                           WHERE Date(date) BETWEEN Date('{back_test_start_date}') AND Date('{back_test_end_date}') 
                           """
    spy_df = database.execute_sql_statement(spy_select)
    spy_df = spy_df.set_index('date')
    spy_df.index = pd.to_datetime(spy_df.index)
    spy_df["daily_return"] = spy_df["adjusted_close"].pct_change()
    spy_df = spy_df.iloc[1:]
    spy_df["cum_daily_return"] = spy_df["daily_return"].cumsum()
    cum_ret.append('{:.2f}'.format(spy_df["cum_daily_return"].iloc[-1] * 100))

    stock_select = f"""
                    SELECT date, open, close
                    FROM stocks_price_current
                    WHERE Date(date) BETWEEN Date('{back_test_start_date}') AND Date('{back_test_end_date}') 
                    AND symbol = ('{tickers[0]}');
                    """
    stocks_df = database.execute_sql_statement(stock_select)
    stocks_df = stocks_df.set_index('date')
    stocks_df.index = pd.to_datetime(stocks_df.index)
    stocks_df = stocks_df.drop(columns='close')
    stocks_df = stocks_df.drop(columns='open')

    for ticker in tickers:
        stock_select = f"""
                            SELECT date, close, open, adjusted_close
                            FROM stocks_price_current
                            WHERE Date(date) BETWEEN Date('{back_test_start_date}') AND Date('{back_test_end_date}') 
                            AND symbol = ('{ticker}');
                            """
        stock = database.execute_sql_statement(stock_select)
        stocks_df[ticker] = (stock["adjusted_close"].pct_change()).values.tolist()
    stocks_df = stocks_df.iloc[1:]
    return_df = stocks_df
    return_df = return_df.drop(columns=tickers)
    weights = get_weights()
    for i in range(len(methods)):
        return_df["daily_ret_" + methods[i]] = (weights[i] * stocks_df).sum(axis=1)
        return_df["cum_ret_" + methods[i]] = return_df["daily_ret_" + methods[i]].cumsum()
        cum_ret.append('{:.2f}'.format(return_df["cum_ret_" + methods[i]].iloc[-1] * 100))
    results.append(return_df)
    results.append(spy_df)
    return cum_ret


def get_results():
    return results


def get_dates():
    return start_date, end_date
