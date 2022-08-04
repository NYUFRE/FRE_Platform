import flask
from flask import render_template, flash

from system.services.btc_algo.btc_backtest import BackTest


def btc_backtest_service(request: flask.request, global_param_dict: dict):
    """
    Used for the backtest of the BTC algorithm.
    :param request: The request object.
    :param global_param_dict: The global parameter dict
    :return: The template html.
    """
    # Get the data built data
    if global_param_dict["btc_data"] is None:
        message = "Please build the algorithm first."
        flash(message)
        return render_template("btc_build.html")
    if global_param_dict["btc_data"]["first"] is True:
        global_param_dict["btc_data"]["first"] = False
        return render_template("btc_backtest.html", time="first")
    flash("The backtest will base on {} algorithm.".format(global_param_dict["btc_data"]["algorithm"]))
    data = global_param_dict["btc_data"]["signal_data"]
    param_dict = {"data": data}
    for key in request.args.keys():
        param_dict[key] = request.args.get(key)
    print(param_dict)
    bt = BackTest(**param_dict)
    performance_list = bt.back_test()
    # do backtest
    return render_template("btc_backtest.html", performance_list=performance_list)
