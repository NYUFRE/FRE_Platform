import sys
import os
import urllib.request
import json

import pandas as pd

class IEXMarketData:
    def __init__(self, api_token):
        self.url_common = "https://cloud-sse.iexapis.com/stable/stock/"
        self.api_token = api_token

    def get_quote(self, symbol):
        quote = {}
        error = ""
        url = self.url_common + symbol + "/quote?token=" + self.api_token
        print(url)
        try:
            with urllib.request.urlopen(url) as req:
                data = json.load(req)
                if not data:
                    error = "symbol has no data"
                    return quote, error
                # print(data)
                quote["symbol"] = symbol

                if "iexBidPrice" in data.keys() and data["iexBidPrice"] != None and \
                        "iexAskPrice" in data.keys() and data["iexAskPrice"] != None:
                    quote["bidPrice"] = data["iexBidPrice"]
                    quote["bidSize"] = data["iexBidSize"]
                    quote["askPrice"] = data["iexAskPrice"]
                    quote["askSize"] = data["iexAskSize"]
                else:
                    random_ratio = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
                    quote["bidPrice"] = data["low"]
                    quote["bidSize"] = round(int(random_ratio * data["latestVolume"]), -2)
                    quote["askPrice"] = data["high"]
                    quote["askSize"] = round(int((1 - random_ratio) * data["latestVolume"]), -2)

            return quote, error

        except(OSError, Exception):
            error = "invalid symbol"
            return quote, error

    def get_price(self, symbol):
        price = {}
        error = ""
        url = self.url_common + symbol + "/quote?token=" + self.api_token
        print(url)
        try:
            with urllib.request.urlopen(url) as req:
                data = json.load(req)
                if not data:
                    error = "symbol has no data"
                    return price, error

                price["symbol"] = symbol
                price["name"] = data["companyName"]
                price["price"] = float(data["latestPrice"])

            return price, error

        except(OSError, Exception):
            error = "invalid symbol"
            return price, error


