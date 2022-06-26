import io
import warnings

from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

from system.services.assets_pricing.assets_pricing import asset_pricing_result

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.assets_pricing import assets_pricing


def discount_plot_service():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    discount_curve = assets_pricing.asset_pricing_result.discount_curve
    date_lst = []
    rate_lst = []
    if discount_curve is not None:
        for dt, rate in discount_curve.nodes():
            date_lst.append(dt.to_date())
            rate_lst.append(rate)
    axis.plot(date_lst, rate_lst, marker='o')
    axis.set(title=asset_pricing_result.curve_benchmark + " Discount Curve")
    axis.legend()

    axis.grid(True)
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response