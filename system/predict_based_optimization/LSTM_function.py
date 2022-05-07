#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 23 12:21:59 2022

@author: Lu
"""

import os
import sys
import numpy as np
import email_validator
from queue import Queue
from typing import Dict
import datetime as dt
from system.database.fre_database import FREDatabase
import pandas as pd
from system.market_data.fre_market_data import EODMarketData
from sqlalchemy import ForeignKey, Integer, Numeric, Text, DATETIME, CHAR, String, DATE, VARCHAR, BLOB, BOOLEAN
from sqlalchemy import create_engine, MetaData
from sqlalchemy import Table, Column
from typing import Collection, List, Dict, Union
from collections import defaultdict
from itertools import product
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
import math
from sklearn.metrics import mean_squared_error


def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-time_step-1):
        a = dataset[i:(i+time_step), 0]   
        dataX.append(a)
        dataY.append(dataset[i + time_step, 0])
    return np.array(dataX), np.array(dataY)
    
def stkclose_price(data, sector, stk):
    subdata = data[sector][stk]['adjusted_close']
    scaler = MinMaxScaler(feature_range = (0,1))
    closeprice = scaler.fit_transform(np.array(subdata).reshape(-1,1))
    
    train = int(len(closeprice)*0.7)
    test = len(closeprice) - train
    train_data, test_data = closeprice[0:train, :], closeprice[train:len(closeprice), :1]
    
    time_step = 100
    x_train, y_train = create_dataset(train_data, time_step)
    x_test, y_test = create_dataset(test_data, time_step)

    return subdata, scaler, x_train, x_test, y_train, y_test

def find_error(data, sector):
    all_stock_names = [symbol for symbol in data[sector]]
    all_x_train, all_x_test, all_y_train, all_y_test = [], [], [], []
    stk_names = []
    
    for stock_name in all_stock_names:
        subdata, scaler, x_train, x_test, y_train, y_test = stkclose_price(data, sector, stock_name)
        all_x_train.append(x_train)
        all_x_test.append(x_test)
        all_y_train.append(y_train)
        all_y_test.append(y_test)
    
    i = 0
    all_var = {}
    errors = {}
    for x_train, x_test, y_train, y_test in zip(all_x_train, all_x_test, all_y_train, all_y_test):
        model = Sequential()
        model.add(LSTM(50, return_sequences = True, input_shape=(100,1)))
        model.add(LSTM(50, return_sequences = True))
        model.add(LSTM(50))
        model.add(Dense(1))
        model.compile(loss = 'mean_squared_error', optimizer = 'adam')
        model.fit(x_train, y_train, validation_data=(x_test,y_test), epochs=10, batch_size=64, verbose=1)
        
        train_predict = model.predict(x_train)
        test_predict = model.predict(x_test)

        train_predict = scaler.inverse_transform(train_predict)
        test_predict = scaler.inverse_transform(test_predict)

        math.sqrt(mean_squared_error(y_train,train_predict))
        math.sqrt(mean_squared_error(y_test,test_predict))

        #print(type(subdata))  

        Ori_data = pd.DataFrame(subdata.iloc[-654:])
        #print(len(Ori_data))
        #print(type(Ori_data))  
        #print(Ori_data) 
        LSTM_predict= pd.DataFrame(test_predict, columns = ['prediction'])
        #print(LSTM_predict)

        predict_return = LSTM_predict.diff(periods = 1).dropna(axis = 0)
        #print(predict_return)
        #print(sum(predict_return))
        actual_return = Ori_data.diff(periods = 1).dropna(axis = 0)
        #print(actual_return)
     
        predict_error = [a - b for a,b in zip(list(actual_return['adjusted_close']), list(predict_return['prediction']))]    
        #predict_error = list(actual_return['adjusted_close']) - list(predict_return['prediction'])
        #print(predict_error)
        #sum(predict_error)
        
        import statistics     
        var = statistics.variance(predict_error)
        
        all_var[all_stock_names[i]] = var
        errors[all_stock_names[i]] = predict_error
        i += 1
        
    return errors, all_var
