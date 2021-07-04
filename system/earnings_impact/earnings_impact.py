import datetime
from yahoo_earnings_calendar import YahooEarningsCalendar
import pandas as pd
from tqdm import tqdm
import numpy as np
import pandas_datareader.data as web
import datetime
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import random



def OneSample(arr):
    '''
    arr.shape = [num_ticker, num_days]
    '''
    length = arr.shape[-1]
    arr, result = np.array(arr), np.zeros(length)
    for i in range(30):
        rand = random.randint(0, length)
        temp = arr[rand]
        result = (i / (i + 1.0)) * result + (1 / (i + 1.0)) * temp
    return result

def BootStrap(arr):
    '''
    arr.shape = [num_ticker, num_days]
    '''
    length = arr.shape[-1]
    arr, result = np.array(arr), np.zeros(length)
    for k in range(30):
        result = (k / (k + 1.0)) * result + (1 / (k + 1.0)) * np.cumsum(OneSample(arr))
    return result


# get SP500 component
payload=pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
SPY_component = list(payload[0]['Symbol'])

# get earnings calendar of each stock
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

# concat the table
table = pd.concat(df, axis = 0)
table['startdatetime'] = table['startdatetime'].apply(lambda x: datetime.datetime.strptime(x[:10], '%Y-%m-%d'))
table['epssurprise'] = table['epsactual'] - table['epsestimate']
table = table[['ticker', 'startdatetime', 'epssurprise']]
for ticker in fail_ticker:
    SPY_component.remove(ticker)
table = table.dropna(subset=['epssurprise'])

# slice of a period of time
# two parameter in the web interface
date_from = '20180101'
date_to = '20180401'
date_from = datetime.datetime.strptime(date_from, '%Y%m%d')
date_to = datetime.datetime.strptime(date_to, '%Y%m%d')
earnings_calendar = table.dropna(subset=['epssurprise'])
earnings_calendar = earnings_calendar.loc[earnings_calendar['startdatetime'].between(date_from, date_to)]
earnings_calendar.drop_duplicates(subset=['ticker'], keep = 'last', inplace = True)
earnings_calendar.set_index('ticker', inplace = True)

# sort ticker according to surprise and group onto three
tickers, surprise = list(earnings_calendar['ticker']), list(earnings_calendar['epssurprise'])
tickers = list(np.array(tickers)[np.argsort(surprise)])
num = int(len(tickers)/3)
lose, draw, beat = tickers[:num], tickers[num:2*num], tickers[2*num:]

# get returns in this whole period
start = date_from - datetime.timedelta(days=60)
end = date_to + datetime.timedelta(days=60)
SP500 = web.DataReader(['sp500'], 'fred', start, end)
start = start.strftime('%m/%d/%Y')
end = end.strftime('%m/%d/%Y')
data = web.get_data_yahoo(SPY_component, start, end)['Adj Close']
data.dropna(axis = 1, inplace = True)
SPY_component = list(data.columns)
returns = pd.concat([SP500, data], axis = 1).dropna(axis = 0)
returns = (returns/returns.shift(1)-1).dropna(axis = 0)
returns = returns.sub(returns['sp500'], axis = 0)

# for each stock, locate the announcement date and get 60 returns nearby into a nparray
# operate through three group
lose_arr = np.zeros((len(lose), 60))
for i, ticker in enumerate(lose):
    date = earnings_calendar.loc[ticker]['startdatetime']
    if date in list(returns.index):
        ind = list(returns.index).index(date)
        lose_arr[i] = np.array(returns[ticker].iloc[ind-30:ind+30])
    else:
        pass
draw_arr = np.zeros((len(draw), 60))
for i, ticker in enumerate(draw):
    date = earnings_calendar.loc[ticker]['startdatetime']
    if date in list(returns.index):
        ind = list(returns.index).index(date)
        draw_arr[i] = np.array(returns[ticker].iloc[ind-30:ind+30])
    else:
        pass
beat_arr = np.zeros((len(beat), 60))
for i, ticker in enumerate(beat):
    date = earnings_calendar.loc[ticker]['startdatetime']
    if date in list(returns.index):
        ind = list(returns.index).index(date)
        beat_arr[i] = np.array(returns[ticker].iloc[ind-30:ind+30])
    else:
        pass

# simple mean plot
# plt.plot(lose_arr.mean(axis=0).cumsum(), label = 'lose')
# plt.plot(draw_arr.mean(axis=0).cumsum(), label = 'draw')
# plt.plot(beat_arr.mean(axis=0).cumsum(), label = 'beat')
# plt.legend(loc = 'best')
# plt.axvline(x=30, linewidth=1.0)
# plt.show()
# plt.close()

# bootstrap plot
# plt.plot(BootStrap(lose_arr), label = 'lose')
# plt.plot(BootStrap(draw_arr), label = 'draw')
# plt.plot(BootStrap(beat_arr), label = 'beat')
# plt.legend(loc = 'best')
# plt.show()
# plt.close()