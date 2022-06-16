import io
import warnings

from flask import make_response, send_file
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.alpha_test.alpha_test import alphatestdata

import base64


def at2_plot_service():
    table = alphatestdata.table
    table_agg = alphatestdata.table_agg
    # Create a empty figure when there is missing data
    if len(table) == 0 or len(table_agg) == 0:
        gif = 'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
        gif_str = base64.b64decode(gif)
        return send_file(io.BytesIO(gif_str), mimetype='image/gif')

    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.bar(table_agg['year'][:-1], table_agg['ic'][:-1])

    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response