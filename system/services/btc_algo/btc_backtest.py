import pandas as pd


class BackTest:
    def __init__(self, data: pd.DataFrame, initial_capital: float = 100000, execution_type: str = "once",
                 execution_amount: int = 10, price_base: str = "close", position_type: str = "both"):
        """
        :param data: The data to use.
        :param initial_capital: The initial capital.
        :param execution_type: The type of execution.
        :param execution_amount: The amount of executions.
        :param price_base: The price base.
        :param position_type: The position type.
        """
        self.data = data
        self.initial_capital = float(initial_capital)
        self.end_capital = None
        self.current_capital = float(initial_capital)
        self.start_price = self.data[price_base].iloc[0]
        self.end_price = self.data[price_base].iloc[-1]
        self.position = 0
        self.long = 0
        self.short = 0
        self.buy_price = 0
        self.sell_price = 0
        self.profit_list = []
        self.capital_list = [self.initial_capital]
        self.transaction_times = 0

        self.execution_type = execution_type
        self.execution_amount = int(execution_amount)
        self.price_base = price_base
        self.position_type = position_type

    def __long_back_test(self, data: pd.DataFrame) -> None:
        """
        Used to handle long position logic.
        :param data: The data to use.
        """
        # if once, that means we only buy or sell once when we see the signal and wait for the opposite signal.
        if self.execution_type == "once":
            for i in range(1, len(data)):
                current_price = data.iloc[i][self.price_base]
                prev_signal = data.iloc[i - 1]["signal"]
                # if we have no position, we can execute.
                if self.position == 0:
                    # if previous signal is 1 and we have no long position, we can buy.
                    if prev_signal == 1 and self.long == 0:
                        # only if we have enough capital to buy price times amount, we can buy.
                        if self.current_capital >= current_price * self.execution_amount:
                            self.position = 1
                            self.long = self.execution_amount
                            self.buy_price = current_price
                            self.current_capital -= self.buy_price * self.long
                # if we have long position, we can sell.
                else:
                    # if previous signal is -1 and we have long position, we can sell.
                    if prev_signal == -1 and self.long > 0:
                        self.sell_price = current_price
                        self.current_capital += self.sell_price * self.long
                        self.profit_list.append((self.sell_price - self.buy_price) * self.long)
                        self.capital_list.append(self.current_capital)
                        self.transaction_times += 1
                        # reset position and long position.
                        self.position = 0
                        self.long = 0
                        self.buy_price = 0
                        self.sell_price = 0
            # end capital is the last capital.
            self.end_capital = self.capital_list[-1]
        elif self.execution_type == "multiple":
            for i in range(1, len(data)):
                current_price = data.iloc[i][self.price_base]
                prev_signal = data.iloc[i - 1]["signal"]
                # once we have signal as 1, we can buy until we don't have enough capital for one execution amount.
                if prev_signal == 1:
                    if self.current_capital >= current_price * self.execution_amount:
                        self.position = 1
                        self.long += self.execution_amount
                        self.buy_price = current_price
                        self.current_capital -= self.buy_price * self.execution_amount
                # once we have signal as -1, we will sell all long position.
                elif prev_signal == -1 and self.long > 0:
                    self.sell_price = current_price
                    self.current_capital += self.sell_price * self.long
                    self.profit_list.append((self.sell_price - self.buy_price) * self.long)
                    self.capital_list.append(self.current_capital)
                    self.transaction_times += 1
                    # reset position and long position.
                    self.position = 0
                    self.long = 0
                    self.buy_price = 0
                    self.sell_price = 0
            # end capital is the last capital.
            self.end_capital = self.capital_list[-1]
        else:
            raise Exception("Execution type is not supported.")

    def __short_back_test(self, data: pd.DataFrame) -> None:
        """
        Used to handle short position logic.
        :param data: The data to use.
        """
        # if once, that means we only buy or sell once when we see the signal and wait for the opposite signal.
        if self.execution_type == "once":
            for i in range(1, len(data)):
                current_price = data.iloc[i][self.price_base]
                prev_signal = data.iloc[i - 1]["signal"]
                # if we have no position, we can execute.
                if self.position == 0:
                    # if previous signal is -1 and we have no short position, we can buy.
                    if prev_signal == -1 and self.short == 0:
                        # only if we have enough capital to buy price times amount, we can buy.
                        if self.current_capital >= current_price * self.execution_amount:
                            self.position = 1
                            self.short = self.execution_amount
                            self.sell_price = current_price
                            self.current_capital += self.sell_price * self.short
                # if we have short position, we can sell.
                else:
                    # if previous signal is 1 and we have short position, we can sell.
                    if prev_signal == 1 and self.short > 0:
                        self.buy_price = current_price
                        self.current_capital -= self.buy_price * self.short
                        self.profit_list.append((self.sell_price - self.buy_price) * self.short)
                        self.capital_list.append(self.current_capital)
                        self.transaction_times += 1
                        # reset position and short position.
                        self.position = 0
                        self.short = 0
                        self.buy_price = 0
                        self.sell_price = 0
            # end capital is the last capital.
            self.end_capital = self.capital_list[-1]
        elif self.execution_type == "multiple":
            for i in range(1, len(data)):
                current_price = data.iloc[i][self.price_base]
                prev_signal = data.iloc[i - 1]["signal"]
                # once we have signal as -1, we can short until we don't have enough capital for one execution amount.
                if prev_signal == -1:
                    if self.current_capital >= current_price * self.execution_amount:
                        self.position = 1
                        self.short += self.execution_amount
                        self.sell_price = current_price
                        self.current_capital += self.sell_price * self.execution_amount
                # once we have signal as 1, we will sell all short position.
                elif prev_signal == 1 and self.short > 0:
                    self.buy_price = current_price
                    self.current_capital -= self.buy_price * self.short
                    self.profit_list.append((self.sell_price - self.buy_price) * self.short)
                    self.capital_list.append(self.current_capital)
                    self.transaction_times += 1
                    # reset position and short position.
                    self.position = 0
                    self.short = 0
                    self.buy_price = 0
                    self.sell_price = 0
            # end capital is the last capital.
            self.end_capital = self.capital_list[-1]
        else:
            raise Exception("Execution type is not supported.")

    def __both_back_test(self, data: pd.DataFrame) -> None:
        """
        Used to handle both position logic.
        :param data: The data to use.
        """
        # if once, that means we only buy and sell once when we see the signal and wait for the opposite signal.
        if self.execution_type == "once":
            for i in range(1, len(data)):
                current_price = data.iloc[i][self.price_base]
                prev_signal = data.iloc[i - 1]["signal"]
                # if we have no position, we can execute.
                if self.position == 0:
                    # if previous signal is 1 and we have no long position, we can buy.
                    if prev_signal == 1 and self.long == 0:
                        # only if we have enough capital to buy price times amount, we can buy.
                        if self.current_capital >= current_price * self.execution_amount:
                            self.position = 1
                            self.long = self.execution_amount
                            self.buy_price = current_price
                            self.current_capital -= self.buy_price * self.long
                    # if previous signal is -1 and we have no short position, we can buy.
                    elif prev_signal == -1 and self.short == 0:
                        # only if we have enough capital to buy price times amount, we can buy.
                        if self.current_capital >= current_price * self.execution_amount:
                            self.position = 1
                            self.short = self.execution_amount
                            self.sell_price = current_price
                            self.current_capital += self.sell_price * self.short
                # if we have long position, we can sell.
                else:
                    # if previous signal is 1 and we have long position, we can buy back.
                    if prev_signal == 1 and self.long > 0:
                        self.buy_price = current_price
                        self.current_capital += self.buy_price * self.long
                        self.profit_list.append((self.sell_price - self.buy_price) * self.long)
                        self.capital_list.append(self.current_capital)
                        self.transaction_times += 1
                        # reset position and long position.
                        self.position = 0
                        self.long = 0
                        self.buy_price = 0
                        self.sell_price = 0
                    # if previous signal is -1 and we have short position, we can sell.
                    elif prev_signal == -1 and self.short > 0:
                        self.sell_price = current_price
                        self.current_capital -= self.sell_price * self.short
                        self.profit_list.append((self.sell_price - self.buy_price) * self.short)
                        self.capital_list.append(self.current_capital)
                        self.transaction_times += 1
                        # reset position and short position.
                        self.position = 0
                        self.short = 0
                        self.buy_price = 0
                        self.sell_price = 0
            # end capital is the last capital.
            self.end_capital = self.capital_list[-1]
        # if multiple, that means we can buy and sell multiple times when we see the signal.
        elif self.execution_type == "multiple":
            for i in range(1, len(data)):
                current_price = data.iloc[i][self.price_base]
                prev_signal = data.iloc[i - 1]["signal"]
                # once we have signal as 1, we can buy until we don't have enough capital for one execution amount.
                if prev_signal == 1:
                    if self.current_capital >= current_price * self.execution_amount:
                        self.position = 1
                        self.long += self.execution_amount
                        self.buy_price = current_price
                        self.current_capital -= self.buy_price * self.execution_amount
                # once we have signal as -1, we will sell all long position.
                elif prev_signal == -1 and self.long > 0:
                    self.sell_price = current_price
                    self.current_capital += self.sell_price * self.long
                    self.profit_list.append((self.sell_price - self.buy_price) * self.long)
                    self.capital_list.append(self.current_capital)
                    self.transaction_times += 1
                    # reset position and long position.
                    self.position = 0
                    self.long = 0
                    self.buy_price = 0
                    self.sell_price = 0
                # once we have signal as -1, we can short until we don't have enough capital for one execution amount.
                elif prev_signal == -1:
                    if self.current_capital >= current_price * self.execution_amount:
                        self.position = 1
                        self.short += self.execution_amount
                        self.sell_price = current_price
                        self.current_capital += self.sell_price * self.execution_amount
                # if we have short position, we can sell.
                elif prev_signal == 1 and self.short > 0:
                    self.buy_price = current_price
                    self.current_capital -= self.buy_price * self.short
                    self.profit_list.append((self.sell_price - self.buy_price) * self.short)
                    self.capital_list.append(self.current_capital)
                    self.transaction_times += 1
                    # reset position and short position.
                    self.position = 0
                    self.short = 0
                    self.buy_price = 0
                    self.sell_price = 0
            # end capital is the last capital.
            self.end_capital = self.capital_list[-1]
        else:
            raise Exception("Execution type is not supported.")

    def back_test(self) -> list:
        """
        Used to back test.
        :return: The performance matrix list.
        """
        execution_data = self.data.copy()[[self.price_base, "signal"]]
        if self.position_type == "long":
            self.__long_back_test(execution_data)
            annual_return = round(((sum(self.profit_list) / self.initial_capital) / len(self.data)) * 365 * 100, 2)
            mdd = round((min(self.capital_list) - max(self.capital_list)) / max(self.capital_list) * 100, 2)
            return [self.transaction_times, self.initial_capital, self.end_capital, annual_return, mdd]
        elif self.position_type == "short":
            self.__short_back_test(execution_data)
            annual_return = round(((sum(self.profit_list) / self.initial_capital) / len(self.data)) * 365 * 100, 2)
            mdd = round((min(self.capital_list) - max(self.capital_list)) / max(self.capital_list) * 100, 2)
            return [self.transaction_times, self.initial_capital, self.end_capital, annual_return, mdd]
        elif self.position_type == "both":
            self.__both_back_test(execution_data)
            annual_return = round(((sum(self.profit_list) / self.initial_capital) / len(self.data)) * 365 * 100, 2)
            mdd = round((min(self.capital_list) - max(self.capital_list)) / max(self.capital_list) * 100, 2)
            return [self.transaction_times, self.initial_capital, self.end_capital, annual_return, mdd]
        else:
            raise Exception("Position type is not supported.")
