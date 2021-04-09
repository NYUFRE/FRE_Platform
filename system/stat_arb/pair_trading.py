# -*- coding: utf-8 -*
# !/usr/bin/env python3
import sys

sys.path.append('../')

import os
import datetime as dt
import pandas as pd
import numpy as np

import statsmodels.tsa.stattools as st
from itertools import combinations
import statsmodels.api as sm

from sqlalchemy import and_

from flask import Flask

from system.market_data.fre_market_data import EODMarketData
from system.database.fre_database import FREDatabase

from typing import Collection, List, Union

#start_date = dt.date(2020, 1, 1).strftime('%Y-%m-%d')
#end_date = dt.datetime.today().strftime('%Y-%m-%d')

#back_testing_start_date = dt.date(2020, 8, 1).strftime('%Y-%m-%d')
#back_testing_end_date = dt.date(2020, 9, 15).strftime('%Y-%m-%d')

database = FREDatabase()
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

app = Flask(__name__)


## TODO! Using populate_stock_data from fre_market_data.py
def populate_stock_data(tickers: Collection[str], table_name: str, start_date: str, end_date: str) -> None:
    """
    This function writes ticker's data into database
    :param tickers: a list of tickers that we want to write
    :param table_name: a string of our database's table name
    """
    column_names = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume']
    price_data = []
    for ticker in tickers:
        stock = eod_market_data.get_daily_data(ticker, start_date, end_date, 'US')
        for stock_data in stock:
            price_data.append([ticker, stock_data['date'], stock_data['open'], stock_data['high'], stock_data['low'], \
                               stock_data['close'], stock_data['adjusted_close'], stock_data['volume']])
        # print(price_data)
    stocks = pd.DataFrame(price_data, columns=column_names)
    stocks.to_sql(table_name, con=database.engine, if_exists='append', index=False)

def populate_stock_data_from_db(tickers: Collection[str], table_name: str, start_date: str, end_date: str) -> None:

    column_names = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume']
    stocks = pd.DataFrame(columns=column_names)
    for ticker in tickers:
        select_stmt = f"""SELECT symbol, date, open, high, low, close, adjusted_close, volume FROM stocks
                      WHERE symbol = "{ticker}" AND date <= "{end_date}" AND date >= "{start_date}";"""
        symbol_df = database.execute_sql_statement(select_stmt)
        stocks = stocks.append(symbol_df, ignore_index=True)
    stocks.to_sql(table_name, con=database.engine, if_exists='append', index=False)


def cointegration_test(ticker1: str, ticker2: str) -> List[Union[str, float]]:
    """
    This function calculate the cointegration of two tickers
    :param ticker1: name of the first ticker
    :param ticker2: name of the second ticker
    :return: a list of the linear regression results
    """
    select1_stmt = f"SELECT close FROM sector_stocks WHERE symbol = '{ticker1}';"
    select2_stmt = f"SELECT close FROM sector_stocks WHERE symbol = '{ticker2}';"
    symbol1_df = database.execute_sql_statement(select1_stmt)
    symbol2_df = database.execute_sql_statement(select2_stmt)
    symbol1_log_close_prices = np.log(symbol1_df['close'].values)
    symbol2_log_close_prices = np.log(symbol2_df['close'].values)
    if len(symbol1_log_close_prices) != len(symbol2_log_close_prices):
        return

    symbol2_log_close_prices = sm.add_constant(symbol2_log_close_prices)
    model = sm.OLS(symbol1_log_close_prices, symbol2_log_close_prices)
    result = model.fit()

    correlation = np.sqrt(result.rsquared)

    adf_pvalue = st.adfuller(result.resid)[1]

    residual_mean = result.resid.mean()
    residual_std = result.resid.std()

    return [ticker1, ticker2] + \
           [correlation] + \
           list(map("{0: .4f}".format, result.params)) + \
           [adf_pvalue, residual_mean, residual_std]


def cointegration_all_test(symbol_list: List[str]) -> None:
    """
    This function calculate the cointegration of all the symbol pairs in the symbol_list and write all the results to "pair_info" table
    :param symbol_list: the list of symbol name
    """
    stock_pair_list = list(combinations(symbol_list, 2))
    cointegration_test_results = []
    for ticker1, ticker2 in stock_pair_list:
        result = cointegration_test(ticker1, ticker2)

        if result is not None:
            cointegration_test_results.append(result)

    pair_df = pd.DataFrame(cointegration_test_results,
                           columns=['symbol1', 'symbol2', 'correlation', 'beta0', 'beta1_hedgeratio', 'adf_p_value',
                                    'res_mean', 'res_std'])
    pair_df.to_sql('pair_info', con=database.engine, if_exists='append', index=False)


