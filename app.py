from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
#from werkzeug.security import check_password_hash, generate_password_hash

import time
import os

from utility.helpers import apology, login_required, usd

from market_data.fre_market_data import IEXMarketData
from database.fre_database import FREDatabase
from stat_arb.pair_trading import *

os.environ["IEX_API_KEY"] = "sk_6ced41d910224dd384355b65b085e529"
os.environ["EOD_API_KEY"] = "5ba84ea974ab42.45160048"

# Make sure API key is set
if not os.environ.get("IEX_API_KEY"):
    raise RuntimeError("IEX_API_KEY not set")

if not os.environ.get("EOD_API_KEY"):
    raise RuntimeError("EOD_API_KEY not set")

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

database = FREDatabase()
iex_market_data = IEXMarketData(os.environ.get("IEX_API_KEY"))

@app.route("/")
@login_required
def index():
    portfolio = database.get_portfolio(session['user_id'])
    cash = portfolio['cash']
    total = cash

    length = len(portfolio['symbol'])
    if length > 0:
        for i in range(len(portfolio['symbol'])):
            price, error = iex_market_data.get_price(portfolio['symbol'][i])
            if len(error) > 0:
                return apology(error)
            portfolio['name'][i] = price['name']
            portfolio['price'][i] = usd(price['price'])
            cost = price['price'] * portfolio['shares'][i]
            portfolio['total'][i] = usd(cost)
            total += cost

        return render_template('index.html', dict=portfolio, total=usd(total), cash=usd(cash), length=length)

    else:
        return render_template("index.html", dict=[], total=usd(cash), cash=usd(cash), length=0)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        symbol = request.form.get('symbol')
        if not symbol:
            return apology('Symbol can not be blank.')

        input_shares = request.form.get('shares')
        if not input_shares:
            return apology("Shares cannot be blank.")
        shares = int(input_shares)
        if not shares > 0:
            return apology("Shares must be positive.")

        price = 0.0
        input_price = request.form.get('price')
        if not input_price:
            latest_price, error = iex_market_data.get_price(symbol)
            if len(error) > 0:
                return apology(error)
            price = latest_price['price']
        else:
            price = float(input_price)
            if not price > 0:
                return apology("price must be positive.")

        uid = session['user_id']
        user = database.get_user('', uid)
        cash = user["cash"]

        total = price * shares
        timestamp = time.strftime("%Y/%m/%d %H:%M:%S")

        # ensure that the user can afford the stocks
        if total > cash:
            return apology("Insufficient fund")
        # if the user can afford, update the cash and insert the purchase data into the history table
        else:
            cash = cash - total
            database.create_buy_transaction(uid, cash, symbol, shares, price, timestamp)

        return redirect(url_for("index"))
    else:
        return render_template("buy.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        symbol = request.form.get('symbol')
        if not symbol:
            return apology('Symbol can not be blank.')

        input_shares = request.form.get('shares')
        if not input_shares:
            return apology("Shares cannot be blank.")
        shares = int(input_shares)
        if not shares > 0:
            return apology("Shares must be positive.")

        price = 0.0
        input_price = request.form.get('price')
        if not input_price:
            latest_price, error = iex_market_data.get_price(symbol)
            if len(error) > 0:
                return apology(error)
            price = latest_price['price']
        else:
            price = float(input_price)
            if not price > 0:
                return apology("price must be positive.")

        uid = session['user_id']
        portfolio = database.get_portfolio(session['user_id'], symbol)
        existing_shares = 0
        if len(portfolio['symbol']) == 1 and portfolio['symbol'][0] == symbol:
            existing_shares = portfolio['shares'][0]
        cash = portfolio['cash']

        if shares > existing_shares:
            return apology("No enough shares to sell.")

        updated_shares = existing_shares - shares

        total = price * shares
        new_cash = cash + total
        timestamp = time.strftime("%Y/%m/%d %H:%M:%S")

        database.create_sell_transaction(uid, new_cash, symbol, updated_shares, -shares, price, timestamp)

        return redirect(url_for("index"))
    else:
        return render_template("sell.html")


@app.route("/history")
@login_required
def history():
    uid = session["user_id"]
    transactions = database.get_transaction(uid)
    length = len(transactions['symbol'])
    return render_template("history.html", length=length, dict=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Must provide username", 403)

        elif not request.form.get("password"):
            return apology("Must provide password", 403)

        user = database.get_user(request.form.get("username"), '')
        if len(user['username']) == 0 or not pwd_context.verify(request.form.get("password"), user["hash"]):
            return apology("invalid username and/or password", 403)

        session["user_id"] = user["user_id"]
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        if not request.form.get("username"):
            return apology("Missing username")

        username = request.form.get("username")
        user = database.get_user(username, '')
        if len(user['username']) > 0:
            return apology("This username is already exists")

        if not request.form.get("password"):
            return apology("Missing password!")

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            return apology("Passwords do not match!")
        else:
            encrypted_password = pwd_context.hash(request.form.get("password"))
            database.create_user(user, encrypted_password)

        user = database.get_user(username, '')
        session["user_id"] = user["user_id"]
        return redirect(url_for("index"))

    else:
        return render_template("register.html")


@app.route("/quote", methods=["GET", "POST"])
def get_quote():
    if request.method == 'POST':
        if not request.form.get("symbol"):
            return apology("symbol missing")

        quote, error = iex_market_data.get_quote(request.form.get("symbol"))

        if len(error) > 0:
            return apology("Invalid symbol")
        else:
            return render_template("quote.html", dict=quote)

    else:
        return render_template("get_quote.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


@app.route('/pair_trade_build_model')
@login_required
def build_model():
    build_pair_trading_model()
    #pair_trading_back_testing(k, back_testing_start_date, back_testing_end_date)
    select_stmt = "SELECT * FROM stock_pairs;"
    result_df = database.execute_sql_statement(select_stmt)
    result_df['volatility'] = result_df['volatility'].map('{:.4f}'.format)
    result_df = result_df.transpose()
    list_of_pairs = [result_df[i] for i in result_df]
    return render_template("pair_trade_build_model.html", pair_list=list_of_pairs)


@app.route('/pair_trade_back_test')
@login_required
def model_back_testing():
    pair_trade_back_test(k, back_testing_start_date, back_testing_end_date)
    select_stmt = "SELECT * FROM stock_pairs;"
    result_df = database.execute_sql_statement(select_stmt)
    result_df['volatility'] = result_df['volatility'].map('{:.4f}'.format)
    result_df['profit_loss'] = result_df['profit_loss'].map('${:,.2f}'.format)
    result_df = result_df.transpose()
    list_of_pairs = [result_df[i] for i in result_df]
    return render_template("pair_trade_back_test.html", pair_list=list_of_pairs)


@app.route('/pair_trade_probation_test')
@login_required
def trade_analysis():
    select_stmt = "SELECT symbol1, symbol2, printf(\"$%.2f\", sum(profit_loss)) AS Profit, count(profit_loss) AS Total_Trades, \
                sum(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) AS Profit_Trades, \
                sum(CASE WHEN profit_loss <=0 THEN 1 ELSE 0 END) AS Loss_Trades FROM pair_trades \
                GROUP BY symbol1, symbol2;"
    result_df = database.execute_sql_statement(select_stmt)
    #print(result_df.to_string(index=False))
    result_df = result_df.transpose()
    trade_results = [result_df[i] for i in result_df]
    return render_template("pair_trade_probation_test.html", trade_list=trade_results)


if __name__ == "__main__":
    table_list = ["users", "portfolios", "transactions"]
    database.create_table(table_list)
    app.run()
