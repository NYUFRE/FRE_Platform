import os
import statistics
import random
import datetime as dt

from market_data.fre_market_data import EODMarketData
from database.fre_database import FREDatabase

#import pandas as pd
#import numpy as np

# from numpy.core._multiarray_umath import ndarray

SP500_NUM_OF_STOCKS = 505
PORTFOLIO_NUM_OF_STOCK = 11

fund = 1000000

os.environ["EOD_API_KEY"] = "5ba84ea974ab42.45160048"

if not os.environ.get("EOD_API_KEY"):
    raise RuntimeError("EOD_API_KEY not set")

start_date = dt.date(2010, 1, 1).strftime('%Y-%m-%d')
end_date = dt.datetime.today().strftime('%Y-%m-%d')

database = FREDatabase()
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)


class Trade:
    def __init__(self):
        self.date = ""
        self.open = 0.0
        self.high = 0.0
        self.low = 0.0
        self.close = 0.0
        self.adjusted_close = 0.0
        self.volume = 0

    '''
    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"
    '''


class Fundamental:
    def __init__(self):
        self.pe_ratio = 0.0
        self.dividend_yield = 0.0
        self.beta = 0.0
        self.high_52weeks = 0
        self.low_52weeks = 0
        self.ma_50days = 0
        self.ma_200days = 0

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"


class ProbationTestTrade:
    def __init__(self):
        self.open_date = ""
        self.close_date = ""
        self.open_price = 0.0
        self.close_price = 0.0
        self.shares = 0
        self.profit_loss = 0.0

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def calculate_profit_loss(self):
        self.profit_loss = (self.close_price - self.open_price) * self.shares

class Stock:
    def __init__(self):
        self.symbol = ""
        self.sector = ""
        self.expected_daily_return = 0.0
        self.expected_risk_free_rate = 0.0
        self.volatility = 0.0
        self.category_pct = 0.0

        self.cumulative_return = 0.0

        self.fundamental = Fundamental()

        self.trades = {}
        self.daily_returns = {}
        self.daily_risk_free_rates = {}
        self.daily_cumulative_returns = {}

        # self.backtest_trades = np.empty(dtype=BackTestTrade, order='C')
        #self.backtest_trades = []

        self.probation_test_trade = ProbationTestTrade()

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def add_trade(self, trade):
        self.trades[trade.date] = trade

    def calculate_daily_return(self):
        for date, trade in self.trades.items():
            self.daily_returns[date] = (trade.close - trade.open) / trade.open

    def calculate_risk_free_rate(self):
        for date, trade in self.trades.items():
            rate = pow((1 + trade.adjusted_close / 100), 1 / 252) - 1
            self.daily_risk_free_rates[date] = rate

    def calculate_expected_return(self):
        daily_returns = self.daily_returns.values()
        self.expected_daily_return = sum(daily_returns) / len(daily_returns)

    def calculate_expected_risk_free_rate(self):
        daily_rates = self.daily_risk_free_rates.values()
        self.expected_risk_free_rate = sum(daily_rates) / len(daily_rates)

    def calculate_volatility(self):
        daily_returns = self.daily_returns.values()
        self.volatility = statistics.stdev(daily_returns)

    def calculate_daily_cumulative_return(self, start_date, end_date):
        self.cumulative_return  = 0
        for date, trade in self.daily_returns.items():
            if date >= start_date and date <= end_date:
                self.daily_cumulative_returns[date] = self.daily_returns[date] + self.cumulative_return
                self.cumulative_return  = self.daily_cumulative_returns[date]
    '''
    def calculate_cumulative_return(self, start_date, end_date):
        for date, daily_return in self.daily_returns.items():
            if date >= start_date and date <= end_date:
                self.cumulative_return += daily_return
    '''

    '''
    def add_probation_trade(self, trade):
        self.probation_test_trades.append(trade)
        
    def calculate_profit_loss(self):
        for trade in self.probation_test_trades:
            self.profit_loss += trade.profit_loss
    '''

