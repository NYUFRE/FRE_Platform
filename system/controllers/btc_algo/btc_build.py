from datetime import date

from flask import render_template

from system.services.btc_algo.btc_algorithm import BTCAlgorithmFactory
from system.services.btc_algo.btc_data import BTCData


def btc_build_service(request, algorithm, global_param_list):
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
    # if algorithm is gate, we enter the introduction page.
    if algorithm == "gate":
        return render_template('btc_build.html', gate=True)
    # clean and get the data from the request.
    if algorithm != "Combination":
        for key in request.args.keys():
            if key == "start_date":
                start_date = request.args.get(key)
            elif key == "end_date":
                end_date = request.args.get(key)
            elif key == "price_base":
                price_base = request.args.get(key)
            else:
                param_kw[key] = request.args.get(key)
    else:
        json_dict = request.get_json()
        start_date_flag = False
        end_date_flag = False
        price_base_flag = False
        for key, value in json_dict.items():
            if key == "start_date":
                start_date = value
                start_date_flag = True
            elif key == "end_date":
                end_date = value
                end_date_flag = True
            elif key == "price_base":
                price_base = value
                price_base_flag = True
        if start_date_flag:
            del json_dict["start_date"]
        if end_date_flag:
            del json_dict["end_date"]
        if price_base_flag:
            del json_dict["price_base"]
        param_kw["json_dict"] = json_dict
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
        return render_template("btc_build.html", gate=False)
    except Exception as e:
        return render_template("btc_build.html", error=e)
