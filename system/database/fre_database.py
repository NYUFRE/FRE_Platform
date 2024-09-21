import pandas as pd
from sqlalchemy import ForeignKey, Integer, Numeric, Text, DATETIME, CHAR, String, DATE, VARCHAR, BLOB, BOOLEAN
from sqlalchemy import create_engine, MetaData, text, inspect
from sqlalchemy import Table, Column
from typing import Collection, List, Dict, Union

class FREDatabase:
    def __init__(self, database_uri='sqlite:///instance/fre_database.db'):
        self.engine = create_engine(database_uri)
        self.conn = self.engine.connect()
        self.conn.execute(text("PRAGMA foreign_keys = ON"))

        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)

    def _ddl(self, table_name: str) -> Table:
        if table_name == "users":
            table = Table(table_name, self.metadata,
                          Column('user_id', Integer, primary_key=True),
                          Column('email', VARCHAR, unique=True, nullable=False),
                          Column('first_name', VARCHAR, nullable=False),
                          Column('last_name', VARCHAR, nullable=False),
                          Column('_password', BLOB, nullable=False),
                          Column('authenticated', BOOLEAN, default=False),
                          Column('email_confirmed', BOOLEAN, nullable=True, default=False),
                          Column('email_confirmed_on', DATETIME, nullable=True),
                          Column('registered_on', DATETIME, nullable=True),
                          Column('last_logged_in', DATETIME, nullable=True),
                          Column('current_logged_in', DATETIME, nullable=True),
                          Column('role', VARCHAR, default='user'),
                          Column('cash', Numeric, nullable=False, server_default='10000.00'),
                          sqlite_autoincrement=True,
                          extend_existing=True)

        elif table_name == "portfolios":
            table = Table(table_name, self.metadata,
                          Column('portfolio_id', Integer, primary_key=True),
                          Column('symbol', Text, nullable=False),
                          Column('shares', Integer, nullable=False),
                          Column('avg_cost', Numeric, nullable=True),
                          Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False),
                          sqlite_autoincrement=True,
                          extend_existing=True)

        elif table_name == "transactions":
            table = Table(table_name, self.metadata,
                          Column('transaction_id', Integer, primary_key=True),
                          Column('symbol', Text, nullable=False),
                          Column('price', Numeric, nullable=False),
                          Column('shares', Integer, nullable=False),
                          Column('timestamp', DATETIME, nullable=False),
                          Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False),
                          sqlite_autoincrement=True,
                          extend_existing=True)

        elif table_name == "stock_pairs":
            table = Table(table_name, self.metadata,
                          Column('symbol1', String(50), primary_key=True, nullable=False),
                          Column('symbol2', String(50), primary_key=True, nullable=False),
                          Column('price_mean', Numeric, nullable=False),
                          Column('volatility', Numeric, nullable=False),
                          Column('profit_loss', Numeric, nullable=False),
                          extend_existing=True)

        elif table_name == "sector_stocks":
            table = Table(table_name, self.metadata,
                          Column('symbol', String(50), primary_key=True, nullable=False),
                          Column('date', DATE, primary_key=True, nullable=False),
                          Column('open', Numeric, nullable=False),
                          Column('high', Numeric, nullable=False),
                          Column('low', Numeric, nullable=False),
                          Column('close', Numeric, nullable=False),
                          Column('adjusted_close', Numeric, nullable=False),
                          Column('volume', Integer, nullable=False),
                          extend_existing=True)

        elif table_name == "pair_info":
            table = Table(table_name, self.metadata,
                          Column('symbol1', String(50), primary_key=True, nullable=False),
                          Column('symbol2', String(50), primary_key=True, nullable=False),
                          Column('correlation', Numeric, nullable=False),
                          Column('beta0', Numeric, nullable=False),
                          Column('beta1_hedgeratio', Numeric, nullable=False),
                          Column('adf_p_value', Numeric, nullable=False),
                          Column('res_mean', Numeric, nullable=False),
                          Column('res_std', Numeric, nullable=False),
                          extend_existing=True)


        elif (table_name == "pair1_stocks" or table_name == "pair2_stocks"):
            if table_name == 'pair1_stocks':
                foreign_key = 'stock_pairs.symbol1'
            else:
                foreign_key = 'stock_pairs.symbol2'
            table = Table(table_name, self.metadata,
                          Column('symbol', String(50), ForeignKey(foreign_key), primary_key=True, nullable=False),
                          Column('date', DATE, primary_key=True, nullable=False),
                          Column('open', Numeric, nullable=False),
                          Column('high', Numeric, nullable=False),
                          Column('low', Numeric, nullable=False),
                          Column('close', Numeric, nullable=False),
                          Column('adjusted_close', Numeric, nullable=False),
                          Column('volume', Integer, nullable=False))


        elif table_name == "pair_prices":
            table = Table(table_name, self.metadata,
                          Column('symbol1', String(50), ForeignKey('pair1_stocks.symbol'), primary_key=True,
                                 nullable=False),
                          Column('symbol2', String(50), ForeignKey('pair2_stocks.symbol'), primary_key=True,
                                 nullable=False),
                          Column('date', DATE, primary_key=True, nullable=False),
                          Column('open1', Numeric, nullable=False),
                          Column('close1', Numeric, nullable=False),
                          Column('open2', Numeric, nullable=False),
                          Column('close2', Numeric, nullable=False),
                          extend_existing=True)


        elif table_name == "pair_trades":
            table = Table(table_name, self.metadata,
                          Column('symbol1', String(50), ForeignKey('pair1_stocks.symbol'), primary_key=True,
                                 nullable=False),
                          Column('symbol2', String(50), ForeignKey('pair2_stocks.symbol'), primary_key=True,
                                 nullable=False),
                          Column('date', DATE, primary_key=True, nullable=False),
                          Column('open1', Numeric, nullable=False),
                          Column('close1', Numeric, nullable=False),
                          Column('open2', Numeric, nullable=False),
                          Column('close2', Numeric, nullable=False),
                          Column('qty1', Integer, nullable=False),
                          Column('qty2', Integer, nullable=False),
                          Column('profit_loss', Numeric, nullable=False),
                          extend_existing=True)

        elif table_name == "sp500":
            table = Table(table_name, self.metadata,
                          Column('symbol', String(20), primary_key=True, nullable=False),
                          Column('name', String(20), nullable=False),
                          Column('sector', String(20),
                                 ForeignKey('sp500.sector', onupdate="CASCADE", ondelete="CASCADE"),
                                 nullable=False),
                          Column('industry', String(20), nullable=False),
                          Column('weight', Numeric, nullable=False),
                          extend_existing=True)

        elif table_name == "sp500_sectors":
            table = Table(table_name, self.metadata,
                          Column('sector', String(20), primary_key=True, nullable=False),
                          Column('equity_pct', Numeric, nullable=False),
                          Column('category_pct', Numeric, nullable=False),
                          extend_existing=True)

        elif table_name == "fundamentals":

            table = Table(table_name, self.metadata,
                          Column('symbol', String(20), ForeignKey('sp500', onupdate="CASCADE", ondelete="CASCADE"),
                                 primary_key=True, nullable=False),
                          Column('pe_ratio', Numeric),
                          Column('dividend_yield', Numeric),
                          Column('beta', Numeric),
                          Column('high_52weeks', Numeric),
                          Column('low_52weeks', Numeric),
                          Column('ma_50days', Numeric),
                          Column('ma_200days', Numeric),
                          Column('market_capitalization', Numeric),
                          extend_existing=True)

        elif table_name == "spy" or table_name == "us10y" or table_name == "stocks" or table_name == "stocks_price" or \
                table_name == "stocks_price_current" or table_name == "btc_data":
            table = Table(table_name, self.metadata,
                          Column('symbol', String(20), primary_key=True, nullable=False),
                          Column('date', DATE, primary_key=True, nullable=False),
                          Column('open', Numeric, nullable=False),
                          Column('high', Numeric, nullable=False),
                          Column('low', Numeric, nullable=False),
                          Column('close', Numeric, nullable=False),
                          Column('adjusted_close', Numeric, nullable=False),
                          Column('volume', Integer, nullable=False),
                          extend_existing=True)

        elif table_name == "bonds_price" or table_name == "bonds_price_current":
            table = Table(table_name, self.metadata,
                          Column('symbol', String(20), primary_key=True, nullable=False),
                          Column('date', DATE, primary_key=True, nullable=False),
                          Column('open', Numeric, nullable=False),
                          Column('high', Numeric, nullable=False),
                          Column('low', Numeric, nullable=False),
                          Column('close', Numeric, nullable=False),
                          Column('adjusted_close', Numeric, nullable=False),
                          Column('volume', Integer, nullable=False),
                          extend_existing=True)

        elif table_name == "best_portfolio":
            table = Table(table_name, self.metadata,
                          Column('symbol', String(20), ForeignKey('sp500', onupdate="CASCADE", ondelete="CASCADE"),
                                 primary_key=True, nullable=False),
                          Column('name', String(20), nullable=False),
                          Column('sector', String(20), nullable=False),
                          Column('category_pct', Numeric, nullable=False),
                          Column('open_date', DATE, nullable=False),
                          Column('open_price', Numeric, nullable=False),
                          Column('close_date', DATE, nullable=False),
                          Column('close_price', Numeric, nullable=False),
                          Column('shares', Integer, nullable=False),
                          Column('profit_loss', Numeric, nullable=False),
                          extend_existing=True)

        elif table_name == "optimal_portfolio":
            table = Table(table_name, self.metadata,
                          Column('symbol', String(20), primary_key=True, nullable=False),
                          Column('name', String(20), nullable=False),
                          Column('weights', Numeric, nullable=False),
                          )

        elif table_name == "earnings_calendar":
            table = Table(table_name, self.metadata,
                          Column('symbol', String(20), primary_key=True, nullable=False),
                          Column('date', DATE, primary_key=True, nullable=False),
                          Column('surprise', Numeric, nullable=False),
                          extend_existing=True)

        elif table_name == "risk_threshold":
            table = Table(table_name, self.metadata,
                          Column('Placeholder', String(20)))

        elif table_name == "saved_bond":
            table = Table(table_name, self.metadata,
                          Column('alias', String(20), primary_key=True, nullable=False),
                          Column('symbol', String(20), primary_key=True, nullable=False),
                          Column('coupon', Numeric, nullable=False),
                          Column('ytm', Numeric, nullable=False),
                          Column('fullprice', Numeric, nullable=False),
                          Column('accruedinterest', Numeric, nullable=False),
                          Column('flatprice', Numeric, nullable=False),
                          Column('maturity_date', String(20), nullable=False),
                          Column('frequency', String(20), nullable=False),
                          Column('savedate', DATE, nullable=False),
                          Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False),
                          sqlite_autoincrement=True,
                          extend_existing=True)

        elif table_name == "saved_bond_ptfl":
            table = Table(table_name, self.metadata,
                          Column('alias', String(20), primary_key=True, nullable=False),
                          Column('mb', String(20), ForeignKey('saved_bond.alias'), nullable=False),
                          Column('hb1', String(20), ForeignKey('saved_bond.alias'), nullable=False),
                          Column('hb2', String(20), ForeignKey('saved_bond.alias'), nullable=False),
                          Column('w0', String(20), nullable=False),
                          Column('w1', String(20), nullable=False),
                          Column('w2', String(20), nullable=False),
                          Column('mb_action',  String(20), nullable=False),
                          Column('h_action', String(20), nullable=False),
                          Column('mb_fullprice', Numeric, nullable=False),
                          Column('hb1_fullprice', Numeric, nullable=False),
                          Column('hb2_fullprice', Numeric, nullable=False),Column('mb_fullprice', Numeric, nullable=False),
                          Column('mb_mv', Numeric, nullable=False),
                          Column('hb1_mv', Numeric, nullable=False),
                          Column('hb2_mv', Numeric, nullable=False),
                          Column('mb_fv', Numeric, nullable=False),
                          Column('hb1_fv', Numeric, nullable=False),
                          Column('hb2_fv', Numeric, nullable=False),
                          Column('savedate', DATE, nullable=False),
                          Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False),
                          sqlite_autoincrement=True,
                          extend_existing=True)

        else:
            raise ValueError("Table name not known")
        return table


    def create_table(self, table_list: Collection[str]) -> None:
        """
        This function is for creating all kinds of tables if that table not exists in database.
        :param table_list: a list of string of table names
        :return: None
        """
        tables = self.metadata.tables.keys()
        for table_name in table_list:
            if table_name not in tables:
                if table_name == "fundamentals" and "sp500" not in tables:
                    self._ddl("sp500").create(self.engine)
                tbl = self._ddl(table_name)
                tbl.create(self.engine)

    def clear_table(self, table_list):
        conn = self.engine.connect()
        for table_name in table_list:
            table = self.metadata.tables[table_name]
            delete_stmt = table.delete()
            conn.execute(delete_stmt)
            conn.commit()

    def drop_table(self, table_name):
        sql_stmt = text('Drop Table if exists ' + table_name + ';')
        with self.engine.connect() as conn:
            conn.execute(sql_stmt)

    def check_table_exists(self, table_name: str) -> bool:
        ins = inspect(self.engine)
        ret = ins.dialect.has_table(self.engine.connect(), table_name)
        return ret
    
    def check_table_empty(self, table_name: str) -> bool:
        """
        Returns True if the table is empty, returns false if the table is not empty
        """
        sql_stmt = text(f'SELECT COUNT(*) FROM "{table_name}";')
        with self.engine.connect() as conn:
            result_set = conn.execute(sql_stmt)
            result = result_set.fetchone()
            if result[0] == 0:
                return True
            else:
                return False

    def execute_sql_statement(self, stmt, change=False):
        with self.engine.connect() as conn:
            if change:
                conn.execute(stmt)
            else:
                sql_stmt = text(stmt)
                result_set = conn.execute(sql_stmt)
                result_df = pd.DataFrame(result_set.fetchall())
                if not result_df.empty:
                    result_df.columns = result_set.keys()
                return result_df

    def get_sp500_symbols(self):
        symbols = []
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT symbol FROM sp500"))
            data = result.fetchall()
            for i in range(len(data)):
                symbols.append(data[i][0])
        return symbols

    def get_sp500_sectors(self):
        sectors = []
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT sector FROM sp500_sectors"))
            data = result.fetchall()
            for i in range(len(data)):
                sectors.append(data[i][0])
        return sectors

    def get_sp500_symbol_map(self):
        sp500_symbol_map = {}
        sectors = self.get_sp500_sectors()
        for sector in sectors:
            sp500_symbol_map[sector] = []

        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM sp500"))
            data = result.mappings().all()  # The content of table formatted as list of dictionary
            for stock_data in data:
                # An data quality issue was found, a SP500 stock did not belong to any SP500 industry
                # The issue is recorded as issue #126
                # The fix is to check the sector for a stock before adding into map
                if stock_data['sector'] in sectors:
                    sp500_symbol_map[stock_data['sector']].append((stock_data['symbol'], stock_data['name']))
        return sp500_symbol_map

    def get_user(self, email_address: str, uid: int) -> Dict[str, Union[int, float, str]]:
        data = []
        user = {'user_id': '', 'cash': 0.0, 'last_name': '', 'first_name': '', 'email': ''}

        if len(email_address) > 0:
            value = {'email_address':email_address}
            with self.engine.connect() as conn:
                stmt = text("SELECT user_id, cash, last_name, first_name, email FROM users WHERE email = :email_address")
                result = conn.execute(stmt, value)
                data = result.fetchall()
        elif uid > 0:
            with self.engine.connect() as conn:
                value = {'uid': uid}
                stmt = text("SELECT user_id, cash, last_name, first_name, email FROM users WHERE user_id = :uid")
                result = conn.execute(stmt, value)
                data = result.fetchall()

        # TODO! Improve the logic for getting users
        if len(data) > 0:
            user['user_id'] = data[0][0] # user_id
            user['cash'] = data[0][1]  # cash'
            user['last_name'] = data[0][2] # last_name
            user['first_name'] = data[0][3] # first_name
            user['email'] = data[0][4] # email_address

        return user

    def get_portfolio(self, uid: int, symbol_: str = "") -> Dict[str, Union[List[float], List[str], str, float]]:
        """
        Get portfolio info or position info(if symbol is provided)
        :param uid: user id
        :param symbol_: stock symbol
        :return: Portfolio (or symbol's position) info in a dictionary
        """
        data = []
        portfolio = {'email': '', 'cash': 0.0, 'symbol': [], 'name': [], 'shares': [],
                     'price': [], 'avg_cost': [], 'total': [], 'pnl': [], 'proportion': []}

        with self.engine.connect() as conn:
            value = {'uid': uid}
            stmt = text("SELECT user_id, cash, last_name, first_name, email FROM users WHERE user_id = :uid")
            result = conn.execute(stmt, value)
            data = result.fetchall()
            if len(data) == 0:
                return portfolio

            email = data[0]['email']
            username = data[0]['first_name'] + ' ' + data[0]['last_name']
            cash = float(data[0]['cash'])

            # if symbol is provided, select the info on that stock position
            if len(symbol_) > 0:
                value = {'symbol_': symbol_, 'uid': uid}
                stmt = text("SELECT symbol, shares, avg_cost FROM portfolios WHERE user_id = :uid AND symbol = :symbol_")
                result = conn.execute(stmt, value)
                data = result.fetchall()
            # if no symbol is provided, select the entire portfolio info
            else:
                value = {'uid': uid}
                stmt = text("SELECT symbol, shares, avg_cost FROM portfolios WHERE user_id = :uid")
                result = conn.execute(stmt, value)
                data = result.fetchall()
                # no record: only cash
                if len(data) == 0:
                    portfolio['cash'] = cash
                    return portfolio

                for row in data:
                    portfolio['symbol'].append(row['symbol'])
                    portfolio['shares'].append(row['shares'])
                    portfolio['avg_cost'].append(row['avg_cost'])
                    portfolio['name'].append('')
                    portfolio['price'].append(0.0)
                    portfolio['pnl'].append(0.0)
                    portfolio['total'].append(0.0)
                    portfolio['proportion'].append(0.0)

            portfolio['email'] = email
            portfolio['username'] = username
            portfolio['cash'] = cash

            print(portfolio['symbol'])
            print('---')
            print(portfolio['shares'])

        return portfolio

    def get_transaction(self, uid: int) -> Dict[str, Union[List[str], List[float], List[int]]]:
        """
        Extract the transaction record from transactions table
        :param uid: user id
        :return: Transaction info in a dictionary
        """
        transactions = {'symbol': [], 'price': [], 'shares': [], 'timestamp': []}
        with self.engine.connect() as conn:
            value = {'uid': uid}
            stmt = text("SELECT symbol, price, shares, timestamp FROM transactions WHERE user_id = :uid")
            result = conn.execute(stmt, value)
            data = result.fetchall()
            for row in data:
                transactions['symbol'].append(row['symbol'])
                transactions['price'].append(row['price'])
                transactions['shares'].append(row['shares'])
                transactions['timestamp'].append(row['timestamp'])
        return transactions

    def get_bonds_suggest(self, keyword: str, month: str, year: str):
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT DISTINCT Name from bond_list where Name LIKE 'keyword%' AND Name LIKE '%monthyear' ORDER BY Name ASC"))
            data = result.fetchall()
            bond_names = []
            for row in data:
                bond_names.append(row['Name'])
        return bond_names

    def get_bond_cusip(self, name: str):
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT Code from bond_list where Name = name"))
            data = result.fetchall()
            return data[0]['Code']

    def save_bond(self, uid_, alias_: str, symbol_: str, coupon_: float, ytm_: float, fullprice_: float,
                  accruedinterest_: float, flatprice_: float, maturdate_: str, freq_: str, saveddate_: str):
        with self.engine.connect() as conn:
            check_existed = conn.execute(text("SELECT alias from saved_bond where alias = alias_ AND user_id = uid_"))
            data = check_existed.fetchall()
            if data:
                return True

            conn.execute(text(f"INSERT INTO saved_bond (alias, symbol, coupon, ytm, fullprice, accruedinterest, flatprice, maturity_date, frequency, savedate, user_id) "
                            f"VALUES (alias_, symbol_, coupon_, ytm_, fullprice_, accruedinterest_, flatprice_, maturdate_, freq_, saveddate_, uid_)"))
            return False

    def save_bond_ptfl(self, uid_, alias_: str, mb_: str, hb1_: str, hb2_: str, w0_: str, w1_: str, w2_: str,
                       mb_action_: str, h_action_: str, mb_fullprice_: float, hb1_fullprice_: float, hb2_fullprice_: float,
                       mb_mv_: float, hb1_mv_: float, hb2_mv_: float, mb_fv_: float, hb1_fv_: float, hb2_fv_: float,
                       saveddate_: str):
        with self.engine.connect() as conn:
            check_existed = conn.execute(text(f"SELECT alias from saved_bond_ptfl where alias = alias_ AND user_id = uid_"))
            data = check_existed.fetchall()
            if data:
                return True

            conn.execute(text(f"INSERT INTO saved_bond_ptfl (alias, mb, hb1, hb2, w0, w1, w2, mb_action, h_action, mb_fullprice, hb1_fullprice, hb2_fullprice, mb_mv, hb1_mv, hb2_mv, mb_fv, hb1_fv, hb2_fv,savedate,user_id) "
                            f"VALUES (alias_, mb_, hb1_, hb2_, w0_, w1_, w2_,mb_action_, h_action_, mb_fullprice_, hb1_fullprice_, hb2_fullprice_, mb_mv_, hb1_mv_, hb2_mv_,mb_fv_,hb1_fv_,hb2_fv_, saveddate_, uid_)"))
            return False

    def get_saved_bonds(self, uid):
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT alias, symbol from saved_bond where user_id = uid ORDER BY savedate DESC"))
            data = result.fetchall()
            return data

    def get_saved_bond_ptfls(self, uid):
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT alias, mb, hb1, hb2 from saved_bond_ptfl where user_id = uid ORDER BY savedate DESC"))
            data = result.fetchall()
            return data

    def get_bond_ptfl_via_alias(self, uid, alias_: str):
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT * from saved_bond_ptfl where user_id = uid and alias = alias_"))
            data = result.fetchall()[0]
            return data

    def get_bond_via_alias(self, uid, alias_: str):
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT symbol, coupon, ytm, flatprice, maturity_date, frequency from saved_bond where alias = alias_ AND user_id = uid"))
            data = result.fetchall()[0]
            return data['symbol'], data['coupon'], data['ytm'], data['flatprice'], data['maturity_date'], data['frequency'],

    def create_buy_transaction(self, uid_, cash_, symbol_, shares_, price_, timestamp_):
        """
        Record the buying transaction info into database
        :param uid_: user idß
        :param cash_: new cash after buying
        :param symbol_: stock ticker
        :param shares_: shares to buy
        :param price_: price to buy at
        :param timestamp_: when the transaction happens
        :return: None
        """
        # Update the cash
        with self.engine.connect() as conn:
            conn.execute(text(f"UPDATE users SET cash = cash_ WHERE user_id = uid_"))

        # Insert the buying record into transactions table
        self.engine.connect().execute(text(f"INSERT INTO transactions (symbol, price, shares, timestamp, user_id) "
                            f"VALUES (symbol_, price_, shares_, timestamp_, uid_)"))

        # Check position and cost
        result = self.engine.connect().execute(text(f"SELECT shares, avg_cost FROM portfolios WHERE user_id = uid_ AND symbol = symbol_"))
        data = result.fetchall()
        # When holding same stock
        if len(data) > 0:
            existing_shares = data[0]['shares']
            # Add new shares to the existing position
            updated_shares = existing_shares + shares_
            if updated_shares == 0:
                self.engine.connect().execute(text(f"DELETE FROM portfolios WHERE user_id = uid_ AND symbol = symbol_"))
            else:
                # calculate avg cost
                existing_cost = data[0]['avg_cost']
                updated_cost = (existing_cost * existing_shares + price_ * shares_) / updated_shares
                self.engine.connect().execute(text(f"UPDATE portfolios SET shares = updated_shares, avg_cost = updated_cost WHERE user_id = uid_ AND symbol = symbol_"))
        # Without holding the stock
        else:
            self.engine.connect().execute(text(f"INSERT INTO portfolios (user_id, shares, symbol, avg_cost) "
                                f"VALUES (uid_, shares_, symbol_,price_)"))

    def create_sell_transaction(self, uid_, new_cash_, symbol_, shares_, new_shares_, price_, timestamp_):
        """
        Record the selling transaction info into database.
        :param uid_: user id
        :param new_cash_: cash after selling
        :param symbol_: stock ticker
        :param shares_: shares holding after selling
        :param new_shares_: negative, shares to sell
        :param price_: price to sell at
        :param timestamp_: when the transaction happens
        :return: None
        """
        # Insert the selling record into transactions table
        self.engine.connect().execute(text(f"INSERT INTO transactions (symbol,shares,price,timestamp,user_id) "
                            f"VALUES (symbol_,new_shares_,price_,timestamp_,uid_)"))
        # If selling all holding on certain stock, delete the record in portfolio and update the cash
        if shares_ == 0:
            self.engine.connect().execute(text(f"DELETE FROM portfolios WHERE user_id = uid_ AND symbol = symbol_"))
            self.engine.connect().execute(text(f"UPDATE users SET cash = new_cash_ WHERE user_id = uid_"))
        # Still remain some holding position in the account, update the portfolios table also the cash
        else:
            self.engine.connect().execute(text(f"UPDATE portfolios set shares = shares_ WHERE user_id = uid_ AND symbol = symbol_"))
            self.engine.connect().execute(text(f"UPDATE users SET cash = new_cash_ WHERE user_id = uid_"))

    def create_short_transaction(self, uid_, new_cash_, symbol_, shares_, new_shares_, price_, timestamp_):
        """
        Record the selling transaction info into database.
        :param uid_: user id
        :param new_cash_: cash after selling
        :param symbol_: stock ticker
        :param shares_: shares holding after selling
        :param new_shares_: negative, shares to sell
        :param price_: price to sell at
        :param timestamp_: when the transaction happens
        :return: None
        """
        # Insert the selling record into transactions table
        self.engine.connect().execute(text(f"INSERT INTO transactions (symbol,shares,price,timestamp,user_id) "
                            f"VALUES (symbol_,new_shares_,price_,timestamp_,uid_)"))

        # Check position and cost
        result = self.engine.connect().execute(
            text(f"SELECT shares, avg_cost FROM portfolios WHERE user_id = uid_ AND symbol = symbol_"))
        data = result.fetchall()
        # When holding same stock
        if len(data) > 0:
            existing_shares = data[0]['shares']
            # calculate avg cost
            existing_cost = data[0]['avg_cost']
            updated_cost = (existing_cost * existing_shares + price_ * new_shares_) / shares_
            self.engine.connect().execute(text(f"UPDATE portfolios SET shares = shares_, avg_cost = updated_cost "
                                f"WHERE user_id = uid_ AND symbol = symbol_"))
            self.engine.connect().execute(text(f"UPDATE users SET cash = new_cash_ WHERE user_id = uid_"))
        # Without holding the stock
        else:
            self.engine.connect().execute(text(f"INSERT INTO portfolios (user_id, shares, symbol, avg_cost) "
                                f"VALUES (uid_, shares_, symbol_,price_)"))
            self.engine.connect().execute(text(f"UPDATE users SET cash = new_cash_ WHERE user_id = uid_"))

    def create_earnings_calendar(self, symbol, date, surprise):
        self.engine.connect().execute(text(f"INSERT INTO earnings_calendar "
                            f"VALUES (symbol, date, surprise)"))
