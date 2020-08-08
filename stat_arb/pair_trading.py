# -*- coding: utf-8 -*
# !/usr/bin/env python3
import sys
sys.path.append('../')

import os
import datetime as dt
import pandas as pd
import numpy as np

from sqlalchemy import and_, or_, not_

from flask import Flask, flash, redirect, render_template, request, url_for

from market_data.fre_market_data import EODMarketData
from database.fre_database import FREDatabase

location_of_pairs = 'csv/PairTrading.csv'

os.environ["EOD_API_KEY"] = "5ba84ea974ab42.45160048"

if not os.environ.get("EOD_API_KEY"):
    raise RuntimeError("EOD_API_KEY not set")

start_date = dt.date(2019, 1, 1).strftime('%Y-%m-%d')
end_date = dt.datetime.today().strftime('%Y-%m-%d')

back_testing_start_date = dt.date(2019, 12, 31).strftime('%Y-%m-%d')
back_testing_end_date = dt.date(2020, 1, 31).strftime('%Y-%m-%d')

k = 2

database = FREDatabase()
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

app = Flask(__name__)

def populate_stock_data(tickers, table_name, start_date, end_date):
    column_names = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume']
    price_data = []
    for ticker in tickers:
        stock = eod_market_data.get_daily_data(ticker, start_date, end_date)
        for stock_data in stock:
            price_data.append([ticker, stock_data['date'], stock_data['open'], stock_data['high'], stock_data['low'], \
                               stock_data['close'], stock_data['adjusted_close'], stock_data['volume']])
        #print(price_data)
    stocks = pd.DataFrame(price_data, columns=column_names)
    stocks.to_sql(table_name, con=database.engine, if_exists='append', index=False)


def build_pair_trading_model():

    tables = ['stock_pairs', 'pair1_stocks', 'pair2_stocks', 'pair_prices', 'pair_trades']
    database.create_table(tables)

    database.clear_table(tables)

    pairs = pd.read_csv(location_of_pairs)
    pairs["volatility"] = 0.0
    pairs["profit_Loss"] = 0.0
    pairs.to_sql('stock_pairs', con=database.engine, if_exists='append', index=False)

    populate_stock_data(pairs['symbol1'].unique(), 'pair1_stocks', start_date, end_date)
    populate_stock_data(pairs['symbol2'].unique(), 'pair2_stocks', start_date, end_date)

    select_stmt = "SELECT stock_pairs.symbol1 AS symbol1, stock_pairs.symbol2 AS symbol2, \
                 pair1_stocks.date AS date, pair1_stocks.open AS open1, pair1_stocks.close AS close1, \
                 pair2_stocks.open AS open2, pair2_stocks.close AS close2 \
                 FROM stock_pairs, pair1_stocks, pair2_stocks \
                 WHERE (((stock_pairs.symbol1 = pair1_stocks.symbol) AND (stock_pairs.symbol2 = pair2_stocks.symbol)) AND \
                 (pair1_stocks.date = pair2_stocks.date)) ORDER BY symbol1, symbol2;"

    result_set = database.execute_sql_statement(select_stmt)
    result_df = pd.DataFrame(result_set.fetchall())
    result_df.columns = result_set.keys()
    result_df.to_sql('pair_prices', con=database.engine, if_exists='append', index=False)

    select_stmt = "SELECT * FROM pair_prices WHERE date <= " + "\"" + back_testing_start_date + "\";"
    result_set = database.execute_sql_statement(select_stmt)
    result_df = pd.DataFrame(result_set.fetchall())
    result_df.columns = result_set.keys()
    result_df['ratio'] = result_df['close1']/result_df['close2']
    result_df_stdev = result_df.groupby(['symbol1', 'symbol2'])['ratio'].std()
    result_df_stdev.to_sql('tmp', con=database.engine, if_exists='replace')

    update_st = """
    Update stock_pairs set volatility = (SELECT t.ratio 
                                        FROM tmp t
                                        WHERE t.symbol1 = stock_pairs.symbol1
                                        AND t.symbol2 = stock_pairs.symbol2)
    WHERE EXISTS(
    SELECT *
    FROM tmp
    WHERE tmp.symbol1 = stock_pairs.symbol1
    and tmp.symbol2 = stock_pairs.symbol2);
    """

    database.execute_sql_statement(update_st)
    database.drop_table('tmp')


