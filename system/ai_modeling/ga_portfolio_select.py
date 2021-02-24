# -*- coding: utf-8 -*
# !/usr/bin/env python3
import sys

from system.ai_modeling.ga_portfolio import Stock, Trade, Fundamental, GAPortfolio, PORTFOLIO_NUM_OF_STOCK

sys.path.append('../')

import copy
import datetime as dt
import random

#SP500_NUM_OF_STOCKS = 505
#PORTFOLIO_NUM_OF_STOCK = 11

start_date = dt.date(2019, 1, 1).strftime('%Y-%m-%d')
end_date = dt.datetime.today().strftime('%Y-%m-%d')

def create_populate_tables(database, eod_market_data):
    tables = ['sp500', 'sp500_sectors', 'fundamentals', 'stocks', 'spy', 'us10y', 'best_portfolios']
    database.create_table(tables)
    database.clear_table(tables)
    eod_market_data.populate_sp500_data('SPY', 'US')
    tickers = database.get_sp500_symbols()
    eod_market_data.populate_stock_data(tickers, "stocks", start_date, end_date, 'US')
    eod_market_data.populate_stock_data(['SPY'], "spy", start_date, end_date, 'US')
    eod_market_data.populate_stock_data(['US10Y'], "us10y", start_date, end_date, 'INDX')
    tickers.append('SPY')
    eod_market_data.populate_fundamental_data(tickers, 'US')

    """
    tables = ['best_portfolio']
    database.create_table(tables)
    database.clear_table(tables)
    """


