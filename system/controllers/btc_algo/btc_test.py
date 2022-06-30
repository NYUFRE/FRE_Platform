from flask import render_template

from system.services.btc_algo.btc_algorithm import Filter, SMA, AlgorithmFactory
from system.services.btc_algo.btc_data import BTCData


def btc_test_service():
    data = BTCData.get_btc_data()
    param_list = ["Filter", data, 0.5]
    test = AlgorithmFactory.create_algorithm(*param_list)
    print(test.indicator("open"))
    print(test.signal("mean reversion"))
    return render_template("ei_introduction.html")