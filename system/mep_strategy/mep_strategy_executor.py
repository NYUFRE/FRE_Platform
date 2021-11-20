import os
import requests
from io import StringIO
from datetime import datetime
import numpy as np
import pandas as pd
from system.mep_strategy import mep_common
from system.mep_strategy.mep_strategy import *
from system.mep_strategy.mep_order import *


class MEPStrategyExecutor:
    stock_data_cache = dict()

    def __init__(self, ticker, start_date, end_date, balance_init=pow(10, 5), alpha=.05, delta=1., gamma=1.):
        self.balance = balance_init
        self.balance_hist = [ self.balance, ]

        self.E = balance_init
        self.E_hist = [ self.E, ]

        self.ticker = ticker
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")

        assert((self.end_date - self.start_date).days > 200)

        self.EOD_URL = f"https://eodhistoricaldata.com/api/eod/{ticker}.US" \
            + f"?from={start_date}&to={end_date}&api_token={os.environ.get('EOD_API_KEY')}"

        key = (ticker, start_date, end_date)
        if key not in MEPStrategyExecutor.stock_data_cache:
            response = requests.get(self.EOD_URL)
            if response.status_code != 200:
                raise ValueError(f"StrategyExecutor EOD request failed. Status Code={response.status_code}")
            MEPStrategyExecutor.stock_data_cache[key] = response.text
        data = StringIO(MEPStrategyExecutor.stock_data_cache[key])

        self.df = pd.read_csv(data)
        self.df.set_index('Date', inplace=True)
        self.df.dropna(how='any', inplace=True)
        self.df.index = pd.to_datetime(self.df.index)

        self.open_orders = []
        self.order_hist = []

        self.position = 0
        self.position_hist = [ self.position, ]

        self.strategy = MEPStrategy(self.df['Open'], self.df['High'], self.df['Low'], self.df['Close'])

        self.alpha = alpha
        self.delta = delta
        self.gamma = gamma

    def process(self):
        signals = self.strategy.generate_signals()

        for d in self.df.index[1:]:
            price = self.df['Close'][d]
            hprice = self.df['High'][d]
            lprice = self.df['Low'][d]

            balance = self.balance
            position = self.position

            orders_to_remove = []
            # Process previous orders
            for i, order in enumerate(self.open_orders):
                order.check(hprice, lprice)
                if order.order_closed:
                    # Update balance and position
                    balance += order.order_pnl + order.order_fund
                    position -= order.order_shares
                    orders_to_remove.append(i)
            self.open_orders = [order for i, order in enumerate(self.open_orders) if i not in orders_to_remove]

            fund = self.alpha * balance
            shares = fund / price
            # Create new orders if there is any
            if d in signals and balance > 0:
                s = signals[d]

                if s == mep_common.TradeSignal.LONG:
                    dist = price - self.strategy.psars[d]
                    order = Order(mep_common.OrderType.BUY_ORDER, price, shares, \
                                  price + self.delta * dist, price - self.gamma * dist)
                    self.open_orders.append(order)
                    balance -= fund
                    position += shares

                else:
                    dist = self.strategy.psars[d] - price
                    order = Order(mep_common.OrderType.SELL_ORDER, price, shares, \
                                  price - self.delta * dist, price + self.gamma * dist)
                    self.open_orders.append(order)
                    balance += fund
                    position -= shares

            self.balance = balance
            self.position = position
            self.E = self.balance + self.position * price

            self.balance_hist.append(self.balance)
            self.E_hist.append(self.E)
            self.position_hist.append(self.position)
            self.order_hist.append((d, *self.open_orders))

    def annualized_return(self):
        T = (self.df.index[-1] - self.df.index[200]).days / 365
        R = max(0, self.E) / self.E_hist[0]
        ret_annualized = pow(R, 1/T) - 1
        return ret_annualized

    # 30-year treasury bill yield is around 2% per year
    def sharpe_ratio(self, rfr=.02):
        arr = np.array(self.E_hist[199:], dtype=float)
        E_ret = (arr[1:] - arr[:-1]) / arr[:-1]
        E_stdev = E_ret.std()
        E_vol = E_stdev * np.sqrt(252)
        return (self.annualized_return() - rfr) / E_vol

    @staticmethod
    def stock_available(ticker, start_date, end_date):
        url = f"https://eodhistoricaldata.com/api/eod/{ticker}.US" \
            + f"?from={start_date}&to={end_date}&api_token={os.environ.get('EOD_API_KEY')}"
        response = requests.get(url)

        return response.status_code == 200