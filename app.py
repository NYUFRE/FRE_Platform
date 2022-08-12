#################
#### imports ####
#################

import sys
import warnings
import pandas as pd
from flask import request
from sqlalchemy.exc import SAWarning
from system import app, database
from system.controllers.ai_modeling.ai_back_test import ai_back_test_service
from system.controllers.ai_modeling.ai_back_test_plot import ai_back_test_plot_service
from system.controllers.ai_modeling.ai_build_model import ai_build_model_service
from system.controllers.ai_modeling.ai_modeling import ai_modeling_service
from system.controllers.ai_modeling.ai_probation_test import ai_probation_test_service
from system.controllers.alpha_test.at_analysis import at_analysis_service
from system.controllers.alpha_test.at_introduction import at_introduction_service
from system.controllers.alpha_test.plot.at1_plot import at1_plot_service
from system.controllers.alpha_test.plot.at2_plot import at2_plot_service
from system.controllers.asset_pricing.ap_CDS import ap_CDS_service
from system.controllers.asset_pricing.ap_american_pricing import ap_american_pricing_service
from system.controllers.asset_pricing.ap_european_pricing import ap_european_pricing_service
from system.controllers.asset_pricing.ap_fixedRateBond import ap_fixedRateBond_service
from system.controllers.asset_pricing.ap_fra import ap_fra_service
from system.controllers.asset_pricing.ap_introduction import ap_introduction_service
from system.controllers.asset_pricing.ap_swap import ap_swap_service
from system.controllers.asset_pricing.ap_yield_curve import ap_yield_curve_service
from system.controllers.asset_pricing.plot.american_plot import american_plot_service
from system.controllers.asset_pricing.plot.discount_plot import discount_plot_service
from system.controllers.asset_pricing.plot.european_plot import european_plot_service
from system.controllers.asset_pricing.plot.yield_plot import yield_plot_service
from system.controllers.btc_algo.btc_backtest import btc_backtest_service
from system.controllers.btc_algo.btc_build import btc_build_service
from system.controllers.btc_algo.btc_introduction import btc_introduction_service
from system.controllers.earning_impact.ei_analysis import ei_analysis_service
from system.controllers.earning_impact.ei_introduction import ei_introduction_service
from system.controllers.earning_impact.ei_plot import ei_plot_service
from system.controllers.fixed_income_trading.fixed_income_bond_info import fixed_income_bond_info_service
from system.controllers.fixed_income_trading.fixed_income_ptfl_result import fixed_income_ptfl_result_service
from system.controllers.fixed_income_trading.fixed_income_saved import fixed_income_saved_service
from system.controllers.fixed_income_trading.fixed_income_saved_info import fixed_income_saved_info_service
from system.controllers.fixed_income_trading.fixed_income_trading_intro import fixed_income_service
from system.controllers.fixed_income_trading.fixed_income_trading_new import fixed_income_trading_new_service
from system.controllers.fixed_income_trading.fixed_income_build_ptfl import fixed_income_build_ptfl_service
from system.controllers.fixed_income_trading.fixed_income_yield_result import fixed_income_yield_sim_result_service
from system.controllers.fixed_income_trading.fixed_income_yield_sim import fixed_income_yield_sim_setup_service
from system.controllers.high_frequency_trading.hf_cleaning_data import hf_cleaning_data_service
from system.controllers.high_frequency_trading.hf_id_plot import hf_id_plot_service
from system.controllers.high_frequency_trading.hf_trading import hf_trading_service
from system.controllers.high_frequency_trading.hf_trading_engine import hf_trading_engine_service
from system.controllers.keltner_channel.keltner_backtest_plot import keltner_backtest_plot_service
from system.controllers.keltner_channel.keltner_build_model import keltner_build_model_service
from system.controllers.keltner_channel.keltner_channel_strategy import keltner_channel_strategy_service
from system.controllers.manual_trading.buy import buy_service
from system.controllers.manual_trading.history import history_service
from system.controllers.manual_trading.portfolio import portfolio_service
from system.controllers.manual_trading.quote import quote_service
from system.controllers.manual_trading.risk_management import risk_management_service
from system.controllers.manual_trading.sell import sell_service
from system.controllers.manual_trading.short import short_service
from system.controllers.manual_trading.var_plot import var_plot_service
from system.controllers.market_data.md_fundamentals import md_fundamentals_service
from system.controllers.market_data.md_sp500 import md_sp500_service
from system.controllers.market_data.md_sp500_sectors import md_sp500_sectors_service
from system.controllers.market_data.md_spy import md_spy_service
from system.controllers.market_data.md_stocks import md_stocks_service
from system.controllers.market_data.md_update_data import md_update_data_service
from system.controllers.market_data.md_us10y import md_us10y_service
from system.controllers.pair_ai_trading.pair_ai_building import pair_ai_building_service
from system.controllers.pair_ai_trading.pair_ai_introduction import pair_ai_introduction_service
from system.controllers.portfolio_optimization.optimize_back_test import optimize_back_test_service
from system.controllers.portfolio_optimization.optimize_build import optimize_build_service
from system.controllers.portfolio_optimization.optimize_introduction import optimize_introduction_service
from system.controllers.portfolio_optimization.plot.opt_back_test_plot1 import opt_back_test_plot1_service
from system.controllers.portfolio_optimization.plot.opt_back_test_plot2 import opt_back_test_plot2_service
from system.controllers.portfolio_optimization.plot.opt_back_test_plot3 import opt_back_test_plot3_service
from system.controllers.portfolio_optimization.plot.opt_back_test_plot4 import opt_back_test_plot4_service
from system.controllers.prediction_portfolio_optimization.pb_opt_backtest import pb_opt_backtest_service
from system.controllers.prediction_portfolio_optimization.pb_opt_backtest_plot import pb_opt_backtest_plot_service
from system.controllers.prediction_portfolio_optimization.pb_opt_build import pb_opt_build_service
from system.controllers.prediction_portfolio_optimization.pb_opt_date_choose import pb_opt_date_choose_service
from system.controllers.prediction_portfolio_optimization.predict_based_optmize import predict_based_optimize_service
from system.controllers.root import root_service
from system.controllers.simulated_trading.sim_auto_trading import sim_auto_trading_service
from system.controllers.simulated_trading.sim_choose_strat import sim_choose_strat_service
from system.controllers.simulated_trading.sim_model_info import sim_model_info_service
from system.controllers.simulated_trading.sim_server_down import sim_server_down_service
from system.controllers.simulated_trading.sim_server_up import sim_server_up_service
from system.controllers.simulated_trading.sim_trading import sim_trading_service
from system.controllers.statistical_arbitrage.pair_trade_back_test import pair_trade_back_test_service
from system.controllers.statistical_arbitrage.pair_trade_build_model_param import pair_trade_build_model_param_service
from system.controllers.statistical_arbitrage.pair_trade_probation_test import pair_trade_probation_test_service
from system.controllers.statistical_arbitrage.pair_trading import pair_trading_service
from system.controllers.stock_selection.stockselect_back_test import stockselect_back_test_service
from system.controllers.stock_selection.stockselect_build import stockselect_build_service
from system.controllers.stock_selection.stockselect_introduction import stockselect_introduction_service
from system.controllers.technical_indicator.technical_indicator_backtest import technical_indicator_backtest_service
from system.controllers.technical_indicator.technical_indicator_plot import technical_indicator_plot_service
from system.controllers.technical_indicator.technical_indicator_probtest import technical_indicator_probtest_service
from system.controllers.technical_indicator.technical_indicator_strategy import technical_indicator_strategy_service
from system.controllers.twitter_sentiments_analysis.tsa_intro import tsa_introduction_service
from system.controllers.twitter_sentiments_analysis.tsa_builder import tsa_builder_service
from system.controllers.twitter_sentiments_analysis.tsa_viewer import tsa_viewer_service
from system.controllers.twitter_sentiments_analysis.Plot.tsa_plot import tsa_plot_roc_service, tsa_plot_lab_service
from system.controllers.user_service.admin_view_users import admin_view_users_service
from system.controllers.user_service.confirm_token import confirm_email_service
from system.controllers.user_service.email_change import email_change_service
from system.controllers.user_service.login import login_service
from system.controllers.user_service.logout import logout_service
from system.controllers.user_service.password_change import password_change_service
from system.controllers.user_service.register import register_service
from system.controllers.user_service.resend_confirmation import resend_confirmation_service
from system.controllers.user_service.reset import reset_service
from system.controllers.user_service.reset_token import reset_token_service
from system.controllers.user_service.user_profile import user_profile_service
from system.services.portfolio.users import add_admin_user
from system.services.sim_trading.client import client_config
from system.services.utility.helpers import login_required

