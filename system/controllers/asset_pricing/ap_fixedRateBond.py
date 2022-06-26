import warnings

import numpy as np
from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.assets_pricing import assets_pricing


def ap_fixedRateBond_service():
    frequency_list = ["Monthly", "Quarterly", "Twice a year", "Annually"]
    input = {"face_value": 1000, "coupon_rate": 0.06, "discount_rate": 0.04,
             "valuation_date": str(np.datetime64('today')), "issue_date": str(np.datetime64('today')),
             "maturity_date": str(np.datetime64('today')), "frequency": ""}
    bond = {}
    if request.method == 'POST':
        form_input = request.form
        try:
            face_value = float(form_input['Face Value'])
        except:
            flash("invalid face value input", "error")
            return render_template("ap_fixedRateBond.html", frequency_list=frequency_list, bond_result=bond,
                                   input=input)

        input["face_value"] = face_value
        try:
            coupon_rate = float(form_input['Coupon Rate'])
        except:
            flash("invalid coupon rate input", "error")
            return render_template("ap_fixedRateBond.html", frequency_list=frequency_list, bond_result=bond,
                                   input=input)
        input["coupon_rate"] = coupon_rate

        try:
            discount_rate = float(form_input['Discount Rate'])
        except:
            flash("invalid discount rate input", "error")
            return render_template("ap_fixedRateBond.html", frequency_list=frequency_list, bond_result=bond,
                                   input=input)
        input["discount_rate"] = discount_rate

        valuation_date = form_input['Valuation Date']
        input["valuation_date"] = valuation_date
        issue_date = form_input['Issue Date']
        input["issue_date"] = issue_date
        maturity_date = form_input['Maturity Date']
        input["maturity_date"] = maturity_date
        frequency_forminput = form_input['Frequency']
        input["frequency"] = frequency_forminput

        print(input["valuation_date"])
        print(type(input["valuation_date"]))
        frequency_dict = {"Monthly": "1m",
                          "Quarterly": "3m",
                          "Twice a year": "6m",
                          "Annually": "1Y"}
        frequency = frequency_dict.get(frequency_forminput)
        bond = assets_pricing.pricing_fixedratebond(face_value, valuation_date, issue_date, maturity_date, frequency,
                                                    coupon_rate, discount_rate)

        return render_template("ap_fixedRateBond.html", frequency_list=frequency_list, bond_result=bond, input=input)
    else:
        return render_template("ap_fixedRateBond.html", frequency_list=frequency_list, bond_result=bond, input=input)
