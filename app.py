from flask import Flask, redirect, render_template, request, session, url_for, make_response
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
#from werkzeug.security import check_password_hash, generate_password_hash

import time
import os
import subprocess

#from utility.config import client_config, trading_queue, trading_event
from utility.config import *
from utility.helpers import apology, login_required, usd

from market_data.fre_market_data import IEXMarketData
from database.fre_database import FREDatabase
from stat_arb.pair_trading import *
from ai_modeling.ga_portfolio import *
from ai_modeling.ga_portfolio_select import *
from ai_modeling.ga_portfolio_back_test import *
from ai_modeling.ga_portfolio_probation_test import *

from sim_trading.network import PacketTypes, Packet
from sim_trading.client import *
#from sim_trading.server import *

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
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

process_list = []

@app.route("/")
@login_required
def index():

    # List the python processes before launching the server
    # www.geeksforgeeks.org/python-get-list-of-running-processes/
    output = os.popen('wmic process get description, processid').read()
    #print(output)
    target_process = "python"
    for line in output.splitlines():
        line = line.strip()
        if target_process in str(line):
            process_list.append(int(line.split(' ', 1)[1].strip()))

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
    table_list = ["users", "portfolios", "transactions"]
    database.create_table(table_list)

    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Must provide username", 403)

        elif not request.form.get("password"):
            return apology("Must provide password", 403)

        user = database.get_user(request.form.get("username"), '')
        if len(user['username']) == 0 or not pwd_context.verify(request.form.get("password"), user["password"]):
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
    table_list = ["users", "portfolios", "transactions"]
    database.create_table(table_list)

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
            database.create_user(username, encrypted_password)

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


# Statistical Arbitrage
@app.route('/pair_trading')
@login_required
def pair_trading():
    return render_template("pair_trading.html")


@app.route('/pair_trade_build_model')
@login_required
def build_model():
    build_pair_trading_model()
    select_stmt = "SELECT * FROM stock_pairs;"
    result_df = database.execute_sql_statement(select_stmt)
    result_df['price_mean'] = result_df['price_mean'].map('{:.4f}'.format)
    result_df['volatility'] = result_df['volatility'].map('{:.4f}'.format)
    result_df = result_df.transpose()
    list_of_pairs = [result_df[i] for i in result_df]
    return render_template("pair_trade_build_model.html", pair_list=list_of_pairs)


@app.route('/pair_trade_back_test')
@login_required
def model_back_testing():
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


@app.route('/pair_trade_probation_test', methods = ['POST', 'GET'])
@login_required
def model_probation_testing():
    if request.method == 'POST':
        form_input = request.form
        probation_testing_start_date = form_input['Start Date']
        probation_testing_end_date = form_input['End Date']
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
        return render_template("pair_trade_probation_test.html")


# AI modeling
@app.route('/ai_modeling')
@login_required
def ai_trading():
    return render_template("ai_modeling.html")


@app.route('/ai_build_model')
@login_required
def ai_build_model():
    database.drop_table('best_portfolio')
    table_list = ['best_portfolio']
    database.create_table(table_list)
    best_portfolio = build_ga_model(database)
    print("yield: %8.4f%%, beta: %8.4f, daily_volatility:%8.4f%%, expected_daily_return:%8.4f%%" %
          ((best_portfolio.portfolio_yield * 100), best_portfolio.beta, (best_portfolio.volatility * 100),
           (best_portfolio.expected_daily_return * 100)))
    print("trend: %8.4f, sharpe_ratio:%8.4f, score:%8.4f" %
          (best_portfolio.trend, best_portfolio.sharpe_ratio, best_portfolio.score))

    stocks = []
    for stock in best_portfolio.stocks:
        #print(stock.symbol, end=",")
        print(stock.symbol, stock.name, stock.sector, stock.category_pct)
        stocks.append((stock.symbol, stock.name, stock.sector, str(round(stock.category_pct*100, 4))))
    length = len(stocks)
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
    global portfolio_ys, spy_ys, n
    best_portfolio, spy = ga_back_test(database)
    portfolio_ys = list(best_portfolio.portfolio_daily_cumulative_returns.values())
    spy_ys = list(spy.daily_cumulative_returns.values())
    n = len(best_portfolio.portfolio_daily_cumulative_returns.keys())
    portfolio_return = "{:.2f}".format(best_portfolio.cumulative_return * 100, 2)
    spy_return = "{:.2f}".format(spy.cumulative_return * 100, 2)
    return render_template('ai_back_test.html', portfolio_return=portfolio_return, spy_return=spy_return)


