import time
import warnings

from flask import flash, redirect, url_for, render_template, session, request
from sqlalchemy.exc import SAWarning

from system import database, iex_market_data
from system.services.VaR.VaR_Calculator import VaR
from system.services.utility.helpers import usd

warnings.simplefilter(action='ignore', category=SAWarning)


def buy_service():
    if database.check_table_exists('risk_threshold'):
        # Warning if exceeded risk threshold
        ### Get threshold
        threshold_db = database.execute_sql_statement("SELECT * FROM risk_threshold")

        if len(threshold_db):
            threshold_db = database.execute_sql_statement("SELECT * FROM risk_threshold").to_dict('r')[0]
            ### Calculate
            portfolio = database.get_portfolio(session['user_id'])
            prices = []
            errors = []
            for i in range(len(portfolio['symbol'])):
                prices.append(0)
                errors.append(0)
                prices[i], errors[i] = iex_market_data.get_price(portfolio['symbol'][i])
            port_var_obj = VaR(int(threshold_db['confidence_threshold']), int(threshold_db['period_threshold']), prices)
            port_var_value, _, _ = port_var_obj.caviar_AS()
            print(f"port_var {port_var_value} threshold {float(threshold_db['var_threshold'])}")
            if port_var_value < -float(threshold_db['var_threshold']):
                flash(f"VaR={-port_var_value}% is currently exceeding threshold={float(threshold_db['var_threshold'])}%. Please reduce your position!")

    if request.method == "POST":
        symbol = request.form.get('symbol').upper()
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