def create_stock_pairs(sector: str, start_date: str = "2020-01-01", end_date: str = None) -> None:
    """
    This function creat pair trades for a given sector of stocks from table "sp500"
    :param sector: the sector name of stocks
    """
    if end_date is None:
        end_date = dt.datetime.today().strftime('%Y-%m-%d')
    table_list = ['sector_stocks', 'pair_info']
    database.create_table(table_list)
    database.clear_table(table_list)
    
    select_stmt = f"""SELECT symbol FROM sp500 WHERE sector ='{sector}' ORDER BY symbol;"""
    result_df = database.execute_sql_statement(select_stmt)
    symbol_list = result_df['symbol'].tolist()
    if database.check_table_empty('sector_stocks'):
        populate_stock_data_from_db(symbol_list, "sector_stocks", start_date, end_date)

    if database.check_table_empty('pair_info'):
        cointegration_all_test(symbol_list)


def build_pair_trading_model(corr_threshold: float = 0.95, adf_threshold: float = 0.01,
                             sector: str = "Technology", start_date: str = "2020-01-01",\
                             back_testing_start_date: str = None, end_date: str = None) -> None:
    """
    This function build a pair_trading model for a given sector of stocks in sp500 and update database tables
    :param corr_threshold: the threshold for stock pair correlation
    :param adf_threshold: the threshold for adf P value
    :param sector: the sector name of stocks
    """
    if end_date is None:
        end_date = dt.datetime.today().strftime('%Y-%m-%d')
    create_stock_pairs(sector, start_date, end_date)

    select_stmt = f"""SELECT symbol1, symbol2 FROM pair_info WHERE correlation >= {corr_threshold} 
                    AND adf_p_value <= {adf_threshold} ORDER BY symbol1, symbol2;"""
    pairs = database.execute_sql_statement(select_stmt)

    tables = ['stock_pairs', 'pair1_stocks', 'pair2_stocks', 'pair_prices', 'pair_trades']
    database.create_table(tables)
    database.clear_table(tables)

    # pairs = pd.read_csv(location_of_pairs)
    pairs["price_mean"] = 0.0
    pairs["volatility"] = 0.0
    pairs["profit_loss"] = 0.0
    pairs.to_sql('stock_pairs', con=database.engine, if_exists='append', index=False)

    select_stmt = f"""SELECT symbol1, symbol2, beta0, beta1_hedgeratio FROM pair_info 
                  WHERE correlation >= {corr_threshold}
                  AND adf_p_value <= {adf_threshold} ORDER BY symbol1, symbol2;"""
    pair_info_df = database.execute_sql_statement(select_stmt)

    populate_stock_data_from_db(pairs['symbol1'].unique(), 'pair1_stocks', start_date, end_date)
    populate_stock_data_from_db(pairs['symbol2'].unique(), 'pair2_stocks', start_date, end_date)

    select_stmt = "SELECT stock_pairs.symbol1 AS symbol1, stock_pairs.symbol2 AS symbol2, \
                 pair1_stocks.date AS date, pair1_stocks.open AS open1, pair1_stocks.close AS close1, \
                 pair2_stocks.open AS open2, pair2_stocks.close AS close2 \
                 FROM stock_pairs, pair1_stocks, pair2_stocks \
                 WHERE (((stock_pairs.symbol1 = pair1_stocks.symbol) AND (stock_pairs.symbol2 = pair2_stocks.symbol)) AND \
                 (pair1_stocks.date = pair2_stocks.date)) ORDER BY symbol1, symbol2;"

    result_df = database.execute_sql_statement(select_stmt)
    result_df.to_sql('pair_prices', con=database.engine, if_exists='append', index=False)

    select_stmt = f"""SELECT symbol1, symbol2, open1, open2, close1, close2 FROM pair_prices 
                    WHERE date <= "{back_testing_start_date}";"""
    pair_price_df = database.execute_sql_statement(select_stmt)
    pair_price_df_updated = pair_price_df.merge(pair_info_df, how='inner', on=['symbol1', 'symbol2'])
    pair_price_df_updated['open_spread'] = np.log(pair_price_df_updated['open1']) - \
                                           pair_price_df_updated['beta0'] - \
                                           pair_price_df_updated['beta1_hedgeratio'] * np.log(
        pair_price_df_updated['open2'])

    pair_price_df_updated['close_spread'] = np.log(pair_price_df_updated['close1']) - \
                                            pair_price_df_updated['beta0'] - \
                                            pair_price_df_updated['beta1_hedgeratio'] * np.log(
        pair_price_df_updated['close2'])

    pair_price_df_mean = pair_price_df_updated.groupby(['symbol1', 'symbol2'])['close_spread'].mean()
    pair_price_df_stdev = pair_price_df_updated.groupby(['symbol1', 'symbol2'])['close_spread'].std()
    pair_price_df_mean_stdev = pd.concat([pair_price_df_mean, pair_price_df_stdev], axis=1)
    pair_price_df_mean_stdev.columns = ['price_mean', 'volatility']
    pair_price_df_mean_stdev.to_sql('tmp', con=database.engine, if_exists='replace')
    update_st = """
        Update stock_pairs set price_mean = (SELECT t.price_mean 
                                            FROM tmp t
                                            WHERE t.symbol1 = stock_pairs.symbol1
                                            AND t.symbol2 = stock_pairs.symbol2),
                                volatility = (SELECT t.volatility 
                                            FROM tmp t
                                            WHERE t.symbol1 = stock_pairs.symbol1
                                            AND t.symbol2 = stock_pairs.symbol2)
        WHERE EXISTS(
        SELECT *
        FROM tmp
        WHERE tmp.symbol1 = stock_pairs.symbol1
        and tmp.symbol2 = stock_pairs.symbol2);
        """

    database.execute_sql_statement(update_st, True)
    database.drop_table('tmp')