@app.route('/plot/ai_back_test_plot')
def ai_back_test_plot():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    line = np.zeros(n)
    t = range(n)
    axis.plot(t, portfolio_ys[0:n], 'ro')
    axis.plot(t, spy_ys[0:n], 'bd')
    axis.plot(t, line, 'b')

    axis.set(xlabel="Date",
           ylabel="Cumulative Returns",
           title="Portfolio Back Test (2020-01-01 to 2020-06-30)",
           xlim=[0, n])

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
    best_portfolio, spy, cash = ga_probation_test(database)
    portfolio_profit = "{:.2f}".format((float(best_portfolio.profit_loss/cash) * 100))
    spy_profit = "{:.2f}".format((float(spy.probation_test_trade.profit_loss/cash) * 100))
    profit = best_portfolio.profit_loss
    length = len(best_portfolio.stocks)
    return render_template('ai_probation_test.html', stock_list=best_portfolio.stocks,
                           portfolio_profit=portfolio_profit, spy_profit=spy_profit,
                           profit=usd(profit), length=length)


# Simulated Trading
@app.route('/sim_trading')
@login_required
def sim_trading():
    return render_template("sim_trading.html")

def start_server_process():
    #cmd = "cd sim_trading"
    cmd = "( python.exe sim_trading/server.py )"
    #FNULL = open(os.devnull, 'w')
    #subprocess.run(["python.exe", "sim_trading/server.py"]) 
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if output and not client_config.server_ready:
            print(output.strip())
            time.sleep(10)
            client_config.server_ready = True

       #eturn_code = process.poll()
       #if return_code is not None:
       #    print('RETURN CODE', return_code)
          
