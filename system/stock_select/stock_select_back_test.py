import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pandas import read_csv
import math
from keras.models import Sequential
from keras.layers import Bidirectional
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from keras.layers.core import Dense, Activation, Dropout
import time #helper libraries
from datetime import datetime
from datetime import timedelta
import os
import sys
import subprocess
import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as mdates
import plotly.graph_objects as go
import plotly.express as px
from base64 import b64encode



def extract_database_mkt(database):
    """
    Extract SPY historical data as market benchmark from the database in order to calculate Sharpe ratio
    """
    spy_select = f"""
                    SELECT *
                    FROM spy
                    ;
                    """
    df_mkt = database.execute_sql_statement(spy_select)
    return df_mkt

def extract_database_rf_10yr(database):
    """
    Extract the us10y price data from the database in order to calculate Sharpe ratio
    """
    rf_select = f"""
                    SELECT *
                    FROM us10y
                    ;
                    """
    df_rf = database.execute_sql_statement(rf_select)
    return df_rf


def extract_database_stock_10yr(database):
    """
    Extract S&P500 historical price data from the database in order to calculate Sharpe ratio
    """
    stock_select = f"""
                    SELECT *
                    FROM stocks
                    ;
                    """
    df_stock_10yr = database.execute_sql_statement(stock_select)
    df_stock_10yr = df_stock_10yr.sort_values(by=['symbol', 'date'])
    return df_stock_10yr


def stock_select_back_test(top_stock, df_mkt, df_stock_10yr, df_rf):
    # Select the top one from each sector

    date_start = datetime.strptime('2021-01-01', "%Y-%m-%d")
    end_str = df_rf.at[df_rf.index[-1], 'date']
    date_end = datetime.strptime(end_str, "%Y-%m-%d")
    print(df_rf)
    print(date_end)
    top_stock_df = pd.DataFrame(columns=['sym', 'date', 'price'])
    idx = 0
    for stock in top_stock:
        print(stock)
        df = df_stock_10yr[(df_stock_10yr['symbol'] == stock) & (df_stock_10yr['date'] >= '2020-12-31')]
        for i in df.index.tolist():
            top_stock_df.loc[idx] = [df.at[i, 'symbol'], df.at[i, 'date'], df.at[i, 'adjusted_close']]
            idx += 1

    # fix the zero price
    for stock in top_stock:
        df = top_stock_df[top_stock_df['sym'] == stock]
        for i in df.index.tolist():
            if float(top_stock_df.at[i, 'price']) == 0:
                top_stock_df.at[i, 'price'] = top_stock_df.at[i - 1, 'price']
    print("xixixixixixi")

    final_stock_df = pd.DataFrame(columns=['sym', 'date', 'return'])
    # calculate return
    idx = 0
    for stock in top_stock:
        df = top_stock_df[top_stock_df['sym'] == stock]
        for i in df.index.tolist()[1:]:
            newVal = (float(top_stock_df.at[i, 'price']) - float(top_stock_df.at[i - 1, 'price'])) / float(
                top_stock_df.at[i - 1, 'price'])
            final_stock_df.loc[idx] = [stock, df.at[i, 'date'], newVal]
            idx += 1
    print("hahahhahaha")
    date_sym = {}  # key --> date, value--> average return of stocks on that day
    end = date_end + timedelta(days=1)
    every_stock_return = {}  # key --> stock, value --> return of each date
    # initialize
    for stock in top_stock:
        every_stock_return[stock] = []

    while date_start != end:
        date_str = date_start.strftime("%Y-%m-%d")
        sum = 0
        count = 0
        print(date_str)
        for stock in top_stock:
            ret = final_stock_df.loc[(final_stock_df['sym'] == stock) & (final_stock_df['date'] == date_str)][
                'return'].tolist()
            if ret != []:
                every_stock_return[stock].append(float(ret[0]))
                sum += float(ret[0])
                count += 1
            # else:
            #   if date_str in final_stock_df['date'].unique():
            #     every_stock_return[stock].append(0)
        if sum != 0:
            date_sym[date_str] = sum / count  # assign equal weight to each stock
        date_start += timedelta(days=1)

    print("Process mkt data")
