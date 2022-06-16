#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 22:47:20 2022

@author: Lu
"""


import os
import numpy as np
import datetime as dt
from system.database.fre_database import FREDatabase
import pandas as pd
from system.services.market_data.fre_market_data import EODMarketData
from collections import defaultdict
from system.services.predict_based_optimization.LSTM_function import find_error
from scipy.stats.stats import pearsonr


def download_data(start_date, end_date, database, eod_market_data):
    symbol_sector_map = database.get_sp500_symbol_map()
    data = defaultdict(dict)
    for sector in list(symbol_sector_map.keys()):
        for symbol, name in symbol_sector_map[sector]:
            stk_data = pd.DataFrame(eod_market_data.get_daily_data(symbol, start_date, end_date,'US'))
            data[sector][symbol] = stk_data
    return data

def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-time_step-1):
        a = dataset[i:(i+time_step), 0]   
        dataX.append(a)
        dataY.append(dataset[i + time_step, 0])
    return np.array(dataX), np.array(dataY)

def find_least2_var(data, sector, var, err):
    V_dict = {}
    for symbols in data[sector]:
        var_sbl = var[symbols]
        corr = 0
        for sbls in data[sector]:
            if symbols != sbls:
                corr += pearsonr(err[symbols], err[sbls])[0]
            else: corr = corr
        v = var_sbl + corr
        V_dict[symbols] = v/(len(data[sector])*len(data[sector]))
    V_final = dict(sorted(V_dict.items(), key=lambda item: item[1]))
    least2sbl = list(V_final)[0:2]
    return V_final, least2sbl

def get_final_portfolio(data):
    portfolio = []
    for sector in data:
        err, var = find_error(data, sector)
        V, stk = find_least2_var(data, sector, var, err)
        portfolio += stk
    return portfolio

def calc_portfolio_ret(portfolio, eod_market_data, start_date, end_date):
    df = pd.DataFrame()
    remove_list = []
    for stk in portfolio:
        target = pd.DataFrame(eod_market_data.get_daily_data(stk, start_date, end_date,'US'))
        try:
            stk_data = target.set_index('date')['adjusted_close']
            df = pd.concat([df, pd.DataFrame(stk_data)], axis=1)
        except:
            remove_list.append(stk)
            portfolio.remove(stk)
    df.dropna(axis = 0, how ='any', inplace = True)   
    ret_data = (np.log(df) - np.log(df.shift(1))).dropna()
    ret_data['row_sum'] = ret_data.sum(axis=1)
    ret_data['cum_ret'] = ret_data['row_sum'].cumsum()
    port_ret = pd.DataFrame(ret_data['cum_ret'])/len(portfolio)
    return port_ret, portfolio, remove_list

def calc_bench_ret(start, end, eod_market_data):
    spy_data = pd.DataFrame(eod_market_data.get_daily_data('SPY', start, end, 'US'))
    sp = spy_data.set_index('date')['adjusted_close']
    spy_data.dropna(axis = 0, how ='any', inplace = True)
    spy_ret = (np.log(sp) - np.log(sp.shift(1))).dropna()
    spy_cum = spy_ret.cumsum()
    return spy_cum

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

def get_optimized_portfolio(start_date, end_date):
    database = FREDatabase()
    eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)
    data = download_data(start_date, end_date, database, eod_market_data)
    #delete the stocks that do not have the column of adjusted price
    for sector in data:
        for symbol in list(data[sector]):
            p = data[sector][symbol]
            if 'adjusted_close' not in list(p.keys()):
                data[sector].pop(symbol)
    #delete the stocks that do not have enough data
    for sector in data:
        for symbol in list(data[sector]):
            if len(data[sector][symbol]) < 2516:
                print(symbol)
                data[sector].pop(symbol)
                
    portfolio = get_final_portfolio(data)
    
    port_table = []
    symbol_map = database.get_sp500_symbol_map()
    
    for stk in portfolio:
        sec, name = get_info(stk, data, symbol_map)
        port_table.append((stk, name, sec))
    print(portfolio)
    return portfolio, port_table
    
def opt_backtest(portfolio):
    end = dt.date.today()
    start = end + dt.timedelta(-90)
    database = FREDatabase()
    eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)
    
    port_ret, portfolio, remove_list = calc_portfolio_ret(portfolio, eod_market_data, start, end)
    bench_cum = calc_bench_ret(start, end, eod_market_data)
    df4plot = pd.concat([port_ret, bench_cum], axis=1)
    df4plot.dropna(axis = 0, how ='any', inplace = True)
    df4plot.columns = ['port_return', 'Benchmark_return']

    #df4plot.plot(y = ['port_return','Benchmark_return'])
    return df4plot, portfolio, remove_list

