from enum import Enum
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import requests
from io import StringIO
from datetime import datetime

from system.mep_strategy.mep_calculate import *
from system.mep_strategy.mep_common import *
from system.mep_strategy.mep_order import *
from system.mep_strategy.mep_strategy import *
from system.mep_strategy.mep_strategy_executor import *


stock_collection = {
    'energy': { 'XOM', 'CVX' },
    'materials': { 'SHW', 'DD' },
    'industrials': { 'BA', 'UNP' },
    'utilities': { 'DUK', 'ED', 'AEP' },
    'healthcare': { 'UNH', 'JNJ' },
    'financials': { 'BRK-A', 'BRK-B', 'JPM' },
    'consumer discretion': { 'AMZN', 'MCD' },
    'consumer staples': { 'KO', 'PG' },
    'information technology': { 'AAPL', 'MSFT' },
    'communication services': { 'FB', 'GOOGL', 'GOOG' },
    'real estate': { 'AMT', 'SPG' }
}

industry_description = {
    'energy': "The largest U.S. stocks in the energy sector are ExxonMobil (NYSE:XOM) and Chevron (NYSE:CVX).",
    'materials': "Well-known materials stocks include paint maker Sherwin-Williams (NYSE:SHW) and chemicals manufacturer DuPont (NYSE:DD).",
    'industrials': "Boeing (NYSE:BA) and Union Pacific (NYSE:UNP) are among the largest U.S. industrials stocks.",
    'utilities': "Utilities tend to be regional in scope, so you might have heard of Duke Energy (NYSE:DUK) in the Southeast U.S., Consolidated Edison (NYSE:ED) in the Northeast, and American Electric Power (NYSE:AEP) across much of the Ohio Valley and the Southern Plains states.",
    'healthcare': "United Health Group (NYSE:UNH) and Johnson & Johnson (NYSE:JNJ) are the two stocks at the top of the healthcare sector.",
    'financials': "Warren Buffett's Berkshire Hathaway (NYSE:BRK-A) (NYSE:BRK-B) and financial giant JPMorgan Chase (NYSE:JPM) are among the best-known stocks in the financials sector.",
    'consumer discretion': "Amazon.com (NASDAQ:AMZN) and McDonald's (NYSE:MCD) are among the biggest stocks in the sector.",
    'consumer staples': "Coca-Cola (NYSE:KO) and Procter & Gamble (NYSE:PG) are two of the most valuable consumer staples stocks in the U.S. market.",
    'information technology': "Apple (NASDAQ:AAPL) and Microsoft (NASDAQ:MSFT) have been switching places back and forth at the top of the list of large U.S. stocks in the information technology sector.",
    'communication services': "Social media giant Facebook (NASDAQ:FB) and search engine pioneer Alphabet (NASDAQ:GOOGL) (NASDAQ:GOOG) are among the biggest stocks in communication services.",
    'real estate': "Among the top stocks in the real estate sector, you'll find cellular communications tower specialist American Tower (NYSE:AMT) and major shopping mall owner and operator Simon Property Group (NYSE:SPG)."
}

def generate_optimized_executor(stock, start_date_train, end_date_train, start_date_test, end_date_test, verbose=True):
    alpha, delta, gamma, _ = search_optimal_parameters(stock, start_date_train, end_date_train, verbose=True)
    se = MEPStrategyExecutor(stock, start_date_test, end_date_test, alpha=alpha, delta=delta, gamma=gamma)
    se.process()
    return se


def generate_executor(stock, start_date_test, end_date_test, alpha, delta, gamma):
    se = MEPStrategyExecutor(stock, start_date_test, end_date_test, alpha=alpha, delta=delta, gamma=gamma)
    se.process()
    return se


stock_available = MEPStrategyExecutor.stock_available

stock_backtest_executors = {}
stock_probtest_executors = {}
