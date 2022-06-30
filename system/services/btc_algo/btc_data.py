from datetime import date, timedelta

from system import database, eod_market_data


class BTCData:
    @staticmethod
    def _need_update():
        last_update_sql = "SELECT date FROM btc_data ORDER BY date DESC LIMIT 1"
        last_update = str(database.execute_sql_statement(last_update_sql).loc[0]["date"])
        if last_update == date.today().strftime("%Y-%m-%d"):
            return False, last_update
        else:
            return True, last_update

    @staticmethod
    def populate_btc_data():
        # no database
        if not database.check_table_exists("btc_data"):
            try:
                database.create_table(["btc_data"])
            except Exception as e:
                print("Error creating btc_data table: ", e)
                return False
            try:
                start_date = "2010-01-01"
                end_date = date.today().strftime("%Y-%m-%d")
                eod_market_data.populate_stock_data(tickers=["BTC-USD"], table_name="btc_data", start_date=start_date,
                                                    end_date=end_date, category="CC")
                return True
            except Exception as e:
                print("Error downloading BTC-USD data")
                return False
        # already has database
        else:
            # if need update
            if BTCData._need_update()[0]:
                print("need update")
                last_update = date.fromisoformat(BTCData._need_update()[1])
                start_date = (last_update + timedelta(days=1)).strftime("%Y-%m-%d")
                end_date = date.today().strftime("%Y-%m-%d")
                eod_market_data.populate_stock_data(tickers=["BTC-USD"], table_name="btc_data", start_date=start_date,
                                                    end_date=end_date, category="CC")
                return True
            # no need update
            else:
                print("no need update")
                return True

    @staticmethod
    def get_btc_data():
        if not BTCData.populate_btc_data():
            return None
        try:
            select_sql = "SELECT date, open, high, low, close, adjusted_close, volume FROM btc_data"
            select_data = database.execute_sql_statement(select_sql)
            print(select_data)
            return select_data
        except Exception as e:
            print("Error getting BTC-USD data: ", e)
            return None
