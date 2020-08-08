# -*- coding: utf-8 -*
# !/usr/bin/env python3
import sys

sys.path.append('../')

import os
import datetime as dt
import copy

import pandas as pd
import numpy as np

from sqlalchemy import and_, or_, not_

from flask import Flask, flash, redirect, render_template, request, url_for

from market_data.fre_market_data import EODMarketData
from database.fre_database import FREDatabase
from ai_trading.ga_portfolio import *

location_of_pairs = 'csv/PairTrading.csv'

os.environ["EOD_API_KEY"] = "5ba84ea974ab42.45160048"

if not os.environ.get("EOD_API_KEY"):
    raise RuntimeError("EOD_API_KEY not set")

start_date = dt.date(2010, 1, 1).strftime('%Y-%m-%d')
end_date = dt.datetime.today().strftime('%Y-%m-%d')

back_testing_start_date = dt.date(2020, 1, 1).strftime('%Y-%m-%d')
back_testing_end_date = dt.date(2020, 6, 30).strftime('%Y-%m-%d')

database = FREDatabase()
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)


def create_populate_tables():
    tables = ['sp500', 'sp500_sectors', 'fundamentals', 'stocks', 'spy', 'us10y']
    database.create_table(tables)
    database.clear_table(tables)
    eod_market_data.populate_sp500_data('SPY', 'US')
    tickers = database.get_sp500_symbols()
    eod_market_data.populate_stock_data(tickers, "stocks", start_date, end_date, 'US')
    eod_market_data.populate_stock_data(['SPY'], "spy", start_date, end_date, 'US')
    eod_market_data.populate_stock_data(['US10Y'], "us10y", start_date, end_date, 'INDX')
    tickers.append('SPY')
    eod_market_data.populate_fundamental_data(tickers, 'US')

    '''
    tables = ['fundamentals']
    database.clear_table(tables)
    tickers = database.get_sp500_symbols()
    eod_market_data.populate_fundamental_data(tickers, 'US')
    '''


