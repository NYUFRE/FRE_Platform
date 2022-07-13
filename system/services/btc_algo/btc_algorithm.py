import time
from abc import ABCMeta, abstractmethod
from datetime import date, timedelta

import numpy as np
import pandas as pd
from tensorflow import keras
from keras import Sequential
from keras.layers import Dropout, Dense
from sklearn.preprocessing import MinMaxScaler


class BTCAlgorithmFactory:
    """
    This class is used to create algorithm.
    """
    @staticmethod
    def create_algorithm(**kwargs):
        """
        Creates an algorithm object based on the given parameters.
        :param kwargs: The parameters used to create the algorithm.
        :return: The algorithm object.
        """
        # Get the algorithm name.
        algorithm = kwargs.pop("algorithm", None)
        if algorithm is None:
            raise ValueError("The algorithm is not specified.")
        # Create the algorithm object.
        if algorithm == "Filter":
            return Filter(**kwargs)
        elif algorithm == "SMA":
            return SMA(**kwargs)
        elif algorithm == "EMA":
            return EMA(**kwargs)
        elif algorithm == "MACD":
            return MACD(**kwargs)
        elif algorithm == "RSI":
            return RSI(**kwargs)
        elif algorithm == "KalmanFilter":
            return KalmanFilter(**kwargs)
        elif algorithm == "GRU":
            return GRU(**kwargs)
        elif algorithm == "LSTM":
            return LSTM(**kwargs)
        elif algorithm == "Combination":
            return Combination(**kwargs)
        else:
            raise Exception("Algorithm not found")


class BTCAlgorithmInterface(metaclass=ABCMeta):
    """
    This class is an interface for all algorithms.
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


# Trend Strategy Algorithms
class Filter(BTCAlgorithmInterface):
    """
    Simple Filter Algorithm
    """
    def __init__(self, data: pd.DataFrame, delta: float = 0.1):
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
        self.data["signal"] = np.where(self.data["indicator"] < -self.delta, -1, self.data["signal"])
        return self.data


class SMA(BTCAlgorithmInterface):
    """
    Simple Moving Average Algorithm
    """
    def __init__(self, data: pd.DataFrame, short_period: int = 20, long_period: int = 50, delta: float = 0.1):
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
        self.data["signal"] = np.where(self.data["indicator"] < -self.delta, -1, self.data["signal"])
        return self.data


class EMA(BTCAlgorithmInterface):
    """
    Exponential Moving Average Algorithm
    """
    def __init__(self, data: pd.DataFrame, short_period: int = 20, long_period: int = 50, delta: float = 0.1):
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
        self.data["signal"] = np.where(self.data["indicator"] < -self.delta, -1, self.data["signal"])
        return self.data


# Momentum Strategy Algorithms
class MACD(BTCAlgorithmInterface):
    """
    Moving Average Convergence/Divergence Algorithm
    """
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


class RSI(BTCAlgorithmInterface):
    """
    Relative Strength Index Algorithm
    """
    def __init__(self, data: pd.DataFrame, period: int = 14, buy_threshold: int = 30, sell_threshold: int = 70, avg_type: str = "SMA"):
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


class KalmanFilter(BTCAlgorithmInterface):
    """
    Kalman Filter Algorithm
    """
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


# Machine Learning Strategy Algorithms
class GRU(BTCAlgorithmInterface):
    """
    GRU Algorithm
    """
    def __init__(self, data: pd.DataFrame, train_test_ratio: float = 0.2,
                 epochs: int = 100, batch_size: int = 32, level: int = 5,
                 dropout: bool = True, dropout_rate: float = 0.2, loss_function: str = "mse", optimizer: str = "adam"):
        """
        :param data: pandas.DataFrame
        :param train_test_ratio: float, the ratio of training data to test data.
        :param epochs: int, the number of epochs.
        :param batch_size: int, the batch size.
        :param level: int, the level of the RNN.
        :param dropout: bool, whether to use dropout.
        :param dropout_rate: float, the dropout rate.
        :param loss_function: str, the loss function.
        :param optimizer: str, the optimizer.
        """
        self.data = data
        self.train_test_ratio = float(train_test_ratio)
        self.epochs = int(epochs)
        self.batch_size = int(batch_size)
        self.dropout = bool(dropout)
        self.dropout_rate = float(dropout_rate)
        self.loss_function = loss_function
        self.optimizer = optimizer
        self.level = int(level)

    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
        # if price base is not in the data, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base is not in the data")
        # set keras random seed according to the current time
        np.random.seed(int(time.time()))
        # define start date and end date
        start_date = self.data.index[int(len(self.data) * self.train_test_ratio)]
        end_date = self.data.index[-1]
        # get the train and test data
        train_data = self.data.loc[:start_date, price_base].values
        train_data = np.array(train_data).reshape(-1, 1)
        test_data = self.data.loc[(date.fromisoformat(start_date) + timedelta(days=1)).strftime("%Y-%m-%d"):end_date, price_base].values
        test_data = np.array(test_data).reshape(-1, 1)
        # normalize the training data
        sc = MinMaxScaler(feature_range=(0, 1))
        sc_train_data = sc.fit_transform(train_data)
        # convert the training data to the LSTM format
        x_train = []
        y_train = []
        window = 60
        for i in range(window, sc_train_data.shape[0]):
            x_train.append(sc_train_data[i - window:i, 0])
            y_train.append(sc_train_data[i, :])
        x_train = np.array(x_train)
        y_train = np.array(y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
        # create the LSTM model
        model = Sequential()
        assert self.level >= 1
        if self.level == 1:
            model.add(keras.layers.GRU(units=50, return_sequences=False, input_shape=(x_train.shape[1], 1)))
            if self.dropout:
                model.add(Dropout(self.dropout_rate))
            model.add(Dense(units=1))
        elif self.level == 2:
            model.add(keras.layers.GRU(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
            if self.dropout:
                model.add(Dropout(self.dropout_rate))
            model.add(keras.layers.GRU(units=50, return_sequences=False))
            if self.dropout:
                model.add(Dropout(self.dropout_rate))
            model.add(Dense(units=1))
        else:
            model.add(keras.layers.GRU(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
            if self.dropout:
                model.add(Dropout(self.dropout_rate))
            for i in range(self.level - 2):
                model.add(keras.layers.GRU(units=50, return_sequences=True))
                if self.dropout:
                    model.add(Dropout(self.dropout_rate))
            model.add(keras.layers.GRU(units=50, return_sequences=False))
            if self.dropout:
                model.add(Dropout(self.dropout_rate))
            model.add(Dense(units=1))
        print(model.summary())
        # compile the model
        model.compile(loss=self.loss_function, optimizer=self.optimizer)
        # fit the model
        model.fit(x_train, y_train, epochs=self.epochs, batch_size=self.batch_size)
        # get the testing data ready
        test_data = np.array(test_data).reshape(-1, 1)
        sc_test_data = sc.transform(test_data)
        x_test = []
        for i in range(window, sc_test_data.shape[0]):
            x_test.append(sc_test_data[i - window:i, 0])
        x_test = np.array(x_test)
        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))
        # make the prediction
        predictions = model.predict(x_test)
        # inverse the normalization
        predictions = sc.inverse_transform(predictions)
        # add prediction column to the data based on start date and end date
        self.data.loc[(date.fromisoformat(start_date) + timedelta(days=61)).strftime("%Y-%m-%d"):end_date, "indicator"] = predictions
        # if indicator is not nan, set indicator to difference between price base column and indicator column
        self.data.loc[self.data["indicator"].notna(), "indicator"] = self.data["indicator"] - self.data[price_base]
        return self.data

    def signal(self) -> pd.DataFrame:
        """
        Calculates the signal based on the given timing.
        Buy when RNN is under buy threshold and sell when RNN is over sell threshold.
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


