import sys
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt import objective_functions
from pypfopt import CLA
from pypfopt import HRPOpt

import datetime as dt
import pandas as pd
import numpy as np

sys.path.append('../../')

start_date = dt.date(2010, 1, 4).strftime('%Y-%m-%d')
end_date = dt.date(2020, 1, 4).strftime('%Y-%m-%d')

tickers = ['BAC', 'NFLX', 'AFL', 'BBY', 'C', 'T', 'AAPL', 'AMZN', 'AXP', 'TMUS', 'SHY', 'VGSH', 'TLT', 'IEF']
weights_results = []
sector_mapper = {'BAC': 'stocks',
                 'NFLX': 'stocks',
                 'AFL': 'stocks',
                 'BBY': 'stocks',
                 'C': 'stocks',
                 'T': 'stocks',
                 'AAPL': 'stocks',
                 'AMZN': 'stocks',
                 'AXP': 'stocks',
                 'TMUS': 'stocks',
                 'SHY': 'bonds',
                 'VGSH': 'bonds',
                 'TLT': 'bonds',
                 'IEF': 'bonds'}
sector_lower = {'stocks': 0.7, 'bonds': 0.3}
sector_upper = {'stocks': 0.7, 'bonds': 0.3}


def get_ticker():
    return tickers


def create_database_table(database, eod_market_data):
    """
    Create the database tables that stores the prices data.
    """
    tables = ['stocks_price', 'us10y']
    database.create_table(tables)
    database.clear_table(tables)
    eod_market_data.populate_stock_data(tickers, "stocks_price", start_date, end_date, 'US')
    eod_market_data.populate_stock_data(['US10Y'], "us10y", start_date, end_date, 'INDX')


def extract_database_rf(database):
    """
    Extract the us10y price data from the database to calculate the average risk free rate.
    """
    stock_select = f"""
                    SELECT date, adjusted_close
                    FROM us10y
                    WHERE Date(date) BETWEEN Date('{start_date}') AND Date('{end_date}');
                    """
    rf_df = database.execute_sql_statement(stock_select)
    rf_df = rf_df.set_index('date')
    rf_df.index = pd.to_datetime(rf_df.index)
    rf_df['rf'] = rf_df['adjusted_close'] / 100
    rf_mean = rf_df['rf'].mean()
    return rf_mean


def extract_database_stock(database):
    """
    Extract the price data for each asset in the portfolio
    Store them in to dataframe
    """
    stock_select = f"""
                SELECT date, adjusted_close
                FROM stocks_price
                WHERE Date(date) BETWEEN Date('{start_date}') AND Date('{end_date}') AND symbol = ('{tickers[0]}');
                """
    stocks_df = database.execute_sql_statement(stock_select)
    stocks_df = stocks_df.set_index('date')
    stocks_df.index = pd.to_datetime(stocks_df.index)

    stocks_df[tickers[0]] = stocks_df['adjusted_close']
    stocks_df = stocks_df.drop(columns='adjusted_close')

    for ticker in tickers:
        stock_select = f"""
            SELECT adjusted_close
            FROM stocks_price
            WHERE Date(date) BETWEEN Date('{start_date}') AND Date('{end_date}') AND symbol = ('{ticker}');
            """
        stock = database.execute_sql_statement(stock_select)
        stocks_df[ticker] = stock['adjusted_close'].values.tolist()
    return stocks_df


def find_optimal_sharpe(stocks_df, rf):
    """
    This algorithm finds the optimal portfolio that maximize the Sharpe Ratio
    """
    ret = expected_returns.mean_historical_return(stocks_df)
    vol = risk_models.sample_cov(stocks_df)
    ef = EfficientFrontier(ret, vol)
    ef.add_sector_constraints(sector_mapper, sector_lower, sector_upper)
    ef.add_objective(objective_functions.L2_reg)
    ef.max_sharpe(risk_free_rate=rf)
    cleaned_weights = ef.clean_weights()
    portfolio_ret, portfolio_vol, sharpe_ratio = ef.portfolio_performance(risk_free_rate=rf)
    weights_results.append(cleaned_weights)

    portfolio_ret = '{:.2f}'.format(portfolio_ret * 100)
    portfolio_vol = '{:.2f}'.format(portfolio_vol * 100)
    sharpe_ratio = '{:.2f}'.format(sharpe_ratio)
    weights = {}
    for ticker in tickers:
        weights[ticker] = '{:.2f}'.format(cleaned_weights[ticker]*100)
    results = [weights, portfolio_ret, portfolio_vol, sharpe_ratio]
    return results


def find_optimal_vol(stocks_df, rf):
    """
    This algorithm optimize the portfolio that has the minimum portfolio volatility
    """
    ret = expected_returns.mean_historical_return(stocks_df)
    vol = risk_models.sample_cov(stocks_df)
    ef = EfficientFrontier(ret, vol)
    ef.add_sector_constraints(sector_mapper, sector_lower, sector_upper)
    ef.add_objective(objective_functions.L2_reg)
    ef.min_volatility()
    cleaned_weights = ef.clean_weights()
    weights_results.append(cleaned_weights)
    portfolio_ret, portfolio_vol, sharpe_ratio = ef.portfolio_performance(risk_free_rate=rf)

    portfolio_ret = '{:.2f}'.format(portfolio_ret * 100)
    portfolio_vol = '{:.2f}'.format(portfolio_vol * 100)
    sharpe_ratio = '{:.2f}'.format(sharpe_ratio)
    weights = {}
    for ticker in tickers:
        weights[ticker] = '{:.2f}'.format(cleaned_weights[ticker]*100)
    results = [weights, portfolio_ret, portfolio_vol, sharpe_ratio]
    return results


