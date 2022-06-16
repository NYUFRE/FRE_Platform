import os
import warnings

import pandas as pd
from flask import render_template, request
from sqlalchemy.exc import SAWarning

from system.services.hf_trading.hf_trading import hf_trading_data

warnings.simplefilter(action='ignore', category=SAWarning)


import statsmodels.api as sm
from sklearn import preprocessing
from sklearn.linear_model import LinearRegression

def hf_trading_engine_service():
    input = {"Threshold": -0.00001}
    table_year_data = []
    x1 = []
    x2 = []
    x3 = []
    x4 = []
    x5 = []
    x6 = []
    t_stats1 = []
    t_stats2 = []
    t_stats3 = []
    t_stats4 = []
    t_stats5 = []
    t_stats6 = []

    project_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), "system")
    project_root = os.path.join(project_root, "hf_trading")
    label_path = os.path.join(os.path.join(project_root, "csv"), "label.csv")
    price_path = os.path.join(os.path.join(project_root, "csv"), "price.csv")

    df = pd.read_csv(label_path)
    price = pd.read_csv(price_path)
    price["Date"] = pd.to_datetime(price["Date"])
    price.index = price["Time"]
    df['Date'] = pd.to_datetime(df['Date'])

    column_names = ['OI', 'OI1', 'OI2', 'OI3', 'OI4', 'OI5', 't_stats1', 't_stats2', 't_stats3', 't_stats4',
                    't_stats5', 't_stats6']
    stats = pd.DataFrame(columns=column_names)
    for data in df.groupby('Date'):
        if len(data[1]) > 1000:
            X = data[1][['x1', 'x2', 'x3', 'x4', 'x5', 'x6']]
            y = data[1]['y']
            scaler = preprocessing.StandardScaler().fit(X)
            X = scaler.transform(X)
            X = sm.add_constant(X)
            model = sm.OLS(y, X)
            results = model.fit()
            x1.append(results.params[1])
            x2.append(results.params[2])
            x3.append(results.params[3])
            x4.append(results.params[4])
            x5.append(results.params[5])
            x6.append(results.params[6])

            t_stats1.append(results.tvalues[1])
            t_stats2.append(results.tvalues[2])
            t_stats3.append(results.tvalues[3])
            t_stats4.append(results.tvalues[4])
            t_stats5.append(results.tvalues[5])
            t_stats6.append(results.tvalues[6])

    stats['OI'] = x1
    stats['OI1'] = x2
    stats['OI2'] = x3
    stats['OI3'] = x4
    stats['OI4'] = x5
    stats['OI5'] = x6
    stats['t_stats1'] = t_stats1
    stats['t_stats2'] = t_stats2
    stats['t_stats3'] = t_stats3
    stats['t_stats4'] = t_stats4
    stats['t_stats5'] = t_stats5
    stats['t_stats6'] = t_stats6

    column_names = ["Average coefficient", "Percent_positive", 'Percent positive and signiﬁcant',
                    "Percent negative and signiﬁcant"]
    stats_final = pd.DataFrame(columns=column_names)
    stats_final["Average coefficient"] = [stats['OI'].mean(), stats['OI1'].mean(), stats['OI2'].mean(),
                                          stats['OI3'].mean(), stats['OI4'].mean(), stats['OI5'].mean()]
    stats_final["Percent_positive"] = [len(stats['OI'] > 0) / len(stats), len(stats['OI1'] > 0) / len(stats),
                                       len(stats['OI2'] > 0) / len(stats)
        , len(stats['OI3'] > 0) / len(stats), len(stats['OI4'] > 0) / len(stats),
                                       len(stats['OI5'] > 0) / len(stats)]

    stats_final["Percent positive and signiﬁcant"] = [
        len(stats[(stats['OI'] > 0) & (stats["t_stats1"] >= 1.96)]) / len(stats),
        len(stats[(stats['OI1'] > 0) & (stats["t_stats2"] >= 1.96)]) / len(stats),
        len(stats[(stats['OI2'] > 0) & (stats["t_stats3"] >= 1.96)]) / len(stats),
        len(stats[(stats['OI3'] > 0) & (stats["t_stats4"] >= 1.96)]) / len(stats),
        len(stats[(stats['OI4'] > 0) & (stats["t_stats5"] >= 1.96)]) / len(stats),
        len(stats[(stats['OI5'] > 0) & (stats["t_stats6"] >= 1.96)]) / len(stats)]

    stats_final["Percent negative and signiﬁcant"] = [
        len(stats[(stats['OI'] < 0) & (stats["t_stats1"] >= 1.96)]) / len(stats),
        len(stats[(stats['OI1'] < 0) & (stats["t_stats2"] >= 1.96)]) / len(stats),
        len(stats[(stats['OI2'] < 0) & (stats["t_stats3"] >= 1.96)]) / len(stats),
        len(stats[(stats['OI3'] < 0) & (stats["t_stats4"] >= 1.96)]) / len(stats),
        len(stats[(stats['OI4'] < 0) & (stats["t_stats5"] >= 1.96)]) / len(stats),
        len(stats[(stats['OI5'] < 0) & (stats["t_stats6"] >= 1.96)]) / len(stats)]

    class Backtest:
        def __init__(self, data):
            self.data = data
            self.cost = 0
            self.cash = 10000
            self.position = 0
            self.total = 10000
            self.trace = []

        def test(self):
            for index, row in self.data.iterrows():
                if row["y_pred"] > 0 and self.position == 0:
                    # print("buy at", row["mid_price"], index)
                    self.cost = row["mid_price"]
                    self.position = int(self.cash / self.cost)
                    self.cash = self.cash - int(self.cash / self.cost) * self.cost
                    self.total = self.cash + self.position * row["mid_price"]

                if self.position != 0:
                    if row["mid_price"] > self.cost or (row["mid_price"] / self.cost) - 1 < -0.00001:
                        # print("sell at ",row["mid_price"], "cost ", self.cost, index)
                        self.total = self.cash + self.position * row["mid_price"]
                        self.position = 0
                        self.cash = self.total
                self.trace.append(self.total)
            return self.trace

    if request.method == "POST":
        Rt = []
        Maxd = []
        Sr = []
        Rsk = []
        hf_trading_data.data_list = []
        Result = pd.DataFrame()
        count = 0

        for data in df.groupby('Date'):
            if len(data[1]) > 1000:
                count = count + 1
                print(count / 22)

                backtest_data = pd.DataFrame()

                X = data[1][['x1', 'x2', 'x3', 'x4', 'x5', 'x6']]
                y = data[1]['y']
                pos = int(0.6 * len(data[1]))
                X_train = X.iloc[:pos, :]
                y_train = y[:pos]
                X_test = X.iloc[pos:, :]
                y_test = y[pos:]

                test_date = data[1]['Date'][pos:]
                test_time = data[1]['Time'][pos:]

                regressor = LinearRegression()
                scaler = preprocessing.StandardScaler().fit(X_train)
                X_train = scaler.transform(X_train)
                X_test = scaler.transform(X_test)
                regressor.fit(X_train, y_train)  # training the algorithm
                backtest_data['Date'] = test_date
                backtest_data.index = test_time
                backtest_data['y_pred'] = regressor.predict(X_test)
                backtest_data['mid_price'] = (price[price["Date"] == test_date.values[0]].loc[test_time]["4352356"] +
                                              price[price["Date"] == test_date.values[0]].loc[test_time]["Ask"]) / 2
                #         backtest_data['Open'] = backtest_data['mid_price']
                #         backtest_data['High'] = backtest_data['mid_price']
                #         backtest_data['Low'] = backtest_data['mid_price']
                #         backtest_data['Close'] = backtest_data['mid_price']
                backtest_data = backtest_data.reset_index()

                bt = Backtest(backtest_data)
                result = pd.DataFrame(bt.test())
                hf_trading_data.data_list.append(result)

                Returni = (result.iloc[-1] / result.iloc[0] - 1).values[0]
                Maxdrop = (-((result.cummax() - result) /
                             result.cummax()).max()).values[0]
                sr = ((result.pct_change()).mean() / (result.pct_change()).std()).values[0]
                risk = ((result.pct_change()).std()).values[0]
                Rt.append(Returni)
                Maxd.append(Maxdrop)
                Sr.append(sr)
                Rsk.append(risk)

        Result["return"] = Rt
        Result["volatility"] = Rsk
        Result["Sharp_ratio"] = Sr
        Result["Max drawdown"] = Maxd
        return render_template("hf_trading_engine.html", input=input, table_year_data=stats_final, table_result=Result,
                               backtest=True, plot_ids=list(range(len(hf_trading_data.data_list))))

    return render_template("hf_trading_engine.html", input=input, table_year_data=stats_final, backtest=False,
                           plot_ids=[])