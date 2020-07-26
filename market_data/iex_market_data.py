import os
import urllib.request
import json


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
