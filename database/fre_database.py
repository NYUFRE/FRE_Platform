from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import Column, ForeignKey, Integer, Float, Numeric, Text, DATETIME, CHAR


class FREDatabase:
    def __init__(self):
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
                              Column('hash', Text, nullable=False),
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
                              Column('side', CHAR, nullable=False),
                              Column('timestamp', DATETIME, nullable=False),
                              Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False),
                              sqlite_autoincrement=True,
                              extend_existing=True)
                table.create(self.engine)

    def get_user(self, usr, uid):
        data = []
        user = {'user_id': '', 'username': '', 'hash': '', 'cash' : 0.0}

        if len(usr) > 0:
            result = self.engine.execute("SELECT * FROM users WHERE username = :username", username=usr)
            data = result.fetchall()
        elif uid > 0:
            result = self.engine.execute("SELECT * FROM users WHERE user_id = :user_id", user_id=uid)
            data = result.fetchall()

        user['user_id'] = data[0]['user_id']
        user['username'] = data[0]['username']
        user['hash'] = data[0]['hash']
        user['cash'] = data[0]['cash']
        return user

    def create_user(self, user, pwd):
        self.engine.execute("INSERT INTO users (username,hash) values(:username,:password)", username=user, password=pwd)

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
            self.engine.execute('UPDATE portfolios SET shares=:shares where user_id=:user_id AND symbol=:symbol',
                                user_id=uid, symbol=symbol, shares=updated_shares)

        else:
            self.engine.execute("INSERT INTO portfolios (user_id, shares, symbol) values (:user_id, :shares, :symbol)",
                               user_id=uid, symbol=symbol, shares=shares)

    def create_sell_transaction(self, uid, new_cash, symbol, shares, new_shares, price, timestamp):
        self.engine.execute(
            "INSERT INTO transactions (symbol,shares,price,timestamp,user_id)values (:symbol,:shares,:price,:timestamp,:user_id)",
            symbol=symbol, shares=new_shares, price=price, timestamp=timestamp, user_id=uid)

        if shares == 0:
            self.engine.execute("DELETE FROM portfolios WHERE user_id=:user_id AND symbol=:symbol", symbol=symbol, user_id=uid)
            self.engine.execute("UPDATE users SET cash=:new_cash WHERE user_id=:user_id", user_id=uid, new_cash=new_cash)

        else:
            self.engine.execute("UPDATE portfolios set shares=:shares WHERE user_id=:user_id AND symbol=:symbol",
                                symbol=symbol, user_id=uid, shares=shares)
            self.engine.execute("UPDATE users SET cash=:new_cash WHERE user_id=:user_id", user_id=uid, new_cash=new_cash)
