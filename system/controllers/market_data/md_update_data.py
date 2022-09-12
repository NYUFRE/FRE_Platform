import warnings
from datetime import datetime, timedelta
import holidays
import traceback
import sys

from flask import flash, render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database, eod_market_data

from system.services.ai_modeling.ga_portfolio_select import start_date

# modify from a similar function in system/services/ai_modeling/ga_portfolio_probation_test.py
def previous_working_day(current_day, holidays=holidays.US()):
    if current_day not in holidays and current_day.weekday() < 5:
        return current_day
    else:
        previous_day = current_day - timedelta(1)
        return previous_working_day(previous_day, holidays)

def md_update_data_service():
    #today = datetime.today().strftime('%Y-%m-%d')
    start_date = '2010-01-01'
    latest_weekday = previous_working_day(datetime.today()).strftime('%Y-%m-%d')
    try:
        # fundamentals (use multi-threads,takes 30 seconnds)
        table_name = 'fundamentals'
        if database.check_table_exists(table_name):
            database.drop_table(table_name)
        table_list = ['fundamentals']
        database.create_table(table_list)
        # database.clear_table(table_list)
        tickers = database.get_sp500_symbols()
        tickers.append('SPY')
        eod_market_data.populate_fundamental_data(tickers, 'US')

        # spy price data
        if database.check_table_empty('spy'):
            # if the table is empty, insert data from start date to today
            eod_market_data.populate_stock_data(['spy'], "spy", start_date, latest_weekday, 'US')
        else:
            # if the table is not empty, insert data from the last date in the existing table to today.
            select_stmt = 'SELECT date FROM spy ORDER BY date DESC limit 1'
            last_date = database.execute_sql_statement(select_stmt)['date'][0]
            # define begin_date here. The rest updates will use the same begin date
            begin_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime(
                '%Y-%m-%d')  # add one day after the last date in table
            if begin_date < latest_weekday:
                eod_market_data.populate_stock_data(['spy'], "spy", begin_date, latest_weekday, 'US')
        # us10y
        database.create_table(['us10y'])
        if database.check_table_empty('us10y'):
            eod_market_data.populate_stock_data(['US10Y'], "us10y", start_date, latest_weekday, 'INDX')
        else:
            select_stmt = 'SELECT date FROM us10y ORDER BY date DESC limit 1'
            last_date = database.execute_sql_statement(select_stmt)['date'][0]
            begin_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            if begin_date < latest_weekday:
                eod_market_data.populate_stock_data(['US10Y'], "us10y", begin_date, latest_weekday, 'INDX')

        # stock daily data (use multi-threads,takes 22 seconnds)
        # TODO: try to use batch request from IEX data to further speed up.
        # Get IEX subscription first. https://iexcloud.io/docs/api/#batch-requests
        database.create_table(['stocks'])
        tickers = database.get_sp500_symbols()

        if database.check_table_empty('stocks'):
            # TODO! Use non-multi-threading version for now as EDO data feed has strange behavior after its upgrade
            # eod_market_data.populate_stocks_data_multi(tickers, "stocks", start_date, today, 'US')
            eod_market_data.populate_stock_data(tickers, "stocks", '2010-01-01', latest_weekday, 'US')
        else:
            select_stmt = 'SELECT date FROM stocks ORDER BY date DESC limit 1'
            last_date_stocks = database.execute_sql_statement(select_stmt)['date'][0]
            begin_date_stocks = (datetime.strptime(last_date_stocks, '%Y-%m-%d') + timedelta(days=1)).strftime(
                '%Y-%m-%d')  # add one day after the last date in table
            if begin_date_stocks < latest_weekday:
                # TODO! Use non-multi-threading version for now as EDO data feed has strange behavior after its upgrade
                # eod_market_data.populate_stocks_data_multi(tickers, "stocks", begin_date_stocks, today, 'US')
                eod_market_data.populate_stock_data(tickers, "stocks", begin_date_stocks, latest_weekday, 'US')
        flash("Stock daily data updated...")

        # sp500 index & sectors
        table_list = ['sp500', 'sp500_sectors']
        database.create_table(table_list)
        if database.check_table_empty('sp500'):
            eod_market_data.populate_sp500_data('SPY', 'US')
        else:
            # update tables
            database.clear_table(table_list)
            eod_market_data.populate_sp500_data('SPY', 'US')
        flash("Thank you for waiting!   All market data is updated!")
    except:
        traceback.print_exception(*sys.exc_info())
        flash("Something went wrong when updating the market data :(")

    return render_template("md_update_data.html")

