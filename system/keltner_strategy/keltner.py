#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime as dt
from system.database.fre_database import FREDatabase
import pandas as pd
import numpy as np
from system.market_data.fre_market_data import EODMarketData
import matplotlib.pyplot as plt
from typing import Collection, List, Dict, Union
from collections import defaultdict

def populate_to_df(start_date, end_date):    
    database = FREDatabase()
    eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database) 
    
    start_time = int(start_date.replace(tzinfo=dt.timezone.utc).timestamp())
    end_time = int(end_date.replace(tzinfo=dt.timezone.utc).timestamp())

    symbol_sector_map = database.get_sp500_symbol_map()
    data = defaultdict(dict)
    for sector in list(symbol_sector_map.keys()):
        for symbol, name in symbol_sector_map[sector]:
            stk_data = pd.DataFrame(eod_market_data.get_intraday_data(symbol, start_time, end_time))
            stk_data.dropna(axis = 0, how ='any', inplace = True)
            data[sector][symbol] = stk_data
    return symbol_sector_map, data
    
def stock_select_highvol(data, lookback_window, n1, predict_days):
    selected_stock = []
    for sector in data:
        stk_std = pd.DataFrame(list(data[sector]))
        stk_std['std'] = 0.0
        for symbol in list(data[sector]):
            std = 0
            if len(data[sector][symbol]) > ((lookback_window+1)*79+predict_days):
                try:
                    stkdata = data[sector][symbol]
                    std = stkdata.close[(-((lookback_window+1)*79+predict_days)):-(predict_days+79)].pct_change().shift(-1).std()
                    print('Volatility of return over stock: ' + symbol + ' is: ' + str(std))
                    stk_std.loc[symbol, 'std'] = std
                    print(std)
                except:
                    print('Cannot get data of Stock:' + symbol)
            else: print('Not enough data of ' + symbol)
        stock_stk = stk_std['std'].sort_values(ascending=False).index[0]
        selected_stock.append(stock_stk)
        #print('selected stock list:', selected_stock)
    return selected_stock
    
def cal_EMA(df, n1, predict_days):    
    #Calculate EMA
    price = list(df['close'])
    sma_0 = sum(price[1:n1+1])/len(price[1:n1+1])
    ema_1 = price[n1+1]*2/(n1+1)+sma_0*(1-2/(n1+1))
    n = 1
    EMA = []
    EMA.append(ema_1)
    #EMA list from day 22 to day 61
    while n < predict_days:
        EMA.append(price[n1+1+n]*2/(n1+1)+EMA[n-1]*(1-2/(n1+1)))
        n += 1
    return EMA

def cal_ATR(df, n1, n2, predict_days):
    #Calculate ATR
    ##TR
    TR_list = []  
    for i in range(n1-n2+2, n1+predict_days):
        TH_TL = list(df['high'])[i] - list(df['low'])[i]
        TH_YC = list(df['high'])[i] - list(df['close'])[i-1]
        YC_TL = list(df['close'])[i-1] - list(df['low'])[i]
        TR = max(TH_TL, TH_YC, YC_TL)
        TR_list.append(TR)
    
    #ATR from day 22 to day 61
    ATR_list = []
    for i in range(0,predict_days):
        ATR = sum(TR_list[i:i+n2])/len(TR_list[i:i+n2])
        ATR_list.append(ATR)
    return ATR_list

def keltner_channel(df, n1, n2, predict_days, k):
    upperband = []
    lowerband = []
    midband = cal_EMA(df, n1, predict_days)
    ATR = cal_ATR(df, n1, n2, predict_days)
    for i in range(0,predict_days):
        upperband.append(midband[i] + k * ATR[i])
        lowerband.append(midband[i] - k * ATR[i])
    return midband, upperband, lowerband

