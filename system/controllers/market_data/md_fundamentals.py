import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database, eod_market_data


def md_fundamentals_service():
    table_name = 'fundamentals'
    if database.check_table_exists(table_name):
        database.drop_table(table_name)
    table_list = ['fundamentals']
    database.create_table(table_list)

    if database.check_table_empty('fundamentals'):
        tickers = database.get_sp500_symbols()
        tickers.append('SPY')
        eod_market_data.populate_fundamental_data(tickers, 'US')

    select_stmt = """
        SELECT symbol,
                printf("%.4f", pe_ratio) as pe_ratio,
                printf("%.4f", dividend_yield) as dividend_yield,
                printf("%.4f", beta) as beta,
                printf("%.2f", high_52weeks) as high_52weeks,
                printf("%.2f", low_52weeks) as low_52weeks,
                printf("%.2f", ma_50days) as ma_50days,
                printf("%.2f", ma_200days) as ma_200days
        FROM fundamentals ORDER BY symbol;
        """
    result_df = database.execute_sql_statement(select_stmt)
    result_df = result_df.transpose()
    list_of_stocks = [result_df[i] for i in result_df]
    return render_template("md_fundamentals.html", stock_list=list_of_stocks)