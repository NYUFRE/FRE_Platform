from flask import render_template

from system.services.btc_algo.btc_algorithm import Filter, SMA, AlgorithmFactory
from system.services.btc_algo.btc_data import BTCData


def btc_test_service(request, algorithm):
    data = BTCData.get_btc_data()
    param_list = [algorithm, data]
    for key in request.args.keys():
        param_list.append(request.args.get(key))
    print(param_list)
    test = AlgorithmFactory.create_algorithm(*param_list)
    print(test.indicator("close"))
    print(test.signal())
    return render_template("ei_introduction.html")