class EODMarketData:
    def __init__(self, api_token, database):
        self.url_common = "https://eodhistoricaldata.com/api/"
        self.api_token = api_token
        self.database = database

    def get_daily_data(self, symbol, start, end, category):
        symbolURL = str(symbol) + '.' + category + '?'
        startURL = 'from=' + str(start)
        endURL = 'to=' + str(end)
        apiKeyURL = 'api_token=' + self.api_token
        completeURL = self.url_common + 'eod/' + symbolURL + startURL + '&' + endURL + '&' + apiKeyURL + '&period=d&fmt=json'
        print(completeURL)
        with urllib.request.urlopen(completeURL) as req:
            data = json.load(req)
            return data

    def get_fundamental_data(self, symbol, category):
        symbolURL = str(symbol) + '.' + category + '?'
        apiKeyURL = 'api_token=' + self.api_token
        completeURL = self.url_common + 'fundamentals/' + symbolURL + '&' + apiKeyURL
        print(completeURL)
        with urllib.request.urlopen(completeURL) as req:
            data = json.load(req)
            return data
    
    def get_intraday_data(self, symbol, startTime='1585800000', endTime='1585886400', category='US'):
        symbolURL = str(symbol) + '.' + category + '?'
        startURL = "from=" + str(startTime)
        endURL = "to=" + str(endTime)
        apiKeyURL = "api_token=" + self.api_token
        completeURL = self.url_common + 'intraday/' + symbolURL + startURL + '&' + endURL + '&' + apiKeyURL + '&period=d&fmt=json'
        print(completeURL)
        with urllib.request.urlopen(completeURL) as req:
            data = json.load(req)
            return data  
        
    def populate_stock_data(self, tickers, table_name, start_date, end_date, category='US', action='append', output_file=sys.stderr):
        column_names = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume']
        price_data = []
        for ticker in tickers:
            stock = self.get_daily_data(ticker, start_date, end_date, category)
            for stock_data in stock:
                price_data.append(
                    [ticker, stock_data['date'], stock_data['open'], stock_data['high'], stock_data['low'], \
                     stock_data['close'], stock_data['adjusted_close'], stock_data['volume']])
            print(price_data[-1], file=output_file)
        stocks = pd.DataFrame(price_data, columns=column_names)
        stocks.to_sql(table_name, con=self.database.engine, if_exists=action, index=False)

    def populate_intraday_stock_data(self, tickers, table_name, start_time, end_time, category='US', action='append', output_file=sys.stderr):
        column_names = ['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        price_data = []
        for ticker in tickers:
            stock = self.get_intraday_data(ticker, start_time, end_time, category)
            print(stock, file=output_file)
            for stock_data in stock:
                if ((stock_data['open'] is not None and stock_data['open'] > 0) and
                    (stock_data['high'] is not None and stock_data['high'] > 0) and
                    (stock_data['low']  is not None and stock_data['low'] > 0) and 
                    (stock_data['close'] is not None and stock_data['close'] > 0) and
                    (stock_data['volume'] is not None and stock_data['volume'] > 0)):
                    price_data.append([stock_data['datetime'], ticker, stock_data['open'], stock_data['high'], stock_data['low'], \
                               stock_data['close'], stock_data['volume']])

            print(price_data, file=output_file)
        stocks = pd.DataFrame(price_data, columns=column_names)
        stocks = stocks.dropna()
        stocks.to_sql(table_name, con=self.database.engine, if_exists=action, index=False)

    def populate_sp500_data(self, spy, category):
        data = self.get_fundamental_data(spy, category)
        sp500_column_names = ['symbol', 'name', 'sector', 'industry', 'weight']
        sp500_data = []
        sp500_holdings = data["ETF_Data"]["Holdings"]
        for holding in sp500_holdings.values():
            symbol = holding["Code"]
            name = holding["Name"]
            sector = holding["Sector"]
            industry = holding["Industry"]
            weight = holding["Assets_%"]
            if symbol.find('-') != -1:
                symbol = symbol.replace('-', '')
            if sector == "Consumer Cyclical":
                sector = "Consumer Cyclicals"
            if sector == "Financial":
                sector = "Financial Services"
            sp500_data.append([symbol, name, sector, industry, weight])
        sp500 = pd.DataFrame(sp500_data, columns=sp500_column_names)
        sp500.to_sql("sp500", con=self.database.engine, if_exists='append', index=False)

        sp500_sector_column_names = ['sector', 'equity_pct', 'category_pct']
        sp500_sector_data = []
        for key, value in data["ETF_Data"]["Sector_Weights"].items():
            sector = key
            equity_pct = float(value['Equity_%'])/100
            category_pct = float(value['Relative_to_Category'])/100
            sp500_sector_data.append([sector, equity_pct, category_pct])
        sp500_sectors = pd.DataFrame(sp500_sector_data, columns=sp500_sector_column_names)
        sp500_sectors.to_sql("sp500_sectors", con=self.database.engine, if_exists='append', index=False)

    def populate_fundamental_data(self, tickers, category):
        column_names = ['symbol', 'pe_ratio', 'dividend_yield', 'beta', 'high_52weeks', 'low_52weeks', 'ma_50days', 'ma_200days']
        fundamental_data = []
        for ticker in tickers:
            data = self.get_fundamental_data(ticker, category)
            if ticker == 'SPY':
                fundamental_data.append(
                    [ticker,
                     data['ETF_Data']['Valuations_Growth']['Valuations_Rates_Portfolio']['Price/Prospective Earnings'],
                     data['ETF_Data']['Yield'],
                     data['Technicals']['Beta'], data['Technicals']['52WeekHigh'],
                     data['Technicals']['52WeekLow'],
                     data['Technicals']['50DayMA'], data['Technicals']['200DayMA']])
            else:
                fundamental_data.append(
                    [ticker,
                     data['Highlights']['PERatio'], data['Highlights']['DividendYield'],
                     data['Technicals']['Beta'], data['Technicals']['52WeekHigh'],
                     data['Technicals']['52WeekLow'],
                     data['Technicals']['50DayMA'], data['Technicals']['200DayMA']])
            print(fundamental_data[-1])
        fundamentals = pd.DataFrame(fundamental_data, columns=column_names)
        fundamentals.fillna(0, inplace=True)
        fundamentals.to_sql("fundamentals", con=self.database.engine, if_exists='append', index=False)