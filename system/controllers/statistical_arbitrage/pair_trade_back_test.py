import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning
from system import database
from system.services.sim_trading.client import client_config
from system.services.stat_arb.pair_trading import pair_trade_back_test

from system.services.utility.helpers import usd

warnings.simplefilter(action='ignore', category=SAWarning)


def pair_trade_back_test_service():
    back_testing_start_date = client_config.back_testing_start_date
    back_testing_end_date = client_config.back_testing_end_date
    pair_trade_back_test(back_testing_start_date, back_testing_end_date)

    select_stmt = f"SELECT symbol1, symbol2, sum(profit_loss) AS Profit, count(profit_loss) AS Total_Trades, \
                        sum(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) AS Profit_Trades, \
                        sum(CASE WHEN profit_loss <0 THEN 1 ELSE 0 END) AS Loss_Trades FROM pair_trades  \
                        WHERE profit_loss <> 0 \
                        GROUP BY symbol1, symbol2;"
    result_df = database.execute_sql_statement(select_stmt)
    total = result_df['Profit'].sum()
    result_df['Profit'] = result_df['Profit'].map('${:,.2f}'.format)
    result_df = result_df.transpose()
    trade_results = [result_df[i] for i in result_df]
    return render_template("pair_trade_back_test_result.html", trade_list=trade_results, total=usd(total))