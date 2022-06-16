import warnings
from datetime import datetime, timedelta

import pandas as pd
from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database, eod_market_data

from system.services.pair_ai import pair_ai
import itertools


def pair_ai_building_service():
    input = {"fund_cat": ["pe_ratio", "beta", "market_capitalization"], "start_date": "2019-01-01",
             "part_date": "2020-01-01", "end_date": "2021-01-01"}
    fund_cat_lst = ["pe_ratio", "beta", "market_capitalization"]
    cluster_dict = {}  # stores all the clusters
    max_epsilon = 0
    best_dict = {}
    prob_dict = {}
    benchmark_sharpe = 0
    benchmark_money_ret = 0

    if request.method == "POST":
        start_date_input = request.form.get('start_date')
        try:
            start_date = pd.to_datetime(start_date_input)
        except:
            flash("invalid training start date input", "error")
            return render_template("pair_ai_building.html", fund_category=fund_cat_lst, clusters=cluster_dict,
                                   best_epsilon=str(round(max_epsilon, 2)), best_df=best_dict, prob_df=prob_dict,
                                   spy_sharpe_prob=benchmark_sharpe, spy_ret_prob=benchmark_money_ret, input=input)
        input["start_date"] = start_date_input

        part_date_input = request.form.get('part_date')
        try:
            part_date = pd.to_datetime(part_date_input)
        except:
            flash("invalid training end date input", "error")
            return render_template("pair_ai_building.html", fund_category=fund_cat_lst, clusters=cluster_dict,
                                   best_epsilon=str(round(max_epsilon, 2)), best_df=best_dict, prob_df=prob_dict,
                                   spy_sharpe_prob=benchmark_sharpe, spy_ret_prob=benchmark_money_ret, input=input)
        input["part_date"] = part_date_input

        end_date_input = request.form.get('end_date')
        try:
            end_date = str(end_date_input)
        except:
            flash("invalid probation test end date")
            return render_template("pair_ai_building.html", fund_category=fund_cat_lst, clusters=cluster_dict,
                                   best_epsilon=str(round(max_epsilon, 2)), best_df=best_dict, prob_df=prob_dict,
                                   spy_sharpe_prob=benchmark_sharpe, spy_ret_prob=benchmark_money_ret, input=input)
        input["end_date"] = end_date_input

        fund_cat_input = request.form.getlist('fund_cat')
        try:
            fund_cat = list(fund_cat_input)
        except:
            flash("invalid funmental information")
            return render_template("pair_ai_building.html", fund_category=fund_cat_lst, clusters=cluster_dict,
                                   best_epsilon=str(round(max_epsilon, 2)), best_df=best_dict, prob_df=prob_dict,
                                   spy_sharpe_prob=benchmark_sharpe, spy_ret_prob=benchmark_money_ret, input=input)
        input["fund_cat"] = fund_cat_input

        start_date = input["start_date"]
        part_date = input["part_date"]
        end_date = input["end_date"]
        today = datetime.today().strftime('%Y-%m-%d')

        table_list = ['spy']
        database.create_table(table_list)
        if database.check_table_empty('spy'):
            # if the table is empty, insert data from start date to today
            eod_market_data.populate_stock_data(['spy'], "spy", start_date, today, 'US')
        else:
            # if the table is not empty, insert data from the last date in the existing table to today.
            select_stmt = 'SELECT date FROM spy ORDER BY date DESC limit 1'
            spy_last_date = database.execute_sql_statement(select_stmt)['date'][0]
            spy_begin_date = (datetime.strptime(spy_last_date, '%Y-%m-%d') + timedelta(days=1)).strftime(
                '%Y-%m-%d')  # add one day after the last date in table
            if spy_begin_date <= today:
                eod_market_data.populate_stock_data(['spy'], "spy", spy_begin_date, today, 'US')
        select_stmt = """
            SELECT date,
                printf("%.2f", adjusted_close) as adjusted_close,
                volume
            FROM spy
            ORDER BY date DESC;
            """
        spy_price = database.execute_sql_statement(select_stmt)
        spy_price['date'] = pd.to_datetime(spy_price['date'])
        spy_price = spy_price.set_index('date')
        spy_price = spy_price.loc[spy_price.index >= start_date]
        spy_price['adjusted_close'] = spy_price['adjusted_close'].astype('float')

        trading_days = spy_price.index
        num_days = len(trading_days)

        ######################################################
        # Get price data for all SP500 stocks
        ######################################################
        table_list = ['stocks']
        database.create_table(table_list)
        if database.check_table_empty('sp500'):
            eod_market_data.populate_sp500_data('SPY', 'US')
        tickers = database.get_sp500_symbols()
        price_data = pd.DataFrame(index=trading_days)

        # create stock table if not exist
        # otherwise, simply update the stock database
        if database.check_table_empty('stocks'):
            eod_market_data.populate_stock_data(tickers, "stocks", start_date, today, 'US')
        else:
            select_stmt = 'SELECT date FROM stocks ORDER BY date DESC limit 1'
            last_date_stocks = database.execute_sql_statement(select_stmt)['date'][0]
            begin_date_stocks = (datetime.strptime(last_date_stocks, '%Y-%m-%d') + timedelta(days=1)).strftime(
                '%Y-%m-%d')  # add one day after the last date in table
            if begin_date_stocks <= today:
                eod_market_data.populate_stock_data(tickers, "stocks", begin_date_stocks, today, 'US')

        symbol_list = database.execute_sql_statement("SELECT DISTINCT symbol FROM stocks;")['symbol']
        for ticker in tickers:
            select_stmt = f"""
                SELECT date,
                    printf("%.2f", adjusted_close) as adjusted_close
                FROM stocks
                WHERE symbol = "{ticker}"
                ORDER BY date;
                """
            try:
                result_df = database.execute_sql_statement(select_stmt)
                result_df['date'] = pd.to_datetime(result_df['date'])
                result_df = result_df.set_index('date')
                result_df = result_df.loc[result_df.index >= start_date]
                if len(result_df) == num_days:
                    price_data[ticker] = result_df['adjusted_close']
            except:
                print(f'Error raised for {ticker}')

        price_data = price_data.astype('float')
        price_data.dropna(axis=1)

        return_df = price_data.pct_change()
        return_df = return_df.iloc[1:, :].dropna(axis=1)

        ########################################
        # Get fundamental data for sp500 stocks
        ########################################
        fund_cat = input["fund_cat"]
        table_list = ['fundamentals']
        database.create_table(table_list)

        if database.check_table_empty('fundamentals'):
            eod_market_data.populate_fundamental_data(tickers, 'US')
            eod_market_data.populate_fundamental_data(['SPY'], 'US')
        # OPTIONAL: uncomment this part if want to update fundamentals every time
        #        else:
        #            database.clear_table(table_list)
        #            eod_market_data.populate_fundamental_data(tickers, 'US')
        #            eod_market_data.populate_fundamental_data(['SPY'], 'US')

        select_stmt = """
            SELECT symbol,
                printf("%.4f", pe_ratio) as pe_ratio,
                printf("%.4f", dividend_yield) as dividend_yield,
                printf("%.4f", beta) as beta,
                market_capitalization
            FROM fundamentals ORDER BY symbol;
            """
        fund_df = database.execute_sql_statement(select_stmt)
        fund_df = fund_df.set_index('symbol')
        fund_df = fund_df[fund_cat].astype('float')
        fund_df = fund_df.dropna()

        #######################################################
        # find the intersection of return data and fundamentals
        #######################################################
        common_tickers = fund_df.index.intersection(return_df.columns)
        return_df = return_df[common_tickers]
        fund_df = fund_df.loc[common_tickers]

        ###################
        # algorithm starts
        ###################
        cluster_dict, max_epsilon = pair_ai.find_clusters(return_df.loc[return_df.index < part_date], fund_df, fund_cat)

        all_pairs = []  # all pairs to evaluate
        for i in range(0, len(cluster_dict)):
            cur_cluster = cluster_dict[str(i)]
            all_pairs.extend(itertools.combinations(cur_cluster, 2))

        ##################################
        # backtest to select 10 best pairs
        ##################################
        backtest_result = pair_ai.backtest(
            price_data.loc[(price_data.index >= part_date) & (price_data.index < end_date)], all_pairs)
        backtest_result = backtest_result.dropna().sort_values(by=['sharpe ratio', 'money return'], ascending=False)
        best_result = backtest_result.iloc[0:10]
        best_result = best_result.round({'money return': 2, 'sharpe ratio': 2})
        best_dict = best_result.to_dict('index')

        #################
        # probation test
        #################
        probation_result = pair_ai.backtest(price_data.loc[price_data.index >= end_date],
                                            list(all_pairs[i] for i in best_result.index))
        probation_result = probation_result.round({'money return': 2, 'sharpe ratio': 2})
        prob_dict = probation_result.to_dict('index')

        benchmark_return = spy_price['adjusted_close'].pct_change()
        benchmark_return = benchmark_return.loc[benchmark_return.index >= end_date]
        benchmark_sharpe = (benchmark_return.mean() - 0) / benchmark_return.std() * (252 ** 0.5)
        benchmark_money_ret = spy_price['adjusted_close'].iloc[-1] - \
                              spy_price['adjusted_close'][spy_price.index >= end_date].iloc[0]

        return render_template("pair_ai_building.html", fund_category=fund_cat_lst, clusters=cluster_dict,
                               best_epsilon=str(round(max_epsilon, 2)), best_df=best_dict, prob_df=prob_dict,
                               spy_sharpe_prob=str(round(benchmark_sharpe, 2)),
                               spy_ret_prob=str(round(benchmark_money_ret, 2)), input=input)
    else:
        return render_template("pair_ai_building.html", fund_category=fund_cat_lst, clusters=cluster_dict,
                               best_epsilon=max_epsilon, best_df=best_dict, prob_df=prob_dict,
                               spy_sharpe_prob=benchmark_sharpe, spy_ret_prob=benchmark_money_ret, input=input)
