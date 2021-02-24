# -*- coding: utf-8 -*
# !/usr/bin/env python3
import sys

from system.ai_modeling.ga_portfolio import Stock, Trade, Fundamental, GAPortfolio, PORTFOLIO_NUM_OF_STOCK

sys.path.append('../')

import copy
import datetime as dt
import random
from typing import List, Tuple, Dict
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

def extract_spy(database, start_date: str, end_date: str, include_fundamental: bool = True) -> Stock:
    """
    Extract SPY's data from database between start and end date
    ------------------------------------------------------------
    params:
        database: 
        start_date: str
        end_date: str
        include_fundamental: True if also include fundamental data; else not include
    return:
        spy: Stock object, with price dataframe (price_df) and fundamental dataframe (fundamental_df)
    """
    spy = Stock()
    spy.symbol = 'spy'

    # Extract price data from table spy
    spy_select = "SELECT date, open, close FROM spy WHERE strftime(\'%Y-%m-%d\', date) BETWEEN \"" + \
                 start_date + "\" AND \"" + end_date + "\";"
    price_df = database.execute_sql_statement(spy_select)

    # Calculate daily return
    price_df['spy_dailyret'] = price_df['close'].pct_change()
    price_df['spy_dailyret'].iloc[0] = price_df['close'].iloc[0] / price_df['open'].iloc[0] - 1.0
    price_df['spy_daily_cumulative_return'] = (price_df['spy_dailyret'] + 1.0).cumprod() - 1.0
    spy.price_df = price_df[['date', 'spy_dailyret', 'spy_daily_cumulative_return']]
    spy.cumulative_return = spy.price_df['spy_daily_cumulative_return'].iloc[-1]
    
    spy.expected_daily_return = price_df['spy_dailyret'].mean()
    spy.volatility = price_df['spy_dailyret'].std()

    # Extract fundamental data from table fundamentals
    if include_fundamental:
        spy_fundamental_select = "SELECT * FROM fundamentals WHERE symbol = \"SPY\";"
        fundamental_df = database.execute_sql_statement(spy_fundamental_select)
        spy.fundamental_df = fundamental_df
    
    return spy 

def extract_us10y(database, start_date: str, end_date: str) -> Stock:
    """
    Extract us10y's data from database between start and end date
    ------------------------------------------------------------
    params:
        database:
        start_date:
        end_date:
    return:
        us10y: Stock Object, with price_df 
    """
    us10y = Stock()
    us10y.symbol = 'us10y'
    # Extract data from db
    us10y_select = "SELECT date, close FROM us10y WHERE strftime(\'%Y-%m-%d\', date) BETWEEN \"" + \
                 start_date + "\" AND \"" + end_date + "\";"
    price_df = database.execute_sql_statement(us10y_select)
    # Calculation
    price_df['rate'] = price_df['close'] / 100
    us10y.expected_daily_return = price_df['rate'].mean()
    us10y.price_df = price_df[['date', 'rate']]
    
    return us10y 


def crossover_and_mutate(num_of_parents: int, num_of_children: int, num_of_mutation: int, markedForParents: List[GAPortfolio], population: Dict[float, GAPortfolio]) -> List[GAPortfolio]:
    """
    description:
        Do crossover and mutate; 2 parent portfolios will generate 1 child portfolio
        child will inherit first 5 stocks of parent 1 and last 6 stocks of parent 2
    ---------------------------
    params:
        num_of_parents: int, # of parents selected
        num_of_children: int, # of children generated
        num_of_mutation: int, # of mutation happens
        markedForParents: List[GAPortfolio], a list of portfolios with highest score
        population: Dict {score: portfolio}
    ---------------------------
    return:
        children: List[GAPortfolio], children portfolios (metrics not calculated)
    """
    # Generate children portfolios by crossover
    children = []
    for i in range(0, num_of_children):
        parent1_index = random.randint(0, num_of_parents - 1)
        parent2_index = random.randint(0, num_of_parents - 1)
        parent1 = markedForParents[parent1_index]
        parent2 = markedForParents[parent2_index]
        child = copy.deepcopy(parent1)
        for index in range(5, PORTFOLIO_NUM_OF_STOCK):
            stock = parent2.get_stock(index)
            child.update_stock(index, stock)
        children.append(child)

    # Mutation
    for i in range(0, num_of_mutation):
        child_index = random.randint(0, num_of_children - 1) # randomly pick a child from children
        stock_index = random.randint(0, PORTFOLIO_NUM_OF_STOCK - 1) # randomly pick a gene to mutate
        population_index = random.randint(0, len(population) - 1)   # randomly pick a portfolio from population
        key = list(population.keys())[population_index] # find the key of select portfolio
        children[child_index].update_stock(stock_index, population[key].get_stock(stock_index)) # mutate the gene with the select portfolio's gene
    
    return children

