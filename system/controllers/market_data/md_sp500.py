import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database, eod_market_data


def md_sp500_service():
    table_list = ['sp500', 'sp500_sectors']
    database.create_table(table_list)
    if database.check_table_empty('sp500'):
        eod_market_data.populate_sp500_data('SPY', 'US')
    else:
        # update tables
        database.clear_table(table_list)
        eod_market_data.populate_sp500_data('SPY', 'US')
    select_stmt = """
        SELECT symbol, name as company_name, sector, industry,
                printf("%.2f", weight) as weight
        FROM sp500 ORDER BY symbol ASC;
        """
    result_df = database.execute_sql_statement(select_stmt)
    result_df = result_df.transpose()
    list_of_stocks = [result_df[i] for i in result_df]
    return render_template("md_sp500.html", stock_list=list_of_stocks)