def build_ga_model(database):
    spy = Stock()
    spy.symbol = 'SPY'

    us10y = Stock()
    us10y.symbol = 'US10Y'

    sp500_stock_map = {}
    sp500_sectors = database.get_sp500_sectors()
    for sector in sp500_sectors:
        sp500_stock_map[sector] = []

    modeling_testing_start_date = dt.date(2019, 1, 1).strftime('%Y-%m-%d')
    modeling_testing_end_date = dt.date(2019, 12, 31).strftime('%Y-%m-%d')

    spy_select = "SELECT * FROM spy WHERE strftime(\'%Y-%m-%d\', date) BETWEEN \"" + \
                 modeling_testing_start_date + "\" AND \"" + modeling_testing_end_date + "\";"
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

    us10y_select = "SELECT * FROM us10y WHERE strftime(\'%Y-%m-%d\', date) BETWEEN \"" + \
                   modeling_testing_start_date + "\" AND \"" + modeling_testing_end_date + "\";"
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
        stock_select = "SELECT * FROM stocks WHERE strftime(\'%Y-%m-%d\', date) BETWEEN \"" + modeling_testing_start_date + "\" AND \"" + \
                       modeling_testing_end_date + "\" AND open > 0 AND close > 0 AND symbol IN (" + ",".join(
            "'" + symbol_name[0] + "'" for symbol_name in symbols) + ");"
        print(stock_select)
        price_df = database.execute_sql_statement(stock_select)
        if price_df.empty:
            exit("price_df is empty")

        fundamental_select = "SELECT * FROM Fundamentals WHERE symbol IN (" + ",".join(
            "'" + symbol_name[0] + "'" for symbol_name in symbols) + ");"
        print(fundamental_select)
        fundamental_df = database.execute_sql_statement(fundamental_select)
        if fundamental_df.empty:
            exit("fundamental_df is empty")

        for symbol_name in sorted(symbols):
            stock = Stock()
            stock.symbol = symbol_name[0]
            stock.name = symbol_name[1]
            stock.sector = key
            stock.category_pct = sp500_sector_map[key]

            trades = price_df.loc[price_df['symbol'] == symbol_name[0]]
            for index, row in trades.iterrows():
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

            fundamental = Fundamental()
            for index, row in fundamental_df.loc[fundamental_df['symbol'] == symbol_name[0]].iterrows():
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
        # print(symbols)

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
            for stock in best_portfolio.stocks:
                # TODO! Move this logic into fre_database
                # portfolio_insert_table = "INSERT INTO portfolios (symbol, sector, category_pct, open_date, open_price, close_date, close_price, shares, profitL_loss) \
                #                        VALUES(\"%s\", \"%s\", %f, \"%s\", %f, \"%s\", %f, %d, %f)" % (stock.symbol, stock.sector, stock.category_pct, "", 0, "", 0, 0, 0)
                # print(portfolio_insert_table)
                # database.engine.execute(portfolio_insert_table, True)

                conn = database.engine.connect()
                table = database.metadata.tables["best_portfolio"]
                insert_stmt = table.insert().values(symbol=stock.symbol, name=stock.name, sector=stock.sector,
                                                    category_pct=stock.category_pct,
                                                    open_date="", open_price=0, close_date="", close_price=0, shares=0,
                                                    profit_loss=0)
                conn.execute(insert_stmt)
            return best_portfolio
        else:
            max_score = best_portfolio.score
    """
    # Back Testing
    back_testing_start_date = dt.date(2020, 1, 1).strftime('%Y-%m-%d')
    back_testing_end_date = dt.date(2020, 6, 30).strftime('%Y-%m-%d')

    for i in range(len(best_portfolio.stocks)):
        stock_select = "SELECT * FROM stocks WHERE strftime(\'%Y-%m-%d\', date) " \
                       "BETWEEN \"" + back_testing_start_date + "\" AND \"" + back_testing_end_date + \
                       "\" AND open > 0 AND close > 0 AND symbol = \'" + best_portfolio.stocks[i].symbol + "\';"
        print(stock_select)
        price_df = database.execute_sql_statement(stock_select)
        if price_df.empty:
            exit("back testing price_df is empty")
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

    # Probation Testing
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
    print("best portfolio cumulative return: %4.2f%%" % (best_portfolio.cumulative_return * 100))
    print("spy cumulative return: %4.2f%%" % (spy.cumulative_return * 100))

    # Probation Testing
    # probation_testing_start_date = "2020-07-01"
    # probation_testing_end_date = "2020-07-31"
    probation_testing_start_date = (dt.date(2020, 6, 30) + dt.timedelta(days=1)).strftime('%Y-%m-%d')
    # probation_testing_end_date = previous_working_day(dt.datetime.today()).strftime('%Y-%m-%d')
    probation_testing_end_date = previous_working_day(dt.date(2020, 8, 1)).strftime('%Y-%m-%d')

    for i in range(len(best_portfolio.stocks)):
        stock_select = "SELECT * FROM stocks WHERE strftime(\'%Y-%m-%d\', date) " \
                       "BETWEEN \"" + probation_testing_start_date + "\" AND \"" + probation_testing_end_date + \
                       "\" AND open > 0 AND close > 0 AND symbol = \'" + best_portfolio.stocks[i].symbol + "\';"
        print(stock_select)
        price_df = database.execute_sql_statement(stock_select)
        if price_df.empty:
            exit("probation testing price_df is empty")
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
        best_portfolio.stocks[i].probation_test_trade.open_price = best_portfolio.stocks[i].trades[
            probation_testing_start_date].adjusted_close
        best_portfolio.stocks[i].probation_test_trade.close_price = best_portfolio.stocks[i].trades[
            probation_testing_end_date].adjusted_close
        best_portfolio.stocks[i].probation_test_trade.shares = int(fund * best_portfolio.stocks[i].category_pct /
                                                                   best_portfolio.stocks[
                                                                       i].probation_test_trade.open_price)
        best_portfolio.stocks[i].probation_test_trade.profit_loss = (best_portfolio.stocks[
                                                                         i].probation_test_trade.close_price -
                                                                     best_portfolio.stocks[
                                                                         i].probation_test_trade.open_price) * \
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

    spy.probation_test_trade.open_date = probation_testing_start_date
    spy.probation_test_trade.close_date = probation_testing_end_date
    spy.probation_test_trade.open_price = spy.trades[probation_testing_start_date].open
    spy.probation_test_trade.close_price = spy.trades[probation_testing_end_date].close
    spy.probation_test_trade.shares = int(fund / spy.probation_test_trade.open_price)
    spy.probation_test_trade.profit_loss = (
                                                       spy.probation_test_trade.close_price - spy.probation_test_trade.open_price) * \
                                           spy.probation_test_trade.shares

    print("Probabtion Test:")
    print("best portfolio return: %4.2f%%" % (float(best_portfolio.profit_loss / fund) * 100))
    print("spy return: %4.2f%%" % (float(spy.probation_test_trade.profit_loss / fund) * 100))
    """