def build_ga_model(database) -> GAPortfolio:
    """
    description:
        Build GA Model, including prepare data, create GAPortfolio objects, crossover & mutate, calculate score
    ---------------------------
    params:
        database:
    ---------------------------
    return:
        best_portfolio
    """
    modeling_testing_start_date = dt.date(2010, 1, 1).strftime('%Y-%m-%d')
    modeling_testing_end_date = dt.date(2020, 1, 1).strftime('%Y-%m-%d')

    # Extract SPY & us10y data from db 
    spy = extract_spy(database, modeling_testing_start_date, modeling_testing_end_date)
    us10y = extract_us10y(database, modeling_testing_start_date, modeling_testing_end_date)

    # Extract stock symbols from table sp500; {sector: (symbol, name)}
    sp500_symbol_map = database.get_sp500_symbol_map()

    # Extract fundamental data from table fundamentals
    # Merge with sector and sector weight
    fundamental_select = "SELECT fundamentals.symbol, pe_ratio, dividend_yield, beta,\
                        ma_50days, ma_200days, sp500_sectors.sector, sp500_sectors.category_pct AS weight\
                        FROM fundamentals, sp500, sp500_sectors\
                        WHERE fundamentals.symbol = sp500.symbol\
                        AND sp500.sector = sp500_sectors.sector;"
    fundamental_df = database.execute_sql_statement(fundamental_select)
    if fundamental_df.empty:
        exit("fundamental_df is empty")
    fundamental_df.sort_values(['sector','symbol'], inplace=True)

    # Extract stock prices from table stocks
    # Merge name, with sector, sector weight
    stock_select = "SELECT stocks.symbol, stocks.date, stocks.open, stocks.close, sp500.name, sp500_sectors.category_pct AS weight\
                    FROM stocks, sp500, sp500_sectors\
                    WHERE stocks.symbol = sp500.symbol\
                    AND sp500.sector = sp500_sectors.sector\
                    AND strftime(\'%Y-%m-%d\', date) BETWEEN \"" + modeling_testing_start_date + "\" AND \"" + \
                    modeling_testing_end_date + "\" AND open > 0 AND close > 0;"
    price_df = database.execute_sql_statement(stock_select)
    if price_df.empty:
        exit("price_df is empty")

    # Calculate stock daily return
    price_df['dailyret'] = price_df.groupby('symbol')['close'].pct_change()
    price_df['dailyret'].fillna(price_df['close']/price_df['open']-1.0, inplace=True)
    price_df.set_index('date', inplace=True)    # set index, easier for further operations

    # Extract sector weight from Table sp500 and convert to a dict {sector: weight}
    sp500_sector_select = "SELECT sector, category_pct from sp500_sectors;"
    sp500_sector_df = database.execute_sql_statement(sp500_sector_select)
    sp500_sector_map = sp500_sector_df.set_index('sector')['category_pct'].to_dict()

    # Begin GA
    population = {}
    number_of_portfolio = 50

    while True:
        portfolio = GAPortfolio()   # create an empty GAPortfolio object
        portfolio.populate_portfolio(sp500_symbol_map, sp500_sector_map)    # randomly select 11 stocks to build portfolio
        portfolio.calculate_portfolio_return(price_df)   # calculate portfolio daily return
        portfolio.calculate_expected_beta(spy.price_df)
        portfolio.populate_portfolio_fundamentals(fundamental_df)   # Extract fundamental data of stocks of this portfolio
        portfolio.calculate_yield()
        portfolio.calculate_beta_and_trend()
        portfolio.calculate_sharpe_ratio(us10y)
        portfolio.calculate_treynor_measure(us10y)
        portfolio.calculate_jensen_measure(spy, us10y)
        portfolio.calculate_score(spy)

        population[portfolio.score] = portfolio
        if len(population) >= number_of_portfolio:
            break

    # print("Generation 1\n")
    # count = 0
    # for key, portfolio in sorted(population.items()):
    #     count += 1
    #     print("Portfolio " + str(count) + ": " + str(key))
    #     print("yield: %8.4f%%, beta: %8.4f, daily_volatility:%8.4f%%, expected_daily_return:%8.4f%%" %
    #           ((portfolio.portfolio_yield * 100), portfolio.beta, (portfolio.volatility * 100),
    #            (portfolio.expected_daily_return * 100)))
    #     print("trend: %8.4f, sharpe_ratio:%8.4f, treynor_measure:%8.4f, jensen_measure:%8.4f, score:%8.4f" %
    #           (portfolio.trend, portfolio.sharpe_ratio, portfolio.treynor_measure, portfolio.jensen_measure,
    #            portfolio.score))

        # for stock in portfolio.stocks:
        #     print(stock.symbol, end=",")
        # print('\n')

    num_of_children = 10
    children = []
    number_of_generation = 100
    max_score = 0
    min_improvement = 0.01

    for i in range(1, number_of_generation):
        # Delete the bottom 10 portfolios
        sorted_population_keys = sorted(population.keys())
        for key in sorted_population_keys[0:num_of_children]:
            del population[key]

        # Select the top 20 portfolios as parents
        markedForParents = []
        num_of_parents = 20
        count = 0
        for key, portfolio in sorted(population.items(), reverse=True):
            markedForParents.append(portfolio)
            count += 1
            if count == num_of_parents:
                break

        # Crossover & Mutation
        num_of_mutation = 5
        children = crossover_and_mutate(num_of_parents, num_of_children, num_of_mutation, markedForParents, population)
        for n in range(num_of_children):
            children[n].calculate_portfolio_return(price_df)   # calculate portfolio daily return
            children[n].calculate_expected_beta(spy.price_df)
            children[n].populate_portfolio_fundamentals(fundamental_df)
            children[n].calculate_yield()
            children[n].calculate_beta_and_trend()
            children[n].calculate_sharpe_ratio(us10y)
            children[n].calculate_treynor_measure(us10y)
            children[n].calculate_jensen_measure(spy, us10y)
            children[n].calculate_score(spy)

        # Insert children into population
        for n in range(num_of_children):
            population[children[n].score] = children[n]
        children.clear()

        # print("Generation " + str(i + 1) + "\n")
        # count = 0
        # for key, portfolio in sorted(population.items()):
        #     count += 1
        #     print("Portfolio " + str(count) + ": " + str(key))
        #     print("yield: %8.4f%%, beta: %8.4f, daily_volatility:%8.4f%%, expected_daily_return:%8.4f%%" %
        #           ((portfolio.portfolio_yield * 100), portfolio.beta, (portfolio.volatility * 100),
        #            (portfolio.expected_daily_return * 100)))
        #     print("trend: %8.4f, sharpe_ratio:%8.4f, treynor_measure:%8.4f, jensen_measure:%8.4f, score:%8.4f" %
        #           (portfolio.trend, portfolio.sharpe_ratio, portfolio.treynor_measure, portfolio.jensen_measure,
        #            portfolio.score))

            # for stock in portfolio.stocks:
            #     print(stock.symbol, end=",")
            # print('\n')

        sorted_fitness = sorted(population.keys(), reverse=True)
        best_portfolio = population[sorted_fitness[0]]
        if abs(best_portfolio.score - max_score) < min_improvement:
            #TODO! Move this logic into fre_database
            for n in range(PORTFOLIO_NUM_OF_STOCK):
                conn = database.engine.connect()
                table = database.metadata.tables["best_portfolio"]
                sector, symbol, weight, name = best_portfolio.stocks[n]
                insert_stmt = table.insert().values(symbol=symbol, name=name, sector=sector,
                                                    category_pct=weight,
                                                    open_date="", open_price=0, close_date="", close_price=0, shares=0,
                                                    profit_loss=0)
                conn.execute(insert_stmt)
            return best_portfolio
        else:
            max_score = best_portfolio.score