@app.route('/sim_server_up')
@login_required
def sim_server_up():
    '''
    if not server_config.server_thread_started:
        server_config.server_thread_started = True
        server_thread = threading.Thread(target=launch_server())
        server_thread.start()
        return render_template("sim_launch_server.html")
    else:
        return render_template("sim_launch_server.html")
    '''
    server_thread = threading.Thread(target=(start_server_process))
    server_thread.start()
    
    while not client_config.server_ready:
        pass
    
    #server_thread.join()
    
    #cmd = "cd sim_trading"
    #cmd = "( python.exe sim_trading/server.py )"
    #FNULL = open(os.devnull, 'w')
    #subprocess.run(["python.exe", "sim_trading/server.py"]) 
    #process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
    #                           stderr=subprocess.STDOUT,
    #                           universal_newlines=True)
    '''
    while True:
       output = process.stdout.readline()
       print(output.strip())
       if "Server is up" in output:
       #eturn_code = process.poll()
       #if return_code is not None:
       #    print('RETURN CODE', return_code)
           break
    #out, err = result.communicate()
    #out = os.system(cmd)
    #out = subprocess.call(cmd, shell=True)
    '''
    #print(out)
    return render_template("sim_launch_server.html")
    #if len(err) == 0:
    #    return render_template("sim_launch_server.html")
    #else:
    #    apology("Server Failure")

    '''
    # server_config.server_output = open
    server_config.server_output = sys.stderr
    server_config.symbols = get_stock_list()

    # USFederalHolidayCalendar has a bug, GoodFriday is not excluded
    us_bd = CustomBusinessDay(holidays=['2020-04-10'], calendar=USFederalHolidayCalendar())

    lastBusDay = datetime.datetime.today()
    if datetime.date.weekday(lastBusDay) == 5:  # if it's Saturday
        lastBusDay = lastBusDay - datetime.timedelta(days=1)  # then make it Friday
    elif datetime.date.weekday(lastBusDay) == 6:  # if it's Sunday
        lastBusDay = lastBusDay - datetime.timedelta(days=2)  # then make it Friday

    end_date = lastBusDay - datetime.timedelta(days=1)  # day before last trading day

    # end_date = datetime.datetime.today() - datetime.timedelta(days = 1) # yesterday
    start_date = end_date + datetime.timedelta(-server_config.total_market_days)

    server_config.market_periods = pd.DatetimeIndex(
        pd.date_range(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), freq=us_bd)).strftime(
        "%Y-%m-%d").tolist()
    print(server_config.market_periods, file=server_config.server_output)
    server_config.total_market_days = len(server_config.market_periods)  # Update for remove non-trading days

    market_period_objects = pd.DatetimeIndex(pd.date_range(start=start_date.strftime("%Y-%m-%d"),
                                                           end=end_date.replace(hour=23, minute=30).strftime(
                                                               "%Y-%m-%d %H:%M:%S"), freq=us_bd)).tolist()
    # market_period_objects = pd.DatetimeIndex(pd.date_range(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d %H:%M:%S"), freq=us_bd)).tolist()

    for i in range(len(market_period_objects)):
        server_config.market_period_seconds.append(
            int(time.mktime(market_period_objects[i].timetuple())))  # As timestamp is 12am of each day
    server_config.market_period_seconds.append(int(time.mktime(
        market_period_objects[len(market_period_objects) - 1].timetuple())) + 24 * 3600)  # For last day intraday data
    # print(market_period_objects)

    # TODO! probably it is better to harden delete table function and use it here
    database.drop_table(server_config.stock_intraday_data)
    eod_market_data.populate_intraday_stock_data(server_config.symbols, server_config.stock_intraday_data,
                                                 server_config.market_period_seconds[0],
                                                 server_config.market_period_seconds[
                                                     len(server_config.market_period_seconds) - 1])

    stock_market_periods = populate_intraday_order_map(server_config.symbols,
                                                        server_config.stock_intraday_data,
                                                        server_config.market_periods)

    print(server_config.intraday_order_map, file=server_config.server_output)

    print(stock_market_periods, file=server_config.server_output)
    for value in stock_market_periods.values():
        if server_config.total_market_days > len(value):
            server_config.total_market_days = len(value)
            server_config.market_periods = value

    print(server_config.market_periods, file=server_config.server_output)

    # TODO! probably it is better to harden delete table function and use it here
    database.drop_table(server_config.stock_daily_data)
    eod_market_data.populate_stock_data(server_config.symbols,
                                        server_config.stock_daily_data,
                                        server_config.market_periods[0],
                                        server_config.market_periods[len(server_config.market_periods) - 1])

    server_config.server_socket.listen(1)
    print("Waiting for client requests", file=server_config.server_output)
    try:
        scheduler = sched.scheduler(time.time, time.sleep)
        current_time_in_seconds = time.time()
        scheduler_thread = threading.Thread(target=set_market_status, args=(scheduler, current_time_in_seconds))
        # scheduler_thread.setDaemon(True)

        server_thread = threading.Thread(target=accept_incoming_connections, args=(trading_queue,))
        create_market_thread = threading.Thread(target=create_market_interest, args=(server_config.symbols,))
        # server_thread.setDaemon(True)

        scheduler_thread.start()
        server_thread.start()
        create_market_thread.start()

        error = trading_queue.get()
        trading_queue.task_done()
        if error is not None:
            raise error

        #scheduler_thread.join()
        #server_thread.join()

        #server_config.server_socket.close()
        #servr_config.server_output.close()
        #sys.exit(0)

        # order_table_file.close()
        # intrday_order_file.close()

        return render_template("sim_launch_server.html")

    except (KeyError, KeyboardInterrupt, SystemExit, Exception):
        # except (KeyboardInterrupt):
        print("Exception in main\n", file=server_config.server_output)
        server_config.server_socket.close()
        server_config.server_output.close()
        apology("Server Failure")
        sys.exit(0)
    '''