class StockPair:
    def __init__(self, symbol1, symbol2, volatility, price_mean):
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.volatility = volatility
        self.price_mean = price_mean
        self.beta0 = 0.0
        self.beta1_hedgeratio = 0.0
        self.trades = {}
        self.total_profit_loss = 0.0

    def update_betas(self, beta0, beta1_hedgeratio):
        self.beta0 = beta0
        self.beta1_hedgeratio = beta1_hedgeratio

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def create_trade(self, date, open1, close1, open2, close2, qty1=0, qty2=0, profit_loss=0.0):
        self.trades[date] = np.array([open1, close1, open2, close2, qty1, qty2, profit_loss])

    def update_trades(self):
        """
        This function update daily qtys and profits of the stockpair
        :return: a dataframe of daily trading records
        """
        trades_matrix = np.array(list(self.trades.values()))
        for index in range(1, trades_matrix.shape[0]):
            open_spread = np.log(trades_matrix[index, 0]) - self.beta0 - self.beta1_hedgeratio * np.log(
                trades_matrix[index, 2])
            z_score = (open_spread - self.price_mean) / self.volatility
            if z_score >= 1.65:
                trades_matrix[index, 4] = -10000
                trades_matrix[index, 5] = int(10000 * self.beta1_hedgeratio)
            elif z_score <= -1.65:
                trades_matrix[index, 4] = 10000
                trades_matrix[index, 5] = int(-10000 * self.beta1_hedgeratio)
            else:
                trades_matrix[index, 4] = 0
                trades_matrix[index, 5] = 0
            trades_matrix[index, 6] = trades_matrix[index, 4] * (trades_matrix[index, 1] - trades_matrix[index, 0]) \
                                      + trades_matrix[index, 5] * (trades_matrix[index, 3] - trades_matrix[index, 2])
            trades_matrix[index, 6] = round(trades_matrix[index, 6], 2)

            self.total_profit_loss += trades_matrix[index, 6]

        for key, index in zip(self.trades.keys(), range(0, trades_matrix.shape[0])):
            self.trades[key] = trades_matrix[index]

        return pd.DataFrame(trades_matrix[:, range(4, trades_matrix.shape[1])], columns=['qty1', 'qty2', 'profit_loss'])


