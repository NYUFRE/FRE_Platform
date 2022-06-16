import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database, eod_market_data


def md_sp500_sectors_service():
    table_list = ['sp500', 'sp500_sectors']
    database.create_table(table_list)
    # don't need to update table again, table already updated in sp500 tab
    if database.check_table_empty('sp500_sectors'):
        eod_market_data.populate_sp500_data('SPY', 'US')
    select_stmt = """
        SELECT sector as sector_name,
                printf("%.4f", equity_pct) as equity_pct,
                printf("%.4f", category_pct) as category_pct
        FROM sp500_sectors ORDER BY sector ASC;
        """
    result_df = database.execute_sql_statement(select_stmt)
    result_df = result_df.transpose()
    list_of_sectors = [result_df[i] for i in result_df]
    return render_template("md_sp500_sectors.html", sector_list=list_of_sectors)