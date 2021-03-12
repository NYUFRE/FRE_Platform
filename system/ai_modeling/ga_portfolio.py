import statistics
import random

from typing import List, Dict, Tuple

import pandas as pd
import numpy as np

SP500_NUM_OF_STOCKS = 505
PORTFOLIO_NUM_OF_STOCK = 11

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
        self.name = ""
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

        self.symbols = []   # List[str]
        self.weights = []   # List[float]

        self.shares = []    # List[int]
        self.start_date = ""
        self.end_date = ""
        self.pnl = []
        self.open_prices = []
        self.close_prices = []

        self.stocks = []    # list of tuple (sector, symbol, weight, name)        self.portfolio_daily_returns = {}
        self.portfolio_daily_returns = {}
        self.portfolio_daily_cumulative_returns = {}
        self.betas = {}

        self.profit_loss = 0.0

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"

    def get_stock(self, index: int) -> Tuple[str, str, float, str]:
        """
        Get stock with its index

        :param index: index of stock needed to return
        :type index: int
        :return: a tuple (sector, symbol, weight, name)
        :rtype: Tuple[str, str, float, str]
        """
        return self.stocks[index]

    def update_stock(self, index: int, stock: Tuple[str, str, float, str]) -> None:
        """
        Update stock with a new stock

        :param index: index of stock needed to update
        :type index: int
        :param stock: new stock (sector, symbol, weight, name)
        :type stock: Tuple[str, str, float, str]
        """
        self.stocks[index] = stock

    def add_beta(self, date, beta):
        self.betas[date] = beta

    def populate_portfolio(self, sp500_symbol_map: Dict[str, Tuple[str, str]], sp500_sector_map: Dict[str, float]) -> None:
        """
        Randomly select 11 symbols from each sector
        Store stock's information in self.stocks: (sector

        :param sp500_symbol_map: {sector:(symbol, name)}
        :type sp500_symbol_map: Dict[str, Tuple[str, str]]
        :param sp500_sector_map: {sector: weight}
        :type sp500_sector_map: Dict[str, float]
        """
        for sector, symbols in sp500_symbol_map.items():
            symbol, name = symbols[random.randint(0, len(symbols)-1)]
            weight = sp500_sector_map[sector]
            self.stocks.append((sector, symbol, weight, name))
        self.stocks.sort()  # Sort the list according to sectors

    def calculate_portfolio_return(self, price_df: pd.DataFrame) -> None:
        """
        Calculate portfolio daily return 
        Calculate cumulative daily return by cumulative product
        Calculate expected daily return by avg(daily return)
        Calculate daily volatility by std(daily return)       

        :param price_df: stock prices df
        :type price_df: pd.DataFrame
        """
        # Keep only data of stocks in the portfolio
        select_query = ' or '.join(f"symbol == '{val[1]}'" for val in self.stocks)
        self.price_df = price_df.query(select_query).copy()   
        # Calculate returns
        self.price_df['weighted_ret'] =  self.price_df['dailyret'] * self.price_df['weight']  # weight * daily return
        self.portfolio_daily_returns = self.price_df.groupby('date')['weighted_ret'].sum()
        self.expected_daily_return = self.portfolio_daily_returns.mean()
        self.volatility = self.portfolio_daily_returns.std()

    def populate_portfolio_by_symbols(self, symbols: List[str], price_df: pd.DataFrame) -> None:
        """
        Given symbols and prices dataframe, populate portfolio
        Also, calculate portfolio return

        :param symbols: A list of symbols
        :type symbols: List[str]
        :param price_df: A dataframe of prices
        :type price_df: pd.DataFrame
        """
        # Keep only portfolio stocks' data
        select_query = ' or '.join(f"symbol == '{symbol}'" for symbol in symbols)
        self.price_df = price_df.query(select_query).copy()

        # Calculate stocks' daily return
        self.price_df['dailyret'] = self.price_df.groupby('symbol')['close'].pct_change()
        self.price_df['dailyret'].fillna(self.price_df['close']/self.price_df['open']-1.0, inplace=True)
        self.price_df['date'] = pd.to_datetime(self.price_df['date'])
        self.price_df.set_index('date', inplace=True)

        # Calculate portoflio daily return
        self.price_df['weighted_ret'] = self.price_df['dailyret'] * self.price_df['weight']   # weight * daily return
        self.portfolio_daily_returns = self.price_df.groupby('date')['weighted_ret'].sum()
        self.portfolio_daily_cumulative_returns = (self.portfolio_daily_returns + 1.0).cumprod() - 1.0
        self.cumulative_return = self.portfolio_daily_cumulative_returns[-1]  # last day's cumulative return

    def calculate_expected_beta(self, spy_df: pd.DataFrame) -> None:
        """
        Calculate portfolio expected_beta by cov(r, rm) / var(rm)
        
        :param spy_df: SPY's prices dataframe
        :type spy_df: pd.DataFrame
        """
        df = pd.merge(pd.DataFrame(self.portfolio_daily_returns), spy_df, on = 'date', how = 'inner')
        self.expected_beta = df['weighted_ret'].cov(df['spy_dailyret']) / df['spy_dailyret'].var()
        

    def populate_portfolio_fundamentals(self, fundamental_df: pd.DataFrame) -> None:
        """
        Extract stocks' fundamental data from db and store in self.fundamental_df

        :param fundamental_df: A dataframe for sp500's fundamental data
        :type fundamental_df: pd.DataFrame
        """
        select_query = ' or '.join("symbol == '" + val[1] + "'" for val in self.stocks)
        self.fundamental_df = fundamental_df.query(select_query).copy()    

    def calculate_sharpe_ratio(self, us10y: Stock) -> None:
        self.sharpe_ratio = (self.expected_daily_return * 252 - us10y.expected_daily_return) / (self.volatility * np.sqrt(252)) # annualized

    def calculate_treynor_measure(self, us10y: Stock) -> None:
        self.treynor_measure = (self.expected_daily_return * 252 - us10y.expected_daily_return) / self.expected_beta

    def calculate_jensen_measure(self, spy: Stock, us10y: Stock) -> None:
        benchmark_return = us10y.expected_daily_return + self.expected_beta * (
                     spy.expected_daily_return * 252 - us10y.expected_daily_return)
        self.jensen_measure = self.expected_daily_return * 252 - benchmark_return   # Annualize

    def calculate_yield(self) -> None:
        """
        Sum of stock's yield * weight
        """
        self.portfolio_yield = sum(self.fundamental_df['dividend_yield'] * self.fundamental_df['weight'])

    def calculate_beta_and_trend(self) -> None:
        """
        Calculate portfolio's fundamental beta by sum(stock_beta * stock weight)
        Calculate trend by compare ma_200days and ma_50days
        """
        self.beta = sum(self.fundamental_df['beta'] * self.fundamental_df['weight'])
        indicator = self.fundamental_df.apply(lambda row : 1 if row['ma_200days'] < row['ma_50days'] else -1, axis=1)
        self.trend = sum(indicator * self.fundamental_df['weight'])


    def calculate_score(self, spy: Stock) -> None:
        spy_yield = spy.fundamental_df['dividend_yield'].iloc[0]
        spy_beta = spy.fundamental_df['beta'].iloc[0]
        spy_volatility = spy.volatility
        self.score = (self.portfolio_yield - spy_yield) + (spy_beta - self.beta) + self.trend + \
                     self.volatility / spy_volatility + \
                     self.sharpe_ratio + self.treynor_measure + self.jensen_measure
    
    def calculate_daily_cumulative_return(self, start_date: str, end_date: str) -> None:
        df = self.price_df.query("date >= '" + start_date + "' and date <= '" + end_date + "'")
        self.cumulative_return = ((df['weighted_ret'] + 1.0).cumprod() - 1.0).iloc[-1]
        
    # def calculate_profit_loss(self):
    #     for stock in self.stocks:
    #         self.profit_loss += stock.probation_test_trade.profit_loss
