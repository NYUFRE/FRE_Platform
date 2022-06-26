from system import mep_common


class Order:
    def __init__(self, order_type, market_price, shares, limit, stoploss):
        assert(isinstance(order_type, mep_common.OrderType))

        if order_type == mep_common.OrderType.BUY_ORDER:
            assert(limit > stoploss)
        else:
            assert(limit < stoploss)

        assert(market_price > min(limit, stoploss))
        assert(market_price < max(limit, stoploss))

        assert(shares > 0)

        self._order_type = order_type
        self._market_price = market_price
        self._shares = shares if order_type == mep_common.OrderType.BUY_ORDER else -shares
        self._limit = limit
        self._stoploss = stoploss

        self._order_closed = False
        self._pnl = 0

    @property
    def order_type(self):
        return self._order_type

    @property
    def order_shares(self):
        return self._shares

    @property
    def order_fund(self):
        return self._shares * self._market_price

    @property
    def order_closed(self):
        return self._order_closed

    @property
    def order_pnl(self):
        return self._pnl

    def check(self, hprice, lprice):
        assert(hprice >= lprice)

        if self.order_closed:
            return

        # Order not closed
        if self._order_type == mep_common.OrderType.BUY_ORDER:
            if hprice >= self._limit:
                self._order_closed = True
                self._pnl = (self._limit - self._market_price) * self._shares
            elif lprice <= self._stoploss:
                self._order_closed = True
                self._pnl = (self._stoploss - self._market_price) * self._shares

        if self._order_type == mep_common.OrderType.SELL_ORDER:
            if lprice <= self._limit:
                self._order_closed = True
                self._pnl = (self._limit - self._market_price) * self._shares
            elif hprice >= self._stoploss:
                self._order_closed = True
                self._pnl = (self._stoploss - self._market_price) * self._shares

    def __str__(self):
        return f"[Order: Shares={self.order_shares}, Fund={self.order_fund}, P&L={self.order_pnl}]"

    def __repr__(self):
        return str(self)
