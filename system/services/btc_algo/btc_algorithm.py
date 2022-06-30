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
    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
        pass

    @abstractmethod
    def signal(self) -> pd.DataFrame:
        """
        Calculates the signal based on the given timing.
        :return: The DataFrame including signal column.
        """
        pass

    @abstractmethod
    def graph(self):
        pass


class Filter(AlgorithmInterface):
    def __init__(self, data: pd.DataFrame, delta: float):
        """
        :param data: pandas.DataFrame
        :param delta: float
        """
        self.data = data
        self.delta = float(delta)

    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
        # if price_base is not open or close, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base not found")
        # calculate basic filter with formula: (price_base - price_base[1]) / price_base[1]
        self.data["indicator"] = self.data[price_base] / self.data[price_base].shift(1)
        self.data.fillna(0, inplace=True)
        return self.data

    def signal(self) -> pd.DataFrame:
        """
        Calculates the signal based on the given timing.
        Buy when indicator is greater than 1+delta and sell when indicator is less than 1-delta.
        :return: The DataFrame including signal column.
        """
        # if no indicator column, throw exception
        if "indicator" not in self.data.columns:
            raise Exception("No indicator calculated, please run indicator first")
        # if indicator is not 0, subtract 1
        self.data["indicator"] = self.data["indicator"].apply(lambda x: x - 1 if x != 0 else x)
        # if indicator is greater than delta, set signal to 1
        self.data["signal"] = np.where(self.data["indicator"] > self.delta, 1, 0)
        # if indicator is less than negative delta, set signal to -1
        self.data["signal"] = np.where(self.data["indicator"] < self.delta, -1, self.data["signal"])
        return self.data

    def graph(self):
        pass


class SMA(AlgorithmInterface):
    def __init__(self, data: pd.DataFrame, short_period: int, long_period: int, delta: float):
        """
        :param data: pandas.DataFrame
        :param short_period: int
        :param long_period: int
        :param delta: float
        """
        self.data = data
        self.short_period = int(short_period)
        self.long_period = int(long_period)
        self.delta = float(delta)

    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
        # if price_base is not open or close, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base not found")
        # calculate short simple moving average with formula: sum(data[i] * (1/short_period))
        short = self.data[price_base].rolling(self.short_period).mean()
        # calculate long simple moving average with formula: sum(data[i] * (1/long_period))
        long = self.data[price_base].rolling(self.long_period).mean()
        # calculate indicator with formula: (short - long) / long
        self.data["indicator"] = (short - long) / long
        self.data.fillna(0, inplace=True)
        return self.data

    def signal(self) -> pd.DataFrame:
        """
        Calculates the signal based on the given timing.
        Buy when indicator is greater than delta and sell when indicator is less than -delta.
        :return: The DataFrame including signal column.
        """
        # if no indicator column, throw exception
        if "indicator" not in self.data.columns:
            raise Exception("No indicator calculated, please run indicator first")
        # if indicator is greater than delta, set signal to 1
        self.data["signal"] = np.where(self.data["indicator"] > self.delta, 1, 0)
        # if indicator is less than negative delta, set signal to -1
        self.data["signal"] = np.where(self.data["indicator"] < self.delta, -1, self.data["signal"])
        return self.data

    def graph(self):
        pass


class EMA(AlgorithmInterface):
    def __init__(self, data: pd.DataFrame, short_period: int, long_period: int, delta: float):
        """
        :param data: pandas.DataFrame
        :param short_period: int
        :param long_period: int
        :param delta: float
        """
        self.data = data
        self.short_period = int(short_period)
        self.long_period = int(long_period)
        self.delta = float(delta)

    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
        # if price_base is not open or close, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base not found")
        # calculate short moving average with formula: sum(data[i] * (i+1) / (i+1+short_period))
        short = self.data[price_base].ewm(span=self.short_period, adjust=False).mean()
        # calculate long moving average with formula: sum(data[i] * (i+1) / (i+1+long_period))
        long = self.data[price_base].ewm(span=self.long_period, adjust=False).mean()
        # calculate indicator with formula: (short - long) / long
        self.data["indicator"] = (short - long) / long
        self.data.fillna(0, inplace=True)
        return self.data

    def signal(self) -> pd.DataFrame:
        """
        Calculates the signal based on the given timing.
        Buy when indicator is greater than delta and sell when indicator is less than -delta.
        :return: The DataFrame including signal column.
        """
        # if no indicator column, throw exception
        if "indicator" not in self.data.columns:
            raise Exception("No indicator calculated, please run indicator first")
        # if indicator is greater than delta, set signal to 1
        self.data["signal"] = np.where(self.data["indicator"] > self.delta, 1, 0)
        # if indicator is less than negative delta, set signal to -1
        self.data["signal"] = np.where(self.data["indicator"] < self.delta, -1, self.data["signal"])
        return self.data

    def graph(self):
        pass


