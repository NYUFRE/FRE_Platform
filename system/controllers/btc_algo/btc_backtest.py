import flask
from flask import render_template

from system.services.btc_algo.btc_backtest import BackTest


def btc_backtest_service(request: flask.request, global_param_list: dict):
    """
    Used for the backtest of the BTC algorithm.
    :param request: The request object.
    :param global_param_list: The global parameter list.
    :return: The template html.
    """
    # Get the data built data
    try:
        data = global_param_list["btc_data"]
        param_dict = {"data": data}
        for key in request.args.keys():
            param_dict[key] = request.args.get(key)
        print(param_dict)
        bt = BackTest(**param_dict)
        performance_list = bt.back_test()
    except Exception as e:
        return render_template("btc_build.html", gate="Please build the algorithm first.")
    # if signal not in the data column, return the error
    if "signal" not in data.columns:
        return render_template("btc_backtest.html", error="The signal column is not in the data.")
    # do backtest
    return render_template("btc_backtest.html", performance_list=performance_list)
