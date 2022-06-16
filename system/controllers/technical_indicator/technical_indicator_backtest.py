import warnings
from datetime import datetime

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

from system.services.mep_strategy.mep import stock_backtest_executors, industry_description, stock_collection, \
    generate_optimized_executor

warnings.simplefilter(action='ignore', category=SAWarning)


def technical_indicator_backtest_service():
    if request.method == 'GET':
        return render_template("technical_indicator_backtest_param.html")

    if request.method == 'POST':
        training_period_start_date = request.form['training_period_start_date']
        training_period_end_date = request.form['training_period_end_date']
        backtest_period_start_date = request.form['backtest_period_start_date']
        backtest_period_end_date = request.form['backtest_period_end_date']

        try:
            tpsd = datetime.strptime(training_period_start_date, '%Y-%m-%d')
            tped = datetime.strptime(training_period_end_date, '%Y-%m-%d')
            bpsd = datetime.strptime(backtest_period_start_date, '%Y-%m-%d')
            bped = datetime.strptime(backtest_period_end_date, '%Y-%m-%d')
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
            return render_template("technical_indicator_backtest_param.html")

        # 1. Make sure that there are at least 8 years in the training period
        if (tped - tpsd).days < 8 * 365:
            flash("Error: There must be at least 8 years for the training period.", 'error')
            return render_template("technical_indicator_backtest_param.html")

        # 2. Make sure that there are at least 1 year in the backtest period
        if (bped - bpsd).days < 365:
            flash("Error: There must be at least 1 year for the backtest period.", 'error')
            return render_template("technical_indicator_backtest_param.html")

        # 3. Make sure that the start date of backtest period is later than the end date of training period
        if bpsd < tped:
            flash("Error: The start date of backtest period must be no earlier than the end date of training period.",
                  'error')
            return render_template("technical_indicator_backtest_param.html")

        # 4. Make sure that the end date of backtest period is earlier than today
        if bped >= datetime.today():
            flash("Error: The end date of backtest period must be earlier than today.", 'error')
            return render_template("technical_indicator_backtest_param.html")

        for industry, stocks in stock_collection.items():
            print(f"@@@@@ INDUSTRY={industry.title()} Sector")

            for stock in stocks:
                print(f"  ### STOCK={stock}")
                se = generate_optimized_executor(stock, training_period_start_date, training_period_end_date, \
                                                 backtest_period_start_date, backtest_period_end_date)
                stock_backtest_executors[stock] = se

        return render_template("technical_indicator_backtest.html", \
                               start_date_train=training_period_start_date, end_date_train=training_period_end_date, \
                               start_date_test=backtest_period_start_date, end_date_test=backtest_period_end_date, \
                               stock_collection=stock_collection, industry_description=industry_description, \
                               stock_backtest_executors=stock_backtest_executors)