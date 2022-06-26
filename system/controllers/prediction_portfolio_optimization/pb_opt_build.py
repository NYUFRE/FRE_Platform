import warnings

from dateutil.relativedelta import relativedelta
from flask import flash, render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.predict_based_optimization.pre_port_opt import get_optimized_portfolio


def pb_opt_build_service(end_date, global_param_list):
    try:
        start_date = end_date + relativedelta(years=-10)
        pb_portfolio, port_list = get_optimized_portfolio(start_date, end_date)

        global_param_list[2] = pb_portfolio

        length = len(port_list)

        return render_template('PB_Opt_build.html', length=length, portfolio=port_list)

    except ValueError:
        flash('Error! There is something wrong about the database, please see the command for error!')
        return render_template("Predict_based_optmize.html")