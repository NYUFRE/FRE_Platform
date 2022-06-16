import warnings

import numpy as np
from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.assets_pricing import assets_pricing


def ap_swap_service():
    input = {"notional_value": 1000, "frequency": 3, "contract_period": 2, "fixed_rate": 0.05,
             "start_date": str(np.datetime64('today'))}
    payer = {}
    if request.method == 'POST':
        form_input = request.form
        try:
            notional_value = float(form_input['Notional Value'])
        except:
            flash("invalid notional value input", "error")
            return render_template("ap_swap.html", payer_result=payer, input=input)
        input["notional_value"] = notional_value

        start_date = form_input['Start Date']
        input["start_date"] = start_date

        try:
            frequency = int(form_input['Frequency'])
        except:
            flash("invalid payment frequency input", "error")
            return render_template("ap_swap.html", payer_result=payer, input=input)
        input["frequency"] = frequency

        try:
            contract_period = int(form_input['Contract Period'])
        except:
            flash("invalid contract period input", "error")
            return render_template("ap_swap.html", payer_result=payer, input=input)
        input["contract_period"] = contract_period

        try:
            fixed_rate = float(form_input['Fixed Rate'])
        except:
            flash("invalid fixed rate input", "error")
            return render_template("ap_swap.html", payer_result=payer, input=input)
        input["fixed_rate"] = fixed_rate

        if contract_period > 60:
            flash("Invalid contract period, maximum contract period is 60", "error")
            return render_template("ap_swap.html", payer_result=payer, input=input)
        if frequency > contract_period:
            flash("Invalid input, payment frequency must less than contract period")
            return render_template("ap_swap.html", payer_result=payer, input=input)
        payer, swap_history = assets_pricing.pricing_swap(notional_value, start_date, frequency, contract_period,
                                                          fixed_rate)
        return render_template("ap_swap.html", payer_result=payer, input=input,
                               tables=[swap_history.to_html(classes='data')], titles=swap_history.columns.values)
    else:
        return render_template("ap_swap.html", payer_result=payer, input=input)