class GAPortfolio:
    def __init__(self):
        self.portfolio_yield = 0.0
        self.volatility = 0.0
        self.expected_daily_return = 0.0
        self.expected_beta = 0.0
        self.beta = 0.0
        self.trend = 0.0
        self.score = 0.0
        self.treynor_measure = 0.0
        self.sharpe_ratio = 0.0
        self.jensen_measure = 0.0
        self.cumulative_return = 0.0

        self.stocks = []
        self.portfolio_daily_returns = {}
        self.portfolio_daily_cumulative_returns = {}
        self.betas = {}

        self.profit_loss = 0.0

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def get_stock(self, index):
        return self.stocks[index]

    def update_stock(self, index, stock):
        self.stocks[index] = stock

    def add_beta(self, date, beta):
        self.betas[date] = beta

    def populate_portfolio(self, sp500_sector_list, sp500_stock_map):
        for i in range(PORTFOLIO_NUM_OF_STOCK):
            self.stocks.append(sp500_stock_map[sp500_sector_list[i]][random.randint(0, PORTFOLIO_NUM_OF_STOCK - 1)])

    def calculate_portfolio_daily_returns(self, sp500_sector_map):
        self.portfolio_daily_returns = self.stocks[0].daily_returns
        stock_weight = sp500_sector_map[self.stocks[0].sector]
        self.portfolio_daily_returns.update(
            (date, daily_return * stock_weight) for date, daily_return in self.portfolio_daily_returns.items())
        for i in range(1, PORTFOLIO_NUM_OF_STOCK):
            stock_weight = sp500_sector_map[self.stocks[i].sector]
            for date, daily_return in self.stocks[i].daily_returns.items():
                if date not in self.portfolio_daily_returns.keys():
                    self.portfolio_daily_returns[date] = 0
                self.portfolio_daily_returns[date] += stock_weight * self.stocks[i].daily_returns[date]

    def calculate_portfolio_daily_return(self):
        self.portfolio_daily_returns = self.stocks[0].daily_returns
        stock_weight = self.stocks[0].category_pct
        self.portfolio_daily_returns.update(
            (date, daily_return * stock_weight) for date, daily_return in self.portfolio_daily_returns.items())
        for i in range(1, PORTFOLIO_NUM_OF_STOCK):
            stock_weight = self.stocks[i].category_pct
            for date, daily_return in self.stocks[i].daily_returns.items():
                if date not in self.portfolio_daily_returns.keys():
                    self.portfolio_daily_returns[date] = 0
                self.portfolio_daily_returns[date] += stock_weight * self.stocks[i].daily_returns[date]

    def calculate_portfolio_daily_beta(self, spy_daily_returns, daily_risk_free_returns):
        for date, daily_return in self.portfolio_daily_returns.items():
            if date in daily_risk_free_returns.keys() and date in daily_risk_free_returns.keys():
                beta = abs((daily_return - daily_risk_free_returns[date]) / (
                            spy_daily_returns[date] - daily_risk_free_returns[date]))
                self.add_beta(date, beta)

    def calculate_expected_beta(self):
        daily_betas = self.betas.values()
        self.expected_beta = sum(daily_betas) / len(daily_betas)

    def calculate_expected_return(self):
        self.expected_daily_return = sum(self.portfolio_daily_returns.values()) / len(
            self.portfolio_daily_returns.values())

    def calculate_volatility(self):
        self.volatility = statistics.stdev(self.portfolio_daily_returns.values())

    def calculate_sharpe_ratio(self, us10y):
        self.sharpe_ratio = (self.expected_daily_return - us10y.expected_daily_return) / self.volatility

    def calculate_treynor_measure(self, us10y):
        self.treynor_measure = (self.expected_daily_return - us10y.expected_daily_return) / self.expected_beta

    def calculate_jensen_measure(self, spy, us10y):
        benchmark_return = us10y.expected_daily_return + spy.fundamental.beta * (
                    spy.expected_daily_return - us10y.expected_daily_return)
        self.jensen_measure = self.expected_daily_return - benchmark_return

    def calculate_yield(self, sp500_sector_map):
        for i in range(PORTFOLIO_NUM_OF_STOCK):
            self.portfolio_yield += sp500_sector_map[self.stocks[i].sector] * self.stocks[i].fundamental.dividend_yield

    def calculate_beta_and_trend(self, sp500_sector_map):
        for i in range(len(self.stocks)):
            self.beta += sp500_sector_map[self.stocks[i].sector] * self.stocks[i].fundamental.beta
            if self.stocks[i].fundamental.ma_200days < self.stocks[i].fundamental.ma_50days:
                self.trend += sp500_sector_map[self.stocks[i].sector]
            else:
                self.trend -= sp500_sector_map[self.stocks[i].sector]

    def calculate_score(self, spy):
        spy_yield = spy.fundamental.dividend_yield
        spy_beta = spy.fundamental.beta
        spy_volatility = spy.volatility
        self.score = (self.portfolio_yield - spy_yield) + (spy_beta - self.beta) + self.trend + \
                     self.volatility / spy_volatility + \
                     self.sharpe_ratio + self.treynor_measure + self.jensen_measure
    '''
    def calculate_cumulative_return(self, start_date, end_date):
        for date, daily_return in self.portfolio_daily_returns.items():
            if date >= start_date and date <= end_date:
                self.cumulative_return += daily_return
    '''

    def calculate_daily_cumulative_return(self, start_date, end_date):
        self.cumulative_return = 0
        for date, daily_return in self.portfolio_daily_returns.items():
            if date >= start_date and date <= end_date:
                self.portfolio_daily_cumulative_returns[date] = self.portfolio_daily_returns[date] + self.cumulative_return
                self.cumulative_return = self.portfolio_daily_cumulative_returns[date]

    def calculate_profit_loss(self):
        for stock in self.stocks:
            self.profit_loss += stock.probation_test_trade.profit_loss