class StockPair:
    def __init__(self, symbol1, symbol2, volatility, k):
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.volatility = volatility
        self.k = k
        self.trades = {}
        self.total_profit_loss = 0.0

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def create_trade(self, date, open1, close1, open2, close2, qty1=0, qty2=0, profit_loss=0.0):
        self.trades[date] = np.array([open1, close1, open2, close2, qty1, qty2, profit_loss])

    def update_trades(self):
        trades_matrix = np.array(list(self.trades.values()))
        for index in range(1, trades_matrix.shape[0]):
            if abs(trades_matrix[index - 1, 1] / trades_matrix[index - 1, 3] - trades_matrix[index, 0] / trades_matrix[
                index, 2]) \
                    > self.k * self.volatility:
                trades_matrix[index, 4] = -10000
                trades_matrix[index, 5] = int(10000 * (trades_matrix[index, 0] / trades_matrix[index, 2]))
            else:
                trades_matrix[index, 4] = 10000
                trades_matrix[index, 5] = int(-10000 * (trades_matrix[index, 0] / trades_matrix[index, 2]))
            trades_matrix[index, 6] = trades_matrix[index, 4] * (trades_matrix[index, 1] - trades_matrix[index, 0]) \
                                      + trades_matrix[index, 5] * (trades_matrix[index, 3] - trades_matrix[index, 2])
            trades_matrix[index, 6] = round(trades_matrix[index, 6], 2)

            self.total_profit_loss += trades_matrix[index, 6]

        for key, index in zip(self.trades.keys(), range(0, trades_matrix.shape[0])):
            self.trades[key] = trades_matrix[index]

        return pd.DataFrame(trades_matrix[:, range(4, trades_matrix.shape[1])], columns=['qty1', 'qty2', 'profit_loss'])


def back_testing(k, back_testing_start_date, back_testing_end_date):
    #database.drop_table('pair_trades')
    stock_pair_map = dict()

    select_stmt = 'SELECT symbol1, symbol2, volatility FROM stock_pairs;'
    result_set = database.execute_sql_statement(select_stmt)
    result_df = pd.DataFrame(result_set.fetchall())
    result_df.columns = result_set.keys()

    for index, row in result_df.iterrows():
        aKey = (row['symbol1'], row['symbol2'])
        stock_pair_map[aKey] = StockPair(row['symbol1'], row['symbol2'], row['volatility'], k)

    select_stmt = "SELECT * FROM pair_prices WHERE date >= " + "\"" + back_testing_start_date + "\"" + \
                " AND date <= " + "\"" + back_testing_end_date + "\"" + ";"
    result_set = database.execute_sql_statement(select_stmt)
    result_df = pd.DataFrame(result_set.fetchall())
    result_df.columns = result_set.keys()

    for index in range(0, result_df.shape[0]):
        aKey = (result_df.at[index, 'symbol1'], result_df.at[index, 'symbol2'])
        stock_pair_map[aKey].create_trade(result_df.at[index, 'date'], result_df.at[index, 'open1'],
                                          result_df.at[index, 'close1'], result_df.at[index, 'open2'], result_df.at[index, 'close2'])

    trades_df = pd.DataFrame(columns=['qty1', 'qty2', 'profit_loss'])
    for key, value in stock_pair_map.items():
        trades_df = trades_df.append(value.update_trades(), ignore_index=True)
        print(trades_df)
        np.set_printoptions(precision=2, floatmode='fixed')
        np.set_printoptions(suppress=True)
        print(key, value)

        table = database.metadata.tables['stock_pairs']
        update_stmt = table.update().values(profit_loss=value.total_profit_loss).where(and_(table.c.symbol1 == value.symbol1, table.c.symbol2 == value.symbol2))
        database.execute_sql_statement(update_stmt)

    result_df = result_df.join(trades_df)
    #print(result_df)
    database.clear_table(['pair_trades'])
    result_df.to_sql('pair_trades', con=database.engine, if_exists='append', index=False)
