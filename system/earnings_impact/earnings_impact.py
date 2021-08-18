from datetime import datetime, timedelta
from yahoo_earnings_calendar import YahooEarningsCalendar
import pandas as pd
from tqdm import tqdm
import numpy as np
import os
import yfinance as yfin
import matplotlib.pyplot as plt
import random
from system import database
yfin.pdr_override()


def load_returns():
    # fetch spy and 500 stocks then concatenate into a dataframe
    select_stmt = 'SELECT symbol, date, adjusted_close FROM stocks'
    spy500 = database.execute_sql_statement(select_stmt)
    spy500 = pd.pivot_table(spy500, index=['date'], columns=['symbol'])['adjusted_close']
    select_stmt = 'SELECT symbol, date, adjusted_close FROM spy'
    spy = database.execute_sql_statement(select_stmt)
    spy = pd.pivot_table(spy, index=['date'], columns=['symbol'])['adjusted_close']
    # don't know why 5 missing days in table spy
    for d in spy500.index:
        if d not in spy.index:
            spy.loc[d, 'spy'] = np.nan
    spy500 = spy500.sort_index()
    spy = spy.sort_index()
    returns = pd.concat([spy, spy500], axis=1)
    returns = (returns / returns.shift(1) - 1)
    returns = returns.sub(returns['spy'], axis=0).fillna(0)
    returns.columns = list(returns.columns)
    returns.index = list(datetime.strptime(x, '%Y-%m-%d') for x in returns.index)
    return returns


def load_local_earnings_impact(SPY_component):
    table = pd.read_pickle('./system/earnings_impact/earnings_calendar_xz.pkl.compress', compression='xz')
    SPY_component = list(set(list(table['ticker'])))
    return table, SPY_component

def load_earnings_impact(SPY_component):
    yec = YahooEarningsCalendar()
    df = []
    fail_ticker = []
    for ticker in tqdm(SPY_component):
        try:
            earnings_list = yec.get_earnings_of(ticker)
            earnings_df = pd.DataFrame(earnings_list)
            df.append(earnings_df)
        except:
            fail_ticker.append(ticker)
    for ticker in fail_ticker:
        SPY_component.remove(ticker)
    table = pd.concat(df, axis=0)
    table['startdatetime'] = table['startdatetime'].apply(lambda x: datetime.strptime(x[:10], '%Y-%m-%d'))
    table['epssurprise'] = table['epsactual'] - table['epsestimate']
    table = table[['ticker', 'startdatetime', 'epssurprise']]
    table = table.dropna(subset=['epssurprise'])
    table.to_pickle('./system/earnings_impact/earnings_calendar_xz.pkl.compress', compression='xz')
    return table, SPY_component

def load_calendar_from_database(SPY_component):
    SPY_component = database.get_sp500_symbols()
    database.create_table(['earnings_calendar'])
    if database.check_table_empty('earnings_calendar'):
        try:
            # table, SPY_component = load_earnings_impact(SPY_component)
            table, _ = load_local_earnings_impact(SPY_component)
        except:
            table, _ = load_local_earnings_impact(SPY_component)
        table = table[table['ticker'].isin(SPY_component)]
        for idx, row in table.iterrows():
            database.create_earnings_calendar(row['ticker'], row['startdatetime'], row['epssurprise'])
    else:
        select_stmt = 'SELECT symbol, date, surprise FROM earnings_calendar'
        table = database.execute_sql_statement(select_stmt)
        table.columns = ['ticker', 'startdatetime', 'epssurprise']
        table['startdatetime'] = table['startdatetime'].apply(lambda x: datetime.strptime(x[:10], '%Y-%m-%d'))
    return table

def slice_period_group(table, date_from, date_to):
    date_from = datetime.strptime(date_from, '%Y%m%d')
    date_to = datetime.strptime(date_to, '%Y%m%d')

    earnings_calendar = table.dropna(subset=['epssurprise'])
    earnings_calendar = earnings_calendar.loc[earnings_calendar['startdatetime'].between(date_from, date_to)]
    earnings_calendar.drop_duplicates(subset=['ticker'], keep='last', inplace=True)
    earnings_calendar.set_index('ticker', inplace=True)

    tickers, surprise = list(earnings_calendar.index), list(earnings_calendar['epssurprise'])
    tickers = list(np.array(tickers)[np.argsort(surprise)])
    num = int(len(tickers) / 3)
    lose, draw, beat = tickers[:num], tickers[num:2 * num], tickers[2 * num:]
    return lose, draw, beat, earnings_calendar


def group_to_array(lose, draw, beat, earnings_calendar, returns):
    lose_arr = np.zeros((len(lose), 60))
    for i, ticker in enumerate(lose):
        date = earnings_calendar.loc[ticker]['startdatetime']
        if date in list(returns.index) and ticker in list(returns.columns):
            ind = list(returns.index).index(date)
            lose_arr[i] = np.array(returns[ticker].iloc[ind - 30:ind + 30])
        else:
            print(ticker, date)
    draw_arr = np.zeros((len(draw), 60))
    for i, ticker in enumerate(draw):
        date = earnings_calendar.loc[ticker]['startdatetime']
        if date in list(returns.index) and ticker in list(returns.columns):
            ind = list(returns.index).index(date)
            draw_arr[i] = np.array(returns[ticker].iloc[ind - 30:ind + 30])
        else:
            print(ticker, date)
    beat_arr = np.zeros((len(beat), 60))
    for i, ticker in enumerate(beat):
        date = earnings_calendar.loc[ticker]['startdatetime']
        if date in list(returns.index) and ticker in list(returns.columns):
            ind = list(returns.index).index(date)
            beat_arr[i] = np.array(returns[ticker].iloc[ind - 30:ind + 30])
        else:
            print(ticker, date)
    return lose_arr, draw_arr, beat_arr


def OneSample(arr):
    length = arr.shape[-1]
    arr, result = np.array(arr), np.zeros(length)
    for i in range(30):
        rand = random.randint(0, length)
        temp = arr[rand]
        result = (i / (i + 1.0)) * result + (1 / (i + 1.0)) * temp
    return result


def BootStrap(arr):
    length = arr.shape[-1]
    arr, result = np.array(arr), np.zeros(length)
    for k in range(30):
        result = (k / (k + 1.0)) * result + (1 / (k + 1.0)) * np.cumsum(OneSample(arr))
    return result


class EarningsImpactData:
    def __init__(self):
        self.Beat = []
        self.Meet = []
        self.Miss = []


earnings_impact_data = EarningsImpactData()

### test code
# date_from = '20180101'
# date_to = '20180401'
#
# table, SPY_component = load_earnings_impact()
# returns = get_returns(SPY_component)
# lose, draw, beat, earnings_calendar = slice_period_group(table, date_from, date_to)
# lose_arr, draw_arr, beat_arr = group_to_array(lose, draw, beat, earnings_calendar, returns)
#
# plt.plot(lose_arr.mean(axis=0).cumsum(), label='lose')
# plt.plot(draw_arr.mean(axis=0).cumsum(), label='draw')
# plt.plot(beat_arr.mean(axis=0).cumsum(), label='beat')
# plt.legend(loc='best')
# plt.axvline(x=30, linewidth=1.0)
# plt.show()
# plt.close()
#
# plt.plot(BootStrap(lose_arr), label='lose')
# plt.plot(BootStrap(draw_arr), label='draw')
# plt.plot(BootStrap(beat_arr), label='beat')
# plt.legend(loc='best')
# plt.show()
# plt.close()

