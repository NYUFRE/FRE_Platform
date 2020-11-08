from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import Column, ForeignKey, Integer, Float, Numeric, Text, DATETIME, CHAR, String

import pandas as pd


class FREDatabase:
    def __init__(self):
        #path = os.path.dirname(os.path.abspath('fre_database.py'))
        #db = os.path.join(path, 'fre_database.db')
        #self.engine = create_engine('sqlite:///' + 'FRE_Platform\\database\\fre_database.db')
        self.engine = create_engine('sqlite:///fre_database.db')
        self.conn = self.engine.connect()
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)

    def create_table(self, table_list):
        tables = self.metadata.tables.keys()
        for table_name in table_list:
            if table_name == "users" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('user_id', Integer, primary_key=True),
                              Column('username', Text, nullable=False),
                              Column('password', Text, nullable=False),
                              Column('cash', Numeric, nullable=False, server_default='10000.00'),
                              sqlite_autoincrement=True,
                              extend_existing=True)
                table.create(self.engine)

            elif table_name == "portfolios" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('portfolio_id', Integer, primary_key=True),
                              Column('symbol', Text, nullable=False),
                              Column('shares', Integer, nullable=False),
                              Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False),
                              sqlite_autoincrement=True,
                              extend_existing=True)
                table.create(self.engine)

            elif table_name == "transactions" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('transaction_id', Integer, primary_key=True),
                              Column('symbol', Text, nullable=False),
                              Column('price', Numeric, nullable=False),
                              Column('shares', Integer, nullable=False),
                              Column('timestamp', DATETIME, nullable=False),
                              Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False),
                              sqlite_autoincrement=True,
                              extend_existing=True)
                table.create(self.engine)

            elif table_name == "stock_pairs" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('symbol1', String(50), primary_key=True, nullable=False),
                              Column('symbol2', String(50), primary_key=True, nullable=False),
                              Column('price_mean', Float, nullable=False),
                              Column('volatility', Float, nullable=False),
                              Column('profit_loss', Float, nullable=False),
                              extend_existing=True)
                table.create(self.engine)

            elif table_name == "sector_stocks" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('symbol', String(50), primary_key=True, nullable=False),
                              Column('date', String(50), primary_key=True, nullable=False),
                              Column('open', Float, nullable=False),
                              Column('high', Float, nullable=False),
                              Column('low', Float, nullable=False),
                              Column('close', Float, nullable=False),
                              Column('adjusted_close', Float, nullable=False),
                              Column('volume', Integer, nullable=False),
                              extend_existing=True)
                table.create(self.engine)

            elif table_name == "pair_info" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('symbol1', String(50), primary_key=True, nullable=False),
                              Column('symbol2', String(50), primary_key=True, nullable=False),
                              Column('correlation', Float, nullable=False),
                              Column('beta0', Float, nullable=False),
                              Column('beta1_hedgeratio', Float, nullable=False),
                              Column('adf_p_value', Float, nullable=False),
                              Column('res_mean', Float, nullable=False),
                              Column('res_std', Float, nullable=False),
                              extend_existing=True)
                table.create(self.engine)

            elif (table_name == "pair1_stocks" or table_name == "pair2_stocks") and table_name not in tables:
                if table_name == 'pair1_stocks':
                    foreign_key = 'stock_pairs.symbol1'
                else:
                    foreign_key = 'stock_pairs.symbol2'
                table = Table(table_name, self.metadata,
                              Column('symbol', String(50), ForeignKey(foreign_key), primary_key=True, nullable=False),
                              Column('date', String(50), primary_key=True, nullable=False),
                              Column('open', Float, nullable=False),
                              Column('high', Float, nullable=False),
                              Column('low', Float, nullable=False),
                              Column('close', Float, nullable=False),
                              Column('adjusted_close', Float, nullable=False),
                              Column('volume', Integer, nullable=False))
                table.create(self.engine)

            elif table_name == "pair_prices" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('symbol1', String(50), ForeignKey('pair1_stocks.symbol'), primary_key=True, nullable=False),
                              Column('symbol2', String(50), ForeignKey('pair2_stocks.symbol'), primary_key=True, nullable=False),
                              Column('date', String(50), primary_key=True, nullable=False),
                              Column('open1', Float, nullable=False),
                              Column('close1', Float, nullable=False),
                              Column('open2', Float, nullable=False),
                              Column('close2', Float, nullable=False),
                              extend_existing=True)
                table.create(self.engine)

            elif table_name == "pair_trades" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('symbol1', String(50), ForeignKey('pair1_stocks.symbol'), primary_key=True, nullable=False),
                              Column('symbol2', String(50), ForeignKey('pair2_stocks.symbol'), primary_key=True, nullable=False),
                              Column('date', String(50), primary_key=True, nullable=False),
                              Column('open1', Float, nullable=False),
                              Column('close1', Float, nullable=False),
                              Column('open2', Float, nullable=False),
                              Column('close2', Float, nullable=False),
                              Column('qty1', Integer, nullable=False),
                              Column('qty2', Integer, nullable=False),
                              Column('profit_loss', Float, nullable=False),
                              extend_existing=True)
                table.create(self.engine)

            elif table_name == "sp500" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('symbol', String(20), primary_key=True, nullable=False),
                              Column('name', String(20), nullable=False),
                              Column('sector', String(20), ForeignKey('sp500.sector', onupdate="CASCADE", ondelete="CASCADE"), nullable=False),
                              Column('industry', String(20), nullable=False),
                              Column('weight', Float, nullable=False),
                              extend_existing=True)
                table.create(self.engine)

            elif table_name == "sp500_sectors" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('sector', String(20), primary_key=True, nullable=False),
                              Column('equity_pct', Float, nullable=False),
                              Column('category_pct', Float, nullable=False),
                              extend_existing = True)
                table.create(self.engine)

            elif table_name == "fundamentals" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('symbol', String(20), ForeignKey('sp500', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False),
                              Column('pe_ratio', Float),
                              Column('dividend_yield', Float),
                              Column('beta', Float),
                              Column('high_52weeks', Float),
                              Column('low_52weeks', Float),
                              Column('ma_50days', Float),
                              Column('ma_200days', Float),
                              extend_existing=True)
                table.create(self.engine)

            elif (table_name == "spy" or table_name == "us10y" or table_name == "stocks") and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('symbol', String(20), primary_key=True, nullable=False),
                              Column('date', String(20), primary_key=True, nullable=False),
                              Column('open', Float, nullable=False),
                              Column('high', Float, nullable=False),
                              Column('low', Float, nullable=False),
                              Column('close', Float, nullable=False),
                              Column('adjusted_close', Float, nullable=False),
                              Column('volume', Integer, nullable=False),
                              extend_existing=True)
                table.create(self.engine)

            elif table_name == "best_portfolio" and table_name not in tables:
                table = Table(table_name, self.metadata,
                              Column('symbol', String(20), ForeignKey('sp500', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False),
                              Column('name', String(20), nullable=False),
                              Column('sector', String(20), nullable=False),
                              Column('category_pct', Float, nullable=False),
                              Column('open_date', String(20), nullable=False),
                              Column('open_price', Float, nullable=False),
                              Column('close_date', String(20), nullable=False),
                              Column('close_price', Float, nullable=False),
                              Column('shares', Integer, nullable=False),
                              Column('profit_loss', Float, nullable=False),
                              extend_existing=True)
                table.create(self.engine)

    def clear_table(self, table_list):
        conn = self.engine.connect()
        for table_name in table_list:
            table = self.metadata.tables[table_name]
            delete_stmt = table.delete()
            conn.execute(delete_stmt)

    def drop_table(self, table_name):
        sql_stmt = 'Drop Table if exists ' + table_name + ';'
        self.engine.execute(sql_stmt)

    def check_table_empty(self, table_name):
        sql_stmt = 'select count(*) from ' + table_name + ';'
        result_set = self.engine.execute(sql_stmt)
        result = result_set.fetchone()
        if result[0] == 0:
            return True
        else:
            return False

    def execute_sql_statement(self, sql_stmt, change=False):
        if change:
            self.engine.execute(sql_stmt)
        else:
            result_set = self.engine.execute(sql_stmt)
            result_df = pd.DataFrame(result_set.fetchall())
            if not result_df.empty:
                result_df.columns = result_set.keys()
            return result_df

    def get_sp500_symbols(self):
        symbols = []
        result = self.engine.execute("SELECT symbol FROM sp500")
        data = result.fetchall()
        for i in range(len(data)):
            symbols.append(data[i][0])
        return symbols

    def get_sp500_sectors(self):
        sectors = []
        result = self.engine.execute("SELECT sector FROM sp500_sectors")
        data = result.fetchall()
        for i in range(len(data)):
            sectors.append(data[i][0])
        return sectors

    def get_sp500_symbol_map(self):
        sp500_symbol_map = {}
        sectors = self.get_sp500_sectors()
        for sector in sectors:
            sp500_symbol_map[sector] = []

        result = self.engine.execute("SELECT * FROM sp500")
        data = result.fetchall()
        for stock_data in data:
            sp500_symbol_map[stock_data['sector']].append((stock_data['symbol'], stock_data['name']))
        return sp500_symbol_map

    def get_user(self, usr, uid):
        data = []
        user = {'user_id': '', 'username': '', 'password': '', 'cash' : 0.0}

        if len(usr) > 0:
            result = self.engine.execute("SELECT * FROM users WHERE username = :username", username=usr)
            data = result.fetchall()
        elif uid > 0:
            result = self.engine.execute("SELECT * FROM users WHERE user_id = :user_id", user_id=uid)
            data = result.fetchall()

        if len(data) > 0:
            user['user_id'] = data[0]['user_id']
            user['username'] = data[0]['username']
            user['password'] = data[0]['password']
            user['cash'] = data[0]['cash']

        return user

    def create_user(self, user, pwd):
        self.engine.execute("INSERT INTO users (username,password) VALUES (:username,:password)", username=user, password=pwd)

    def get_portfolio(self, uid, symbol=""):
        data = []
        portfolio = {'username': '', 'cash': 0, 'symbol': [], 'name': [], 'shares': [], 'price': [], 'total': []}

        result = self.engine.execute('SELECT * FROM users WHERE user_id=:user_id', user_id=uid)
        data = result.fetchall()
        username = data[0]["username"]
        cash = float(data[0]["cash"])

        if len(symbol) > 0:
            result = self.engine.execute('SELECT * FROM portfolios WHERE user_id=:user_id AND symbol=:symbol', user_id=uid, symbol=symbol)
            data = result.fetchall()
        else:
            result = self.engine.execute('SELECT * FROM portfolios WHERE user_id=:user_id', user_id=uid)
            data = result.fetchall()

        for row in data:
            portfolio['symbol'].append(row['symbol'])
            portfolio['shares'].append(row['shares'])
            portfolio['name'].append('')
            portfolio['price'].append(0.0)
            portfolio['total'].append(0.0)

        portfolio['username'] = username
        portfolio['cash'] = cash

        return portfolio

    def get_transaction(self, uid):
        transactions = {'symbol': [], 'price': [], 'shares': [], 'price': [], 'timestamp': []}

        result = self.engine.execute('SELECT * FROM transactions WHERE user_id=:user_id', user_id=uid)
        data = result.fetchall()
        for row in data:
            transactions['symbol'].append(row['symbol'])
            transactions['price'].append(row['price'])
            transactions['shares'].append(row['shares'])
            transactions['timestamp'].append(row['timestamp'])

        return transactions

    def create_buy_transaction(self, uid, cash, symbol, shares, price, timestamp):
        self.engine.execute("UPDATE users SET cash=:cash WHERE user_id=:user_id", cash=cash, user_id=uid)

        self.engine.execute("INSERT INTO transactions (symbol, price, shares, timestamp, user_id) VALUES (:symbol, :price, :shares, :timestamp, :user_id)",
                            symbol=symbol, price=price, shares=shares, timestamp=timestamp, user_id=uid)

        result = self.engine.execute("SELECT * FROM portfolios WHERE user_id=:user_id AND symbol=:symbol", user_id=uid, symbol=symbol)
        data = result.fetchall()
        if len(data) > 0:
            existing_shares = data[0]['shares']
            updated_shares = existing_shares + shares
            self.engine.execute('UPDATE portfolios SET shares=:shares WHERE user_id=:user_id AND symbol=:symbol',
                                user_id=uid, symbol=symbol, shares=updated_shares)

        else:
            self.engine.execute("INSERT INTO portfolios (user_id, shares, symbol) VALUES (:user_id, :shares, :symbol)",
                               user_id=uid, symbol=symbol, shares=shares)

    def create_sell_transaction(self, uid, new_cash, symbol, shares, new_shares, price, timestamp):
        self.engine.execute(
            "INSERT INTO transactions (symbol,shares,price,timestamp,user_id) VALUES (:symbol,:shares,:price,:timestamp,:user_id)",
            symbol=symbol, shares=new_shares, price=price, timestamp=timestamp, user_id=uid)

        if shares == 0:
            self.engine.execute("DELETE FROM portfolios WHERE user_id=:user_id AND symbol=:symbol", symbol=symbol, user_id=uid)
            self.engine.execute("UPDATE users SET cash=:new_cash WHERE user_id=:user_id", user_id=uid, new_cash=new_cash)

        else:
            self.engine.execute("UPDATE portfolios set shares=:shares WHERE user_id=:user_id AND symbol=:symbol",
                                symbol=symbol, user_id=uid, shares=shares)
            self.engine.execute("UPDATE users SET cash=:new_cash WHERE user_id=:user_id", user_id=uid, new_cash=new_cash)
