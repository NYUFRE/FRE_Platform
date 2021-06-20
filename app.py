#################
#### imports ####
#################

from datetime import datetime, timedelta
import os
import socket
import subprocess
import sys
import threading
import time
import json
import matplotlib.pyplot as plt
import base64
import plotly
import plotly.express as px
import plotly.graph_objs as go
from sys import platform
import io

import numpy as np
import pandas_market_calendars as mcal

from flask import flash, abort, redirect, url_for, render_template, session, make_response, request
from flask_login import login_user, current_user, logout_user
from itsdangerous import URLSafeTimedSerializer
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy.exc import IntegrityError, SAWarning

import warnings
warnings.simplefilter(action='ignore', category=SAWarning)

from system import app, db, bcrypt, database, iex_market_data, eod_market_data, process_list
from system.ai_modeling.ga_portfolio_back_test import ga_back_test
from system.ai_modeling.ga_portfolio_probation_test import ga_probation_test
from system.ai_modeling.ga_portfolio_select import build_ga_model, start_date, end_date
from system.portfolio.forms import RegisterForm, LoginForm, EmailForm, PasswordForm
from system.portfolio.models import User
from system.portfolio.users import send_confirmation_email, send_password_reset_email, add_admin_user
from system.sim_trading.client import client_config, client_receive, send_msg, set_event, server_down, \
    wait_for_an_event, join_trading_network, quit_connection

from system.ai_modeling.ga_portfolio import Stock, ProbationTestTrade
from system.ai_modeling.ga_portfolio_select import build_ga_model, start_date, end_date
from system.ai_modeling.ga_portfolio_back_test import ga_back_test, ga_back_test_result
from system.ai_modeling.ga_portfolio_probation_test import ga_probation_test
from system.sim_trading.network import PacketTypes, Packet

