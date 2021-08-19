import talib
from talib import abstract
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


def TALIB(data, func, t = False):
    # data.shape -> (date, symbol)
    data = np.array(data)
    alpha = np.zeros(data.shape)
    for i in range(data.shape[1]):
        if not t:
            alpha[:,i] = func(data[:,i])
        else:
            alpha[:, i] = func(data[:, i], timeperiod = t)
    return alpha

def orth(alpha):
    # 去极值，标准化
    lower = alpha.mean(axis=1) - 3 * alpha.std(axis=1)
    lower = np.array([lower for i in range(alpha.shape[1])]).T
    upper = alpha.mean(axis=1) + 3 * alpha.std(axis=1)
    upper = np.array([upper for i in range(alpha.shape[1])]).T
    alpha[alpha > upper] = upper[alpha > upper]
    alpha[alpha < lower] = lower[alpha < lower]

    alpha = alpha - alpha.mean(axis=1, keepdims = True)
    alpha = alpha / alpha.std(axis=1, keepdims = True)
    return alpha

def Test(alpha, target):
    days = alpha.index
    days = [datetime.strptime(str(x), '%Y-%m-%d').date() for x in days]
    alpha, target = np.array(alpha), np.array(target)
    alpha = orth(alpha)
    # beta = cov(x,y)/sig(x)^2
    # ic = cov(x,y)/sig(x)/sig(y)
    numerator = (alpha * target).sum(axis=1)
    beta = numerator / (alpha * alpha).sum(axis=1)
    ic = numerator / np.sqrt((alpha * alpha).sum(axis=1) * (target * target).sum(axis=1))

    # annual aggregation
    table = pd.DataFrame({'beta': beta, 'ic': ic}, index=days).fillna(0)
    table['year'] = [day.year for day in table.index]
    table_agg = table.groupby('year').mean()
    table_agg['icir'] = table[['ic', 'year']].groupby('year').apply(lambda x: np.sqrt(len(x)) * np.mean(x) / np.std(x))[
        'ic']
    table_agg.loc['ALL', :] = table_agg.mean(axis=0)
    table_agg.loc['ALL', 'icir'] = np.sqrt(len(table['ic'])) * np.mean(table['ic']) / np.std(table['ic'])

    # plt.figure(figsize=(15,4))
    # plt.subplot(1,2,1)
    # plt.grid(linestyle='-.')
    # plt.plot(table['beta'].cumsum())
    # plt.title('Simple beta cumsum')
    # plt.subplot(1,2,2)
    # plt.bar(table_agg.index[:-1], table_agg['ic'][:-1])
    # plt.title('Simple beta ic')
    # plt.show()
    # plt.close()

    return table, table_agg

class AlphaTestData:
    def __init__(self):
        self.table = pd.DataFrame()
        self.table_agg = pd.DataFrame()


alphatestdata = AlphaTestData()