import io
import warnings

import numpy as np
from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.model_optimization.opt_back_test import get_results, get_dates


def opt_back_test_plot3_service():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    results = get_results()
    start_date_back, end_date_back = get_dates()
    portfolio_ret = results[0]
    spy_ret = results[1]
    n = len(spy_ret)
    line = np.zeros(n)
    axis.plot(portfolio_ret["cum_ret_max_const"], 'ro')
    axis.plot(spy_ret["cum_daily_return"], 'bd')
    axis.plot(portfolio_ret.index, line, 'b')

    axis.set(xlabel="Date",
             ylabel="Cumulative Returns",
             title=f"Portfolio Back Test ({start_date_back} to {end_date_back})")

    axis.text(0.2, 0.9, 'Red - Max Sharpe Constraint, Blue - SPY',
              verticalalignment='center',
              horizontalalignment='center',
              transform=axis.transAxes,
              color='black', fontsize=10)

    # Shan add 3
    axis.grid(True)
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response