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
import pandas as pd
import time  # helper libraries
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


top_stocks_res = [] #要恢复的， 下面注释掉
# top_stocks_res = [["Technology", "CDAY", 0.5084448084148229], ["Consumer Cyclicals", "MHK", 0.2309246121838686],['Communication Services','GOOG',0.3595421289718121],
#                       ['Financial Services','COF', 0.32354740302580615], ['Healthcare','OGN',0.4680826119800676], ['Consumer Defensive','COST', 0.24867235116256786],
#                       ['Energy','OKE',0.30835734657071145], ['Basic Materials','NUE',0.2707254014392585], ['Utilities', 'DUK', 0.1984543789672999], ['Industrials', 'AVY',0.3897337106016211],
#                       ['Real Estate', 'MAA', 0.3247365404443218]]
# top_stocks_res = [["Technology", "FLT", 0.5084448084148229], ["Consumer Cyclicals", "GM", 0.2309246121838686],['Communication Services','FB',0.3595421289718121],
#                       ['Financial Services','BRKB', 0.32354740302580615], ['Healthcare','HCA',0.4680826119800676], ['Consumer Defensive','TGT', 0.24867235116256786],
#                       ['Energy','KMI',0.30835734657071145], ['Basic Materials','FCX',0.2707254014392585], ['Utilities', 'EXC', 0.1984543789672999], ['Industrials', 'NLSN',0.3897337106016211],
#                       ['Real Estate', 'SPG', 0.3247365404443218]] #just change stock names, not the value--try do the backtest

# Select Data
def extract_database_sector(database):
    """
    Extract S&P500 Sector data from the database to classify each stock in corresponding sector.
    """
    sector_classify = f"""
                    SELECT *
                    FROM sp500
                    ;
                    """
    df_sector = database.execute_sql_statement(sector_classify)
    return df_sector


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