class MACD(AlgorithmInterface):
    def __init__(self, data: pd.DataFrame, short_period: int = 12, long_period: int = 26, signal_period: int = 9):
        """
        :param data: pandas.DataFrame
        :param short_period: int
        :param long_period: int
        :param signal_period: int
        """
        self.data = data
        self.short_period = int(short_period)
        self.long_period = int(long_period)
        self.signal_period = int(signal_period)

    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
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

    def signal(self) -> pd.DataFrame:
        """
        Calculates the signal based on the given timing.
        Buy when MACD cross above MACD signal and sell when MACD cross below MACD signal.
        :return: The DataFrame including signal column.
        """
        # if no indicator column, throw exception
        if "indicator" not in self.data.columns:
            raise Exception("No indicator calculated, please run indicator first")
        # create a helper column to store the previous indicator value
        self.data["prev_indicator"] = self.data["indicator"].shift(1)
        # if indicator is positive and previous indicator is negative, set signal to 1
        self.data["signal"] = np.where((self.data["indicator"] > 0) & (self.data["prev_indicator"] < 0), 1, 0)
        # if indicator is negative and previous indicator is positive, set signal to -1
        self.data["signal"] = np.where((self.data["indicator"] < 0) & (self.data["prev_indicator"] > 0), -1, self.data["signal"])
        # drop the helper column
        self.data.drop("prev_indicator", axis=1, inplace=True)
        return self.data

    def graph(self):
        pass


class RSI(AlgorithmInterface):
    def __init__(self, data: pd.DataFrame, period: int, buy_threshold: int = 30, sell_threshold: int = 70, avg_type: str = "SMA"):
        """
        :param data: pandas.DataFrame
        :param period: int
        :param buy_threshold: int
        :param sell_threshold: int
        :param avg_type: str
        """
        self.data = data
        self.period = int(period)
        self.buy_threshold = int(buy_threshold)
        self.sell_threshold = int(sell_threshold)
        self.avg_type = avg_type

    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
        # if price_base is not open or close, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base not found")
        # calculate basic RSI with formula: 100 - 100 / (1 + avg(gain / loss))
        delta = self.data[price_base].diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        if self.avg_type == "SMA":
            up_avg = abs(up.rolling(self.period).mean())
            down_avg = abs(down.rolling(self.period).mean())
        elif self.avg_type == "EMA":
            up_avg = abs(up.ewm(span=self.period, adjust=False).mean())
            down_avg = abs(down.ewm(span=self.period, adjust=False).mean())
        else:
            raise Exception("Average type not found")
        rs = up_avg / down_avg
        rsi = 100 - (100 / (1 + rs))
        self.data["indicator"] = rsi
        self.data.fillna(0, inplace=True)
        return self.data

    def signal(self) -> pd.DataFrame:
        """
        Calculates the signal based on the given timing.
        Buy when RSI is under buy threshold and sell when RSI is over sell threshold.
        :return: The DataFrame including signal column.
        """
        # if no indicator column, throw exception
        if "indicator" not in self.data.columns:
            raise Exception("No indicator calculated, please run indicator first")
        # if indicator is over sell threshold, set signal to -1
        self.data["signal"] = np.where(self.data["indicator"] > self.sell_threshold, -1, 0)
        # if indicator is under buy threshold, set signal to 1
        self.data["signal"] = np.where(self.data["indicator"] < self.buy_threshold, 1, self.data["signal"])
        # set first periods days signal to 0
        self.data["signal"].iloc[:self.period] = 0
        return self.data

    def graph(self):
        pass


class KalmanFilter(AlgorithmInterface):
    def __init__(self, data: pd.DataFrame):
        """
        :param data: pandas.DataFrame
        """
        self.data = data

    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
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

    def signal(self) -> pd.DataFrame:
        """
        Calculates the signal based on the given timing.
        Buy when predict price cross above real price and sell when predict price cross below real price.
        """
        # if no indicator column, throw exception
        if "indicator" not in self.data.columns:
            raise Exception("No indicator calculated, please run indicator first")
        # create a helper column to store the previous indicator value
        self.data["prev_indicator"] = self.data["indicator"].shift(1)
        # if indicator is positive and previous indicator is negative, set signal to 1
        self.data["signal"] = np.where((self.data["indicator"] > 0) & (self.data["prev_indicator"] < 0), 1, 0)
        # if indicator is negative and previous indicator is positive, set signal to -1
        self.data["signal"] = np.where((self.data["indicator"] < 0) & (self.data["prev_indicator"] > 0), -1, self.data["signal"])
        # drop the helper column
        self.data.drop("prev_indicator", axis=1, inplace=True)
        return self.data

    def graph(self):
        pass


class LSTM(AlgorithmInterface):
    def __init__(self, data: pd.DataFrame):
        """
        :param data: pandas.DataFrame
        """
        self.data = data

    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
        pass

    def signal(self) -> pd.DataFrame:
        pass