warnings.simplefilter(action='ignore', category=SAWarning)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    This function is for new user registration.
    It will take user inputs: email, firstname, lastname and password,
    and create a new user in fre_database.
    The new users are required to confirm their email addresses
    through the links sent to their email addresses.\n
    :return: register.html
    """
    return register_service()


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    This function is for user to login FRE platform.\n
    :return: login.html
    """
    return login_service()


@app.route('/logout')
@login_required
def logout():
    return logout_service()


@app.route('/confirm/<token>')
def confirm_email(token):
    return confirm_email_service(token)


@app.route('/reset', methods=["GET", "POST"])
def reset():
    return reset_service()


@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    return reset_token_service(token)


@app.route('/user_profile')
@login_required
def user_profile():
    return user_profile_service()


@app.route('/email_change', methods=["GET", "POST"])
@login_required
def email_change():
    return email_change_service()


@app.route('/password_change', methods=["GET", "POST"])
@login_required
def user_password_change():
    return password_change_service()


@app.route('/resend_confirmation')
@login_required
def resend_email_confirmation():
    return resend_confirmation_service()


@app.route('/admin_view_users')
@login_required
def admin_view_users():
    return admin_view_users_service()


# Manual Trading
@app.route("/")
@login_required
def index():
    # List the python processes before launching the server
    # Window env
    return root_service()


