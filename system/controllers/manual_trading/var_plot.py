import io
import warnings

from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.VaR.VaR_Calculator import var_data


def var_plot_service():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    axis.plot(var_data.date, var_data.port_returns, label='Portfolio Return')
    axis.plot(var_data.date, var_data.VaR, label='VaR')

    axis.legend(loc='best')
    axis.grid(True)
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response