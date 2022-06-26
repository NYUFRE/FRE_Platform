import warnings

from flask import render_template, request
from sqlalchemy.exc import SAWarning

from system.services.assets_pricing.assets_pricing import asset_pricing_result

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.assets_pricing import assets_pricing


def ap_yield_curve_service():
    benchmark_lst = ["Libor", "US Treasury"]

    if request.method == "POST":
        benchmark_input = request.form.get('benchmark')

        yield_curve, discount_curve = assets_pricing.build_yield_curve(benchmark_input)
        asset_pricing_result.yield_curve = yield_curve
        asset_pricing_result.discount_curve = discount_curve
        asset_pricing_result.curve_benchmark = benchmark_input
        return render_template("ap_yield_curve.html", benchmark_lst=benchmark_lst)
    else:
        return render_template("ap_yield_curve.html", benchmark_lst=benchmark_lst)