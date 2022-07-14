import io
import warnings

from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def keltner_backtest_plot_service(global_param_dict):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    final_df = global_param_dict["final_df"]

    axis.plot(list(final_df.iloc[:, 0]), 'r-')
    axis.plot(list(final_df.iloc[:, 1]), 'b-')

    axis.set(xlabel="Time Series of Intraday Data",
             ylabel="Cumulative Returns",
             title=f"Portfolio Cumulative Return using Strategy vs. using Buy and Hold")

    axis.text(0.2, 0.9, 'Red - Strategy \nBlue - Buy and Hold',
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