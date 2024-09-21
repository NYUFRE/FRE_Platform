import warnings
from datetime import datetime, timedelta
import pandas_market_calendars as mcal

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning
from system import database
from system.services.sim_trading.client import client_config
from system.services.stat_arb.pair_trading import build_pair_trading_model

warnings.simplefilter(action='ignore', category=SAWarning)


def pair_trade_build_model_param_service():
    if request.method == 'POST':
        select_stmt = "SELECT DISTINCT sector FROM sp500;"
        result_df = database.execute_sql_statement(select_stmt)
        sector_list = list(result_df['sector'])

        form_input = request.form
        corr_threshold = form_input['Corr Threshold']
        adf_threshold = form_input['P Threshold']
        pair_trading_start_date = form_input['Start Date']
        pair_trading_end_date = form_input['End Date']
        sector = form_input['Sector']

        if not (corr_threshold and adf_threshold and pair_trading_end_date and pair_trading_start_date and sector):
            flash('Error!  Incorrect Values!', 'error')
            return render_template("pair_trade_build_model_param.html", sector_list=sector_list,
                                   done_pair_trade_model=client_config.done_pair_model)

        if float(corr_threshold) >= 1 or float(corr_threshold) <= - 1:
            flash('Error!  Incorrect Correlation Threshold!', 'error')
            return render_template("pair_trade_build_model_param.html", sector_list=sector_list,
                                   done_pair_trade_model=client_config.done_pair_model)

        if float(adf_threshold) >= 1 or float(adf_threshold) <= 0:
            flash('Error! Incorrect P Value Threshold!', 'error')
            return render_template("pair_trade_build_model_param.html", sector_list=sector_list,
                                   done_pair_trade_model=client_config.done_pair_model)

        if datetime.strptime(pair_trading_end_date, "%Y-%m-%d") > datetime.now():
            flash('Error! Incorrect End Date! Should not be later than today!', 'error')
            return render_template("pair_trade_build_model_param.html", sector_list=sector_list,
                                   done_pair_trade_model=client_config.done_pair_model)

        least_start_date = datetime.strptime(pair_trading_end_date, "%Y-%m-%d") - timedelta(365)
        if least_start_date < datetime.strptime(pair_trading_start_date, "%Y-%m-%d"):
            flash('Error! Incorrect Date Range! At least one year data is needed, such as ' +
                  f'{least_start_date.strftime("%Y-%m-%d")} ' + ' to ' +
                  f'{datetime.strptime(pair_trading_end_date, "%Y-%m-%d").strftime("%Y-%m-%d")}', 'error')
            return render_template("pair_trade_build_model_param.html",
                                   sector_list=sector_list, done_pair_trade_model=client_config.done_pair_model)

        trading_calendar = mcal.get_calendar('NYSE')
        latest_trading_date = trading_calendar.schedule(
            start_date=datetime.strptime(pair_trading_start_date, "%Y-%m-%d"),
            end_date=datetime.strptime(pair_trading_end_date, "%Y-%m-%d")).index.strftime("%Y-%m-%d").tolist()[-1]

        max_db_date = database.execute_sql_statement("SELECT MAX(date) AS max FROM stocks;")["max"][0]
        if datetime.strptime(latest_trading_date, "%Y-%m-%d") > datetime.strptime(max_db_date, "%Y-%m-%d"):
            flash("Warning! There is not enough data in database. Should go to MarketData page and update first!")
            return render_template("pair_trade_build_model_param.html",
                                   sector_list=sector_list, done_pair_trade_model=client_config.done_pair_model)

        back_testing_start_date = (datetime.strptime(pair_trading_start_date, "%Y-%m-%d") +
                                   timedelta(270)).strftime("%Y-%m-%d")
        back_testing_end_date = (datetime.strptime(pair_trading_start_date, "%Y-%m-%d") +
                                 timedelta(330)).strftime("%Y-%m-%d")

        client_config.pair_trading_start_date = pair_trading_start_date
        client_config.pair_trading_end_date = pair_trading_end_date
        client_config.back_testing_start_date = back_testing_start_date
        client_config.back_testing_end_date = back_testing_end_date

        error = build_pair_trading_model(float(corr_threshold), float(adf_threshold),
                                         sector, pair_trading_start_date,
                                         back_testing_start_date, pair_trading_end_date)
        if len(error) > 0:
            flash("Warning! " + error + " Select different Corr Threshold and P Threshold!")
            return render_template("pair_trade_build_model_param.html", sector_list=sector_list,
                                   done_pair_trade_model=client_config.done_pair_model)

        select_stmt = f"SELECT * FROM stock_pairs;"
        result_df = database.execute_sql_statement(select_stmt)
        result_df['price_mean'] = result_df['price_mean'].map('{:.4f}'.format)
        result_df['volatility'] = result_df['volatility'].map('{:.4f}'.format)
        result_df = result_df.transpose()
        list_of_pairs = [result_df[i] for i in result_df]
        client_config.done_pair_model = "pointer-events:auto"
        return render_template("pair_trade_build_model.html", pair_list=list_of_pairs)
    else:
        select_stmt = f"SELECT DISTINCT sector FROM sp500;"
        result_df = database.execute_sql_statement(select_stmt)
        sector_list = list(result_df['sector'])
        return render_template("pair_trade_build_model_param.html", sector_list=sector_list,
                               done_pair_trade_model=client_config.done_pair_model)