import warnings

import numpy as np
from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.assets_pricing import assets_pricing


def ap_fra_service():
    input = {"notional_value": 1000, "month_to_start": 3, "month_to_termination": 6, "fra_quote": 0,
             "valuation_date": str(np.datetime64('today'))}
    buyer = {}
    if request.method == 'POST':
        form_input = request.form
        try:
            notional_value = float(form_input['Notional Value'])
        except:
            flash("Invalid notional value input", "error")
            return render_template("ap_fra.html", buyer_result=buyer, input=input)
        input["notional_value"] = notional_value

        valuation_date = form_input['Valuation Date']
        input["valuation_date"] = valuation_date

        try:
            month_to_start = float(form_input['Month To Start'])
        except:
            flash("Invalid month to start input", "error")
            return render_template("ap_fra.html", buyer_result=buyer, input=input)
        input["month_to_start"] = month_to_start

        try:
            month_to_termination = float(form_input['Month To Termination'])
        except:
            flash("Invalid month to termination input", "error")
            return render_template("ap_fra.html", buyer_result=buyer, input=input)
        input["month_to_termination"] = month_to_termination

        try:
            fra_quote = float(form_input['FRA Quote'])
        except:
            flash("Invalid FRA quote input", "error")
            return render_template("ap_fra.html", buyer_result=buyer, input=input)
        input["fra_quote"] = fra_quote

        buyer = assets_pricing.pricing_fra(notional_value, valuation_date, month_to_start, month_to_termination,
                                           fra_quote)
        return render_template("ap_fra.html", buyer_result=buyer, input=input)
    else:
        return render_template("ap_fra.html", buyer_result=buyer, input=input)