def build_model_predict_select(df_stock_10yr, df_rf, df_sector):
    # convert an array of values into a dataset matrix
    def create_dataset(dataset, look_back=1):
        dataX, dataY = [], []
        for i in range(len(dataset) - look_back):
            a = dataset[i:(i + look_back), 0]
            dataX.append(a)
            dataY.append(dataset[i + look_back, 0])
        return np.array(dataX), np.array(dataY)

    # fix random seed for reproducibility
    np.random.seed(5)

    # build simple LSTM model
    data_dict = {}  # key --> sym :  value: list1[] --> all predicted prices, list2[]--> all RF correlated to the data of test
    index = 0
    date_dict = {}  # key --> sym : value --> the start date of the test data
    for sym in df_stock_10yr['symbol'].unique():
        sym_df = df_stock_10yr.loc[df_stock_10yr['symbol'] == sym]
        dataset = sym_df['adjusted_close'].values.reshape(-1, 1)

        # normalize the dataset
        scaler = MinMaxScaler(feature_range=(0, 1))
        dataset = scaler.fit_transform(dataset)

        # split into train and test sets, 10% test data, 90% training data
        train_size = int(len(dataset) * 0.9)
        test_size = len(dataset) - train_size
        train, test = dataset[0:train_size, :], dataset[train_size:len(dataset), :]
        # reshape into X=t and Y=t+1, timestep 7
        look_back = 7
        trainX, trainY = create_dataset(train, look_back)
        testX, testY = create_dataset(test, look_back)

        date = str(sym_df.at[sym_df.index[0] + train_size, 'date'])

        date_dict[sym] = date
        # RF data matching the test date for each stock
        date_values = sym_df['date'].values
        data_rf = []
        for date in date_values:
            if len(df_rf.loc[df_rf['date'] == date]) == 0:
                data_rf.append(0)
            else:
                idx = df_rf.loc[df_rf['date'] == date].index[0]
                data_rf.append(df_rf.loc[df_rf['date'] == date].at[idx, 'adjusted_close'])
        data_rf = data_rf[int(len(data_rf) * 0.9) + look_back: len(data_rf)]
        print('date_rf length:', len(data_rf))
        # reshape input to be [samples, time steps, features]
        trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
        testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

        # create and fit the LSTM network, optimizer=adam, dropout 0.1
        # parameters tuned
        model = Sequential()
        model.add(LSTM(4, input_shape=(1, look_back)))
        model.add(Dropout(0.1))
        model.add(Dense(1))  # avoid overfitting
        model.compile(loss='mse', optimizer='adam', metrics=['acc'])
        model.fit(trainX, trainY, epochs=3, batch_size=1, verbose=0)

        # make predictions
        testPredict = model.predict(testX)

        # invert predictions
        testPredict = scaler.inverse_transform(testPredict)
        testY = scaler.inverse_transform([testY])
        data_dict[sym] = [testPredict.reshape(-1), data_rf]
        print('test length:', len(testPredict.reshape(-1)))

        # calculate root mean squared error
        testScore = math.sqrt(mean_squared_error(testY[0], testPredict[:, 0]))
        print('Test Score: %.2f RMSE' % (testScore))

        # testY = scaler.inverse_transform([testY])
        index += 1
        print("Current progress", str(index / 503))

    # # change from string to float
    # for key in data_dict.keys():
    #     for i in range(len(data_dict[key][1])):
    #         data_dict[key][1][i] = float(data_dict[key][1][i])

    # calculate Sharpe ratio for each stock using predicted price data
    SR = {}  # key -> stock/symbol, values ->ratio = (Rs - Rf)/std(Rs_i - Rf_i)
    for sym in data_dict.keys():
        return_daily_sym = []
        list = data_dict[sym][0]
        for i in range(len(list) - 1):
            return_daily = (list[i + 1] - list[i]) / list[i]
            return_daily_sym.append(return_daily)

        return_rf = []
        list_rf = data_dict[sym][1]
        for i in range(len(list_rf) - 1):
            return_daily_rf = 0
            if float(list_rf[i]) == 0:
                return_daily_rf = (float(list_rf[i + 1]) - float(list_rf[i])) / float(0.0001)
            else:
                return_daily_rf = (float(list_rf[i + 1]) - float(list_rf[i])) / float(list_rf[i])
            return_rf.append(return_daily_rf)

        xr = []  # calculate daily excess return
        for i in range(len(return_rf)):
            xr.append(return_daily_sym[i] - return_rf[i])
        SR[sym] = (np.mean(return_daily_sym) - np.mean(return_rf)) / np.std(xr)  # according to the definition of SR

    sector_dict = {}  # key --> sym, value --> sector

    # Assign each stock to its corresponding sector
    # sector = sector_dict.keys
    for i in range(1, len(df_sector.index)):
        if not df_sector.at[i, 'symbol'] in sector_dict.keys():
            sector_dict[df_sector.at[i, 'symbol']] = df_sector.at[i, 'sector']

    sector_sym_r = {}  # key->sector, value -> {sym : sym_ratio, .....}
    for sym in sector_dict.keys():
        if not sector_dict[sym] in sector_sym_r.keys():
            sector_sym_r[sector_dict[sym]] = {}
        sector_sym_r[sector_dict[sym]][sym] = SR[sym]

    # Sort the stock results in each sector based on the ratio
    for key in sector_sym_r.keys():
        sector_sym_r[key] = dict(sorted(sector_sym_r[key].items(), key=lambda item: item[1], reverse=True))

    # Print out the top stock selected in the webpage
    top_stocks = []
    for sec in sector_sym_r.keys():
        print(sec)
        for stock, value in sector_sym_r[sec].items():
            print(stock + " " + str(value))
            top_stocks.append([sec, stock, value])
            break;
        print()
    # remove JEC which is from 'other' sector
    top_stocks_res = top_stocks[:-1]
    return top_stocks_res

def get_top_stocks():
    return top_stocks_res

# def get_rf():
#     return df_rf_g
#
# def get_stock_10yr():
#     return df_stock_10yr_g