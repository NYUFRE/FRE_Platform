import io
import warnings

from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.assets_pricing import assets_pricing


def european_plot_service():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    x_lst = assets_pricing.asset_pricing_result.xvalue
    call_lst = assets_pricing.asset_pricing_result.call
    put_lst = assets_pricing.asset_pricing_result.put
    axis.plot(x_lst, call_lst, label="Call Option")
    axis.plot(x_lst, put_lst, label="Put Option")
    axis.set(xlabel=assets_pricing.asset_pricing_result.xparameter,
             ylabel=assets_pricing.asset_pricing_result.yparameter,
             title=f"European Option {assets_pricing.asset_pricing_result.yparameter} VS {assets_pricing.asset_pricing_result.xparameter}")
    axis.legend()

    axis.grid(True)
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response