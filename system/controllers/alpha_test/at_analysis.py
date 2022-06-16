import warnings

import pandas as pd
from flask import render_template, request
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database

from system.services.alpha_test.alpha_test import TALIB, Test, alphatestdata

from talib import abstract


def at_analysis_service():
    input = {"AlphaName": 'NotSelected', "Timeperiod": 5}
    AlphaName_list = ['EMA', 'RSI', 'T3', 'TRIMA', 'CMO', 'ROCP', 'ROC', 'LINEARREG_ANGLE', 'VAR']
    table_year_data = []
    # fetch 500 stocks price volumn data
    select_stmt = 'SELECT symbol, date, adjusted_close FROM stocks'
    spy500 = database.execute_sql_statement(select_stmt)
    close = pd.pivot_table(spy500, index=['date'], columns=['symbol'])['adjusted_close']
    close = close.fillna(method='ffill')
    returns = (close / close.shift(1) - 1).fillna(0)
    target = returns.shift(-1).fillna(0)

    if request.method == "POST":
        AlphaName = request.form.get('AlphaName')
        AlphaName = str(AlphaName)
        Timeperiod = request.form.get('Timeperiod')
        Timeperiod = int(Timeperiod)
        input['AlphaName'] = AlphaName
        input['Timeperiod'] = Timeperiod
        alpha = TALIB(close, abstract.Function(AlphaName), Timeperiod)
        alpha = pd.DataFrame(alpha, index=close.index, columns=close.columns).fillna(0)

        alpha_table, alpha_table_agg = Test(alpha, target)
        alphatestdata.table = alpha_table
        alphatestdata.table_agg = alpha_table_agg
        alpha_table_agg.reset_index(inplace=True)
        for i in range(len(alpha_table_agg)):
            temp = alpha_table_agg.iloc[i, :].copy()
            temp[1:] = temp[1:].apply(lambda x: '%.4f' % float(x))
            table_year_data.append(temp)

        return render_template("at_analysis.html", input=input, AlphaName_list=AlphaName_list,
                               table_year_data=table_year_data)
    else:
        return render_template("at_analysis.html", input=input, AlphaName_list=AlphaName_list,
                               table_year_data=table_year_data)