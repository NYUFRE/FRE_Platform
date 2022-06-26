import datetime as dt
import warnings
from datetime import datetime

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

from system.controllers.prediction_portfolio_optimization.pb_opt_build import pb_opt_build_service

warnings.simplefilter(action='ignore', category=SAWarning)


def pb_opt_date_choose_service(global_param_list):
    if request.method == "POST":
        data_end = request.form['end_date']
        try:
            data_end_date = datetime.strptime(data_end, '%Y-%m-%d').date()
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
            return render_template('PB_Opt_date_choose.html', end_date=dt.date(2020, 1, 1).strftime('%Y-%m-%d'))
        # Make sure that the ending date would be earlier than backtest starting date
        if data_end_date > dt.date.today() + dt.timedelta(-90):
            flash(
                "Error: The end date should earlier than the start date of back-test period, which is three months before today.",
                'error')
            return render_template('PB_Opt_date_choose.html', end_date=data_end_date.strftime('%Y-%m-%d'))

        return pb_opt_build_service(data_end_date, global_param_list)

    else:
        return render_template("PB_Opt_date_choose.html", end_date=dt.date(2020, 1, 1).strftime('%Y-%m-%d'))