class LSTM(BTCAlgorithmInterface):
    """
    LSTM Algorithm
    """
    def __init__(self, data: pd.DataFrame, train_test_ratio: float = 0.2,
                 epochs: int = 100, batch_size: int = 32, level: int = 5,
                 dropout: bool = True, dropout_rate: float = 0.2, loss_function: str = "mse", optimizer: str = "adam"):
        """
        :param data: pandas.DataFrame
        :param train_test_ratio: float, the ratio of training data to test data.
        :param epochs: int, the number of epochs.
        :param batch_size: int, the batch size.
        :param level: int, the number of layers.
        :param dropout: bool, whether to use dropout.
        :param dropout_rate: float, the dropout rate.
        :param loss_function: str, the loss function.
        :param optimizer: str, the optimizer.
        """
        self.data = data
        self.train_test_ratio = float(train_test_ratio)
        self.epochs = int(epochs)
        self.batch_size = int(batch_size)
        self.dropout = bool(dropout)
        self.dropout_rate = float(dropout_rate)
        self.loss_function = loss_function
        self.optimizer = optimizer
        self.level = int(level)

    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
        # if price base is not in the data, throw exception
        if price_base not in self.data.columns:
            raise Exception("Price base is not in the data")
        # set keras random seed according to the current time
        np.random.seed(int(time.time()))
        # define start date and end date
        start_date = self.data.index[int(len(self.data) * self.train_test_ratio)]
        end_date = self.data.index[-1]
        # get the train and test data
        train_data = self.data.loc[:start_date, price_base].values
        train_data = np.array(train_data).reshape(-1, 1)
        test_data = self.data.loc[(date.fromisoformat(start_date) + timedelta(days=1)).strftime("%Y-%m-%d"):end_date, price_base].values
        test_data = np.array(test_data).reshape(-1, 1)
        # normalize the training data
        sc = MinMaxScaler(feature_range=(0, 1))
        sc_train_data = sc.fit_transform(train_data)
        # convert the training data to the LSTM format
        x_train = []
        y_train = []
        window = 60
        for i in range(window, sc_train_data.shape[0]):
            x_train.append(sc_train_data[i - window:i, 0])
            y_train.append(sc_train_data[i, :])
        x_train = np.array(x_train)
        y_train = np.array(y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
        # create the LSTM model
        model = Sequential()
        assert self.level >= 1
        if self.level == 1:
            model.add(keras.layers.LSTM(units=50, return_sequences=False, input_shape=(x_train.shape[1], 1)))
            if self.dropout:
                model.add(Dropout(self.dropout_rate))
            model.add(Dense(units=1))
        elif self.level == 2:
            model.add(keras.layers.LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
            if self.dropout:
                model.add(Dropout(self.dropout_rate))
            model.add(keras.layers.LSTM(units=50, return_sequences=False))
            if self.dropout:
                model.add(Dropout(self.dropout_rate))
            model.add(Dense(units=1))
        else:
            model.add(keras.layers.LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
            if self.dropout:
                model.add(Dropout(self.dropout_rate))
            for i in range(self.level - 2):
                model.add(keras.layers.LSTM(units=50, return_sequences=True))
                if self.dropout:
                    model.add(Dropout(self.dropout_rate))
            model.add(keras.layers.LSTM(units=50, return_sequences=False))
            if self.dropout:
                model.add(Dropout(self.dropout_rate))
            model.add(Dense(units=1))
        print(model.summary())
        # compile the model
        model.compile(loss=self.loss_function, optimizer=self.optimizer)
        # fit the model
        model.fit(x_train, y_train, epochs=self.epochs, batch_size=self.batch_size)
        # get the testing data ready
        test_data = np.array(test_data).reshape(-1, 1)
        sc_test_data = sc.transform(test_data)
        x_test = []
        for i in range(window, sc_test_data.shape[0]):
            x_test.append(sc_test_data[i - window:i, 0])
        x_test = np.array(x_test)
        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))
        # make the prediction
        predictions = model.predict(x_test)
        # inverse the normalization
        predictions = sc.inverse_transform(predictions)
        # add prediction column to the data based on start date and end date
        self.data.loc[(date.fromisoformat(start_date) + timedelta(days=61)).strftime("%Y-%m-%d"):end_date, "indicator"] = predictions
        # if indicator is not nan, set indicator to difference between price base column and indicator column
        self.data.loc[self.data["indicator"].notna(), "indicator"] = self.data["indicator"] - self.data[price_base]
        return self.data

    def signal(self) -> pd.DataFrame:
        """
        Calculates the signal based on the indicator.
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


# Combination Strategy
class Combination(BTCAlgorithmInterface):
    """
    Combination Algorithm
    """
    def __init__(self, data: pd.DataFrame, json_dict: dict):
        """
        :param data: pandas.DataFrame
        :param json_dict: The json dictionary of the combination strategy.
        """
        self.data = data.copy()
        self.algorithms = {}
        # parse the json parameters and create the algorithm objects
        for algo, params in json_dict.items():
            param_dict = {"algorithm": algo, "data": data}
            for param, param_value in params.items():
                param_dict[param] = param_value
            self.algorithms[algo] = BTCAlgorithmFactory.create_algorithm(**param_dict)

    def indicator(self, price_base: str) -> pd.DataFrame:
        """
        Calculates the indicator based on the given price base.
        :param price_base: The price base like open, close.
        :return: The DataFrame including indicator column.
        """
        # calculate the indicator for each algorithm
        indicator_list = [self.data]
        for algo, algo_obj in self.algorithms.items():
            indicator_list.append(algo_obj.indicator(price_base).rename(columns={"indicator": algo+"_indicator"})[algo+"_indicator"])
        # merge the indicator columns
        self.data = pd.concat(indicator_list, axis=1)
        return self.data

    def signal(self) -> pd.DataFrame:
        """
        Calculates the signal based on the given timing.
        Act when all the algorithms have same strategy.
        :return: The DataFrame including signal column.
        """
        # for each algorithm, check if they in self.data column and if not throw exception
        for algo in self.algorithms.keys():
            if algo+"_indicator" not in self.data.columns:
                raise Exception("No indicator calculated for {}".format(algo))
        # calculate the signal for each algorithm, if all have same signal, set signal for self.data to that signal
        signal_list = [self.data]
        signal_name_list = []
        for algo, algo_obj in self.algorithms.items():
            signal_list.append(algo_obj.signal().rename(columns={"signal": algo+"_signal"})[algo+"_signal"])
            # store the signal name for later calculation
            signal_name_list.append(algo+"_signal")
        # merge the signal columns
        self.data = pd.concat(signal_list, axis=1)
        # if the sum of the row equals to the number of algorithms, set signal to sell
        self.data["signal"] = np.where(self.data[signal_name_list].sum(axis=1) == len(self.algorithms.keys()), 1, 0)
        # if the sum of the row equals to the minus number of algorithms, set signal to buy
        self.data["signal"] = np.where(self.data[signal_name_list].sum(axis=1) == -len(self.algorithms.keys()), -1, self.data["signal"])
        return self.data
