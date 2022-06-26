import warnings
from datetime import datetime
import datetime as dt

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database

from system.services.ai_modeling.ga_portfolio_back_test import ga_back_test, ga_back_test_result


def ai_back_test_service():
    if request.method == 'GET':
        bpsd = dt.date(2020, 1, 1).strftime('%Y-%m-%d')
        bped = dt.date(2020, 12, 31).strftime('%Y-%m-%d')
        best_portfolio, spy = ga_back_test(database, bpsd, bped)

        # Used for function "ai_back_test_plot"
        ga_back_test_result.bt_start_date = str(spy.price_df.index[0])[:10]
        ga_back_test_result.bt_end_date = str(spy.price_df.index[-1])[:10]
        ga_back_test_result.portfolio_cum_rtn = best_portfolio.portfolio_daily_cumulative_returns.copy()
        ga_back_test_result.spy_cum_rtn = spy.price_df['spy_daily_cumulative_return'].copy()

        portfolio_return = "{:.2f}".format(best_portfolio.cumulative_return * 100, 2)
        spy_return = "{:.2f}".format(spy.cumulative_return * 100, 2)
        return render_template('ai_back_test.html', portfolio_return=portfolio_return,
                               spy_return=spy_return, start_date_test=bpsd, end_date_test=bped)

    if request.method == 'POST':
        backtest_period_start_date = request.form['backtest_period_start_date']
        backtest_period_end_date = request.form['backtest_period_end_date']
        try:
            bpsd = datetime.strptime(backtest_period_start_date, '%Y-%m-%d')
            bped = datetime.strptime(backtest_period_end_date, '%Y-%m-%d')
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
            return render_template('ai_back_test.html')
        # Make sure that the ending date would be earlier than starting date
        if bped < bpsd:
            flash(
                "Error: The ending date of backtest period must be no earlier than the start date of backtest period.",
                'error')
            return render_template('ai_back_test.html')

        # Make sure that the end date of backtest period is earlier than today
        if bped >= datetime.today():
            flash("Error: The end date of backtest period must be earlier than today.", 'error')
            return render_template('ai_back_test.html')

        best_portfolio, spy = ga_back_test(database, bpsd, bped)

        # Used for function "ai_back_test_plot"
        ga_back_test_result.bt_start_date = str(spy.price_df.index[0])[:10]
        ga_back_test_result.bt_end_date = str(spy.price_df.index[-1])[:10]
        ga_back_test_result.portfolio_cum_rtn = best_portfolio.portfolio_daily_cumulative_returns.copy()
        ga_back_test_result.spy_cum_rtn = spy.price_df['spy_daily_cumulative_return'].copy()

        portfolio_return = "{:.2f}".format(best_portfolio.cumulative_return * 100, 2)
        spy_return = "{:.2f}".format(spy.cumulative_return * 100, 2)
        return render_template('ai_back_test.html', portfolio_return=portfolio_return,
                               spy_return=spy_return, start_date_test=bpsd, end_date_test=bped)