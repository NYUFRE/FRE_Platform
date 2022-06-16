import io
import warnings

from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def pb_opt_backtest_plot_service(global_param_list):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    df_pb_opt = global_param_list[3]

    axis.plot(list(df_pb_opt.iloc[:, 0]), 'r-')
    axis.plot(list(df_pb_opt.iloc[:, 1]), 'b-')

    axis.set(xlabel="Number of Trading Days",
             ylabel="Cumulative Returns")

    axis.text(0.2, 0.9, 'Red - Portfolio \nBlue - SPY',
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