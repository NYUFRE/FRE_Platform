import warnings
from datetime import datetime

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

from system.services.mep_strategy.mep import stock_available, generate_executor, stock_probtest_executors

warnings.simplefilter(action='ignore', category=SAWarning)


def technical_indicator_probtest_service():
    if request.method == 'GET':
        return render_template("technical_indicator_probtest_param.html")

    if request.method == 'POST':
        probtest_period_start_date = request.form['probtest_period_start_date']
        probtest_period_end_date = request.form['probtest_period_end_date']
        probtest_stock = request.form['probtest_stock']
        probtest_alpha = request.form['probtest_alpha']
        probtest_delta = request.form['probtest_delta']
        probtest_gamma = request.form['probtest_gamma']

        try:
            ppsd = datetime.strptime(probtest_period_start_date, '%Y-%m-%d')
            pped = datetime.strptime(probtest_period_end_date, '%Y-%m-%d')
            probtest_alpha = float(probtest_alpha)
            probtest_delta = float(probtest_delta)
            probtest_gamma = float(probtest_gamma)
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
            return render_template("technical_indicator_probtest_param.html")

        # 1. Make sure that the probation test end date is at least 1 year from the start date
        if (pped - ppsd).days < 365:
            flash("Error: There must be at least 1 year for the probation test period.", 'error')
            return render_template("technical_indicator_probtest_param.html")

        # 2. Make sure that the end date of probation test is earlier than today
        if pped >= datetime.today():
            flash("Error: The end date of probation test must be earlier than today.", 'error')
            return render_template("technical_indicator_probtest_param.html")

        # 3. Make sure that the range of alpha is 0.05 <= alpha <= 0.35
        if probtest_alpha < 0.05 or probtest_alpha > 0.35:
            flash("Error: Alpha must be within range [0.05, 0.35].", 'error')
            return render_template("technical_indicator_probtest_param.html")

        # 4. Make sure that the range of delta is 0.10 <= delta <= 1.90
        if probtest_delta < 0.10 or probtest_delta > 1.90:
            flash("Error: Delta must be within range [0.10, 1.90].", 'error')
            return render_template("technical_indicator_probtest_param.html")

        # 5. Make sure that the range of gamma is 0.10 <= gamma <= 1.90
        if probtest_gamma < 0.10 or probtest_gamma > 1.90:
            flash("Error: Gamma must be within range [0.10, 1.90].", 'error')
            return render_template("technical_indicator_probtest_param.html")

        # 6. Make sure that the stock exists
        if not stock_available(probtest_stock, probtest_period_start_date, probtest_period_end_date):
            flash("Error: Request failed. Please check if the stock symbol and probation test period are correct.",
                  'error')
            return render_template("technical_indicator_probtest_param.html")

        se = generate_executor(probtest_stock, probtest_period_start_date, probtest_period_end_date, \
                               probtest_alpha, probtest_delta, probtest_gamma)
        stock_probtest_executors[probtest_stock] = se

        return render_template("technical_indicator_probtest.html", \
                               stock=probtest_stock, alpha=probtest_alpha, delta=probtest_delta, gamma=probtest_gamma, \
                               start_date_test=probtest_period_start_date, end_date_test=probtest_period_end_date, \
                               stock_probtest_executors=stock_probtest_executors)