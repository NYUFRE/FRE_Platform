from flask import render_template

from system.services.btc_algo.btc_algorithm import Filter, SMA, BTCAlgorithmFactory
from system.services.btc_algo.btc_data import BTCData


def btc_test_service(request, algorithm):
    data = BTCData.get_btc_data()
    param_list = [algorithm, data]
    if algorithm != "Combination":
        for key in request.args.keys():
            param_list.append(request.args.get(key))
    else:
        param_list.append(request.get_json())
    test = BTCAlgorithmFactory.create_algorithm(*param_list)
    print(test.indicator("close"))
    print(test.signal())
    return render_template("ei_introduction.html")