import io
import warnings

from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

from system.services.hf_trading.hf_trading import hf_trading_data

warnings.simplefilter(action='ignore', category=SAWarning)


def hf_id_plot_service(plot_id):
    plot_df = hf_trading_data.data_list[int(plot_id)]

    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.grid(linestyle='-.')
    axis.plot(plot_df)
    axis.set_xlabel("seconds")
    axis.set_ylabel("cumulative return")

    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response