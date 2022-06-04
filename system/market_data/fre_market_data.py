import concurrent.futures
import json
import os
import pandas as pd
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from io import TextIOWrapper
from typing import Collection


class IEXMarketData:
    def __init__(self, api_token: str):
        self.url_common = "https://cloud.iexapis.com/stable/stock/"
        self.api_token = api_token

    def get_quote(self, symbol: str):
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
                quote['Market'] = "Open" if data["isUSMarketOpen"] else "Closed"
                # When latestVolume is None -> use previousVolume
                if data["latestVolume"] is None:
                    if data["previousVolume"] is None:
                        data["latestVolume"] = 0
                    else:
                        data["latestVolume"] = data["previousVolume"]
                # When high, low are None -> Use week52Low and week52High
                if data["low"] is None:
                    if data["week52Low"] is None:
                        data["low"] = 0
                    else:
                        data["low"] = data["week52Low"]
                if data["high"] is None:
                    if data["week52High"] is None:
                        data["high"] = 0
                    else:
                        data["high"] = data["week52High"]
                if data.get("iexBidPrice", None) is not None and data.get("iexAskPrice", None) is not None:
                    # print(data)
                    random_ratio = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
                    # BidPrice & Size exists
                    if data["iexBidPrice"] != 0:
                        quote["bidPrice"] = data["iexBidPrice"]
                        quote["bidSize"] = data["iexBidSize"]
                    # Bid Price is 0 in Market Closed, generate bid price and size
                    # found that quote price could be zero even though market status is open
                    #elif quote['Market'] == "Closed":
                    else:
                        quote["bidPrice"] = data["low"]
                        #quote["bidSize"] = round(int(random_ratio * data["latestVolume"] / 6.5 / 3600), -2)
                        quote["bidSize"] = int(random_ratio * data["latestVolume"] / 6.5 / 3600)
                    # AskPrice & Size exists
                    if data["iexAskPrice"] != 0:
                        quote["askPrice"] = data["iexAskPrice"]
                        quote["askSize"] = data["iexAskSize"]
                    # Ask Price is 0 in Market Closed, generate ask price and size
                    # found that quote price could be zero even though market status is open
                    #elif quote['Market'] == "Closed":
                    else:
                        quote["askPrice"] = data["high"]
                        #quote["askSize"] = round(int((1 - random_ratio) * data["latestVolume"] / 6.5 / 3600), -2)
                        quote["askSize"] = int((1 - random_ratio) * data["latestVolume"] / 6.5 / 3600)

                else:
                    # When data form not containing keys, generate price and size
                    # print('Not right form data.')
                    # print(data)
                    random_ratio = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
                    quote["bidPrice"] = data["low"]
                    #quote["bidSize"] = round(int(random_ratio * data["latestVolume"] / 6.5 / 3600), -2)
                    quote["bidSize"] = int(random_ratio * data["latestVolume"] / 6.5 / 3600)
                    quote["askPrice"] = data["high"]
                    #quote["askSize"] = round(int((1 - random_ratio) * data["latestVolume"] / 6.5 / 3600), -2)
                    quote["askSize"] = int((1 - random_ratio) * data["latestVolume"] / 6.5 / 3600)
            return quote, error

        except(OSError, Exception):
            error = "invalid symbol"
            return quote, error

    def get_price(self, symbol: str):
        price = {}
        error = ""
        url = f"{self.url_common}{symbol}/quote?token={self.api_token}"
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
    def __init__(self, api_token: str, database):
        self.url_common = "https://eodhistoricaldata.com/api/"
        self.api_token = api_token
        self.database = database

    def get_daily_data(self, symbol: str, start: str, end: str, category: str):
        symbolURL = f"{symbol}.{category}?"
        startURL = f'from={start}' if start != '' else ''
        endURL = f'to={end}' if end != '' else ''
        apiKeyURL = f'api_token={self.api_token}'
        completeURL = f"{self.url_common}eod/{symbolURL}{startURL}&{endURL}&{apiKeyURL}&period=d&fmt=json"
        print(completeURL)
        with urllib.request.urlopen(completeURL) as req:
            data = json.load(req)
            return data

    def get_fundamental_data(self, symbol: str, category: str):
        symbolURL = f"{symbol}.{category}?"
        apiKeyURL = f'api_token={self.api_token}'
        completeURL = f"{self.url_common}fundamentals/{symbolURL}&{apiKeyURL}"
        print(completeURL)
        with urllib.request.urlopen(completeURL) as req:
            data = json.load(req)
            return data
    
    def get_intraday_data(self, symbol: str, startTime: str ='1585800000', endTime: str ='1585886400', category: str ='US'):
        symbolURL = f"{symbol}.{category}?"
        startURL = f"from={startTime}"
        endURL = f"to={endTime}"
        apiKeyURL = f'api_token={self.api_token}'
        completeURL = f"{self.url_common}intraday/{symbolURL}{startURL}&{endURL}&{apiKeyURL}&period=d&fmt=json"
        print(completeURL)
        with urllib.request.urlopen(completeURL) as req:
            data = json.load(req)
            return data  
        
    def populate_stock_data(self, tickers: Collection[str], table_name: str, start_date: str, end_date: str, category: str = 'US',
                            action: str = 'append', output_file: TextIOWrapper = sys.stderr) -> None:
        """
        Retrieve stock(s)'s daily historical data and store the data into a desired table.
        :param tickers: a list of ticker(s)
        :param table_name: a string of table name (only one table)
        :param start_date: string ('%Y-%m-%d')
        :param end_date: string ('%Y-%m-%d')
        """
        column_names = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume']
        price_data = []
        for ticker in tickers:
            stock = self.get_daily_data(ticker, start_date, end_date, category)
            for stock_data in stock:
                price_data.append(
                    [ticker, stock_data['date'], stock_data['open'], stock_data['high'], stock_data['low'], \
                     stock_data['close'], stock_data['adjusted_close'], stock_data['volume']])
        stocks = pd.DataFrame(price_data, columns=column_names)
        stocks.to_sql(table_name, con=self.database.engine, if_exists=action, index=False)

    def populate_intraday_stock_data(self, tickers: Collection[str], table_name: str, start_date: str, end_date: str, category: str = 'US',
                                    action: str = 'append', output_file: TextIOWrapper = sys.stderr) -> None:
        """
        Retrieve stock(s)'s intraday historical data and store the data into a desired table.
        :param tickers: a list of ticker(s)
        :param table_name: a string of table name (only one table)
        :param start_date: string ('%Y-%m-%d')
        :param end_date: string ('%Y-%m-%d')
        """
        column_names = ['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        price_data = []
        for ticker in tickers:
            stock = self.get_intraday_data(ticker, start_date, end_date, category)
            print(stock, file=output_file)
            for stock_data in stock:
                if ((stock_data['open'] is not None and stock_data['open'] > 0) and
                        (stock_data['high'] is not None and stock_data['high'] > 0) and
                        (stock_data['low'] is not None and stock_data['low'] > 0) and
                        (stock_data['close'] is not None and stock_data['close'] > 0) and
                        (stock_data['volume'] is not None and stock_data['volume'] > 0)):
                    price_data.append([stock_data['datetime'], ticker, stock_data['open'], stock_data['high'],
                                       stock_data['low'], stock_data['close'], stock_data['volume']])

            # print(price_data, file=output_file)
        stocks = pd.DataFrame(price_data, columns=column_names)
        stocks = stocks.dropna()
        stocks.to_sql(table_name, con=self.database.engine, if_exists=action, index=False)

    def populate_sp500_data(self, spy: str, category: str) -> None:
        """
        Retrieve sp500 data and store data into tables: "sp500" and "sp500_sectors"
        :param spy: a string,  should be 'spy'
        :param category: a string, should be 'US'
        """
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
            equity_pct = float(value['Equity_%']) / 100
            category_pct = float(value['Relative_to_Category']) / 100
            sp500_sector_data.append([sector, equity_pct, category_pct])
        sp500_sectors = pd.DataFrame(sp500_sector_data, columns=sp500_sector_column_names)
        sp500_sectors.to_sql("sp500_sectors", con=self.database.engine, if_exists='append', index=False)

    def populate_fundamental_data(self, tickers: Collection[str], category: str) -> None:
        """
        Retrieve fundamental data and store data into table: "fundamentals"
        Utilize multi-threads
        :param tickers: a list of tickers
        :param category: a string, should be 'US'
        """
        column_names = ['symbol', 'pe_ratio', 'dividend_yield', 'beta', 'high_52weeks', 'low_52weeks', 'ma_50days',
                        'ma_200days', 'market_capitalization']
        def fundamental_data_helper(ticker_list):
            fundamental_data = []
            for ticker in ticker_list:
                data = self.get_fundamental_data(ticker, category)
                if ticker == 'SPY':
                    fundamental_data.append(
                        [ticker,
                         data['ETF_Data']['Valuations_Growth']['Valuations_Rates_Portfolio'][
                             'Price/Prospective Earnings'],
                         data['ETF_Data']['Yield'],
                         data['Technicals']['Beta'], data['Technicals']['52WeekHigh'],
                         data['Technicals']['52WeekLow'],
                         data['Technicals']['50DayMA'], data['Technicals']['200DayMA'], 0])
                else:
                    fundamental_data.append(
                        [ticker,
                         data['Highlights']['PERatio'], data['Highlights']['DividendYield'],
                         data['Technicals']['Beta'], data['Technicals']['52WeekHigh'],
                         data['Technicals']['52WeekLow'],
                         data['Technicals']['50DayMA'], data['Technicals']['200DayMA'], data['Highlights']['MarketCapitalization']])
            fundamentals = pd.DataFrame(fundamental_data, columns=column_names)
            fundamentals.fillna(0, inplace=True)
            return fundamentals

        # divide the tickers list into 20 sub-lists,if len(tickers) cannot be divided by 20, add the remining tickers to the last sub-list.
        if len(tickers) > 20:
            n = len(tickers) // 20
            tickers_list = [tickers[x:x + n] for x in range(0, n * 20, n)]
            tickers_list[-1] = tickers_list[-1] + tickers[-(len(tickers) % 20):len(tickers)]
        else:
            tickers_list = [tickers]

        # multi-threads: 20 threads
        result_df = pd.DataFrame(columns=column_names)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for sub_tickers in tickers_list:
                futures.append(executor.submit(fundamental_data_helper, ticker_list=sub_tickers))
            for future in concurrent.futures.as_completed(futures):
                # Future instances are created by Executor.submit()
                # https://docs.python.org/3/library/concurrent.futures.html
                # .result() -> Return the value returned by the call. 
                # If the call hasn’t yet completed then this method will wait up to timeout seconds.
                # result_df = result_df.append(future.result(), ignore_index=True) -> depreciated
                result_df = pd.concat([result_df, future.result()], ignore_index=True, axis=0)
        result_df.to_sql("fundamentals", con=self.database.engine, if_exists='append', index=False)

    def populate_stocks_data_multi(self, tickers: Collection[str], table_name: str, start_date: str, end_date: str,
                                   category: str = 'US',
                                   action: str = 'append', output_file: TextIOWrapper = sys.stderr) -> None:
        """
        Retrieve a large amount of stocks's historical data and store data into database.
        Utilize multi-threads.
        :param tickers: a list of ticker(s)
        :param table_name: a string of table name (only one table)
        :param start_date: string ('%Y-%m-%d')
        :param end_date: string ('%Y-%m-%d')
        """

        column_names = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume']

        def stocks_data_helper(tickers, start_date, end_date, category='US'):
            price_data = []
            for ticker in tickers:
                stock = self.get_daily_data(ticker, start_date, end_date, category)
                for stock_data in stock:
                    price_data.append(
                        [ticker, stock_data['date'], stock_data['open'], stock_data['high'], stock_data['low'], \
                         stock_data['close'], stock_data['adjusted_close'], stock_data['volume']])
            stocks = pd.DataFrame(price_data, columns=column_names)
            return stocks

        # multi-threads: 10 threads
        if len(tickers) > 10:
            n = len(tickers) // 10
            tickers_list = [tickers[x:x + n] for x in range(0, n * 10, n)]
            tickers_list[-1] = tickers_list[-1] + tickers[-(len(tickers) % 10):len(tickers)]
        else:
            tickers_list = [tickers]
        result_df = pd.DataFrame(columns=column_names)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for sub_tickers in tickers_list:
                futures.append(
                    executor.submit(stocks_data_helper, tickers=sub_tickers, start_date=start_date, end_date=end_date))
            for future in concurrent.futures.as_completed(futures):
                result_df = result_df.append(future.result(), ignore_index=True)
        result_df = result_df.drop_duplicates()
        result_df.to_sql(table_name, con=self.database.engine, if_exists=action, index=False)
