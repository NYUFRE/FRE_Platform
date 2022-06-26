import io
import warnings

import matplotlib.pyplot as plt
from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning

from system.services.mep_strategy.mep import stock_probtest_executors, stock_backtest_executors

warnings.simplefilter(action='ignore', category=SAWarning)
from system.services.VaR.VaR_Calculator import var_data


def technical_indicator_plot_service(test, ticker_strings):
    plt.rcParams['figure.figsize'] = (16, 8)
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    if test == 'backtest':
        tickers = ticker_strings.split('+')
        for ticker in tickers:
            axis.plot(stock_backtest_executors[ticker].df.index, stock_backtest_executors[ticker].E_hist)
        axis.set_title(f"{ticker_strings} E history")
        axis.legend(tickers)
    elif test == 'probtest':
        ticker = ticker_strings
        axis.plot(stock_probtest_executors[ticker].df.index, stock_probtest_executors[ticker].E_hist)
        axis.set_title(f"{ticker} E history")
    else:
        return None

    fig.autofmt_xdate()

    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

    # line = np.zeros(len(port_var))
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