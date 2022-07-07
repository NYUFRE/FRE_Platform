import warnings

import pandas as pd
from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.keltner_strategy.keltner import kelt_cha_sty


def keltner_build_model_service(global_param_list):
    # all the 79 in this part is because for the intraday data, there are 79 data a day
    # make it a global variable for plotting use
    stock_table, length, strategy, buynhold = kelt_cha_sty()
    # join the two dataframe by date and drop the missing value
    final_df = pd.concat([strategy, buynhold], axis=1)
    final_df.dropna(axis=0, how='any', inplace=True)
    global_param_list["final_df"] = final_df
    # pick out the start and end time of prediction
    date_list = list(final_df.index)
    sd = date_list[0]
    ed = date_list[-1]

    st_ret = "{:.2f}".format(final_df.loc[date_list[-1]][0] * 100, 2)
    bh_ret = "{:.2f}".format(final_df.loc[date_list[-1]][1] * 100, 2)
    return render_template('keltner_build_model.html', stock_list=stock_table,
                           length=length, start_date_test=sd, end_date_test=ed,
                           strategy_return=st_ret, bh_return=bh_ret)