def kelter_strategy(df, n1, n2, predict_days, k, upper_days, lower_days):
    mid, upper, lower = keltner_channel(df, n1, n2, predict_days, k)
    price = list(df['close'][n1:n1+predict_days])
    #position: 0 = close trades; 1 = prepare to long, 2 = begin long, 
                               #-1 = prepare to short, -2 = begin short
    position = []
    if price[0] < lower[0]: position.append(1) 
    elif price[0] > upper[0]: position.append(-1) 
    else: position.append(0)
    
    for i in range(1, predict_days):
        if price[i] > upper[i]:
            #print('Above')
            if len(position) <= upper_days: position.append(-1)
            elif position[i-1] == -1: 
                if price[i] <= min(price[i-upper_days:i]): position.append(-2)
                else: position.append(-1)
            elif position[i-1] == -2: position.append(-2)
            else: position.append(-1)
        elif price[i] < lower[i]:
            #print('below')
            if len(position) <= lower_days: position.append(1)
            elif position[i-1] == 1: 
                if price[i] >= max(price[i-lower_days:i]): position.append(2)
                else: position.append(1)
            elif position[i-1] == 2: position.append(2)
            else: position.append(1)            
        else:
            #print('mid')
            position.append(0)
    
    sty_return = []
    sty_return.append(0)
    bh_return = []
    bh_return.append(0)
    pst = 0
    cum_rtn_s = 0
    cum_rtn_b = 0
    logrtn_s = 0
    logrtn_b = 0
    pst_list = []
    pst_list.append(0)
    for i in range(1, predict_days):
        if position[i] == 2: 
            rtn = (price[i]-price[i-1])/price[i-1]
            logrtn_s = np.log(price[i]/price[i-1])
            pst = 1
            
        elif position[i] == -2: 
            rtn = -(price[i]-price[i-1])/price[i-1]
            logrtn_s = -np.log(price[i]/price[i-1])
            pst = -1
            
        elif position[i] == 1 or position[i] == -1:             
            if pst == 1:
                rtn = (price[i]-price[i-1])/price[i-1]
                logrtn_s = np.log(price[i]/price[i-1])
                pst = pst
            elif pst == -1: 
                rtn = -(price[i]-price[i-1])/price[i-1]
                logrtn_s = -np.log(price[i]/price[i-1])
                pst = pst
            else: 
                rtn = 0
                logrtn_s = 0
                pst = pst           
        else: 
            rtn = 0
            logrtn_s = 0
            pst = 0
        #pst_list.append(pst)
        cum_rtn_s += logrtn_s
        sty_return.append(cum_rtn_s)
        
        #set stop loss
        if cum_rtn_s <= -0.08: #and logrtn_s < 0:
            position[i+1:i+2] = [0]
            
        cum_rtn_b += np.log(price[i]/price[i-1])
        bh_return.append(cum_rtn_b)          
    strategy = pd.DataFrame()
    bnh = pd.DataFrame()                                 
    strategy['time'] = df['datetime'][n1:n1+predict_days]
    strategy['return'] = sty_return
    bnh['time'] = df['datetime'][n1:n1+predict_days]
    bnh['return'] = bh_return
    return strategy, bnh

def get_info(stk, data, symbol_map):
    sec = ''
    for sector in data:
        if stk in data[sector]:
            sec = sector
            break
    for i in range(len(symbol_map[sec])):
        if stk == symbol_map[sec][i][0]:
            name = symbol_map[sec][i][1]
            break
    return sec, name

def kelt_cha_sty():
    end_date = dt.datetime(dt.datetime.now().year, dt.datetime.now().month, dt.datetime.now().day)
    lookback_window = 60 #real days for getting data
    start_date = end_date + dt.timedelta(-lookback_window)
    symbol_map, data = populate_to_df(start_date, end_date)
    lb_wd = 21 #trading days to calculate vol
    #n2 should not greater than n1
    n1 = 5 * 79  #EMA period
    n2 = 3 * 79    #ATR period / cannot be too big
    k = 2
    predict_days = 79*3
    upper_days = 5
    lower_days = 3
    stk_list = stock_select_highvol(data, lb_wd,n1, predict_days)
    print(stk_list)
    # Show stocks' information of the portfolio
    stock_table = []
    
    for stock in stk_list:
        sector, name = get_info(stock, data, symbol_map)
        stock_table.append((stock, name, sector))
    length = len(stock_table)
    
   
    for stk in stk_list:
        target = None
        for sector in data:
            if stk in data[sector]:
                target = data[sector][stk]
                break
        stk_data = target[-(predict_days+n1+79):]
        
        strategy = pd.DataFrame()
        buynhold = pd.DataFrame()
        
        sty, bnh = kelter_strategy(stk_data, n1, n2, predict_days, k, upper_days, lower_days)
        #put return of each stock into one dataframe
        sty = sty.set_index('time')
        bnh = bnh.set_index('time')
        strategy = pd.concat([strategy, sty], axis = 1)
        buynhold = pd.concat([buynhold, bnh], axis = 1)

    #drop all the date with missing value
    strategy.dropna(axis = 0, how = 'any', inplace = True)
    buynhold.dropna(axis = 0, how = 'any', inplace = True)
    #calculate the cumulative return of the portfolio
    strategy['sum_sty'] = strategy.sum(axis = 1)
    buynhold['sum_bh'] = buynhold.sum(axis = 1)
    #save only the last column for further use
    strategy = strategy.iloc[:,-1]
    buynhold = buynhold.iloc[:,-1]
    return stock_table, length, strategy, buynhold