@app.route("/portfolio")
@login_required
def portfolio():
    # List the python processes before launching the server
    # Window env

    # Get portfolio data from database
    return portfolio_service()


@app.route("/quote", methods=["GET", "POST"])
def get_quote():
    return quote_service()


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    return buy_service()


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    return sell_service()


@app.route("/short", methods=["GET", "POST"])
@login_required
def short():
    return short_service()


@app.route("/history")
@login_required
def history():
    return history_service()


@app.route('/risk_management', methods=["GET", "POST"])
@login_required
def risk_management():
    return risk_management_service()


@app.route('/plot/var')
def plot_var():
    return var_plot_service()


# Statistical Arbitrage
@app.route('/pair_trading')
@login_required
def pair_trading():
    return pair_trading_service()


@app.route('/pair_trade_build_model_param', methods=['POST', 'GET'])
@login_required
def build_model():
    return pair_trade_build_model_param_service()


@app.route('/pair_trade_back_test')
@login_required
def model_back_testing():
    return pair_trade_back_test_service()


@app.route('/pair_trade_probation_test', methods=['POST', 'GET'])
@login_required
def model_probation_testing():
    return pair_trade_probation_test_service()


# AI modeling
@app.route('/ai_modeling')
@login_required
def ai_trading():
    return ai_modeling_service()


@app.route('/ai_build_model')
@login_required
def ai_build_model():
    # database.drop_table('best_portfolio')
    # While drop the table, table name "best_portfolio" still in metadata
    # therefore, everytime only clear table instead of drop it.
    return ai_build_model_service()


