import json
import os
import urllib.request
import warnings

import numpy as np
from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

from system.services.assets_pricing.assets_pricing import asset_pricing_result

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.assets_pricing import assets_pricing



def ap_american_pricing_service():
    url_common = "https://cloud.iexapis.com/stable/stock/"
    url = url_common + "AAPL" + "/quote?token=" + os.environ.get("IEX_API_KEY")
    with urllib.request.urlopen(url) as req:
        data = json.load(req)
    a = float(data["latestPrice"])
    strk = round(float(a - 25), 2)
    input = {"spot": a, "strike": strk, "day": 90, "rf": 0.02, "div": 0, "vol": 0.3}
    call = {}
    put = {}
    yparameter_lst = ["Value", "Delta", "Gamma", "Theta"]
    xparameter_lst = ["Strike", "Spot", "Days_to_Maturity", "Risk_Free_Rate", "Dividend", "Volatility"]
    if request.method == "POST":
        spot_input = request.form.get('spot')
        try:
            spot = float(spot_input)
        except:
            flash("invalid spot value input", "error")
            return render_template("ap_american_pricing.html", call_dict=call, put_dict=put, y_parameter=yparameter_lst,
                                   x_parameter=xparameter_lst, input=input)
        input["spot"] = spot_input

        strike_input = request.form.get('strike')
        try:
            strike = float(strike_input)
        except:
            flash("invalid strike input", "error")
            return render_template("ap_american_pricing.html", call_dict=call, put_dict=put, y_parameter=yparameter_lst,
                                   x_parameter=xparameter_lst, input=input)
        input["strike"] = strike_input

        day_input = request.form.get('day')
        try:
            day = int(day_input)
        except:
            flash("invalid day to expiration input", "error")
            return render_template("ap_american_pricing.html", call_dict=call, put_dict=put, y_parameter=yparameter_lst,
                                   x_parameter=xparameter_lst, input=input)
        input["day"] = day_input

        rf_input = request.form.get('rf')
        try:
            rf = float(rf_input)
        except:
            flash("invalid risk free rate input", "error")
            return render_template("ap_american_pricing.html", call_dict=call, put_dict=put, y_parameter=yparameter_lst,
                                   x_parameter=xparameter_lst, input=input)
        input["rf"] = rf_input

        div_input = request.form.get('div')
        try:
            div = float(div_input)
        except:
            flash("Invalid dividend rate input", "error")
            return render_template("ap_american_pricing.html", call_dict=call, put_dict=put, y_parameter=yparameter_lst,
                                   x_parameter=xparameter_lst, input=input)
        input["div"] = div_input

        vol_input = request.form.get('vol')
        try:
            vol = float(vol_input)
        except:
            flash("Invalid implied volatility input", "error")
            return render_template("ap_american_pricing.html", call_dict=call, put_dict=put, y_parameter=yparameter_lst,
                                   x_parameter=xparameter_lst, input=input)
        input["vol"] = vol_input

        call, put = assets_pricing.pricing_american(spot, strike, day, rf, div, vol)
        xparameter = request.form.get("xparameter")
        if xparameter == "Strike":
            step = np.linspace(-int(0.8 * strike), int(0.8 * strike), 300)
            x_lst = strike + step
            call_lst = []
            put_lst = []
            for strike in x_lst:
                call_at_value, put_at_value = assets_pricing.pricing_american(spot, strike, day, rf, div, vol)
                call_lst.append(call_at_value[request.form.get("yparameter")])
                put_lst.append(put_at_value[request.form.get("yparameter")])
        elif xparameter == "Spot":
            # x_lst = [x for x in range (1, 350, 1)]
            step = np.linspace(-int(0.8 * spot), int(0.8 * spot), 300)
            x_lst = spot + step
            call_lst = []
            put_lst = []
            for spot in x_lst:
                call_at_value, put_at_value = assets_pricing.pricing_american(spot, strike, day, rf, div, vol)
                call_lst.append(call_at_value[request.form.get("yparameter")])
                put_lst.append(put_at_value[request.form.get("yparameter")])
        elif xparameter == "Days_to_Maturity":
            x_lst = [x for x in range(1, 3 * 365, 5)]
            call_lst = []
            put_lst = []
            for day in x_lst:
                call_at_value, put_at_value = assets_pricing.pricing_american(spot, strike, day, rf, div, vol)
                call_lst.append(call_at_value[request.form.get("yparameter")])
                put_lst.append(put_at_value[request.form.get("yparameter")])
        elif xparameter == "Risk_Free_Rate":
            x_lst = [x / 100 for x in range(0, 25, 1)]
            call_lst = []
            put_lst = []
            for rf in x_lst:
                call_at_value, put_at_value = assets_pricing.pricing_american(spot, strike, day, rf, div, vol)
                call_lst.append(call_at_value[request.form.get("yparameter")])
                put_lst.append(put_at_value[request.form.get("yparameter")])
        elif xparameter == "Dividend":
            x_lst = [x / 100 for x in range(0, 25, 1)]
            call_lst = []
            put_lst = []
            for div in x_lst:
                call_at_value, put_at_value = assets_pricing.pricing_american(spot, strike, day, rf, div, vol)
                call_lst.append(call_at_value[request.form.get("yparameter")])
                put_lst.append(put_at_value[request.form.get("yparameter")])
        elif xparameter == "Volatility":
            x_lst = [x / 100 for x in range(0, 50, 2)]
            call_lst = []
            put_lst = []
            for vol in x_lst:
                call_at_value, put_at_value = assets_pricing.pricing_american(spot, strike, day, rf, div, vol)
                call_lst.append(call_at_value[request.form.get("yparameter")])
                put_lst.append(put_at_value[request.form.get("yparameter")])
        asset_pricing_result.xvalue = x_lst
        asset_pricing_result.call = call_lst
        asset_pricing_result.put = put_lst
        asset_pricing_result.yparameter = request.form.get("yparameter")
        asset_pricing_result.xparameter = request.form.get("xparameter")
        return render_template("ap_american_pricing.html", call_dict=call, put_dict=put, y_parameter=yparameter_lst,
                               x_parameter=xparameter_lst, input=input)
    else:
        return render_template("ap_american_pricing.html", call_dict=call, put_dict=put, y_parameter=yparameter_lst,
                               x_parameter=xparameter_lst, input=input)