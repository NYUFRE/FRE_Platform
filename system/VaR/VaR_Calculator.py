import pandas as pd

from system import database
import yfinance as yf
from typing import *
import datetime
import numpy as np
from matplotlib import pyplot as plt
from arch import arch_model
from scipy.stats import t, rv_continuous
from scipy import optimize
import random
from flask import session
from system import eod_market_data
from scipy.optimize import minimize

pd.options.mode.chained_assignment = None  # default='warn'
# Cache data for stock returns
port_returns_data = dict()
class VaR:
    def __init__(self, confidence_level: int, days: int = 1) -> None:
        self.confidence_level = confidence_level
        self.days = days
        self.portfolio = database.get_portfolio(session['user_id'])
        self.symbols = self.portfolio['symbol']
        self.shares = self.portfolio['shares']

    @classmethod
    def port_return(cls, symbols: List[str], shares: List[int], interval: int = 1) -> pd.DataFrame:
        '''
        :param symbols: List of ticker
        :param shares:
        :param period:
        :return: dataframe of returns
        '''
        # Get cached data if available
        global port_returns_data
        if port_returns_data.get(tuple(symbols + shares), None) is not None:
            cached_date = port_returns_data[tuple(symbols + shares)].index[-1].to_pydatetime().strftime('%Y-%m-%d')
            calculating_date = [(datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in [0, 1]]
        cached = port_returns_data.get(tuple(symbols + shares), None) is not None and cached_date in calculating_date
        if cached:
            return port_returns_data[tuple(symbols + shares)]

        if len(symbols) == 0:
            return None

        data = pd.DataFrame(eod_market_data.get_daily_data(symbol=symbols[0], start='', end='', category='US'))\
                                [['date', 'adjusted_close']]
        data['date'] = pd.to_datetime(data.date)
        data.columns = ['date', symbols[0]]

        for symbol in symbols[1:]:
            tickerData = pd.DataFrame(eod_market_data.get_daily_data(symbol=symbol, start='', end='', category='US'))\
                                [['date', 'adjusted_close']]
            tickerData['date'] = pd.to_datetime(tickerData.date)
            tickerData.columns = ['date', symbol]

            if len(data) > len(tickerData):
                data = pd.merge_asof(data, tickerData, left_on='date', right_on='date', direction='forward')
            else:
                data = pd.merge_asof(tickerData, data, left_on='date', right_on='date', direction='forward')

        data.index = data['date']
        data = data[symbols].pct_change(periods=interval).dropna()
        port_weight = [share / np.sum(shares) for share in shares]
        data['port_returns'] = data.dot(port_weight)
        port_returns_data[tuple(symbols + shares)] = data[['port_returns']] # save result into cache

        return data[['port_returns']]


    def historical_simulation_method(self, window: int = 1000) -> Tuple[float, float, pd.DataFrame]:
        '''
        This method totally bases on historical return of given portfolio.
        It sorts the returns of portfolio and pick the percentile value corresponding to confidence level
        :return: VaR, expected loss
        '''
        # Calculate portfolio return
        port_returns = VaR.port_return(self.symbols, self.shares)
        if port_returns is None: return 0, 0, None

        # Calculate historical VaR (for plotting purpose)
        percentile_select = lambda x: np.percentile(x, 100 - self.confidence_level)
        port_returns['VaR'] = port_returns['port_returns'].rolling(window).apply(percentile_select)

        # Calculate VaR and Expected Shortfall
        VaR_value = np.percentile(port_returns['port_returns'][-window:], 100 - self.confidence_level)
        expected_shortfall = np.mean([port_return for port_return in port_returns['port_returns'][-window:]\
                                      if port_return < VaR_value])
        # Adjust for days
        VaR_value = min(VaR_value * np.sqrt(self.days), 1)
        expected_shortfall = min(expected_shortfall * np.sqrt(self.days), 1)

        return round(VaR_value*100, 4), round(expected_shortfall*100, 4), port_returns


    def GARCH_method(self, window: int = 1000) -> Tuple[float, float, pd.DataFrame]:
        '''
        This method use GARCH model to forecast stock volatility before establish return distribution
        :return: VaR, expected loss
        '''
        from arch.__future__ import reindexing
        # Calculate portfolio parameters( 1. returns; 2. mean return; 3. standard deviation)
        port_returns = VaR.port_return(self.symbols, self.shares)
        if port_returns is None: return 0, 0, None

        port_returns = port_returns[-window:] if window <= len(port_returns) else port_returns
        ## Rescale for optimization
        port_returns['port_returns_rescaled'] = port_returns['port_returns'] * 100

        # Calculate conditional volatility based on GARCH model (using 'arch' library)
        ## specify GARCH model assumptions
        garch_model_spec = arch_model(port_returns['port_returns_rescaled'], p=1, q=1, mean='constant', vol='GARCH', dist='StudentsT')
        ## Fit the model
        garch_model = garch_model_spec.fit(disp='off')
        ## Forecasting data
        garch_forecast = garch_model.forecast(horizon=1)

        # Calculate params
        mean_port_return = np.mean(port_returns['port_returns_rescaled'])
        forecast_std = np.sqrt(garch_forecast.variance['h.' + str(1)].iloc[-1])

        # Calculate VaR, expected shortfall
        VaR_value = t.ppf(1-self.confidence_level*0.01, df=len(port_returns)-1, loc = mean_port_return, scale=forecast_std)
        expected_shortfall = t.expect(args=(len(port_returns)-1,), loc=mean_port_return, scale=forecast_std, ub=VaR_value, conditional=True)
        # Adjust for days
        VaR_value = min(VaR_value * np.sqrt(self.days), 1)
        expected_shortfall = min(expected_shortfall * np.sqrt(self.days), 1)

        # Populate historical VaR_GARCH (current with forward looking bias else it takes too much time to fit every time)
        port_returns['sigma2'] = 0
        port_returns.iloc[0,2] = port_returns['port_returns_rescaled'].var()
        for i in range(1, len(port_returns)):
            port_returns.iloc[i, 2] = garch_model.params['omega'] + \
                garch_model.params['alpha[1]'] * port_returns.iloc[i-1,1]**2 + \
                garch_model.params['beta[1]'] * port_returns.iloc[i-1,2]
        port_returns['sigma'] = port_returns['sigma2']**0.5
        port_returns['VaR'] = -port_returns['sigma'] * t(garch_model.params['nu']).ppf(1-self.confidence_level*0.01) * \
                              ((garch_model.params['nu'] - 2)/(garch_model.params['nu']))**0.5
        port_returns['VaR'] = -port_returns['VaR']*np.sqrt(self.days)/100

        return round(VaR_value,4), round(expected_shortfall,4), port_returns


    def extreme_value_method(self, window: int = 1000) -> Tuple[float, float]:
        '''

        :return: VaR, expected loss
        '''

        # Calculate portfolio return
        port_returns = VaR.port_return(self.symbols, self.shares)
        if port_returns is None: return 0, 0, None

        port_returns = port_returns[-window:] if window <= len(port_returns) else port_returns

        # Find the start of the tails <- Fit t-distribution to historical portfolio return
        fit_df, fit_loc, fit_scale = t.fit(port_returns['port_returns']) # (df, loc, scale)
        return_lower_tail = t.ppf(1-self.confidence_level*0.01, df=fit_df, loc=fit_loc, scale=fit_scale)
        return_upper_tail = t.ppf(self.confidence_level*0.01, df=fit_df, loc=fit_loc, scale=fit_scale)
        # Need GARCH fit to better predict the volatility

        # Simulate return
        n_sim = 100000
        sim_port_returns = []

        for i in range(n_sim):
            rand_return = random.choice(port_returns['port_returns']) # Random select past return
            if rand_return < return_lower_tail:
                # Draw return from t-distribution lower tail
                sim_tail_return = t.rvs(df=fit_df, loc=fit_loc, scale=fit_scale) # bug: not select point at wanted tail
                sim_port_returns.append(sim_tail_return)
            else:
                if rand_return > return_upper_tail:
                    # Draw return from t-distribution upper tail
                    sim_tail_return = t.rvs(df=fit_df, loc=fit_loc, scale=fit_scale) # bug: not select point at wanted tail
                    sim_port_returns.append(sim_tail_return)
                else:
                    # keep rand_return
                    sim_port_returns.append(rand_return)
        print(len(sim_port_returns))

        # Calculate VaR and ES
        VaR_value = np.percentile(sim_port_returns, 100-self.confidence_level)
        expected_shortfall = np.mean([sim_return for sim_return in sim_port_returns if sim_return < VaR_value])

        # Adjust for days
        VaR_value = min(VaR_value * np.sqrt(self.days), 1)
        expected_shortfall = min(expected_shortfall * np.sqrt(self.days), 1)

        # Populate historical VaR --

        return round(VaR_value * 100,4) , round(expected_shortfall * 100,4), None

    def caviar_SAV(self, window: int = 1000) -> Tuple[float, float, pd.DataFrame]:
        # Calculate portfolio returns
        port_returns = VaR.port_return(self.symbols, self.shares)
        if port_returns is None: return 0, 0, None

        port_returns = port_returns[-window:] if window <= len(port_returns) else port_returns

        # historical var -> use as first value
        emp_quantile = np.percentile(port_returns['port_returns'], 1 - self.confidence_level*0.01)
        port_returns['VaR'] = emp_quantile

        # Fit SAV model by LAD
        def cost_function(beta):
            x = np.array(port_returns['port_returns'], dtype=np.float64)
            y = np.array([emp_quantile for i in range(len(x))], dtype=np.float64)
            theta = 1 - self.confidence_level*0.01

            for i in range(1, len(x)):
                y[i] = beta[0] + beta[1]*y[i-1] + beta[2]*abs(x[i-1])
            cost = 0
            for i in range(len(x)):
                indi = 1 if x[i] < y[i] else 0
                cost += (theta - indi) * (x[i]-y[i])

            return cost/len(x)

        beta = [random.uniform(0,1),random.uniform(0,1),random.uniform(0,1),random.uniform(0,1)]
        output = minimize(cost_function, beta, method='Nelder-Mead', tol=1e-10)
        beta = output.x

        for i in range(1, len(port_returns)):
            port_returns['VaR'][i] = beta[0] + beta[1]*port_returns['VaR'][i-1] + \
                                      beta[2]*abs(port_returns['port_returns'][i-1])

        VaR_value = beta[0] + beta[1]*port_returns['VaR'][-1] + beta[2]*abs(port_returns['port_returns'][-1])
        expected_shortfall = (1 + np.exp(min(beta))) * VaR_value # min here only try to get a small arbitrary number (not theoretical based)

        # Adjust for days
        for i in range(len(port_returns)):
            port_returns['VaR'][i] = port_returns['VaR'][i] * np.sqrt(self.days)
        VaR_value = min(VaR_value * np.sqrt(self.days), 1)
        expected_shortfall = min(expected_shortfall * np.sqrt(self.days), 1)

        return round(VaR_value*100, 4), round(expected_shortfall*100, 4), port_returns


    def caviar_AS(self, window: int = 1000) -> Tuple[float, float, pd.DataFrame]:
        # Calculate portfolio returns
        port_returns = VaR.port_return(self.symbols, self.shares)
        if port_returns is None: return 0, 0, None

        port_returns = port_returns[-window:] if window <= len(port_returns) else port_returns

        # historical var -> use as first value
        emp_quantile = np.percentile(port_returns['port_returns'], 1 - self.confidence_level*0.01)
        port_returns['VaR'] = emp_quantile

        def cost_function_as(beta): # f(x, y, params)
            x = np.array(port_returns['port_returns'], dtype=np.float64)
            y = np.array([emp_quantile for i in range(len(x))], dtype=np.float64)
            theta = 1 - self.confidence_level*0.01

            for i in range(1, len(x)):
                x_plus = x[i-1] if x[i-1] >= 0 else 0
                x_minus = x[i-1] if x[i-1] <= 0 else 0
                y[i] = beta[0] + beta[1]*y[i-1] + beta[2]*x_plus + beta[3]*x_minus

            cost = 0
            for i in range(len(x)):
                indi = 1 if x[i] < y[i] else 0
                cost += (theta - indi) * (x[i]-y[i])

            return cost/len(x)

        random.seed(1)
        beta = [random.uniform(0,1),random.uniform(0,1),random.uniform(0,1),random.uniform(0,1)]
        output = minimize(cost_function_as, beta, method='Nelder-Mead',tol=1e-10)
        output.x

        beta_as = output.x
        for i in range(1, len(port_returns)):
          return_plus = port_returns['port_returns'][i-1] if port_returns['port_returns'][i-1] >= 0 else 0
          return_minus = port_returns['port_returns'][i-1] if port_returns['port_returns'][i-1] <= 0 else 0
          port_returns['VaR'][i] = (beta_as[0] + beta_as[1]*port_returns['VaR'][i-1] + \
                                   beta_as[2]*return_plus + beta_as[3]*return_minus) # self.days

        return_plus = port_returns['port_returns'][-1] if port_returns['port_returns'][-1] >= 0 else 0
        return_minus = port_returns['port_returns'][-1] if port_returns['port_returns'][-1] <= 0 else 0
        VaR_value = beta_as[0] + beta_as[1]*port_returns['VaR'][-1] + \
                    beta_as[2]* return_plus + beta_as[3]* return_minus
        expected_shortfall = (1 + np.exp(min(beta))) * VaR_value # min here only try to get a small arbitrary number (not theoretical based)

        # Adjust for day
        for i in range(len(port_returns)):
            port_returns['VaR'][i] = port_returns['VaR'][i] * np.sqrt(self.days)
        VaR_value = min(VaR_value * np.sqrt(self.days), 1)
        expected_shortfall = min(expected_shortfall * np.sqrt(self.days), 1)

        return round(VaR_value * 100,4), round(expected_shortfall*100, 4), port_returns

def set_risk_threshold(database, threshold: Dict) -> bool:
    '''
    Create a table in database storing risk thresholds
    '''
    if threshold['enable_threshold'] is not None:
        threshold_df = pd.DataFrame(threshold, index=[0])
        tables = ['risk_threshold']
        database.create_table(tables)
        database.clear_table(tables)
        print('in set risk\n', threshold_df)
        threshold_df.to_sql('risk_threshold', con=database.engine, if_exists='replace', index=False)
        return True
    else:
        database.clear_table(['risk_threshold'])
        return False


# data storage for plotting
class VaR_data:
    def __init__(self):
        self.date = []
        self.port_returns = []
        self.VaR = []

var_data = VaR_data()
