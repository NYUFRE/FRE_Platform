from datetime import date, timedelta

import pandas as pd
from sklearn.utils import deprecated

from system import database, eod_market_data


class BTCData:
    """
    This class is used to manipulate BTC data from database.
    """
    @staticmethod
    def __need_update() -> tuple:
        """
        This method is used to check if the data needs to be updated.
        :return: A tuple containing whether need to update or not, and time of the last update.
        """
        # get the last update time
        last_update_sql = "SELECT date FROM btc_data ORDER BY date DESC LIMIT 1"
        last_update = str(database.execute_sql_statement(last_update_sql).loc[0]["date"])
        # compare the last update time with yesterday because we cannot access today data
        print("The last update time is: " + last_update)
        print("The newest data time is: ", (date.today() - timedelta(days=1)).strftime("%Y-%m-%d"))
        if last_update == (date.today() - timedelta(days=1)).strftime("%Y-%m-%d"):
            return False, last_update
        else:
            return True, last_update

    @staticmethod
    def populate_btc_data() -> bool:
        """
        This method is used to populate BTC data with eod api.
        :return: Whether the data is populated or not.
        """
        # check if the database exists
        if not database.check_table_exists("btc_data"):
            try:
                # create the table
                database.create_table(["btc_data"])
            except Exception as e:
                print("Error creating btc_data table: ", e)
                return False
            try:
                # populate the table
                # BTC starts from 2010-07-17
                # end date is today
                start_date = "2010-01-01"
                end_date = date.today().strftime("%Y-%m-%d")
                eod_market_data.populate_stock_data(tickers=["BTC-USD"], table_name="btc_data", start_date=start_date,
                                                    end_date=end_date, category="CC")
                return True
            except Exception as e:
                print("Error downloading BTC-USD data")
                return False
        # if the database exists, check if the data needs to be updated
        else:
            # check if the data needs to be updated
            need_update, last_update = BTCData.__need_update()
            if need_update:  # if the data needs to be updated
                print("need update")
                # get the last update time, and the start date is the last update time + 1 day
                last_update = date.fromisoformat(last_update)
                start_date = (last_update + timedelta(days=1)).strftime("%Y-%m-%d")
                end_date = date.today().strftime("%Y-%m-%d")
                eod_market_data.populate_stock_data(tickers=["BTC-USD"], table_name="btc_data", start_date=start_date,
                                                    end_date=end_date, category="CC")
                return True
            else:  # no need update
                print("no need update")
                return True

    @staticmethod
    @deprecated
    def get_btc_data_all() -> pd.DataFrame:
        """
        This method is used to get all BTC data.
        :return: BTC data.
        """
        # if something goes wrong, throw exception
        if not BTCData.populate_btc_data():
            raise Exception("Error downloading BTC-USD data")
        # get the data
        try:
            select_sql = """
                        SELECT * FROM btc_data ORDER BY date DESC
                        """.replace("\n", "").strip()
            print(select_sql)
            data = database.execute_sql_statement(select_sql)
            data.drop(columns=["symbol"], inplace=True)
            return data
        except Exception as e:
            print("Error getting BTC-USD data: ", e)
            raise Exception("Error getting BTC-USD data")

    @staticmethod
    def get_btc_data_range(start_date: str, end_date: str) -> pd.DataFrame:
        """
        This method is used to get BTC data from database.
        :param start_date: The start date to choose.
        :param end_date: The end date to choose.
        :return: BTC data DataFrame.
        """
        # if something goes wrong, throw exception
        if not BTCData.populate_btc_data():
            raise Exception("Error downloading BTC-USD data")
        try:
            # get the data from database, without symbol
            select_sql = """
                        SELECT date, open, high, low, close FROM btc_data where date between '{}' and '{}'
                        """.format(start_date, end_date).replace("\n", "").strip()
            print(select_sql)
            select_data = database.execute_sql_statement(select_sql)
            # set the index to date
            select_data.set_index("date", inplace=True)
            return select_data
        except Exception as e:
            raise Exception("Error getting BTC-USD data")