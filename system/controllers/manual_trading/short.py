import time
import warnings

from flask import flash, redirect, url_for, render_template, session, request
from sqlalchemy.exc import SAWarning

from system import database, iex_market_data
from system.services.utility.helpers import usd

warnings.simplefilter(action='ignore', category=SAWarning)


def short_service():
    if request.method == "POST":
        symbol = request.form.get('symbol').upper()
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
        threshold = cash / 4

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