@app.route('/sim_server_down')
@login_required
def sim_server_down():
    try:
        client_config.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_config.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        status = client_config.client_socket.connect_ex(client_config.ADDR)
        if status != 0:
            return apology("Fail in connecting to server")

        client_config.receiver_stop = False
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

        output = os.popen('wmic process get description, processid').read()
        #process = subprocess.Popen(['ps'], stdout=subprocess)
        #output, error = process.communicate()
        #print(output)
        target_process = "python"
        for line in output.splitlines():
            line = line.strip()
            if target_process in str(line):
                pid = int(line.split(' ', 1)[1].strip())
                if pid not in process_list:
                    os.kill(pid, 9)

        client_config.server_ready = False
        client_config.client_thread_started = False
        return render_template("sim_server_down.html")
    except(OSError, Exception):
        return render_template("sim_server_down.html")


@app.route('/sim_auto_trading')
@login_required
def sim_auto_trading():
    if not client_config.client_thread_started:
        client_config.client_thread_started = True
        client_config.receiver_stop = False

        client_config.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_config.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        status = client_config.client_socket.connect_ex(client_config.ADDR)
        if status != 0:
            return apology("Fail in connecting to server")

        client_config.client_up = True
        client_config.orders = []
        client_packet = Packet()
        msg_data = {}

        client_config.client_receiver = threading.Thread(target=client_receive, args=(trading_queue, trading_event))
        client_config.client_thread = threading.Thread(target=join_trading_network, args=(trading_queue, trading_event))

        client_config.client_receiver.start()
        client_config.client_thread.start()

    while not client_config.trade_complete:
        pass

    if client_config.client_up == True:
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
        #client_config.receiver_stop = True
        client_config.trade_complete = False
        client_config.client_socket.close()

        #print(client_config.orders, sep="\n")

    return render_template("sim_auto_trading.html", trading_results=client_config.orders)


@app.route('/sim_adhoc_trading')
@login_required
def sim_adhoc_trading():
    if not client_config.client_socket_connected:
        status = client_config.client_socket.connect_ex(client_config.ADDR)
        if status != 0:
            return apology("Fail in connecting to server")
        else:
            client_config.client_socket_connected = True

    return render_template("sim_adhoc_trading.html")


@app.route('/sim_trading_result', methods=['POST'])
def sim_trading_result():
    if request.method == 'POST':
        form_input = request.form
        client_packet = Packet()

        order_id = request.form.get('OrderId')
        symbol = request.form.get('Symbol')
        side = request.form.get('Side')
        price = request.form.get('Price')
        qty = request.form.get('Quantity')

        order_type = "Mkt"
        if float(price) > 0:
            order_type = "Lmt"

        client_msg = enter_a_new_order(client_packet, order_id, symbol, order_type, side, price, qty)
        print(client_msg)
        send_msg(client_msg)
        data = get_response(trading_queue)
        print(data)
        return render_template("sim_trading_result.html", trading_results=data)

"""
@app.route('/sim_client_down')
@login_required
def sim_client_down():
    client_packet = Packet()
    msg_data = {}

    if client_config.client_thread_started:
        try:
            send_msg(quit_connection(client_packet))
            msg_type, msg_data = trading_queue.get()
            trading_queue.task_done()
            print(msg_data)
            client_config.client_thread_started = False
            client_config.orders = []
            client_config.client_socket.close()
            return render_template("sim_client_down.html", server_response=msg_data)
        except(OSError, Exception):
            print(msg_data)
            client_config.client_thread_started = False
            client_config.orders = []
            client_config.client_socket.close()
            return render_template("sim_client_down.html", server_response=msg_data)
    else:
        return apology("Client was not started")
"""


# Market Data
@app.route('/md_sp500')
@login_required
def market_data_sp500():
    table_list = ['sp500', 'sp500_sectors']
    database.create_table(table_list)
    if database.check_table_empty('sp500'):
        eod_market_data.populate_sp500_data('SPY', 'US')
    select_stmt = 'SELECT symbol, name as company_name, sector, industry, printf("%.2f", weight) as weight FROM sp500 ORDER BY symbol ASC;'
    result_df = database.execute_sql_statement(select_stmt)
    result_df = result_df.transpose()
    list_of_stocks = [result_df[i] for i in result_df]
    return render_template("md_sp500.html", stock_list=list_of_stocks)


