#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 20 18:30:44 2023

@author: songtang

"""
import yfinance
from pyalgotrade.barfeed import yahoofeed

def download_yahoo_finance_data(symbol="spy", start_date="2010-01-01", end_date="2023-08-31"):
	data = yfinance.download(symbol.upper(), start=start_date, end=end_date)
	csv_location = "./system/csv/" + symbol + "_" + start_date + "_" + end_date + ".csv"
	data.to_csv(csv_location)

def open_yahoo_finance_data(feed, symbol="spy", start_date="2010-01-01", end_date="2023-08-31"):
	# Load the bar feed from the CSV file
	csv_location = "./system/csv/" + symbol + "_" + start_date + "_" + end_date + ".csv"
	feed.addBarsFromCSV(symbol, csv_location)
