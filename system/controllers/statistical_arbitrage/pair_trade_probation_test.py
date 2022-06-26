import warnings
from datetime import datetime

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning
from system import database
from system.services.sim_trading.client import client_config
from system.services.stat_arb.pair_trading import pair_trade_probation_test

from system.services.utility.helpers import usd

warnings.simplefilter(action='ignore', category=SAWarning)


def pair_trade_probation_test_service():
    if request.method == 'POST':

        form_input = request.form
        probation_testing_start_date = form_input['Start Date']
        probation_testing_end_date = form_input['End Date']
        pair_trading_end_date = client_config.pair_trading_end_date
        back_testing_end_date = client_config.back_testing_end_date

        if (not probation_testing_end_date) or (not probation_testing_start_date):
            flash('Error! Start or End Date missing!', 'error')
            return render_template("pair_trade_probation_test.html", back_testing_end_date=back_testing_end_date)

        if datetime.strptime(probation_testing_start_date, "%Y-%m-%d") >= datetime.strptime(probation_testing_end_date,
                                                                                            "%Y-%m-%d"):
            flash('Error!  Start Date should be before End Date!', 'error')
            return render_template("pair_trade_probation_test.html", back_testing_end_date=back_testing_end_date)

        if datetime.strptime(probation_testing_end_date, "%Y-%m-%d") > datetime.strptime(pair_trading_end_date,
                                                                                         "%Y-%m-%d"):
            flash('Error! Incorrect Date Range! Probation Testing Start and End Dates should be between ' +
                  f'{back_testing_end_date} ' + ' to ' + f'{pair_trading_end_date}', 'error')
            return render_template("pair_trade_probation_test.html", back_testing_end_date=back_testing_end_date)

        pair_trade_probation_test(probation_testing_start_date, probation_testing_end_date)

        select_stmt = "SELECT symbol1, symbol2, sum(profit_loss) AS Profit, count(profit_loss) AS Total_Trades, \
                               sum(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) AS Profit_Trades, \
                               sum(CASE WHEN profit_loss <0 THEN 1 ELSE 0 END) AS Loss_Trades FROM pair_trades  \
                               WHERE profit_loss <> 0 \
                               GROUP BY symbol1, symbol2;"
        result_df = database.execute_sql_statement(select_stmt)
        total = result_df['Profit'].sum()
        result_df['Profit'] = result_df['Profit'].map('${:,.2f}'.format)
        result_df = result_df.transpose()
        trade_results = [result_df[i] for i in result_df]
        return render_template("pair_trade_probation_test_result.html", trade_list=trade_results, total=usd(total))
    else:
        back_testing_end_date = client_config.back_testing_end_date
        return render_template("pair_trade_probation_test.html", back_testing_end_date=back_testing_end_date)