@app.route('/md_sp500_sectors')
@login_required
def market_data_sp500_sectors():
    table_list = ['sp500', 'sp500_sectors']
    database.create_table(table_list)
    if database.check_table_empty('sp500_sectors'):
        eod_market_data.populate_sp500_data('SPY', 'US')
    select_stmt = 'SELECT sector as sector_name, printf("%.4f", equity_pct) as equity_pct, printf("%.4f", category_pct) as category_pct FROM sp500_sectors ORDER BY sector ASC;'
    result_df = database.execute_sql_statement(select_stmt)
    result_df = result_df.transpose()
    list_of_sectors = [result_df[i] for i in result_df]
    return render_template("md_sp500_sectors.html", sector_list=list_of_sectors)


@app.route('/md_spy')
@login_required
def market_data_spy():
    table_list = ['spy']
    database.create_table(table_list)
    if database.check_table_empty('spy'):
        eod_market_data.populate_stock_data(['SPY'], "spy", start_date, end_date, 'US')
    select_stmt = 'SELECT symbol, date, printf("%.2f", open) as open, printf("%.2f", high) as high, ' \
                  'printf("%.2f", low) as low, printf("%.2f", close) as close, ' \
                  'printf("%.2f", adjusted_close) as adjusted_close, volume FROM spy ORDER BY date;'
    result_df = database.execute_sql_statement(select_stmt)
    result_df = result_df.transpose()
    list_of_spy = [result_df[i] for i in result_df]
    return render_template("md_spy.html", spy_list=list_of_spy)


@app.route('/md_us10y')
@login_required
def market_data_us10y():
    table_list = ['us10y']
    database.create_table(table_list)
    if database.check_table_empty('us10y'):
        eod_market_data.populate_stock_data(['US10Y'], "us10y", start_date, end_date, 'INDX')
    select_stmt = 'SELECT symbol, date, printf("%.2f", open) as open, printf("%.2f", high) as high, ' \
                  'printf("%.2f", low) as low, printf("%.2f", close) as close, ' \
                  'printf("%.2f", adjusted_close) as adjusted_close FROM us10y ORDER BY date;'
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
    select_stmt = 'SELECT symbol, printf("%.4f", pe_ratio) as pe_ratio, printf("%.4f", dividend_yield) as dividend_yield, ' \
                  'printf("%.4f", beta) as beta, printf("%.2f", high_52weeks) as high_52weeks, printf("%.2f", low_52weeks) as low_52weeks, ' \
                  'printf("%.2f", ma_50days) as ma_50days, printf("%.2f", ma_200days) as ma_200days FROM fundamentals ORDER BY symbol;'
    result_df = database.execute_sql_statement(select_stmt)
    result_df = result_df.transpose()
    list_of_stocks = [result_df[i] for i in result_df]
    return render_template("md_fundamentals.html", stock_list=list_of_stocks)


@app.route('/md_stocks', methods=["GET", "POST"])
@login_required
def market_data_stock():
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

        select_stmt = 'SELECT symbol, date, printf("%.2f", open) as open, printf("%.2f", high) as high, ' \
                      'printf("%.2f", low) as low, printf("%.2f", close) as close, ' \
                      'printf("%.2f", adjusted_close) as adjusted_close, volume FROM stocks ' \
                      'WHERE symbol = \"' + ticker + '\" AND strftime(\'%Y-%m-%d\', date) BETWEEN \"' + date1 + '\" AND \"' + date2 + '\"' + \
                      'ORDER BY date;'
        result_df = database.execute_sql_statement(select_stmt)
        result_df = result_df.transpose()
        list_of_stock = [result_df[i] for i in result_df]
        return render_template("md_stock.html", stock_list=list_of_stock)

    else:
        return render_template("md_get_stock.html")


if __name__ == "__main__":

    table_list = ["users", "portfolios", "transactions"]
    database.create_table(table_list)

    try:
        # client_thread = threading.Thread(target=send, args=(q,))
        #client_thread = threading.Thread(target=join_trading_network, args=(q, e))
        #bClientThreadStarted = False
        #bTradeComplete = False

        app.run(host='127.0.0.1', port=80, debug=False)

        if client_config.client_thread.is_alive() is True:
            client_config.client_thread.join()

    except (KeyError, KeyboardInterrupt, SystemExit, RuntimeError, Exception):
        client_config.client_socket.close()
        sys.exit(0)


