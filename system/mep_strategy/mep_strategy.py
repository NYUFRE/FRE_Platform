from system.mep_strategy import mep_calculate
from system.mep_strategy import mep_common


class MEPStrategy:
    def __init__(self, openprices, highprices, lowprices, closeprices):
        assert(len(openprices) == len(highprices))
        assert(len(lowprices) == len(closeprices))
        assert(len(openprices) == len(closeprices))

        assert((openprices.index == highprices.index).all())
        assert((lowprices.index == closeprices.index).all())
        assert((openprices.index == closeprices.index).all())

        self.index = openprices.index
        self.openprices = openprices
        self.highprices = highprices
        self.lowprices = lowprices
        self.closeprices = closeprices

    def generate_signals(self):
        ema200_records = mep_calculate.calculate_EMA(self.closeprices, window_size=200)
        psar_records = mep_calculate.calculate_PSAR(self.highprices, self.lowprices)
        macd_records = mep_calculate.calculate_MACD(self.closeprices)
        signal_records = mep_calculate.calculate_MACD_signal(self.closeprices)

        assert(len(ema200_records) == len(psar_records))
        assert(len(macd_records) == len(signal_records))
        assert(len(ema200_records) == len(macd_records))

        intervals = mep_common.find_intervals(macd_records, signal_records, start_from=200)
        trade_signals = dict()

        for index_start, index_end, trend_current in intervals:
            if trend_current == mep_common.Trend.BULL:
                # Find the time ti where Parabolic SAR shows uptrend
                ti = None

                for i in range(index_start, index_end + 1):
                    if psar_records[i] <= self.lowprices[i]:
                        # PSAR shows uptrend
                        ti = i
                        break

                # Make sure that price_t > 200 EMA
                if ti is not None and self.lowprices[ti] > ema200_records[ti]:
                    trade_signals[self.index[ti]] = mep_common.TradeSignal.LONG
            else:
                # Find the time ti where Parabolic SAR shows downtrend
                ti = None

                for i in range(index_start, index_end + 1):
                    if psar_records[i] >= self.highprices[i]:
                        # PSAR shows downtrend
                        ti = i
                        break

                # Make sure that price_t < 200 EMA
                if ti is not None and self.highprices[ti] < ema200_records[ti]:
                    trade_signals[self.index[ti]] = mep_common.TradeSignal.SHORT

        self.ema200s = ema200_records
        self.psars = psar_records
        self.macds = macd_records
        self.signals = signal_records

        return trade_signals
