import warnings

from flask import flash, render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.predict_based_optimization.pre_port_opt import opt_backtest


def pb_opt_backtest_service(global_param_list):
    pb_portfolio = global_param_list[2]
    if len(pb_portfolio) == 0:
        flash('Please click "Choose End Date" to select stocks before run the back test!')
        return render_template("Predict_based_optmize.html")
    else:
        df_pb_opt, new_portfolio, remove_list = opt_backtest(pb_portfolio)
        length = len(new_portfolio)
        remove_len = len(remove_list)
        global_param_list[3] = df_pb_opt
        return render_template('PB_Opt_backtest.html', length=length, portfolio=new_portfolio, rmlen=remove_len,
                               removed=remove_list)