import io
import warnings

from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning
import numpy as np

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.twitter_sentiment_analysis.tsa_service import tsa_res

def tsa_plot_demo_service():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    if tsa_res.demo_deg is not None:
        x = np.arange(11)
        y = 2.5 * np.sin(tsa_res.demo_deg * x / 10 * np.pi) 
    else:
        x = []
        y = []
        
    axis.plot(x, y, label=f"degree = {tsa_res.demo_deg}")
    axis.set(xlabel='XX', ylabel='Y', title="demo" )
    axis.legend()
    axis.grid(True)

    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response