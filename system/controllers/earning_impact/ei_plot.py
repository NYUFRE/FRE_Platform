import io
import warnings

from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

from system.services.earnings_impact.earnings_impact import earnings_impact_data

warnings.simplefilter(action='ignore', category=SAWarning)


def ei_plot_service():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.plot(earnings_impact_data.Beat, label='Beat')
    axis.plot(earnings_impact_data.Meet, label='Meet')
    axis.plot(earnings_impact_data.Miss, label='Miss')
    axis.legend(loc='best')
    axis.axvline(x=30, linewidth=1.0)

    axis.grid(True)
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response