import os
import urllib.request
import json


class IEXMarketData:
    def __init__(self, symbol, api_token):
        self.quote = {}
        self.url_common = "https://cloud-sse.iexapis.com/stable/stock/"
        self.api_token = api_token
        self.symbol = symbol
        self.error = ""

    def get_quote(self):
        url_common = "https://cloud-sse.iexapis.com/stable/stock/"

        url = url_common + self.symbol + "/quote?token=" + self.api_token
        print(url)
        try:
            with urllib.request.urlopen(url) as req:
                data = json.load(req)
                if not data:
                    self.error = "symbol has no data"
                    return self.quote, self.error
                # print(data)
                self.quote["symbol"] = self.symbol
                if "iexBidPrice" in data.keys() and data["iexBidPrice"] != None and \
                        "iexAskPrice" in data.keys() and data["iexAskPrice"] != None:
                    self.quote["bidPrice"] = data["iexBidPrice"]
                    self.quote["bidSize"] = data["iexBidSize"]
                    self.quote["askPrice"] = data["iexAskPrice"]
                    self.quote["askSize"] = data["iexAskSize"]
                else:
                    random_ratio = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
                    self.quote["bidPrice"] = data["low"]
                    self.quote["bidSize"] = int(random_ratio * data["latestVolume"])
                    self.quote["askPrice"] = data["high"]
                    self.quote["askSize"] = int((1 - random_ratio) * data["latestVolume"])
            return self.quote, self.error

        except(OSError, Exception):
            self.error = "invalid symbol"
            return self.quote, self.error
