from abc import ABCMeta, abstractmethod

import numpy as np
import pandas as pd
import scipy.signal


class AlgorithmFactory:
    @staticmethod
    def create_algorithm(*args):
        """
        Creates an algorithm object based on the given parameters.
        :param args: The parameters for the algorithm.
        :return: The algorithm object.
        """
        if args[0] == "Filter":
            return Filter(*args[1:])
        elif args[0] == "SMA":
            return SMA(*args[1:])
        elif args[0] == "EMA":
            return EMA(*args[1:])
        elif args[0] == "MACD":
            return MACD(*args[1:])
        elif args[0] == "RSI":
            return RSI(*args[1:])
        elif args[0] == "KalmanFilter":
            return KalmanFilter(*args[1:])
        elif args[0] == "LSTM":
            return LSTM(*args[1:])
        else:
            raise Exception("Algorithm not found")


class AlgorithmInterface(metaclass=ABCMeta):
    """
    The interface for all algorithms.
    """
    @abstractmethod
    def indicator(self, price_base):
        pass

    @abstractmethod
    def signal(self, timing):
        pass


class Filter(AlgorithmInterface):
    def __init__(self, data, delta):
        """
        :param data: pandas.DataFrame
        :param delta: float
        """
        self.data = data
        self.delta = delta

    def indicator(self, price_base):
        # if price_base is not open or close, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base not found")
        # calculate basic filter with formula: (price_base - price_base[1]) / price_base[1]
        self.data["indicator"] = self.data[price_base] / self.data[price_base].shift(1)
        self.data.fillna(0, inplace=True)
        return self.data

    def signal(self, timing):
        # if no indicator, throw exception
        if "indicator" not in self.data.columns:
            raise Exception("No indicator calculated, please run indicator first")
        # if indicator is not 0, subtract 1
        self.data["indicator"] = self.data["indicator"].apply(lambda x: x - 1 if x != 0 else x)
        if timing == "immediate":
            # if indicator is greater than delta, set signal to 1
            self.data["signal"] = np.where(self.data["indicator"] > self.delta, 1, 0)
            # if indicator is less than negative delta, set signal to -1
            self.data["signal"] = np.where(self.data["indicator"] < self.delta, -1, self.data["signal"])
            # if indicator is between delta and negative delta, set signal to 0
            self.data["signal"] = np.where(np.abs(self.data["indicator"]) <= self.delta, 0, self.data["signal"])
            return self.data
        elif timing == "mean reversion":
            # if indicator is not local minimum or maximum, set signal to 0
            self.data["signal"] = pd.Series(0, index=self.data.index)
            # if indicator is local minimum, set signal to 1
            self.data["signal"].iloc[list(scipy.signal.argrelextrema(np.array(self.data["indicator"]), np.less))] = 1
            # if indicator is local maximum, set signal to -1
            self.data["signal"].iloc[list(scipy.signal.argrelextrema(np.array(self.data["indicator"]), np.greater))] = -1
            return self.data


class SMA(AlgorithmInterface):
    def __init__(self, data, period):
        self.data = data
        self.period = period

    def indicator(self, price_base):
        # if price_base is not open or close, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base not found")
        # calculate basic SMA with formula: sum(price_base) / period
        self.data["indicator"] = self.data[price_base].rolling(self.period).mean()
        self.data.fillna(0, inplace=True)
        return self.data

    def signal(self, timing):
        pass


class EMA(AlgorithmInterface):
    def __init__(self, data, period):
        self.data = data
        self.period = period

    def indicator(self, price_base):
        # if price_base is not open or close, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base not found")
        # calculate basic EMA with formula: (price_base[1] * (period - 1) + price_base * 2 / period) / (period + 1)
        self.data["indicator"] = self.data[price_base].ewm(span=self.period, adjust=False).mean()
        self.data.fillna(0, inplace=True)
        return self.data

    def signal(self, timing):
        pass


class MACD(AlgorithmInterface):
    def __init__(self, data, short_period=12, long_period=26, signal_period=9):
        self.data = data
        self.short_period = short_period
        self.long_period = long_period
        self.signal_period = signal_period

    def indicator(self, price_base):
        # if price_base is not open or close, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base not found")
        # calculate basic MACD with formula: EMA(short_period) - EMA(long_period)
        # MACD signal with formula: EMA(signal_period)
        # MACD histogram with formula: MACD - MACD signal
        macd = self.data[price_base].ewm(span=self.short_period, adjust=False).mean() - \
                self.data[price_base].ewm(span=self.long_period, adjust=False).mean()
        signal = macd.ewm(span=self.signal_period, adjust=False).mean()
        self.data["indicator"] = macd - signal
        self.data.fillna(0, inplace=True)
        return self.data

    def signal(self, timing):
        pass


class RSI(AlgorithmInterface):
    def __init__(self, data, period):
        self.data = data
        self.period = period

    def indicator(self, price_base):
        # if price_base is not open or close, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base not found")
        # calculate basic RSI with formula: 100 - 100 / (1 + sum(price_base[1] / price_base[period])
        delta = self.data[price_base].diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        up_sum = up.rolling(self.period).sum()
        down_sum = down.rolling(self.period).sum()
        rs = up_sum / down_sum
        rsi = 100 - (100 / (1 + rs))
        self.data["indicator"] = rsi
        self.data.fillna(0, inplace=True)
        return self.data

    def signal(self, timing):
        pass


class KalmanFilter(AlgorithmInterface):
    def __init__(self, data):
        self.data = data

    def indicator(self, price_base):
        # if price_base is not open or close, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base not found")
        # initialize kalman filter
        x = np.array([self.data[price_base][0], [0]])
        P = np.full((2, 2), 2 ** 2)
        Q = np.full((2, 2), 1 ** 2)
        F = np.array([[1, 1],
                    [0, 1]])
        R = np.array([[0.5 ** 2]])
        H = np.array([[1, 0]])

        real_price = []
        kf_price = []
        state = (x, P)
        for i in range(len(self.data[price_base])):
            prior = (np.matmul(F, state[0]), np.matmul(F, np.matmul(state[1], F.T)) + Q)
            z_pred = np.matmul(H, prior[0])
            y = self.data[price_base][i] - z_pred
            S = np.matmul(H, np.matmul(prior[1], H.T)) + R
            K = np.matmul(prior[1], np.matmul(H.T, np.linalg.inv(S)))
            post = (prior[0] + np.matmul(K, y), np.matmul((np.identity(prior[1].shape[0]) - np.matmul(K, H)), prior[1]))
            state = post
            real_price.append(self.data[price_base][i])
            kf_price.append(post[0][0][0])

        self.data["indicator"] = pd.Series(kf_price) - pd.Series(real_price)
        self.data.fillna(0, inplace=True)
        return self.data

    def signal(self, timing):
        pass


class LSTM(AlgorithmInterface):
    def __init__(self, data):
        self.data = data

    def indicator(self, price_base):
        pass

    def signal(self, timing):
        pass