def pair_trade_back_test(back_testing_start_date: str, back_testing_end_date: str) -> None:
    """
    This function do pair trades back testing and write all the results to the "pair_trades" table and "stock_pairs" table. The profit_loss is the total loss of a given stock pair performance during back testing period
    :param back_testing_start_date: the start date of back testing
    :param back_testing_end_date: the end date of back testing
    """

    # database.drop_table('pair_trades')
    stock_pair_map = dict()

    select_stmt = 'SELECT symbol1, symbol2, price_mean, volatility FROM stock_pairs;'
    result_df = database.execute_sql_statement(select_stmt)

    for index, row in result_df.iterrows():
        aKey = (row['symbol1'], row['symbol2'])
        stock_pair_map[aKey] = StockPair(row['symbol1'], row['symbol2'], row['price_mean'], row['volatility'])

    select_stmt = "SELECT stock_pairs.symbol1 as symbol1, stock_pairs.symbol2 as symbol2, beta0, beta1_hedgeratio " \
                  "FROM stock_pairs, pair_info " \
                  "WHERE pair_info.symbol1 = stock_pairs.symbol1 AND pair_info.symbol2 = stock_pairs.symbol2;"
    result_df = database.execute_sql_statement(select_stmt)
    for index, row in result_df.iterrows():
        aKey = (row['symbol1'], row['symbol2'])
        stock_pair_map[aKey].update_betas(row['beta0'], row['beta1_hedgeratio'])

    select_stmt = f"""SELECT symbol1, symbol2, date, open1, open2, close1, close2
                    FROM pair_prices WHERE date >= "{back_testing_start_date}" 
                    AND date <= "{back_testing_end_date}";"""
    result_df = database.execute_sql_statement(select_stmt)

    for index in range(0, result_df.shape[0]):
        aKey = (result_df.at[index, 'symbol1'], result_df.at[index, 'symbol2'])
        stock_pair_map[aKey].create_trade(result_df.at[index, 'date'], result_df.at[index, 'open1'],
                                          result_df.at[index, 'close1'], result_df.at[index, 'open2'],
                                          result_df.at[index, 'close2'])

    trades_df = pd.DataFrame(columns=['qty1', 'qty2', 'profit_loss'])
    for key, value in stock_pair_map.items():
        trades_df = trades_df.append(value.update_trades(), ignore_index=True)
        print(trades_df)
        np.set_printoptions(precision=2, floatmode='fixed')
        np.set_printoptions(suppress=True)
        print(key, value)

        table = database.metadata.tables['stock_pairs']
        update_stmt = table.update().values(profit_loss=value.total_profit_loss).where(
            and_(table.c.symbol1 == value.symbol1, table.c.symbol2 == value.symbol2))
        database.execute_sql_statement(update_stmt, True)

    result_df = result_df.join(trades_df)
    # print(result_df)
    database.clear_table(['pair_trades'])
    result_df.to_sql('pair_trades', con=database.engine, if_exists='append', index=False)


def pair_trade_probation_test(probation_testing_start_date: str, probation_testing_end_date: str) -> None:
    stock_pair_map = dict()
    select_stmt = 'SELECT symbol1, symbol2, price_mean, volatility FROM stock_pairs;'
    result_df = database.execute_sql_statement(select_stmt)

    for index, row in result_df.iterrows():
        aKey = (row['symbol1'], row['symbol2'])
        stock_pair_map[aKey] = StockPair(row['symbol1'], row['symbol2'], row['price_mean'], row['volatility'])

    select_stmt = "SELECT stock_pairs.symbol1 as symbol1, stock_pairs.symbol2 as symbol2, beta0, beta1_hedgeratio " \
                  "FROM stock_pairs, pair_info " \
                  "WHERE pair_info.symbol1 = stock_pairs.symbol1 AND pair_info.symbol2 = stock_pairs.symbol2;"
    result_df = database.execute_sql_statement(select_stmt)
    for index, row in result_df.iterrows():
        aKey = (row['symbol1'], row['symbol2'])
        stock_pair_map[aKey].update_betas(row['beta0'], row['beta1_hedgeratio'])

    select_stmt = f"""SELECT symbol1, symbol2, date, open1, open2, close1, close2
                  FROM pair_prices WHERE date >= "{probation_testing_start_date}" 
                  AND date <= "{probation_testing_end_date}";"""
    result_df = database.execute_sql_statement(select_stmt)

    for index in range(0, result_df.shape[0]):
        aKey = (result_df.at[index, 'symbol1'], result_df.at[index, 'symbol2'])
        stock_pair_map[aKey].create_trade(result_df.at[index, 'date'], result_df.at[index, 'open1'],
                                          result_df.at[index, 'close1'], result_df.at[index, 'open2'],
                                          result_df.at[index, 'close2'])

    trades_df = pd.DataFrame(columns=['qty1', 'qty2', 'profit_loss'])
    for key, value in stock_pair_map.items():
        trades_df = trades_df.append(value.update_trades(), ignore_index=True)
        print(trades_df)
        np.set_printoptions(precision=2, floatmode='fixed')
        np.set_printoptions(suppress=True)
        print(key, value)

    result_df = result_df.join(trades_df)
    database.clear_table(['pair_trades'])
    result_df.to_sql('pair_trades', con=database.engine, if_exists='append', index=False)
