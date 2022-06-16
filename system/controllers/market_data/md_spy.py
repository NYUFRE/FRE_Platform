import warnings
from datetime import datetime, timedelta

from flask import render_template
from sqlalchemy.exc import SAWarning

from system.services.ai_modeling.ga_portfolio_select import start_date

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database, eod_market_data


def md_spy_service():
    table_list = ['spy']
    database.create_table(table_list)
    today = datetime.today().strftime('%Y-%m-%d')
    if database.check_table_empty('spy'):
        # if the table is empty, insert data from start date to today
        eod_market_data.populate_stock_data(['spy'], "spy", start_date, today, 'US')
    else:
        # if the table is not empty, insert data from the last date in the existing table to today.
        select_stmt = 'SELECT date FROM spy ORDER BY date DESC limit 1'
        last_date = database.execute_sql_statement(select_stmt)['date'][0]
        begin_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime(
            '%Y-%m-%d')  # add one day after the last date in table
        if begin_date <= today:
            eod_market_data.populate_stock_data(['spy'], "spy", begin_date, today, 'US')
    select_stmt = """
        SELECT symbol, date,
                printf("%.2f", open) as open,
                printf("%.2f", high) as high,
                printf("%.2f", low) as low,
                printf("%.2f", close) as close,
                printf("%.2f", adjusted_close) as adjusted_close,
                volume
        FROM spy ORDER BY date DESC;
        """
    result_df = database.execute_sql_statement(select_stmt)
    result_df = result_df.transpose()
    list_of_spy = [result_df[i] for i in result_df]
    return render_template("md_spy.html", spy_list=list_of_spy)