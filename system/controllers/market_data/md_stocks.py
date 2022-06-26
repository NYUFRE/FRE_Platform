import warnings
from datetime import datetime

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database, eod_market_data

from system.services.ai_modeling.ga_portfolio_select import start_date, end_date


def md_stocks_service():
    # TODO: if ticker not in database, add new data to database.
    table_list = ['stocks']
    database.create_table(table_list)
    if database.check_table_empty('stocks'):
        tickers = database.get_sp500_symbols()
        eod_market_data.populate_stock_data(tickers, "stocks", start_date, end_date, 'US')

    if request.method == 'POST':
        ticker = "A"
        if request.form.get("symbol"):
            ticker = request.form.get("symbol")

        date1 = start_date
        if request.form.get("start_date"):
            date1 = request.form.get("start_date")

        date2 = end_date
        if request.form.get("end_date"):
            date2 = request.form.get("end_date")

        # if ticker is not in database, update the data from EOD and store it into database
        symbol_list = database.execute_sql_statement("SELECT DISTINCT symbol FROM stocks;")['symbol']
        if ticker not in list(symbol_list):
            try:
                today = datetime.today().strftime('%Y-%m-%d')
                eod_market_data.populate_stock_data([ticker], "stocks", start_date, today, 'US')
            except:
                flash('Can\'t find data. Please enter correct ticker name and dates.')

        select_stmt = f"""
               SELECT symbol, date,
                   printf("%.2f", open) as open,
                   printf("%.2f", high) as high,
                   printf("%.2f", low) as low,
                   printf("%.2f", close) as close,
                   printf("%.2f", adjusted_close) as adjusted_close,
                   volume
               FROM stocks
               WHERE symbol = "{ticker}" AND strftime('%Y-%m-%d', date) BETWEEN "{date1}" AND "{date2}"
               ORDER BY date;
               """
        result_df = database.execute_sql_statement(select_stmt)
        if result_df.empty:
            flash('Can\'t find data. Please enter correct ticker name and dates.')
        result_df = result_df.transpose()
        list_of_stock = [result_df[i] for i in result_df]
        return render_template("md_stock.html", stock_list=list_of_stock)
    else:
        return render_template("md_get_stock.html")