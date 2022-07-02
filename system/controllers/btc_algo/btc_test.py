from datetime import date

from flask import render_template

from system.services.btc_algo.btc_algorithm import Filter, SMA, BTCAlgorithmFactory
from system.services.btc_algo.btc_data import BTCData


def btc_test_service(request, algorithm):
    all_data = BTCData.get_btc_data_all()
    print(all_data)
    data = BTCData.get_btc_data_range("2020-01-01", date.today().strftime("%Y-%m-%d"))
    param_kw = {"algorithm": algorithm, "data": data}
    if algorithm != "Combination":
        for key in request.args.keys():
            param_kw[key] = request.args.get(key)
    else:
        param_kw["json_dict"] = request.get_json()
    print(param_kw)
    test = BTCAlgorithmFactory.create_algorithm(**param_kw)
    print(test.indicator("close"))
    return render_template("btc_introduction.html")