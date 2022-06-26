import warnings

import numpy as np
from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.assets_pricing import assets_pricing


def ap_CDS_service():
    frequency_list = ["Monthly", "Quarterly", "Twice a year", "Annually"]
    input = {"notional": 1000, "spread": 0.02, "recovery_rate": 0.6, "hazard_rate": 0, "discount_rate": 0.04,
             "issue_date": str(np.datetime64('today')), "maturity_date": str(np.datetime64('today')), "frequency": ""}
    buyer = {}
    seller = {}
    if request.method == 'POST':
        form_input = request.form
        try:
            notional_value = float(form_input['Notional'])
        except:
            flash("invalid notional value input", "error")
            return render_template("ap_CDS.html", frequency_list=frequency_list, buyer_result=buyer,
                                   seller_result=seller, input=input)
        input["notional"] = notional_value

        try:
            spread = float(form_input['Spread'])
        except:
            flash("invalid spread value input", "error")
            return render_template("ap_CDS.html", frequency_list=frequency_list, buyer_result=buyer,
                                   seller_result=seller, input=input)
        input["spread"] = spread

        try:
            recovery_rate = float(form_input['Recovery Rate'])
        except:
            flash("invalid recovery rate input", "error")
            return render_template("ap_CDS.html", frequency_list=frequency_list, buyer_result=buyer,
                                   seller_result=seller, input=input)
        input["recovery_rate"] = recovery_rate

        try:
            hazard_rate = float(form_input['Hazard Rate'])
        except:
            flash("invalid hazard rate input", "error")
            return render_template("ap_CDS.html", frequency_list=frequency_list, buyer_result=buyer,
                                   seller_result=seller, input=input)
        input["hazard_rate"] = hazard_rate

        try:
            discount_rate = float(form_input['Discount Rate'])
        except:
            flash("invalid discount rate input", "error")
            return render_template("ap_CDS.html", frequency_list=frequency_list, buyer_result=buyer,
                                   seller_result=seller, input=input)
        input["discount_rate"] = discount_rate

        issue_date = form_input['Issue Date']
        input["issue_date"] = issue_date
        maturity_date = form_input['Maturity Date']
        input["maturity_date"] = maturity_date
        frequency_forminput = form_input['Frequency']
        input["frequency"] = frequency_forminput

        frequency_dict = {"Monthly": "1m",
                          "Quarterly": "3m",
                          "Twice a year": "6m",
                          "Annually": "1Y"}
        frequency = frequency_dict.get(frequency_forminput)
        buyer, seller = assets_pricing.pricing_cds(notional_value, spread,
                                                   issue_date,
                                                   maturity_date,
                                                   frequency,
                                                   discount_rate,
                                                   recovery_rate,
                                                   hazard_rate)

        return render_template("ap_CDS.html", frequency_list=frequency_list, buyer_result=buyer, seller_result=seller,
                               input=input)
    else:
        return render_template("ap_CDS.html", frequency_list=frequency_list, buyer_result=buyer, seller_result=seller,
                               input=input)