def find_optimal_cla(stocks_df, rf):
    """
    This algorithm doesn't support sector map, so it's not used on the current model
    """
    ret = expected_returns.mean_historical_return(stocks_df)
    vol = risk_models.sample_cov(stocks_df)
    cla = CLA(ret, vol)
    cla.max_sharpe()
    cleaned_weights = cla.clean_weights()
    portfolio_ret, portfolio_vol, sharpe_ratio = cla.portfolio_performance(risk_free_rate=rf)
    weights = ['{:.2f}'.format(float(item)) for item in cleaned_weights]
    results = [weights, portfolio_ret, portfolio_vol, sharpe_ratio]
    return results


def find_optimal_hrp(stocks_df, rf):
    """
    This algorithm doesn't support sector map, so it's not used on the current model
    """
    ret = stocks_df.pct_change().dropna()
    hrp = HRPOpt(ret)
    hrp.optimize()
    cleaned_weights = hrp.clean_weights()
    portfolio_ret, portfolio_vol, sharpe_ratio = hrp.portfolio_performance(risk_free_rate=rf)
    weights_results.append(cleaned_weights)
    weights = ['{:.2f}'.format(float(item)) for item in cleaned_weights]
    results = [weights, portfolio_ret, portfolio_vol, sharpe_ratio]
    return results


def find_optimal_max_constraint(stocks_df, rf):
    """
    This algorithm find the optimal portfolio that maximize the Sharpe Ratio with constraint that none of the ticker can
    have more than 30% weights for its own type.
    """
    ret = expected_returns.mean_historical_return(stocks_df)
    vol = risk_models.sample_cov(stocks_df)
    ef = EfficientFrontier(ret, vol)

    max_stock_weight = 0.3  # 0.3 of the 0.7
    total_stock_weight = 0.7
    max_bond_weight = 0.3
    total_bond_weight = 0.3

    max_weight = []
    for ticker in tickers:
        if sector_mapper[ticker] == "stocks":
            max_weight.append(max_stock_weight * total_stock_weight)
        elif sector_mapper[ticker] == "bonds":
            max_weight.append(max_bond_weight * total_bond_weight)

    ef.add_constraint(lambda x: x <= np.array(max_weight))
    ef.add_objective(objective_functions.L2_reg)
    ef.max_sharpe()
    cleaned_weights = ef.clean_weights()
    portfolio_ret, portfolio_vol, sharpe_ratio = ef.portfolio_performance(risk_free_rate=rf)
    weights_results.append(cleaned_weights)

    portfolio_ret = '{:.2f}'.format(portfolio_ret * 100)
    portfolio_vol = '{:.2f}'.format(portfolio_vol * 100)
    sharpe_ratio = '{:.2f}'.format(sharpe_ratio)
    weights = {}
    for ticker in tickers:
        weights[ticker] = '{:.2f}'.format(cleaned_weights[ticker]*100)
    results = [weights, portfolio_ret, portfolio_vol, sharpe_ratio]
    return results


def find_optimal_min_constraint(stocks_df, rf):
    """
    This algorithm find the optimal portfolio that minimize the volatility with constraint that none of the ticker can
    have more than 30% weights for its own type.
    """
    ret = expected_returns.mean_historical_return(stocks_df)
    vol = risk_models.sample_cov(stocks_df)
    ef = EfficientFrontier(ret, vol)

    max_stock_weight = 0.3  # 0.3 of the 0.7
    total_stock_weight = 0.7
    max_bond_weight = 0.3
    total_bond_weight = 0.3

    max_weight = []
    for ticker in tickers:
        if sector_mapper[ticker] == "stocks":
            max_weight.append(max_stock_weight * total_stock_weight)
        elif sector_mapper[ticker] == "bonds":
            max_weight.append(max_bond_weight * total_bond_weight)

    ef.add_constraint(lambda x: x <= np.array(max_weight))
    ef.add_objective(objective_functions.L2_reg)
    ef.min_volatility()
    cleaned_weights = ef.clean_weights()
    portfolio_ret, portfolio_vol, sharpe_ratio = ef.portfolio_performance(risk_free_rate=rf)
    weights_results.append(cleaned_weights)

    portfolio_ret = '{:.2f}'.format(portfolio_ret * 100)
    portfolio_vol = '{:.2f}'.format(portfolio_vol * 100)
    sharpe_ratio = '{:.2f}'.format(sharpe_ratio)
    weights = {}
    for ticker in tickers:
        weights[ticker] = '{:.2f}'.format(cleaned_weights[ticker]*100)
    results = [weights, portfolio_ret, portfolio_vol, sharpe_ratio]
    return results


def get_weights():
    return weights_results
