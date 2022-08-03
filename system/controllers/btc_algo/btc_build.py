from datetime import date

import flask
from flask import render_template, redirect, flash

from system.services.btc_algo.btc_algorithm import BTCAlgorithmFactory
from system.services.btc_algo.btc_data import BTCData


def btc_build_service(request: flask.request, algorithm: str, global_param_list: dict):
    """
    Builds the service for the BTC algorithm.
    :param request: The request object.
    :param algorithm: The algorithm to use.
    :param global_param_list: The global parameter list.
    :return: The template html.
    """
    # Get the data from the request.
    start_date = "2020-01-01"
    end_date = date.today().strftime("%Y-%m-%d")
    price_base = None
    param_kw = {"algorithm": algorithm}
    print(algorithm)
    # if algorithm is none, we enter the introduction page.
    if algorithm == "gate":
        return render_template('btc_build.html')
    # clean and get the data from the request.
    else:
        for key in request.args.keys():
            if key == "start_date":
                start_date = request.args.get(key)
            elif key == "end_date":
                end_date = request.args.get(key)
            elif key == "price_base":
                price_base = request.args.get(key)
            elif key == "method_list":
                param_kw["method_list"] = request.args.getlist(key)
            else:
                param_kw[key] = request.args.get(key)
    # get data
    data = BTCData.get_btc_data_range(start_date, end_date)
    # build parameters
    param_kw["data"] = data
    # build the algorithm, do the service
    try:
        algo = BTCAlgorithmFactory.create_algorithm(**param_kw)
        indi_data = algo.indicator(price_base)
        signal_data = algo.signal()
        global_param_list["btc_data"] = signal_data
        print(signal_data)
        message = "The algorithm: {} has been built successfully.".format(algorithm)
        flash(message)
        return redirect("/btc_backtest")
    except Exception as e:
        return render_template("btc_build.html", error=e)
