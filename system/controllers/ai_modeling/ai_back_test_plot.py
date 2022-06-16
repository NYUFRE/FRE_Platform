import io
import warnings

import numpy as np
from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.ai_modeling.ga_portfolio_back_test import ga_back_test_result


def ai_back_test_plot_service():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    n = len(ga_back_test_result.portfolio_cum_rtn)
    line = np.zeros(n)
    axis.plot(ga_back_test_result.portfolio_cum_rtn, 'ro')
    axis.plot(ga_back_test_result.spy_cum_rtn, 'bd')
    axis.plot(ga_back_test_result.portfolio_cum_rtn.index, line, 'b')

    axis.set(xlabel="Date",
             ylabel="Cumulative Returns",
             title=f"Portfolio Back Test ({ga_back_test_result.bt_start_date} to {ga_back_test_result.bt_end_date})")

    axis.text(0.2, 0.9, 'Red - Portfolio, Blue - SPY',
              verticalalignment='center',
              horizontalalignment='center',
              transform=axis.transAxes,
              color='black', fontsize=10)

    axis.grid(True)
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response