@app.route('/ai_back_test', methods=["GET", "POST"])
@login_required
def ai_back_test():
    return ai_back_test_service()


@app.route('/plot/ai_back_test_plot')
def ai_back_test_plot():
    return ai_back_test_plot_service()


@app.route('/ai_probation_test', methods=["GET", "POST"])
@login_required
def ai_probation_test():
    return ai_probation_test_service()


# Simulated Trading
@app.route('/sim_trading')
@login_required
def sim_trading():
    return sim_trading_service()


@app.route('/sim_server_up')
@login_required
def sim_server_up():
    return sim_server_up_service()


@app.route('/sim_server_down')
@login_required
def sim_server_down():
    return sim_server_down_service()


@app.route('/sim_choose_strat', methods=["GET", "POST"])
@login_required
def sim_choose_strat():
    return sim_choose_strat_service()


@app.route('/sim_auto_trading')
@login_required
def sim_auto_trading(strategy=None):
    return sim_auto_trading_service(strategy)


@app.route('/sim_model_info')
@login_required
def sim_model_info():
    return sim_model_info_service()


# Market Data
@app.route('/md_sp500')
@login_required
def market_data_sp500():
    return md_sp500_service()

@app.route('/md_sp500_sectors')
@login_required
def market_data_sp500_sectors():
    return md_sp500_sectors_service()


@app.route('/md_spy')
@login_required
def market_data_spy():
    return md_spy_service()


@app.route('/md_us10y')
@login_required
def market_data_us10y():
    return md_us10y_service()


@app.route('/md_fundamentals')
@login_required
def market_data_fundamentals():
    return md_fundamentals_service()


@app.route('/md_stocks', methods=["GET", "POST"])
@login_required
def market_data_stock():
    return md_stocks_service()


@app.route('/md_update_data')
@login_required
def update_market_data():
    """
    This function is for updating the MatketData database.
    Click the update_market_data tab, all market data will be updated. Takes around 1 min.
    # TODOs:
        Automatically trigger this function once everyday, then delete the update part in
        market_data_sp500(), market_data_spy(), and market_data_us10y().
    """
    return md_update_data_service()

# Pair Trading with AI
@app.route('/pair_ai_introduction')
@login_required
def pair_ai_introduction():
    return pair_ai_introduction_service()

@app.route("/pair_ai_building", methods=["GET", "POST"])
def pair_ai_building():
    return pair_ai_building_service()

# Fixed Income Securities Trading
@app.route('/fixed_income_trading')
@login_required
def fixed_income_trading():
    return fixed_income_service()

@app.route("/fixed_income_trading_new", methods=["GET", "POST"])
def fixed_income_trading_new():
    return fixed_income_trading_new_service()

@app.route("/fixed_income_ptfl", methods=["GET", "POST"])
def fixed_income_ptfl():
    return fixed_income_build_ptfl_service()

@app.route("/fixed_income_ptfl_result", methods=["GET", "POST"])
def fixed_income_ptfl_result():
    return fixed_income_ptfl_result_service()

@app.route("/fixed_income_yield_curve", methods=["GET", "POST"])
def fixed_income_yield_curve():
    return fixed_income_yield_sim_setup_service()

@app.route("/fixed_income_yield_curve_result", methods=["GET", "POST"])
def fixed_income_yield_curve_result():
    return fixed_income_yield_sim_result_service()

@app.route("/fixed_income_saved", methods=["GET", "POST"])
def fixed_income_saved():
    return fixed_income_saved_service()

@app.route("/saved_info", methods=["GET", "POST"])
def fixed_income_saved_info():
    return fixed_income_saved_info_service()

@app.route("/bond_info", methods=["GET", "POST"])
def fixed_income_bond_info():
    return fixed_income_bond_info_service()

# Asset Pricing
@app.route('/ap_introduction')
@login_required
def ap_introduction():
    return ap_introduction_service()


