from datetime import datetime
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import sys


def cleanse(s):
    return s.translate({ ord(c): None for c in ' $,' })


class EarningsCrawler:
    ZACKS_URL_FMT = "http://zacks.thestreet.com/CompanyView.php?ticker={}&tab=earnings_announcements&targetCompanyTab=earnings_announcements&Go=Go"
    ZACKS_TOOL_URL = "http://zacks.thestreet.com/tools/earnings_announcements_company.php"
    GET_REQUEST_HEADERS = {
        'origin':'http://zacks.thestreet.com',
        'referer':'http://zacks.thestreet.com/CompanyView.php',
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }

    @staticmethod
    def parse_date(date):
        return datetime.strptime(date, '%d-%b-%y')

    @staticmethod
    def parse_estimate(estimate):
        if "N/A" in estimate:
            return np.nan
        estimate = cleanse(estimate)
        return float(estimate)

    @staticmethod
    def parse_surprise(surprise):
        if "N/A" in surprise:
            return np.nan
        surprise = cleanse(surprise)
        return float(surprise)

    @staticmethod
    def parse_surprise_percent(surprise_pct):
        if "N/A" in surprise_pct:
            return np.nan
        surprise_pct = cleanse(surprise_pct)
        surprise_pct = surprise_pct[:-1]
        return float(surprise_pct) / 100

    @classmethod
    def pull(cls, ticker):
        url = cls.ZACKS_URL_FMT.format(ticker)
        res = requests.get(url, headers=cls.GET_REQUEST_HEADERS)

        if res.status_code != 200:
            return None, f"Request failed: error code={res.status_code}"

        total_pages = None

        try:
            soup = BeautifulSoup(res.text, 'html.parser')
            div = soup.find_all('td', class_='linktext')[-1].find_all('div')[0]

            desc_list = div.text.split()
            desc_list = [ s for s in desc_list if s.isalnum() ]
            total_pages = int(desc_list[desc_list.index('of') + 1])
        except Exception as e:
            return None, f"Parsing failure for {ticker} caused the following error: " + str(e)

        print(f"{total_pages} pages in total for {ticker.upper()}")

        error_messages = []
        records = dict()

        for pg in range(1, total_pages + 1):
            print(f"Retrieving page {pg} for {ticker.upper()}...")

            post_request_data = {
                'ticker': ticker,
                'pg_no': pg,
                'recordsToDisplay': 10,
                'maxNoOfPages': 10,
                'recordsPerPage': 10
            }
            res = requests.post(cls.ZACKS_TOOL_URL, data=post_request_data)

            if res.status_code != 200:
                error_messages.append(f"Request failed for ticker {ticker} on page {pg}: error code={res.status_code}")
                continue

            try:
                soup = BeautifulSoup(res.text, 'html.parser')
                table = soup.find_all('table')[-2].find_all('tr')

                for row in table[1:]:
                    items = row.find_all('td')
                    record = {
                        'ticker': ticker,
                        'date': cls.parse_date(items[0].text[:-1]),
                        'period_ending': items[1].text[:-1],
                        'estimate': cls.parse_estimate(items[2].text[:-1]),
                        'reported': cls.parse_estimate(items[3].text[:-1]),
                        'surprise': cls.parse_surprise(items[4].text[:-1]),
                        'surprise%': cls.parse_surprise_percent(items[5].text[:-1])
                    }

                    key = (record['ticker'], record['date'])
                    records[key] = record
            except Exception as e:
                error_messages.append(str(e))
                continue

        print()
        for em in error_messages:
            print(em, file=sys.stderr)

        return list(records.values()), None


# calendar, errmsg = EarningsCrawler.pull('tsla')

# if calendar is None:
#     print(errmsg)
# else:
#     print(calendar)