from enum import Enum
from system.services.mep_strategy.mep_strategy_executor import *


class Trend(Enum):
    BULL = 1
    BEAR = -1


class TradeSignal(Enum):
    LONG = 1
    HOLD = 0
    SHORT = -1


class OrderType(Enum):
    BUY_ORDER = 1
    SELL_ORDER = -1


def find_intervals(macd_records, signal_records, start_from=0):
    assert(len(macd_records) == len(signal_records))

    if len(macd_records) <= start_from + 1:
        return []

    if macd_records[start_from] == signal_records[start_from]:
        trend_prev = None
    else:
        trend_prev = Trend.BULL if macd_records[start_from] > signal_records[start_from] else Trend.BEAR

    index_start = start_from
    index_end = None

    intervals = []

    for i in range(start_from + 1, len(macd_records)):

        if macd_records[i] == signal_records[i]:
            if trend_prev is not None:
                intervals.append((index_start, i, trend_prev))
            index_start = i
            trend_prev = None
            continue

        trend = Trend.BULL if macd_records[i] > signal_records[i] else Trend.BEAR

        if trend_prev is None:
            # Set trend and continue
            trend_prev = trend
            continue

        # trend_prev is not None
        if trend != trend_prev:
            if index_start != i - 1:
                intervals.append((index_start, i - 1, trend_prev))
            index_start = i
            trend_prev = trend

    if index_start != len(macd_records) - 1:
        intervals.append((index_start, len(macd_records) - 1, trend_prev))

    return intervals


def search_optimal_parameters(ticker, start_date, end_date, alpha_range=np.arange(.05, .4, .05), \
                delta_range=np.arange(.1, 2., .1), gamma_range=np.arange(.1, 2., .1), verbose=False):

    alpha_default = 0
    delta_default = .1
    gamma_default = .1

    alpha_opt = alpha_default
    delta_opt = delta_default
    gamma_opt = gamma_default

    sharpe_ratio_max = None

    for alpha in alpha_range:
        se = MEPStrategyExecutor(ticker, start_date, end_date, alpha=alpha, delta=delta_opt, gamma=gamma_opt)
        se.process()

        ratio = se.sharpe_ratio()
        if sharpe_ratio_max is None or ratio > sharpe_ratio_max:
            if verbose:
                print(f"alpha updated: {alpha_opt:.2f} => {alpha:.2f}")
            sharpe_ratio_max = ratio
            alpha_opt = alpha

    for delta in delta_range:
        se = MEPStrategyExecutor(ticker, start_date, end_date, alpha=alpha_opt, delta=delta, gamma=gamma_opt)
        se.process()

        ratio = se.sharpe_ratio()
        if ratio > sharpe_ratio_max:
            if verbose:
                print(f"delta updated: {delta_opt:.2f} => {delta:.2f}")
            sharpe_ratio_max = ratio
            delta_opt = delta

    for gamma in gamma_range:
        se = MEPStrategyExecutor(ticker, start_date, end_date, alpha=alpha_opt, delta=delta_opt, gamma=gamma)
        se.process()

        ratio = se.sharpe_ratio()
        if ratio > sharpe_ratio_max:
            if verbose:
                print(f"gamma updated: {gamma_opt:.2f} => {gamma:.2f}")
            sharpe_ratio_max = ratio
            gamma_opt = gamma

    return alpha_opt, delta_opt, gamma_opt, sharpe_ratio_max
