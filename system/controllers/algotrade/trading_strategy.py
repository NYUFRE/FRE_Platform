#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 20 18:30:44 2023

@author: songtang

PyAlgoTrade Tutorial gbeced.github.io/pyalgotrade/docs/v0.20/html/tutorial.html
"""

from pyalgotrade.barfeed import yahoofeed
from pyalgotrade import plotter
from pyalgotrade.stratanalyzer import returns
import itertools
from pyalgotrade.optimizer import local
from system.controllers.algotrade.yahoo_finance import open_yahoo_finance_data
from system.services.algotrade.trading_strategy_service import Simple_Strategy, SMA_Strategy, SMA_RSI_Strategy
from system.services.algotrade.trading_strategy_service import SMA_Trading, SMA_CrossOver, RSI2


class Stock:
	def __init__(self, symbol, start_date, end_date):
		self.symbol = symbol
		self.start_date = start_date
		self.end_date = end_date


def build_strategy(stock, type="simple"):
	feed = yahoofeed.Feed()
	open_yahoo_finance_data(feed, stock.symbol, stock.start_date, stock.end_date)

	try:
		# Evaluate the strategy with the feed's bars.
		if type == "simple": 
			myStrategy = Simple_Strategy(feed, stock.symbol)
			myStrategy.run()
		elif type == "sma":
			myStrategy = SMA_Strategy(feed, stock.symbol)
			myStrategy.run()
		elif type == "sma_rsi":
			myStrategy = SMA_RSI_Strategy(feed, stock.symbol)
			myStrategy.run()
		else:
			print("No strategy to build")
	except:
		print("Error in building a trading strategy!")


def run_strategy(stock, type="simple", smaPeriod=0):
	feed = yahoofeed.Feed()
	open_yahoo_finance_data(feed, stock.symbol, stock.start_date, stock.end_date)
	try:
		if type == "sma_trading":
			myStrategy = SMA_Trading(feed, stock.symbol, smaPeriod)
			myStrategy.run()
			print("Final portfolio value: $%.2f" % myStrategy.getBroker().getEquity())
		else:
			print("No Strategy to simulate trading")
	except:
		print("Error in simulation of trading a strategy!")


def plot_strategy(stock, type="simple", smaPeriod=0):
	feed = yahoofeed.Feed()
	open_yahoo_finance_data(feed, stock.symbol, stock.start_date, stock.end_date)

	try:
		# Evaluate the strategy with the feed's bars.
		if type == "sma_crossover":
			# Evaluate the strategy with the feed's bars.
			myStrategy = SMA_CrossOver(feed, stock.symbol, smaPeriod)

			# Attach a returns analyzers to the strategy.
			returnsAnalyzer = returns.Returns()
			myStrategy.attachAnalyzer(returnsAnalyzer)

			# Attach the plotter to the strategy.
			plt = plotter.StrategyPlotter(myStrategy)
			# Include the SMA in the instrument's subplot to get it displayed along with the closing prices.
			plt.getInstrumentSubplot(stock.symbol).addDataSeries(type.capitalize(), myStrategy.getSMA())
			# Plot the simple returns on each bar.
			plt.getOrCreateSubplot("returns").addDataSeries(type.capitalize() + " returns", returnsAnalyzer.getReturns())

			# Run the strategy.
			myStrategy.run()
			myStrategy.info("Final portfolio value: $%.2f" % myStrategy.getResult())

			# Plot the strategy.
			plt.plot()

		else:
			print("No strategy to plot")
	except:
		print("Error in plotting a trading strategy!")


def parameters_generator(symbol):
	instrument = [symbol]
	entrySMA = range(150, 251)
	exitSMA = range(5, 16)
	rsiPeriod = range(2, 11)
	overBoughtThreshold = range(75, 96)
	overSoldThreshold = range(5, 26)
	return itertools.product(instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)


def optimize_strategy(stock_list, type='simple'):
	feed = yahoofeed.Feed()

	for stock in stock_list:
		open_yahoo_finance_data(feed, stock.symbol, stock.start_date, stock.end_date)

	try:
		if type == "sma_rsi":
			# Due the capacity of my Mac laptop, use 2 worker and reduce batchSize to 2, keep log level as 40
			local.run(RSI2, feed, parameters_generator(stock_list[0].symbol), 2, 40, 2)
		else:
			print("No strategy to optimize")

	except KeyboardInterrupt:
		print("Manually terminate optimizing the strategy due to time limitation")
	except:
		print("Error in optimizing a trading strategy!")