### Process mkt data
    date_start = datetime.strptime('2020-12-31', "%Y-%m-%d")
    return_mkt = \
    df_mkt.loc[(df_mkt['date'] >= date_start.strftime("%Y-%m-%d")) & (df_mkt['date'] <= date_end.strftime("%Y-%m-%d"))]['adjusted_close'].values

    return_mkt_arr = []
    # if the market return on some day is 0, then set that day's return to the previous day
    for i in range(1, len(return_mkt)):
        if return_mkt[i] == 0:
            return_mkt[i] = return_mkt[i - 1]
    # calculate the market daily return
    for i in range(1, len(return_mkt)):
        return_mkt_arr.append((float(return_mkt[i]) - float(return_mkt[i - 1])) / float(return_mkt[i - 1]))

    # SP,= plt.plot(return_mkt_arr,label = 'S&P 500')
    fig = go.Figure([go.Scatter(name="Top stocks", x=list(date_sym.keys()), y=list(date_sym.values()))])
    fig.add_trace(go.Scatter(name="Market Data", x=list(date_sym.keys()), y=return_mkt_arr))
    encoding = b64encode(fig.to_image(format='png')).decode()
    img_bytes_portfolio_daily = "data:image/png;base64," + encoding
    print(img_bytes_portfolio_daily)
    print()

    print("Cumulative return")
    ### Cumulative return
    mkt_cumu_return = []
    stock_cumu_return = []

    # market cumulative return
    for i in range(1, len(return_mkt_arr)):
        return_mkt_arr[i] = return_mkt_arr[i - 1] + return_mkt_arr[i]
        mkt_cumu_return.append(return_mkt_arr[i])

    stock_return = list(date_sym.values())
    for i in range(1, len(stock_return)):
        stock_return[i] = float(stock_return[i - 1]) + float(stock_return[i])
        stock_cumu_return.append(stock_return[i])

    every_stock_cumu = {}

    for stock in every_stock_return.keys():
        stock_r = list(every_stock_return[stock])
        stock_cumu_r = []
        for i in range(1, len(stock_r)):
            stock_r[i] = float(stock_r[i - 1]) + float(stock_r[i])
            stock_cumu_r.append(stock_r[i])
        every_stock_cumu[stock] = stock_cumu_r

    fig = go.Figure([go.Scatter(name="Top Stocks\nCumulative Return", x=list(date_sym.keys()), y=stock_cumu_return)])
    fig.add_trace(go.Scatter(name="Market Cumulative Return", x=list(date_sym.keys()), y=mkt_cumu_return))
    encoding_cu = b64encode(fig.to_image(format='png')).decode()
    img_bytes_portfolio_cumdaily = "data:image/png;base64," + encoding_cu
    print(img_bytes_portfolio_cumdaily)
    print()

    # Plot individual stock's cumulative return
    img_bytes_stocks_cumdaily = []
    for stock in every_stock_cumu.keys():
        print(stock)
        fig = go.Figure([go.Scatter(name=stock, x=list(final_stock_df[final_stock_df['sym'] == stock]['date'].tolist()),
                                    y=every_stock_cumu[stock])])
        fig.add_trace(go.Scatter(name="Market Data", x=list(date_sym.keys()), y=return_mkt_arr))
        img_bytes_stock_cumdaily = "data:image/png;base64," + b64encode(fig.to_image(format='png')).decode()
        print(img_bytes_stock_cumdaily)
        print()
        img_bytes_stocks_cumdaily.append(img_bytes_stock_cumdaily)


# put result images into a dictionary
    images = {}
    images["portfolio_daily"] = img_bytes_portfolio_daily
    images["portfolio_cumdaily"] = img_bytes_portfolio_cumdaily
    images["stocks_individual"] = img_bytes_stocks_cumdaily

    return images






