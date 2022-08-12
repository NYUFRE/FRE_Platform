from tkinter import N
import warnings

from flask import render_template, request, flash
from sqlalchemy.exc import SAWarning
from system.services.twitter_sentiment_analysis.tsa_service import tsa_res
from scipy.stats import pearsonr, spearmanr
import pandas as pd
import numpy as np
warnings.simplefilter(action='ignore', category=SAWarning)


pdlist_curve1 = ['MSFT_Adj_Close', 'pos/neg', 'neg/pos', 'EMA(pos/neg)', 'EMA(neg/pos)', 'Likes', 'pos', 'neg', 'compound', 'RetweetCount', 'QuoteCount']
pdlist_curve2 = ['MSFT_Adj_Close', 'pos/neg', 'neg/pos', 'EMA(pos/neg)', 'EMA(neg/pos)', 'Likes', 'pos', 'neg', 'compound', 'RetweetCount', 'QuoteCount']
special_curves = ['MSFT_Adj_Close','pos/neg', 'neg/pos', 'EMA(pos/neg)', 'EMA(neg/pos)']


def helper_getX(Xname):
    if Xname not in special_curves:
        return tsa_res.data[Xname]
    else:
        if Xname == 'MSFT_Adj_Close':
            return tsa_res.data['Adj_close']
        elif Xname == 'pos/neg':
            return (tsa_res.data['pos'] + 1)/(tsa_res.data['neg'] + 1)
        elif Xname == 'neg/pos':
            return (tsa_res.data['neg'] + 1)/(tsa_res.data['pos'] + 1)
        elif Xname == 'EMA(pos/neg)':
            x = (tsa_res.data['pos'] + 1)/(tsa_res.data['neg'] + 1).ewm(span=10, adjust=False).mean()
            x[0:10] = None
            return x
        elif Xname == 'EMA(neg/pos)':
            x = (tsa_res.data['neg'] + 1)/(tsa_res.data['pos'] + 1).ewm(span=10, adjust=False).mean()
            x[0:10] = None
            return x
        else:
            return []


def tsa_viewer_service():

    coeff_pr_pval = None, 
    coeff_pr_corr = None, 

    coeff_sp_pval = None,
    coeff_sp_corr = None, 

    X1 = []
    X2 = []
    curve1_name = 'MSFT_Adj_Close'
    curve2_name = 'EMA(pos/neg)'
    if request.method == "POST" and tsa_res.isBuilt:
        spot_input = request.form.get('spot')
        curve1_name = str(request.form.get('curve1'))
        curve2_name = str(request.form.get('curve2'))
        # get data for curve1:X1 and curve2:X2
        X1 = helper_getX(curve1_name)
        X2 = helper_getX(curve2_name)
        # calc for corr
        XX = pd.concat([pd.DataFrame(X1), pd.DataFrame(X2)], join='inner', axis=1)
        XX.dropna(inplace=True)
        XX.columns = ['x1','x2']
        coeff_pr = pearsonr(XX['x1'], XX['x2'])
        coeff_pr_corr = np.round(coeff_pr[0], 4)
        coeff_pr_pval = np.round(coeff_pr[1], 4)
        coeff_sp = spearmanr(XX['x1'], XX['x2'])
        coeff_sp_corr = np.round(coeff_sp[0], 4)
        coeff_sp_pval = np.round(coeff_sp[1], 4)
        # Pass X1 and X2 into plot service
        tsa_res.labplotX = [X1, X2]
        tsa_res.labplotXname = [curve1_name, curve2_name]
        tsa_res.isPlot = True
        return render_template(
            "tsa_viewer.html", 
            curve1_name = curve1_name,
            curve2_name = curve2_name,
            coeff_pr_pval = coeff_pr_pval, 
            coeff_pr_corr = coeff_pr_corr, 

            coeff_sp_pval = coeff_sp_pval,
            coeff_sp_corr = coeff_sp_corr, 

            pdlist_curve1 = pdlist_curve1, 
            pdlist_curve2 = pdlist_curve2
        )
    else:
        return render_template(
            "tsa_viewer.html", 
            curve1_name = curve1_name,
            curve2_name = curve2_name,
            coeff_pr_pval = coeff_pr_pval, 
            coeff_pr_corr = coeff_pr_corr, 

            coeff_sp_pval = coeff_sp_pval,
            coeff_sp_corr = coeff_sp_corr, 

            pdlist_curve1 = pdlist_curve1, 
            pdlist_curve2 = pdlist_curve2
        )
