
import io
import warnings

from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import SAWarning
import numpy as np
import pandas as pd
from sklearn import svm, metrics
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import scale
warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.twitter_sentiment_analysis.tsa_service import tsa_res


def tsa_plot_roc_service():
    fig = Figure(figsize = (10,10))

    axis = fig.add_subplot(1, 1, 1)

    if tsa_res.isBuilt:
        y_test_pred = tsa_res.clf.classifier.predict_proba(tsa_res.clf.X_test)
        # print("y_test_pred[:,0]",y_test_pred[:,0])
        fpr, tpr, thresholds = metrics.roc_curve(tsa_res.clf.y_test, y_test_pred[:,0], pos_label=1)
        auc = metrics.roc_auc_score(tsa_res.clf.y_test, y_test_pred[:,0])
    else:
        auc = None
        fpr = []
        tpr = []
    # print(fpr)
    axis.set_facecolor('xkcd:light grey')
    axis.plot(fpr, tpr, label=f"AUC : {auc}", c='black')
    axis.set(xlabel='FP rate', ylabel='TR rate', title=f"ROC Curve, Model : {tsa_res.clf.model}" )
    axis.legend()
    axis.grid(True)

    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response



def tsa_plot_lab_service():
    fig = Figure(figsize = (20,30))

    axis1 = fig.add_subplot(3, 1, 3)
    axis2 = fig.add_subplot(3, 1, 2)
    axis3 = fig.add_subplot(3, 1, 1)

    y1 = []
    y2 = []
    x = []
    y1name = 'None'
    y2name = 'None'
    # instantiate the values
    if tsa_res.isPlot:
        y1 = tsa_res.labplotX[0]
        y2 = tsa_res.labplotX[1]
        x = pd.to_datetime(tsa_res.data['Date'])
        y1name = tsa_res.labplotXname[0]
        y2name = tsa_res.labplotXname[1]
    # ploting
    axis3.set_facecolor('xkcd:light grey')
    if tsa_res.isPlot:
        axis3.plot(x, scale(y1), label=f"Curve : {y1name}", c='b')
        axis3.plot(x, scale(y2), label=f"Curve : {y2name}", c='r')
    else:
        axis3.plot(x, y1, label=f"Curve : {y1name}", c='b')
        axis3.plot(x, y2, label=f"Curve : {y2name}", c='r')
    axis3.set(xlabel='Date', ylabel='Value', title=f"Combined : {y2name}" )
    axis3.legend()
    axis3.grid(True)

    axis1.plot(x, y1, label=f"Curve : {y1name}", c='b')
    axis1.set(xlabel='Date', ylabel='Value', title=f"Curve : {y1name}" )
    axis1.legend()
    axis1.grid(True)

    axis2.plot(x, y2, label=f"Curve : {y2name}", c='r')
    axis2.set(xlabel='Date', ylabel='Value', title=f"Curve : {y2name}" )
    axis2.legend()
    axis2.grid(True)
    
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response