def build_ga_model():
    spy = Stock()
    spy.symbol = 'SPY'

    us10y = Stock()
    us10y.symbol = 'US10Y'

    sp500_stock_map = {}
    sp500_sectors = database.get_sp500_sectors()
    for sector in sp500_sectors:
        sp500_stock_map[sector] = []

    # TODO!Avoid hard-coding start and end dates
    spy_select = "SELECT * FROM spy WHERE strftime(\'%Y-%m-%d\', date) BETWEEN \"2010-01-01\" AND \"2019-12-31\";"
    print(spy_select)
    price_df = database.execute_sql_statement(spy_select)
    for index, row in price_df.iterrows():
        trade = Trade()
        trade.date = row['date']
        trade.open = row['open']
        trade.high = row['high']
        trade.low = row['low']
        trade.close = row['close']
        trade.adjusted_close = row['adjusted_close']
        trade.volume = row['volume']
        spy.add_trade(trade)

    spy.calculate_daily_return()
    spy.calculate_expected_return()
    spy.calculate_volatility()

    spy_fundamental_select = "SELECT * FROM fundamentals WHERE symbol = \"SPY\";"
    print(spy_fundamental_select)
    fundamental_df = database.execute_sql_statement(spy_fundamental_select)
    fundamental = Fundamental()
    for index, row in fundamental_df.iterrows():
        fundamental.pe_ratio = row['pe_ratio']
        fundamental.dividend_yield = row['dividend_yield']
        fundamental.beta = row['beta']
        fundamental.high_52weeks = row['high_52weeks']
        fundamental.low_52weeks = row['low_52weeks']
        fundamental.ma_50days = row['ma_50days']
        fundamental.ma_200days = row['ma_200days']
    spy.fundamental = fundamental

    us10y_select = "SELECT * FROM us10y WHERE strftime(\'%Y-%m-%d\', date) BETWEEN \"2010-01-01\" AND \"2019-12-31\";";
    print(us10y_select)
    price_df = database.execute_sql_statement(us10y_select)
    for index, row in price_df.iterrows():
        trade = Trade()
        trade.date = row['date']
        trade.open = row['open']
        trade.high = row['high']
        trade.low = row['low']
        trade.close = row['close']
        trade.adjusted_close = row['adjusted_close']
        trade.volume = row['volume']
        us10y.add_trade(trade)

    us10y.calculate_risk_free_rate()
    us10y.calculate_expected_risk_free_rate()

    sp500_sector_map = {}
    sp500_sector_select = "SELECT sector, category_pct from sp500_sectors;"
    print(sp500_sector_select)
    sp500_sector_df = database.execute_sql_statement(sp500_sector_select)
    for index, row in sp500_sector_df.iterrows():
        sp500_sector_map[row['sector']] = row['category_pct']

    sp500_symbol_map = database.get_sp500_symbol_map()
    for key, symbols in sorted(sp500_symbol_map.items()):
        for symbol in sorted(symbols):
            stock = Stock()
            stock.symbol = symbol
            stock.sector = key
            stock.category_pct = sp500_sector_map[key]

            stock_select = "SELECT * FROM stocks WHERE strftime(\'%Y-%m-%d\', date) " \
                           "BETWEEN \"2010-01-01\" AND \"2019-12-31\" AND open > 0 AND close > 0 AND symbol = \'" + symbol + "\';"
            print(stock_select)
            price_df = database.execute_sql_statement(stock_select)
            if price_df.empty:
                continue

            for index, row in price_df.iterrows():
                trade = Trade()
                trade.date = row['date']
                trade.open = row['open']
                trade.high = row['high']
                trade.low = row['low']
                trade.close = row['close']
                trade.adjusted_close = row['adjusted_close']
                trade.volume = row['volume']
                stock.add_trade(trade)

            stock.calculate_daily_return()

            fundamental_select = "SELECT * FROM Fundamentals WHERE symbol = \"" + symbol + "\";"
            print(fundamental_select)

            fundamental_df = database.execute_sql_statement(fundamental_select)
            fundamental = Fundamental()
            for index, row in fundamental_df.iterrows():
                fundamental.pe_ratio = row['pe_ratio']
                fundamental.dividend_yield = row['dividend_yield']
                fundamental.beta = row['beta']
                fundamental.high_52weeks = row['high_52weeks']
                fundamental.low_52weeks = row['low_52weeks']
                fundamental.ma_50days = row['ma_50days']
                fundamental.ma_200days = row['ma_200days']
            stock.fundamental = fundamental
            # print(stock)
            sp500_stock_map[stock.sector].append(stock)

    population = {}
    number_of_portfolio = 50

    while True:
        portfolio = GAPortfolio()
        portfolio.populate_portfolio(sp500_sectors, sp500_stock_map)
        portfolio.calculate_portfolio_daily_returns(sp500_sector_map)
        portfolio.calculate_portfolio_daily_beta(spy.daily_returns, us10y.daily_risk_free_rates)
        portfolio.calculate_expected_return()
        portfolio.calculate_expected_beta()
        portfolio.calculate_volatility()
        portfolio.calculate_yield(sp500_sector_map)
        portfolio.calculate_beta_and_trend(sp500_sector_map)
        portfolio.calculate_sharpe_ratio(us10y)
        portfolio.calculate_treynor_measure(us10y)
        portfolio.calculate_jensen_measure(spy, us10y)
        portfolio.calculate_score(spy)

        print(portfolio)

        population[portfolio.score] = portfolio
        if len(population) >= number_of_portfolio:
            break

    print("Generation 1\n")
    count = 0
    for key, portfolio in sorted(population.items()):
        count += 1
        print("Portfolio " + str(count) + ": " + str(key))
        print("yield: %8.4f%%, beta: %8.4f, daily_volatility:%8.4f%%, expected_daily_return:%8.4f%%" %
              ((portfolio.portfolio_yield * 100), portfolio.beta, (portfolio.volatility * 100),
               (portfolio.expected_daily_return * 100)))
        print("trend: %8.4f, sharpe_ratio:%8.4f, treynor_measure:%8.4f, jensen_measure:%8.4f, score:%8.4f" %
              (portfolio.trend, portfolio.sharpe_ratio, portfolio.treynor_measure, portfolio.jensen_measure,
               portfolio.score))

        for stock in portfolio.stocks:
            print(stock.symbol, end=",")
        print('\n')

    number_of_children = 10
    children = []
    number_of_generation = 100
    max_score = 0
    min_improvement = 0.01

    for i in range(1, number_of_generation):
        sorted_population_keys = sorted(population.keys())
        for key in sorted_population_keys[0:number_of_children]:
            del population[key]

        markedForParents = []
        number_of_parents = 20
        count = 0
        for key, portfolio in sorted(population.items(), reverse=True):
            markedForParents.append(portfolio)
            count += 1
            if count == number_of_parents:
                break

        for j in range(0, number_of_children):
            parent1_index = random.randint(0, number_of_parents - 1)
            parent2_index = random.randint(0, number_of_parents - 1)
            parent1 = markedForParents[parent1_index]
            parent2 = markedForParents[parent2_index]
            child = copy.deepcopy(parent1)
            for index in range(5, PORTFOLIO_NUM_OF_STOCK):
                stock = parent2.get_stock(index)
                child.update_stock(index, stock)

            child.calculate_portfolio_daily_returns(sp500_sector_map)
            child.calculate_portfolio_daily_beta(spy.daily_returns, us10y.daily_risk_free_rates)
            child.calculate_expected_return()
            child.calculate_expected_beta()
            child.calculate_volatility()
            child.calculate_yield(sp500_sector_map)
            child.calculate_beta_and_trend(sp500_sector_map)
            child.calculate_sharpe_ratio(us10y)
            child.calculate_treynor_measure(us10y)
            child.calculate_jensen_measure(spy, us10y)
            child.calculate_score(spy)
            children.append(child)

        num_of_mutation = 5
        for j in range(0, num_of_mutation):
            child_index = random.randint(0, number_of_children - 1)
            stock_index = random.randint(0, PORTFOLIO_NUM_OF_STOCK - 1)
            population_index = random.randint(0, len(population) - 1)
            key = list(population.keys())[population_index]
            children[child_index].update_stock(stock_index, population[key].get_stock(stock_index))
            children[child_index].calculate_portfolio_daily_returns(sp500_sector_map)
            children[child_index].calculate_portfolio_daily_beta(spy.daily_returns, us10y.daily_risk_free_rates)
            children[child_index].calculate_expected_return()
            children[child_index].calculate_expected_beta()
            children[child_index].calculate_volatility()
            children[child_index].calculate_yield(sp500_sector_map)
            children[child_index].calculate_beta_and_trend(sp500_sector_map)
            children[child_index].calculate_sharpe_ratio(us10y)
            children[child_index].calculate_treynor_measure(us10y)
            children[child_index].calculate_jensen_measure(spy, us10y)
            children[child_index].calculate_score(spy)

        for j in range(0, len(children)):
            population[children[j].score] = children[j]
        children.clear()

        print("Generation " + str(i + 1) + "\n")
        count = 0
        for key, portfolio in sorted(population.items()):
            count += 1
            print("Portfolio " + str(count) + ": " + str(key))
            print("yield: %8.4f%%, beta: %8.4f, daily_volatility:%8.4f%%, expected_daily_return:%8.4f%%" %
                  ((portfolio.portfolio_yield * 100), portfolio.beta, (portfolio.volatility * 100),
                   (portfolio.expected_daily_return * 100)))
            print("trend: %8.4f, sharpe_ratio:%8.4f, treynor_measure:%8.4f, jensen_measure:%8.4f, score:%8.4f" %
                  (portfolio.trend, portfolio.sharpe_ratio, portfolio.treynor_measure, portfolio.jensen_measure,
                   portfolio.score))

            for stock in portfolio.stocks:
                print(stock.symbol, end=",")
            print('\n')

        sorted_fitness = sorted(population.keys(), reverse=True)
        best_portfolio = population[sorted_fitness[0]]
        if abs(best_portfolio.score - max_score) < min_improvement:
            break
        else:
            max_score = best_portfolio.score

    for i in range(len(best_portfolio.stocks)):
        stock_select = "SELECT * FROM stocks WHERE strftime(\'%Y-%m-%d\', date) " \
                       "BETWEEN \"" + back_testing_start_date + "\" AND \"" + back_testing_end_date + \
                       "\" AND open > 0 AND close > 0 AND symbol = \'" + best_portfolio.stocks[i].symbol + "\';"
        print(stock_select)
        price_df = database.execute_sql_statement(stock_select)
        if price_df.empty:
            continue

        for index, row in price_df.iterrows():
            trade = Trade()
            trade.date = row['date']
            trade.open = row['open']
            trade.high = row['high']
            trade.low = row['low']
            trade.close = row['close']
            trade.adjusted_close = row['adjusted_close']
            trade.volume = row['volume']
            best_portfolio.stocks[i].add_trade(trade)

        best_portfolio.stocks[i].calculate_daily_return()

    best_portfolio.calculate_portfolio_daily_returns(sp500_sector_map)
    best_portfolio.calculate_cumulative_return(back_testing_start_date, back_testing_end_date)

    # make SPY captical in spy table
    spy_select = "SELECT * FROM spy WHERE strftime(\'%Y-%m-%d\', date) " \
                 "BETWEEN \"" + back_testing_start_date + "\" AND \"" + back_testing_end_date + \
                 "\" AND open > 0 AND close > 0 AND symbol = 'spy';"
    print(spy_select)
    price_df = database.execute_sql_statement(spy_select)

    for index, row in price_df.iterrows():
        trade = Trade()
        trade.date = row['date']
        trade.open = row['open']
        trade.high = row['high']
        trade.low = row['low']
        trade.close = row['close']
        trade.adjusted_close = row['adjusted_close']
        trade.volume = row['volume']
        spy.add_trade(trade)

    spy.calculate_daily_return()
    spy.calculate_cumulative_return(back_testing_start_date, back_testing_end_date)

    print("Back Test:")
    print("best portfolio cumulative return: %4.2f%%" % (best_portfolio.cumulative_return*100))
    print("spy cumulative return: %4.2f%%" % (spy.cumulative_return*100))


    ## TODO! make it base on back_testing_end_date
    probation_testing_start_date = "2020-07-01"
    probation_testing_end_date = "2020-07-31"

    fund = 1000000

    for i in range(len(best_portfolio.stocks)):
        stock_select = "SELECT * FROM stocks WHERE strftime(\'%Y-%m-%d\', date) " \
                       "BETWEEN \"" + probation_testing_start_date + "\" AND \"" + probation_testing_end_date + \
                       "\" AND open > 0 AND close > 0 AND symbol = \'" + best_portfolio.stocks[i].symbol + "\';"
        print(stock_select)
        price_df = database.execute_sql_statement(stock_select)
        if price_df.empty:
            continue

        for index, row in price_df.iterrows():
            trade = Trade()
            trade.date = row['date']
            trade.open = row['open']
            trade.high = row['high']
            trade.low = row['low']
            trade.close = row['close']
            trade.adjusted_close = row['adjusted_close']
            trade.volume = row['volume']
            best_portfolio.stocks[i].add_trade(trade)

        best_portfolio.stocks[i].calculate_daily_return()

    best_portfolio.calculate_portfolio_daily_returns(sp500_sector_map)

    for i in range(len(best_portfolio.stocks)):
        best_portfolio.stocks[i].probation_test_trade.open_date = probation_testing_start_date
        best_portfolio.stocks[i].probation_test_trade.close_date = probation_testing_end_date
        best_portfolio.stocks[i].probation_test_trade.open_price = best_portfolio.stocks[i].trades[probation_testing_start_date].open
        best_portfolio.stocks[i].probation_test_trade.close_price = best_portfolio.stocks[i].trades[probation_testing_end_date].close
        best_portfolio.stocks[i].probation_test_trade.shares = int(fund*best_portfolio.stocks[i].category_pct/
                                                                   best_portfolio.stocks[i].probation_test_trade.open_price)
        best_portfolio.stocks[i].probation_test_trade.profit_loss = (best_portfolio.stocks[i].probation_test_trade.close_price -
                                                                     best_portfolio.stocks[i].probation_test_trade.open_price) * \
                                                                    best_portfolio.stocks[i].probation_test_trade.shares

    best_portfolio.calculate_profit_loss()

    # make SPY captical in spy table
    spy_select = "SELECT * FROM spy WHERE strftime(\'%Y-%m-%d\', date) " \
                 "BETWEEN \"" + probation_testing_start_date + "\" AND \"" + probation_testing_end_date + \
                 "\" AND open > 0 AND close > 0 AND symbol = 'spy';"
    print(spy_select)
    price_df = database.execute_sql_statement(spy_select)

    for index, row in price_df.iterrows():
        trade = Trade()
        trade.date = row['date']
        trade.open = row['open']
        trade.high = row['high']
        trade.low = row['low']
        trade.close = row['close']
        trade.adjusted_close = row['adjusted_close']
        trade.volume = row['volume']
        spy.add_trade(trade)

    spy.calculate_daily_return()
    # TODO! We have an issue when there is a stock split or reverse split
    spy.probation_test_trade.open_date = probation_testing_start_date
    spy.probation_test_trade.close_date = probation_testing_end_date
    spy.probation_test_trade.open_price = spy.trades[probation_testing_start_date].open
    spy.probation_test_trade.close_price = spy.trades[probation_testing_end_date].close
    spy.probation_test_trade.shares = int(fund/spy.probation_test_trade.open_price)
    spy.probation_test_trade.profit_loss = (spy.probation_test_trade.close_price - spy.probation_test_trade.open_price) * \
                                           spy.probation_test_trade.shares

    print("Probabtion Test:")
    print("best portfolio return: %4.2f%%" % (float(best_portfolio.profit_loss/fund)*100))
    print("spy return: %4.2f%%" % (float(spy.probation_test_trade.profit_loss/fund)*100))

if __name__ == "__main__":
    #create_populate_tables()
    build_ga_model()
