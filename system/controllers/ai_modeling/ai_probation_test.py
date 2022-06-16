import warnings
from datetime import datetime
import datetime as dt

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

from system.services.ai_modeling.ga_portfolio_probation_test import ga_probation_test

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database

from system.services.ai_modeling.ga_portfolio import Stock, ProbationTestTrade


from system.services.utility.helpers import usd


def ai_probation_test_service():
    if request.method == 'GET':
        probation_start_date = (dt.date(2020, 12, 31) + dt.timedelta(days=1)).strftime('%Y-%m-%d')
        probation_end_date = dt.date.today().strftime('%Y-%m-%d')
        best_portfolio, spy_profit_loss, cash = ga_probation_test(database, probation_start_date, probation_end_date)
        portfolio_profit = "{:.2f}".format((float(best_portfolio.profit_loss / cash) * 100))
        spy_profit = "{:.2f}".format((float(spy_profit_loss / cash) * 100))
        profit = best_portfolio.profit_loss

        # stock_list = [val[0] for val in best_portfolio.stocks]
        stock_list = []
        for i, stock in enumerate(best_portfolio.stocks):
            stock_obj = Stock()
            stock_obj.symbol = stock[1]
            stock_obj.name = stock[3]
            stock_obj.category_pct = stock[2]
            stock_obj.sector = stock[0]

            probation_obj = ProbationTestTrade()
            probation_obj.open_date = best_portfolio.start_date
            probation_obj.close_date = best_portfolio.end_date
            probation_obj.open_price = best_portfolio.open_prices[i]
            probation_obj.close_price = best_portfolio.close_prices[i]
            probation_obj.shares = best_portfolio.shares[i]
            probation_obj.profit_loss = best_portfolio.pnl[i]

            stock_obj.probation_test_trade = probation_obj
            stock_list.append(stock_obj)

        length = len(stock_list)
        return render_template('ai_probation_test.html', stock_list=stock_list,
                               portfolio_profit=portfolio_profit, spy_profit=spy_profit,
                               profit=usd(profit), length=length, probation_start_date=probation_start_date,
                               probation_end_date=probation_end_date)

    if request.method == 'POST':
        probation_start_date = request.form['probation_start_date']
        probation_end_date = request.form['probation_end_date']
        try:
            psd = datetime.strptime(probation_start_date, '%Y-%m-%d')
            ped = datetime.strptime(probation_end_date, '%Y-%m-%d')
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
            return render_template('ai_probation_test.html')
        # Make sure that the ending date would be earlier than starting date
        if ped < psd:
            flash(
                "Error: The ending date of backtest period must be no earlier than the start date of backtest period.",
                'error')
            return render_template('ai_probation_test.html')

        # Make sure that the end date of backtest period is earlier than today
        if ped >= datetime.today():
            flash("Error: The end date of backtest period must be earlier than today.", 'error')
            return render_template('ai_probation_test.html')

        best_portfolio, spy_profit_loss, cash = ga_probation_test(database, psd, ped)
        portfolio_profit = "{:.2f}".format((float(best_portfolio.profit_loss / cash) * 100))
        spy_profit = "{:.2f}".format((float(spy_profit_loss / cash) * 100))
        profit = best_portfolio.profit_loss

        # stock_list = [val[0] for val in best_portfolio.stocks]
        stock_list = []
        for i, stock in enumerate(best_portfolio.stocks):
            stock_obj = Stock()
            stock_obj.symbol = stock[1]
            stock_obj.name = stock[3]
            stock_obj.category_pct = stock[2]
            stock_obj.sector = stock[0]

            probation_obj = ProbationTestTrade()
            probation_obj.open_date = best_portfolio.start_date
            probation_obj.close_date = best_portfolio.end_date
            probation_obj.open_price = best_portfolio.open_prices[i]
            probation_obj.close_price = best_portfolio.close_prices[i]
            probation_obj.shares = best_portfolio.shares[i]
            probation_obj.profit_loss = best_portfolio.pnl[i]

            stock_obj.probation_test_trade = probation_obj
            stock_list.append(stock_obj)

        length = len(stock_list)
        return render_template('ai_probation_test.html', stock_list=stock_list,
                               portfolio_profit=portfolio_profit, spy_profit=spy_profit,
                               profit=usd(profit), length=length, probation_start_date=psd, probation_end_date=ped)