@app.route("/ap_european_pricing", methods=["GET", "POST"])
def cal_european():
    return ap_european_pricing_service()


@app.route('/plot/european')
def plot_european():
    return european_plot_service()


@app.route("/ap_american_pricing", methods=["GET", "POST"])
def cal_american():
    return ap_american_pricing_service()


@app.route('/plot/american')
def plot_american():
    return american_plot_service()


@app.route('/ap_fixedRateBond', methods=['POST', 'GET'])
@login_required
def pricing_fixedratebond():
    return ap_fixedRateBond_service()


@app.route('/ap_CDS', methods=['POST', 'GET'])
@login_required
def pricing_cds():
    return ap_CDS_service()


@app.route('/ap_fra', methods=['POST', 'GET'])
@login_required
def pricing_fra():
    return ap_fra_service()


@app.route('/ap_swap', methods=['POST', 'GET'])
@login_required
def pricing_swap():
    return ap_swap_service()


@app.route('/ap_yield_curve', methods=['POST', 'GET'])
@login_required
def ap_yield_curve():
    return ap_yield_curve_service()


@app.route('/plot/yield')
def plot_yield_curve():
    return yield_plot_service()


@app.route('/plot/discount')
def plot_discount_curve():
    return discount_plot_service()


@app.route('/optimize_introduction')
@login_required
def optimize_introduction():
    return optimize_introduction_service()


# Shan add exception here
@app.route("/optimize_build")
@login_required
def optimize_build():
    return optimize_build_service()


@app.route("/optimize_back_test")
@login_required
def optimize_back_test():
    return optimize_back_test_service()


@app.route('/plot/opt_back_test_plot1')
def opt_back_test_plot1():
    return opt_back_test_plot1_service()


@app.route('/plot/opt_back_test_plot2')
def opt_back_test_plot2():
    return opt_back_test_plot2_service()


@app.route('/plot/opt_back_test_plot3')
def opt_back_test_plot3():
    return opt_back_test_plot3_service()


@app.route('/plot/opt_back_test_plot4')
def opt_back_test_plot4():
    return opt_back_test_plot4_service()


# Earnings Impact
@app.route('/ei_introduction')
@login_required
def ei_introduction():
    return ei_introduction_service()


@app.route("/ei_analysis", methods=["GET", "POST"])
def ei_analysis():
    return ei_analysis_service()


@app.route('/plot/ei')
def plot_ei():
    return ei_plot_service()


# Alpha Test
@app.route('/at_introduction')
@login_required
def at_introduction():
    return at_introduction_service()


@app.route("/at_analysis", methods=["GET", "POST"])
def at_analysis():
    return at_analysis_service()


@app.route('/plot/at1')
def plot_at1():
    return at1_plot_service()


@app.route('/plot/at2')
def plot_at2():
    return at2_plot_service()


# High Frequency Trading
@app.route('/hf_trading')
def hf_trading():
    return hf_trading_service()


@app.route('/hf_cleaning_data')
def hf_cleaning_data():
    return hf_cleaning_data_service()


@app.route("/hf_trading_engine", methods=["GET", "POST"])
def hf_trading_engine():
    return hf_trading_engine_service()


@app.route('/hf_plot/<plot_id>')
def plot_hf(plot_id):
    return hf_id_plot_service(plot_id)


# Stock Selection
@app.route('/stockselect_introduction')
@login_required
def stockselect_introduction():
    return stockselect_introduction_service()


@app.route("/stockselect_build")
@login_required
def stockselect_build():
    return stockselect_build_service()


@app.route("/stockselect_back_test")
@login_required
def stockselect_back_test():
    return stockselect_back_test_service(global_param_dict)


# Technical Indicator Strategy
@app.route('/technical_indicator_strategy')
@login_required
def technical_indicator_strategy():
    return technical_indicator_strategy_service()