from system.stat_arb.pair_trading import build_pair_trading_model, pair_trade_back_test, pair_trade_probation_test
from system.utility.config import trading_queue, trading_event
from system.utility.helpers import error_page, login_required, usd, get_python_pid


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
    form = RegisterForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                new_user = User(form.email.data, form.first_name.data, form.last_name.data, form.password.data)
                new_user.authenticated = True
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                send_confirmation_email(new_user.email)
                flash('Thanks for registering!  Please check your email to confirm your email address.', 'success')
                return redirect(url_for('login'))
            except IntegrityError:
                db.session.rollback()
                flash('ERROR! Email ({}) already exists.'.format(form.email.data), 'error')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    This function is for user to login FRE platform.\n
    :return: login.html
    """
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None and user.is_correct_password(form.password.data):
                user.authenticated = True
                user.last_logged_in = user.current_logged_in
                user.current_logged_in = datetime.now()
                db.session.add(user)
                db.session.commit()
                login_user(user)
                user = database.get_user(request.form.get("email"), '')
                session["user_id"] = user["user_id"]
                client_config.client_id = user['first_name']
                return redirect(url_for('index'))
            else:
                flash('ERROR! Incorrect login credentials.', 'error')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    flash('Goodbye!', 'info')
    session.clear()
    client_config.done_pair_model = "pointer-events:none;color:grey;"
    return redirect(url_for('login'))


@app.route("/")
@login_required
def index():
    # List the python processes before launching the server
    # Window env

    process_list.update(get_python_pid())
    return render_template('index.html')


@app.route("/portfolio")
@login_required
def portfolio():
    # List the python processes before launching the server
    # Window env

    # Get portfolio data from database
    portfolio = database.get_portfolio(session['user_id'])

    cash = portfolio['cash']
    total = cash

    length = len(portfolio['symbol'])

    # Initializing Chart
    labels = ['Cash']
    sizes = [1.0]

    # When holding stocks
    if length > 0:
        for i in range(len(portfolio['symbol'])):
            # Get the latest price for each holding stocks
            price, error = iex_market_data.get_price(portfolio['symbol'][i])
            if len(error) > 0:
                return error_page(error)
            portfolio['name'][i] = price['name']
            portfolio['price'][i] = price['price']
            portfolio['pnl'][i] = (price['price'] - portfolio['avg_cost'][i]) * portfolio['shares'][i]
            cost = price['price'] * portfolio['shares'][i]
            portfolio['total'][i] = cost
            total += cost
        # Calculate proportion
        for i in range(len(portfolio['symbol'])):
            portfolio['proportion'][i] = "{:.2%}".format(portfolio['total'][i] / total)
        cash_proportion = "{:.2%}".format(cash / total)

        # Pie Chart Plot
        labels = portfolio['symbol'] + ['Cash']
        sizes = portfolio['proportion'] + [cash_proportion]
        sizes = [float(num[:-1]) for num in sizes]
        graph_values = [{'labels': labels, 'values': sizes, 'type': 'pie', 'textinfo': 'label+percent',
                         'insidetextfont': {'color': '#FFFFFF', 'size': '14'},
                         'textfont': {'color': '#FFFFFF', 'size': '14'},
                         'hole': '.6', 'marker': {'colors': px.colors.qualitative.Bold}}]
        layout = {'title': '<b>Portfolio Holdings</b>'}

        # PnL Bar_plot
        trace2 = go.Bar(x=portfolio['symbol'], y=portfolio['pnl'], marker={'color': px.colors.qualitative.Bold},
                        width=0.5, opacity=0.85, text=portfolio['pnl'], textposition='auto', texttemplate='%{text:.2f}')
        layout2 = dict(title="<b>Portfolio Unrealized PnL</b>", xaxis=dict(title="Symbol"), yaxis=dict(title="PnL"), )
        pnl_plot = [trace2]
        fig = go.Figure(data=pnl_plot, layout=layout2)
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('portfolio.html', dict=portfolio, total=usd(total), cash=usd(cash),
                               cash_proportion=cash_proportion, length=length, graph_values=graph_values, layout=layout,
                               graphJSON=graphJSON)

    # Only cash
    else:
        # Method 2 with plotly
        graph_values = [{
            'labels': labels,
            'values': sizes,
            'type': 'pie',
            'textinfo': 'label+percent',
            'insidetextfont': {'color': '#FFFFFF',
                               'size': '14'},
            'textfont': {'color': '#FFFFFF',
                         'size': '14'},
            'hole': '.6',
            'marker': {'colors': px.colors.qualitative.Bold}
        }]
        layout = {'title': '<b>Portfolio Holdings</b>'}
        return render_template("portfolio.html", dict=[], total=usd(cash), cash=usd(cash), cash_proportion="100%",
                               length=0, graph_values=graph_values, layout=layout)


@app.route("/quote", methods=["GET", "POST"])
def get_quote():
    if request.method == 'POST':
        if not request.form.get("symbol"):
            flash('ERROR! symbol missing.', 'error')
            return render_template("get_quote.html")

        # Get quote data from IEX, quoted prices (Ask & Bid) are different from the latest price
        quote, error = iex_market_data.get_quote(request.form.get("symbol"))
        price, error = iex_market_data.get_price(request.form.get("symbol"))

        if len(error) > 0 or len(price) == 0 or len(quote) == 0:
            flash('ERROR! Invalid symbol.', 'error')
            return render_template("get_quote.html")
        else:
            quote['Latest Price'] = price['price']
            return render_template("quote.html", dict=quote)

    else:
        return render_template("get_quote.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        symbol = request.form.get('symbol')
        if not symbol:
            flash('ERROR! Symbol can not be blank.', 'error')
            return render_template("buy.html")

        input_shares = request.form.get('shares')
        if not input_shares:
            flash('ERROR! Shares cannot be blank.', 'error')
            return render_template("buy.html")

        shares = int(input_shares)
        if not shares > 0:
            flash('ERROR! Shares must be positive.', 'error')
            return render_template("buy.html")

        # Get quote ask price -> potential buy price
        quote, error = iex_market_data.get_quote(symbol)
        if len(error) > 0:
            flash('ERROR! ' + error, 'error')
            return render_template("buy.html")
        best_ask = quote["askPrice"]
        # When best ask is not positive, cannot buy in
        if not best_ask > 0 or not quote["askSize"] > 0:
            flash('Order Rejected! No Selling Orders in the Market Now. Please Try Later.', 'error')
            return render_template("buy.html")
        # Partial Fill
        if quote["askSize"] < shares:
            shares = quote["askSize"]
            flash(f'Only {shares} share(s) of {symbol} available to buy from the market.', 'Notice')
        price = 0.0
        input_price = request.form.get('price')
        # When no input price -> Market order
        if not input_price:
            price = quote["askPrice"]
        # When input price exists
        else:
            price = float(input_price)
            if not price > 0:
                flash('ERROR! Price must be positive.', 'error')
                return render_template("buy.html")
            # When input price is lower than best ask, prompt out info
            if price < best_ask:
                flash(f'Order Rejected! Your price is lower than the best Offer price at {usd(best_ask)}', 'error')
                return render_template("buy.html")
            # When input price is higher than best ask, prompt out info and buy at best ask
            if price >= best_ask:
                flash(f'Order Executed. Your price is higher than the best Ask price at {usd(best_ask)}.'
                      f'Now you bought {shares} share(s) of {symbol} at {usd(best_ask)}.', 'Notice')
                price = best_ask
        uid = session['user_id']
        user = database.get_user('', uid)
        cash = user["cash"]

        total = price * shares
        timestamp = time.strftime("%Y/%m/%d %H:%M:%S")

        # ensure that the user has sufficient fund
        if total > cash:
            flash('ERROR! Insufficient fund.', 'error')
            return render_template("buy.html")

        # update the cash balance
        else:
            cash = cash - total
            # Record this buying trade in DB
            database.create_buy_transaction(uid, cash, symbol, shares, price, timestamp)

        # When finish buying -> redirect the page to "Portfolio" page
        return redirect(url_for("portfolio"))
    else:
        return render_template("buy.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        symbol = request.form.get('symbol')
        if not symbol:
            flash('ERROR! Symbol can not be blank.', 'error')
            return render_template("sell.html")

        input_shares = request.form.get('shares')
        if not input_shares:
            flash('ERROR! Shares can not be blank.', 'error')
            return render_template("sell.html")

        shares = int(input_shares)
        if not shares > 0:
            flash('ERROR! Shares must be positive.', 'error')
            return render_template("sell.html")
        # Get position info
        portfolio = database.get_portfolio(session['user_id'], symbol)
        existing_shares = 0
        if len(portfolio['symbol']) == 1 and portfolio['symbol'][0] == symbol:
            existing_shares = portfolio['shares'][0]
        else:
            flash('ERROR! Stock not in your portfolio.', 'error')
            return render_template("sell.html")

        cash = portfolio['cash']

        if shares > existing_shares:
            flash('ERROR! No enough shares to sell.', 'error')
            return render_template("sell.html")

        # Get quote bid price -> potential sell price
        quote, error = iex_market_data.get_quote(symbol)
        if len(error) > 0:
            flash('ERROR! ' + error, 'error')
            return render_template("sell.html")
        best_bid = quote["bidPrice"]
        # When best bid is not positive, cannot sell to others
        if not best_bid > 0 or not quote["bidSize"] > 0:
            flash('Order Rejected! No Buying Orders in the Market Now. Please Try Later.', 'error')
            return render_template("sell.html")
        # Partial Fill
        if quote["bidSize"] < shares:
            shares = quote["bidSize"]
            flash(f'Only {shares} share(s) of {symbol} available to sell to the market.', 'Notice')
        price = 0.0
        input_price = request.form.get('price')
        # Market order, Use the best bid price as selling price
        if not input_price:
            price = quote["bidPrice"]
        # Sell at input price
        else:
            price = float(input_price)
            if not price > 0:
                flash('ERROR! Price must be positive.', 'error')
                return render_template("sell.html")
            # When input price is higher than best bid, prompt out info
            if price > best_bid:
                flash(f'Order Rejected! Your price is higher than the best Bid price at {usd(best_bid)}.', 'error')
                return render_template("sell.html")
            # When input price is lower than best bid, prompt out info and sell at best bid
            if price <= best_bid:
                flash(f'Order Executed. Your price is lower than the best Bid price at {usd(best_bid)}.'
                      f'Now you sold {shares} share(s) of {symbol} at {usd(best_bid)}.', 'Notice')
                price = best_bid
        uid = session['user_id']

        updated_shares = existing_shares - shares

        total = price * shares
        new_cash = cash + total
        timestamp = time.strftime("%Y/%m/%d %H:%M:%S")
        # Record this selling trade in DB:
        database.create_sell_transaction(uid, new_cash, symbol, updated_shares, -shares, price, timestamp)
        # When finish buying -> redirect the page to "Portfolio" page
        return redirect(url_for("portfolio"))
    else:
        return render_template("sell.html")

@app.route("/short", methods=["GET", "POST"])
@login_required
def short():
    if request.method == "POST":
        symbol = request.form.get('symbol')
        if not symbol:
            flash('ERROR! Symbol can not be blank.', 'error')
            return render_template("short.html")

        input_shares = request.form.get('shares')
        if not input_shares:
            flash('ERROR! Shares can not be blank.', 'error')
            return render_template("short.html")

        shares = int(input_shares)
        if not shares > 0:
            flash('ERROR! Shares must be positive.', 'error')
            return render_template("short.html")
        # Get position info
        portfolio = database.get_portfolio(session['user_id'], symbol)
        existing_shares = 0
        if len(portfolio['symbol']) == 1 and portfolio['symbol'][0] == symbol:
            existing_shares = portfolio['shares'][0]

        # If user is holding long position of the stock, then he cannot short that stock
        if existing_shares > 0:
            flash("Order Rejected! You cannot hold both short and long position of the same stock!")
            return render_template("short.html")

        cash = portfolio['cash']
        threshold = cash/4

        # Get quote bid price -> potential sell price
        quote, error = iex_market_data.get_quote(symbol)
        if len(error) > 0:
            flash('ERROR! ' + error, 'error')
            return render_template("short.html")
        best_bid = quote["bidPrice"]

        # if the total short price is more than 1/4 of the total cash, then reject the short
        if threshold <= shares * best_bid:
            flash('Order Rejected! Your cash is below the threshold. Please make sure you have enough cash.', 'error')
            return render_template("short.html")

        # When best bid is not positive, cannot sell to others
        if not best_bid > 0 or not quote["bidSize"] > 0:
            flash('Order Rejected! No Buying Orders in the Market Now. Please Try Later.', 'error')
            return render_template("short.html")
        # Partial Fill
        if quote["bidSize"] < shares:
            shares = quote["bidSize"]
            flash(f'Only {shares} share(s) of {symbol} available to sell to the market.', 'Notice')
        price = 0.0
        input_price = request.form.get('price')
        # Market order, Use the best bid price as selling price
        if not input_price:
            price = quote["bidPrice"]
        # Sell at input price
        else:
            price = float(input_price)
            if not price > 0:
                flash('ERROR! Price must be positive.', 'error')
                return render_template("short.html")
            # When input price is higher than best bid, prompt out info
            if price > best_bid:
                flash(f'Order Rejected! Your price is higher than the best Bid price at {usd(best_bid)}.', 'error')
                return render_template("short.html")
            # When input price is lower than best bid, prompt out info and sell at best bid
            if price <= best_bid:
                flash(f'Order Executed. Your price is lower than the best Bid price at {usd(best_bid)}.'
                      f'Now you sold {shares} share(s) of {symbol} at {usd(best_bid)}.', 'Notice')
                price = best_bid
        uid = session['user_id']

        updated_shares = existing_shares - shares

        total = price * shares
        new_cash = cash + total
        timestamp = time.strftime("%Y/%m/%d %H:%M:%S")
        # Record this short trade in DB:
        database.create_short_transaction(uid, new_cash, symbol, updated_shares, -shares, price, timestamp)
        # When finish shorting -> redirect the page to "Portfolio" page
        return redirect(url_for("portfolio"))
    else:
        return render_template("short.html")

@app.route("/history")
@login_required
def history():
    uid = session["user_id"]
    # Extract transaction record from transactions table
    transactions = database.get_transaction(uid)
    length = len(transactions['symbol'])
    return render_template("history.html", length=length, dict=transactions)


@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = confirm_serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
    except:
        flash('The confirmation link is invalid or has expired.', 'error')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()

    if user.email_confirmed:
        flash('Account already confirmed. Please login.', 'info')
    else:
        user.email_confirmed = True
        user.email_confirmed_on = datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('Thank you for confirming your email address!')

        login_user(user)
        user = database.get_user(email, '')
        session["user_id"] = user["user_id"]
        client_config.client_id = user['first_name']

    return redirect(url_for('index'))


@app.route('/reset', methods=["GET", "POST"])
def reset():
    form = EmailForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first_or_404()
        except:
            flash('Invalid email address!', 'error')
            return render_template('password_reset_email.html', form=form)

        if user.email_confirmed:
            send_password_reset_email(user.email)
            flash('Please check your email for a password reset link.', 'success')
        else:
            flash('Your email address must be confirmed before attempting a password reset.', 'error')
        return redirect(url_for('login'))

    return render_template('password_reset_email.html', form=form)


@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))

    form = PasswordForm()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=email).first_or_404()
        except IntegrityError:
            flash('Invalid email address!', 'error')
            return redirect(url_for('login'))

        user._password = bcrypt.generate_password_hash(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password_with_token.html', form=form, token=token)


@app.route('/user_profile')
@login_required
def user_profile():
    return render_template('user_profile.html')


@app.route('/email_change', methods=["GET", "POST"])
@login_required
def email_change():
    form = EmailForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                user_check = User.query.filter_by(email=form.email.data).first()
                if user_check is None:
                    user = current_user
                    user.email = form.email.data
                    user.email_confirmed = False
                    user.email_confirmed_on = None
                    user.email_confirmation_sent_on = datetime.now()
                    db.session.add(user)
                    db.session.commit()
                    send_confirmation_email(user.email)
                    flash('Email changed!  Please confirm your new email address (link sent to new email).', 'success')
                    return redirect(url_for('user_profile'))
                else:
                    flash('Sorry, that email already exists!', 'error')
            except IntegrityError:
                flash('Error! That email already exists!', 'error')
    return render_template('email_change.html', form=form)


@app.route('/password_change', methods=["GET", "POST"])
@login_required
def user_password_change():
    form = PasswordForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = current_user
            user._password = bcrypt.generate_password_hash(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Password has been updated!', 'success')
            return redirect(url_for('user_profile'))

    return render_template('password_change.html', form=form)


@app.route('/resend_confirmation')
@login_required
def resend_email_confirmation():
    try:
        send_confirmation_email(current_user.email)
        flash('Email sent to confirm your email address.  Please check your email!', 'success')
    except IntegrityError:
        flash('Error!  Unable to send email to confirm your email address.', 'error')

    return redirect(url_for('user_profile'))


@app.route('/admin_view_users')
@login_required
def admin_view_users():
    if current_user.role != 'admin':
        abort(403)
    else:
        users = User.query.order_by(User.id).all()
        return render_template('admin_view_users.html', users=users)
    return redirect(url_for('user_profile'))


# Statistical Arbitrage
@app.route('/pair_trading')
@login_required
def pair_trading():
    return render_template("pair_trading.html", done_pair_trade_model=client_config.done_pair_model)


@app.route('/pair_trade_build_model_param', methods=['POST', 'GET'])
@login_required
def build_model():
    if request.method == 'POST':
        select_stmt = "SELECT DISTINCT sector FROM sp500;"
        result_df = database.execute_sql_statement(select_stmt)
        sector_list = list(result_df['sector'])

        form_input = request.form
        corr_threshold = form_input['Corr Threshold']
        adf_threshold = form_input['P Threshold']
        pair_trading_start_date = form_input['Start Date']
        pair_trading_end_date = form_input['End Date']
        sector = form_input['Sector']

        if not (corr_threshold and adf_threshold and pair_trading_end_date and pair_trading_start_date and sector):
            flash('Error!  Incorrect Values!', 'error')
            return render_template("pair_trade_build_model_param.html", sector_list=sector_list, done_pair_trade_model=client_config.done_pair_model)

        if float(corr_threshold) >= 1 or float(corr_threshold) <= - 1:
            flash('Error!  Incorrect Correlation Threshold!', 'error')
            return render_template("pair_trade_build_model_param.html", sector_list=sector_list, done_pair_trade_model=client_config.done_pair_model)

        if float(adf_threshold) >= 1 or float(adf_threshold) <= 0:
            flash('Error! Incorrect P Value Threshold!', 'error')
            return render_template("pair_trade_build_model_param.html", sector_list=sector_list, done_pair_trade_model=client_config.done_pair_model)

        if datetime.strptime(pair_trading_end_date, "%Y-%m-%d") > datetime.now():
            flash('Error! Incorrect End Date! Should not be later than today!', 'error')
            return render_template("pair_trade_build_model_param.html", sector_list=sector_list, done_pair_trade_model=client_config.done_pair_model)

        least_start_date = datetime.strptime(pair_trading_end_date, "%Y-%m-%d") - timedelta(365)
        if least_start_date < datetime.strptime(pair_trading_start_date, "%Y-%m-%d"):
            flash('Error! Incorrect Date Range! At least one year data is needed, such as ' +
                  f'{least_start_date.strftime("%Y-%m-%d")} ' + ' to ' +
                  f'{datetime.strptime(pair_trading_end_date, "%Y-%m-%d").strftime("%Y-%m-%d")}', 'error')
            return render_template("pair_trade_build_model_param.html",
                                   sector_list=sector_list, done_pair_trade_model=client_config.done_pair_model)

        trading_calendar = mcal.get_calendar('NYSE')
        latest_trading_date = trading_calendar.schedule(
            start_date=datetime.strptime(pair_trading_start_date, "%Y-%m-%d"),
            end_date=datetime.strptime(pair_trading_end_date, "%Y-%m-%d")).index.strftime("%Y-%m-%d").tolist()[-1]

        max_db_date = database.execute_sql_statement("SELECT MAX(date) AS max FROM stocks;")["max"][0]
        if datetime.strptime(latest_trading_date, "%Y-%m-%d") > datetime.strptime(max_db_date, "%Y-%m-%d"):
            flash("Warning! There is not enough data in database. Should go to MarketData page and update first!")
            return render_template("pair_trade_build_model_param.html",
                                   sector_list=sector_list, done_pair_trade_model=client_config.done_pair_model)

        back_testing_start_date = (datetime.strptime(pair_trading_start_date, "%Y-%m-%d") +
                                   timedelta(270)).strftime("%Y-%m-%d")
        back_testing_end_date = (datetime.strptime(pair_trading_start_date, "%Y-%m-%d") +
                                 timedelta(330)).strftime("%Y-%m-%d")

        client_config.pair_trading_start_date = pair_trading_start_date
        client_config.pair_trading_end_date = pair_trading_end_date
        client_config.back_testing_start_date = back_testing_start_date
        client_config.back_testing_end_date = back_testing_end_date

        error = build_pair_trading_model(corr_threshold, adf_threshold,
                                         sector, pair_trading_start_date,
                                         back_testing_start_date, pair_trading_end_date)
        if len(error) > 0:
            flash("Warning! " + error + " Select different Corr Threshold and P Threshold!")
            return render_template("pair_trade_build_model_param.html", sector_list=sector_list,
                                   done_pair_trade_model=client_config.done_pair_model)

        select_stmt = "SELECT * FROM stock_pairs;"
        result_df = database.execute_sql_statement(select_stmt)
        result_df['price_mean'] = result_df['price_mean'].map('{:.4f}'.format)
        result_df['volatility'] = result_df['volatility'].map('{:.4f}'.format)
        result_df = result_df.transpose()
        list_of_pairs = [result_df[i] for i in result_df]
        client_config.done_pair_model = "pointer-events:auto"
        return render_template("pair_trade_build_model.html", pair_list=list_of_pairs)
    else:
        select_stmt = "SELECT DISTINCT sector FROM sp500;"
        result_df = database.execute_sql_statement(select_stmt)
        sector_list = list(result_df['sector'])
        return render_template("pair_trade_build_model_param.html", sector_list=sector_list, done_pair_trade_model=client_config.done_pair_model)


@app.route('/pair_trade_back_test')
@login_required
def model_back_testing():
    back_testing_start_date = client_config.back_testing_start_date
    back_testing_end_date = client_config.back_testing_end_date
    pair_trade_back_test(back_testing_start_date, back_testing_end_date)

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
    return render_template("pair_trade_back_test_result.html", trade_list=trade_results, total=usd(total))


@app.route('/pair_trade_probation_test', methods=['POST', 'GET'])
@login_required
def model_probation_testing():
    if request.method == 'POST':

        form_input = request.form
        probation_testing_start_date = form_input['Start Date']
        probation_testing_end_date = form_input['End Date']
        pair_trading_end_date = client_config.pair_trading_end_date
        back_testing_end_date = client_config.back_testing_end_date

        if (not probation_testing_end_date) or (not probation_testing_start_date):
            flash('Error! Start or End Date missing!', 'error')
            return render_template("pair_trade_probation_test.html", back_testing_end_date = back_testing_end_date)

        if datetime.strptime(probation_testing_start_date, "%Y-%m-%d") >= datetime.strptime(probation_testing_end_date,"%Y-%m-%d"):
            flash('Error!  Start Date should be before End Date!', 'error')
            return render_template("pair_trade_probation_test.html", back_testing_end_date=back_testing_end_date)

        if datetime.strptime(probation_testing_end_date, "%Y-%m-%d") > datetime.strptime(pair_trading_end_date, "%Y-%m-%d"):
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
        return render_template("pair_trade_probation_test.html", back_testing_end_date = back_testing_end_date)


# AI modeling
@app.route('/ai_modeling')
@login_required
def ai_trading():
    return render_template("ai_modeling.html")


@app.route('/ai_build_model')
@login_required
def ai_build_model():
    # database.drop_table('best_portfolio')
    # While drop the table, table name "best_portfolio" still in metadata
    # therefore, everytime only clear table instead of drop it.

    table_list = ['best_portfolio']
    database.create_table(table_list)
    database.clear_table(table_list)
    best_portfolio = build_ga_model(database)
    print("yield: %8.4f%%, beta: %8.4f, daily_volatility:%8.4f%%, expected_daily_return:%8.4f%%" %
          ((best_portfolio.portfolio_yield * 100), best_portfolio.beta, (best_portfolio.volatility * 100),
           (best_portfolio.expected_daily_return * 100)))
    print("trend: %8.4f, sharpe_ratio:%8.4f, score:%8.4f" %
          (best_portfolio.trend, best_portfolio.sharpe_ratio, best_portfolio.score))
    # Show stocks' information of best portfolio
    stocks = []
    for stock in best_portfolio.stocks:
        print(stock)  # (symbol, name, sector,weight)
        stocks.append((stock[1], stock[3], stock[0], str(round(stock[2] * 100, 4))))
    length = len(stocks)
    # Show portfolio's score metrics
    portfolio_yield = str(round(best_portfolio.portfolio_yield * 100, 4)) + '%'
    beta = str(round(best_portfolio.beta, 4))
    volatility = str(round(best_portfolio.volatility * 100, 4)) + '%'
    daily_return = str(round(best_portfolio.expected_daily_return * 100, 4)) + '%'
    trend = str(round(best_portfolio.trend, 4))
    sharpe_ratio = str(round(best_portfolio.sharpe_ratio, 4))
    score = str(round(best_portfolio.score, 4))
    return render_template('ai_best_portfolio.html', stock_list=stocks, portfolio_yield=portfolio_yield,
                           beta=beta, volatility=volatility, daily_return=daily_return, trend=trend,
                           sharpe_ratio=sharpe_ratio, score=score, length=length)


@app.route('/ai_back_test')
@login_required
def ai_back_test():
    best_portfolio, spy = ga_back_test(database)

    # Used for function "ai_back_test_plot"
    ga_back_test_result.bt_start_date = str(spy.price_df.index[0])[:10]
    ga_back_test_result.bt_end_date = str(spy.price_df.index[-1])[:10]
    ga_back_test_result.portfolio_cum_rtn = best_portfolio.portfolio_daily_cumulative_returns.copy()
    ga_back_test_result.spy_cum_rtn = spy.price_df['spy_daily_cumulative_return'].copy()

    portfolio_return = "{:.2f}".format(best_portfolio.cumulative_return * 100, 2)
    spy_return = "{:.2f}".format(spy.cumulative_return * 100, 2)
    return render_template('ai_back_test.html', portfolio_return=portfolio_return, spy_return=spy_return)


@app.route('/plot/ai_back_test_plot')
def ai_back_test_plot():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    n = len(ga_back_test_result.portfolio_cum_rtn)
    line = np.zeros(n)
    axis.plot(ga_back_test_result.portfolio_cum_rtn, 'ro')
    axis.plot(ga_back_test_result.spy_cum_rtn, 'bd')
    axis.plot(ga_back_test_result.portfolio_cum_rtn.index, line, 'b')

    axis.set(xlabel="Date",
             ylabel="Cumulative Returns",
             title=f"Portfolio Back Test ({ga_back_test_result.bt_start_date} to {ga_back_test_result.bt_end_date})")

    axis.text(0.2, 0.9, 'Red - Portfolio, Blue - SPY',
              verticalalignment='center',
              horizontalalignment='center',
              transform=axis.transAxes,
              color='black', fontsize=10)

    axis.grid(True)
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response


@app.route('/ai_probation_test')
@login_required
def ai_probation_test():
    best_portfolio, spy_profit_loss, cash = ga_probation_test(database)
    portfolio_profit = "{:.2f}".format((float(best_portfolio.profit_loss / cash) * 100))
    spy_profit = "{:.2f}".format((float(spy_profit_loss / cash) * 100))
    profit = best_portfolio.profit_loss

    # stock_list = [val[0] for val in best_portfolio.stocks]
    stock_list = []
    for i, stock in enumerate(best_portfolio.stocks):
        stock_obj = Stock()
        stock_obj.symbol = stock[1]
        stock_obj.name = stock[3]
        stock_obj.category_pct = stock[2]
        stock_obj.sector = stock[0]

        probation_obj = ProbationTestTrade()
        probation_obj.open_date = best_portfolio.start_date
        probation_obj.close_date = best_portfolio.end_date
        probation_obj.open_price = best_portfolio.open_prices[i]
        probation_obj.close_price = best_portfolio.close_prices[i]
        probation_obj.shares = best_portfolio.shares[i]
        probation_obj.profit_loss = best_portfolio.pnl[i]

        stock_obj.probation_test_trade = probation_obj
        stock_list.append(stock_obj)

    length = len(stock_list)
    return render_template('ai_probation_test.html', stock_list=stock_list,
                           portfolio_profit=portfolio_profit, spy_profit=spy_profit,
                           profit=usd(profit), length=length)


# Simulated Trading
@app.route('/sim_trading')
@login_required
def sim_trading():
    return render_template("sim_trading.html")


def start_server_process():
    cmd = "( python.exe server.py )" if platform == "win32" else "python server.py"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if client_config.server_tombstone:
            return

        if output and not client_config.server_ready:
            print(output.strip())
            time.sleep(5)
            client_config.server_ready = True


@app.route('/sim_server_up')
@login_required
def sim_server_up():
    if not client_config.server_ready:
        client_config.server_tombstone = False
        server_thread = threading.Thread(target=(start_server_process))
        server_thread.start()

        while not client_config.server_ready:
            pass

    return render_template("sim_launch_server.html")


@app.route('/sim_server_down')
@login_required
def sim_server_down():
    if client_config.server_ready:
        try:
            client_config.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_config.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            status = client_config.client_socket.connect_ex(client_config.ADDR)
            if status != 0:
                #TODO: Per Professor, a better clean-up logic needs to be added here
                print("sim_server_down:", str(status))
                client_config.server_tombstone = True
                client_config.server_ready = False
                #Even though connection to server failed such as return code 10016
                #But set server_tomstone to True should get server stop
                #flash("Failure in server: please restart the program")
                return render_template("sim_server_down.html")

            client_config.receiver_stop = False     #TODO Look like it is not used
            client_config.server_tombstone = True

            client_config.client_receiver = threading.Thread(target=client_receive, args=(trading_queue, trading_event))
            client_config.client_receiver.start()

            set_event(trading_event)
            client_packet = Packet()
            send_msg(server_down(client_packet))
            wait_for_an_event(trading_event)
            msg_type, msg_data = trading_queue.get()
            print(msg_data)
            if msg_type == PacketTypes.SERVER_DOWN_RSP.value:
                time.sleep(2)
                print("Server down confirmed!")
                client_config.client_socket.close()

            existing_py_process = get_python_pid()

            for item in existing_py_process:
                if item not in process_list:
                    os.kill(item, 9)

            client_config.server_ready = False
            client_config.client_thread_started = False

        except(OSError, Exception):
            # TODO Need a Web page to indicate we throw an exception and print full stack.
            client_config.server_ready = False
            client_config.server_tombstone = True
            client_config.client_thread_started = False
            return render_template("sim_server_down.html")

    return render_template("sim_server_down.html")


@app.route('/sim_auto_trading')
@login_required
def sim_auto_trading():
    if client_config.server_ready:
        if not client_config.client_thread_started:
            client_config.client_thread_started = True
            client_config.receiver_stop = False

            client_config.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_config.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            status = client_config.client_socket.connect_ex(client_config.ADDR)
            if status != 0:
                print("sim_auto_trading:", str(status))
                #client_config.client_socket.close()
                flash("Failure in server: please restart the program")
                return render_template("error_auto_trading.html")
            client_config.client_up = True
            client_config.orders = []
            client_packet = Packet()
            msg_data = {}

            client_config.client_receiver = threading.Thread(target=client_receive, args=(trading_queue, trading_event))
            client_config.client_thread = threading.Thread(target=join_trading_network,
                                                           args=(trading_queue, trading_event))

            client_config.client_receiver.start()
            client_config.client_thread.start()

        while not client_config.trade_complete:
            pass

        if client_config.client_up:
            client_config.client_up = False
            client_packet = Packet()
            msg_data = {}
            set_event(trading_event)
            send_msg(quit_connection(client_packet))
            wait_for_an_event(trading_event)
            msg_type, msg_data = trading_queue.get()
            if msg_type != PacketTypes.END_RSP.value:
                client_config.orders.append(msg_data)
                msg_type, msg_data = trading_queue.get()
            trading_queue.task_done()
            print(msg_data)
            client_config.client_thread_started = False
            # client_config.receiver_stop = True
            client_config.trade_complete = False
            client_config.client_socket.close()

        return render_template("sim_auto_trading.html", trading_results=client_config.orders,
                               pnl_results=client_config.ticker_pnl)

    else:
        return render_template("error_auto_trading.html")


@app.route('/sim_model_info')
@login_required
def sim_model_info():
    return render_template("sim_model_info.html")


# Market Data
@app.route('/md_sp500')
@login_required
def market_data_sp500():
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


@app.route('/md_sp500_sectors')
@login_required
def market_data_sp500_sectors():
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


@app.route('/md_spy')
@login_required
def market_data_spy():
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


@app.route('/md_us10y')
@login_required
def market_data_us10y():
    table_list = ['us10y']
    database.create_table(table_list)
    # update the database to today
    today = datetime.today().strftime('%Y-%m-%d')
    if database.check_table_empty('us10y'):
        eod_market_data.populate_stock_data(['US10Y'], "us10y", start_date, today, 'INDX')
    else:
        # if the table is not empty, insert data from the last date in the existing table to today.
        select_stmt = 'SELECT date FROM us10y ORDER BY date DESC limit 1'
        last_date = database.execute_sql_statement(select_stmt)['date'][0]
        begin_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        if begin_date <= today:
            eod_market_data.populate_stock_data(['US10Y'], "us10y", begin_date, today, 'INDX')
    select_stmt = """
    SELECT symbol, date, 
            printf("%.2f", open) as open, 
            printf("%.2f", high) as high, 
            printf("%.2f", low) as low, 
            printf("%.2f", close) as close,
            printf("%.2f", adjusted_close) as adjusted_close 
    FROM us10y ORDER BY date DESC;
    """
    result_df = database.execute_sql_statement(select_stmt)
    result_df = result_df.transpose()
    list_of_us10y = [result_df[i] for i in result_df]
    return render_template("md_us10y.html", us10y_list=list_of_us10y)


@app.route('/md_fundamentals')
@login_required
def market_data_fundamentals():
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


@app.route('/md_stocks', methods=["GET", "POST"])
@login_required
def market_data_stock():
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
    today = datetime.today().strftime('%Y-%m-%d')
    try:

        # fundamentals (use multi-threads,takes 30 seconnds)
        table_list = ['fundamentals']
        database.create_table(table_list)
        database.clear_table(table_list)
        tickers = database.get_sp500_symbols()
        tickers.append('SPY')
        eod_market_data.populate_fundamental_data(tickers, 'US')

        # spy price data
        if database.check_table_empty('spy'):
            # if the table is empty, insert data from start date to today
            eod_market_data.populate_stock_data(['spy'], "spy", start_date, today, 'US')
        else:
            # if the table is not empty, insert data from the last date in the existing table to today.
            select_stmt = 'SELECT date FROM spy ORDER BY date DESC limit 1'
            last_date = database.execute_sql_statement(select_stmt)['date'][0]
            # define begin_date here. The rest updates will use the same begin date
            begin_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime(
                '%Y-%m-%d')  # add one day after the last date in table
            if begin_date <= today:
                eod_market_data.populate_stock_data(['spy'], "spy", begin_date, today, 'US')
        # us10y
        database.create_table(['us10y'])
        if database.check_table_empty('us10y'):
            eod_market_data.populate_stock_data(['US10Y'], "us10y", start_date, today, 'INDX')
        else:
            select_stmt = 'SELECT date FROM us10y ORDER BY date DESC limit 1'
            last_date = database.execute_sql_statement(select_stmt)['date'][0]
            begin_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            if begin_date <= today:
                eod_market_data.populate_stock_data(['US10Y'], "us10y", begin_date, today, 'INDX')

        # stock daily data (use multi-threads,takes 22 seconnds)
        # TODO: try to use batch request from IEX data to further speed up.
        # Get IEX subscription first. https://iexcloud.io/docs/api/#batch-requests
        database.create_table(['stocks'])
        tickers = database.get_sp500_symbols()
        if database.check_table_empty('stocks'):
            # TODO! Use non-multi-threading version for now as EDO data feed has strange behavior after its upgrade
            # eod_market_data.populate_stocks_data_multi(tickers, "stocks", start_date, today, 'US')
            eod_market_data.populate_stock_data(tickers, "stocks", start_date, today, 'US')
        else:
            select_stmt = 'SELECT date FROM stocks ORDER BY date DESC limit 1'
            last_date_stocks = database.execute_sql_statement(select_stmt)['date'][0]
            begin_date_stocks = (datetime.strptime(last_date_stocks, '%Y-%m-%d') + timedelta(days=1)).strftime(
                '%Y-%m-%d')  # add one day after the last date in table
            if begin_date_stocks <= today:
                # TODO! Use non-multi-threading version for now as EDO data feed has strange behavior after its upgrade
                # eod_market_data.populate_stocks_data_multi(tickers, "stocks", begin_date_stocks, today, 'US')
                eod_market_data.populate_stock_data(tickers, "stocks", begin_date_stocks, today, 'US')
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
        flash("Something went wrong when updating the market data :(")

    return render_template("md_update_data.html")


if __name__ == "__main__":
    table_list = ["users", "portfolios", "spy", "transactions"]
    database.create_table(table_list)
    add_admin_user()

    try:
        app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
        if client_config.client_thread.is_alive() is True:
            client_config.client_thread.join()

    except (KeyError, KeyboardInterrupt, SystemExit, RuntimeError, Exception):
        client_config.client_socket.close()
        sys.exit(0)
