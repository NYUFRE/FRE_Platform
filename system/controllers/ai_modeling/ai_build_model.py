import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

from system.services.ai_modeling.ga_portfolio_select import build_ga_model

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database


def ai_build_model_service():
    table_list = ['best_portfolio']
    database.create_table(table_list)
    database.clear_table(table_list)
    best_portfolio = build_ga_model(database)
    print("yield: %8.4f%%, beta: %8.4f, daily_volatility:%8.4f%%, expected_daily_return:%8.4f%%" %
          ((best_portfolio.portfolio_yield * 100), best_portfolio.beta, (best_portfolio.volatility * 100),
           (best_portfolio.expected_daily_return * 100)))
    print("trend: %8.4f, sharpe_ratio:%8.4f, score:%8.4f" %
          (best_portfolio.trend, best_portfolio.sharpe_ratio, best_portfolio.score))
    # Show stocks' information of best portfolio
    stocks = []
    for stock in best_portfolio.stocks:
        print(stock)  # (symbol, name, sector,weight)
        stocks.append((stock[1], stock[3], stock[0], str(round(stock[2] * 100, 4))))
    length = len(stocks)
    # Show portfolio's score metrics
    portfolio_yield = str(round(best_portfolio.portfolio_yield * 100, 4)) + '%'
    beta = str(round(best_portfolio.beta, 4))
    volatility = str(round(best_portfolio.volatility * 100, 4)) + '%'
    daily_return = str(round(best_portfolio.expected_daily_return * 100, 4)) + '%'
    trend = str(round(best_portfolio.trend, 4))
    sharpe_ratio = str(round(best_portfolio.sharpe_ratio, 4))
    score = str(round(best_portfolio.score, 4))
    return render_template('ai_best_portfolio.html', stock_list=stocks, portfolio_yield=portfolio_yield,
                           beta=beta, volatility=volatility, daily_return=daily_return, trend=trend,
                           sharpe_ratio=sharpe_ratio, score=score, length=length)