@app.route('/technical_indicator_backtest', methods=["GET", "POST"])
def technical_indicator_backtest():
    return technical_indicator_backtest_service()


@app.route('/technical_indicator_probtest', methods=["GET", "POST"])
def technical_indicator_probtest():
    return technical_indicator_probtest_service()


@app.route('/technical_indicator_plot/<test>/<ticker_strings>')
def technical_indicator_plot(test, ticker_strings):
    return technical_indicator_plot_service(test, ticker_strings)


## BEGIN{Keltner Channel Strategy}
@app.route('/keltner_channel_strategy')
@login_required
def keltner_channel_strategy():
    return keltner_channel_strategy_service()


@app.route('/keltner_build_model')
@login_required
def keltner_build_model():
    return keltner_build_model_service(global_param_dict)


@app.route('/plot/keltner_backtest_plot')
def keltner_back_test_plot():
    return keltner_backtest_plot_service(global_param_dict)


# Prediction-based portfolio optimization
@app.route('/Predict_based_optmize')
@login_required
def optimization_portfolio():
    return predict_based_optimize_service()


@app.route('/PB_Opt_date_choose', methods=["GET", "POST"])
@login_required
def pre_opt_choose():
    return pb_opt_date_choose_service(global_param_dict)


@app.route('/PB_Opt_build')
@login_required
def pre_opt_build(end_date=None):
    return pb_opt_build_service(end_date, global_param_dict)


@app.route('/PB_Opt_backtest')
@login_required
def pre_opt_back_test():
    return pb_opt_backtest_service(global_param_dict)


@app.route('/plot/pre_opt_backtest_plot')
def pre_opt_backtest_plot():
    return pb_opt_backtest_plot_service(global_param_dict)


# Bitcoin Algorithm Trading
@app.route('/btc_introduction')
def btc_introduction():
    """
    This function map to the first webpage and render the html file.
    """
    return btc_introduction_service()


@app.route('/btc_build/<algorithm>')
def btc_build_algorithm(algorithm):
    """
    This function map to the logic of build an algorithm model and generate signal data for later backtest.
    :param algorithm: the algorithm name
    """
    return btc_build_service(request, algorithm, global_param_dict)


@app.route('/btc_backtest')
def btc_backtest():
    """
    This function map to the logic of backtest and will generate relevant matrix and render the webpage.
    """
    return btc_backtest_service(request, global_param_dict)


# Twitter Sentiment Analysis, in short: tsa, eg. tsa_introduction
@app.route('/tsa_introduction')
def tsa_introduction():
    return tsa_introduction_service()   


@app.route('/tsa_builder', methods=["GET", "POST"])
def tsa_builder():
    return tsa_builder_service()   


@app.route('/tsa_viewer', methods=["GET", "POST"])
def tsa_viewer():
    return tsa_viewer_service() 

# Plotting service 
@app.route('/plot/tsa_plot_roc')
def tsa_plot_roc():
    return tsa_plot_roc_service()     



@app.route('/plot/tsa_plot_lab')
def tsa_plot_lab():
    return tsa_plot_lab_service()     



if __name__ == "__main__":
    table_list = ["users", "portfolios", "spy", "transactions"]

    # global parameters
    top_stocks_list = []
    database.create_table(table_list)
    add_admin_user()

    final_df = pd.DataFrame()

    pb_portfolio = None

    df_pb_opt = None

    btc_data = None

    global_param_dict = {"top_stocks_list": top_stocks_list,
                         "final_df": final_df,
                         "pb_portfolio": pb_portfolio,
                         "df_pb_opt": df_pb_opt,
                         "btc_data": btc_data}

    try:
        app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
        if client_config.client_thread.is_alive() is True:
            client_config.client_thread.join()

    except (KeyError, KeyboardInterrupt, SystemExit, RuntimeError, Exception):
        client_config.client_socket.close()
        sys.exit(0)
