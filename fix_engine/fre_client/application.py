# -*- coding: utf8 -*-
import sys
sys.path.append('../')

import quickfix as fix
import logging
import time
from model import field
from model.message import Base, Types, __SOH__
from model.logger import setup_logger

# Logger
setup_logger('logfix', 'Logs/message.log')
client_log = logging.getLogger('logfix')

#TODO Change class name to FIXClient
class Application(fix.Application):

    def __init__(self, session):
        super(Application, self).__init__()
        #self.logger = logging.getLogger(self.__class__.__name__)
        self.session = session
        self.connected = False
        self.lastOrderID = 0

    def onCreate(self, sessionID):
        #self.logger = logging.getLogger(self.__class__.__name__)
        #self.logger.info('Application created with sessionID = %s.', sessionID.toString())
        client_log.info('Application created: %s.', sessionID.toString())

    def onLogon(self, sessionID):
        self.sessionID = sessionID
        #self.logger.info('Logon.')
        self.connected = True
        client_log.info('Session Login')

    def onLogout(self, sessionID):
        #self.logger.info('Logout.')
        self.connected = False
        client_log.info('Session Logout')

    def toAdmin(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        #self.logger.info("Sending Admin Msg >> %s" % msg)
        client_log.info("Sending Admin Msg >> %s" % msg)

    def fromAdmin(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        client_log.info("Receiving Admin Msg << %s" % msg)

    def toApp(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        client_log.info("Sending App Msg >> %s" % msg)

    def fromApp(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        client_log.info("Receiving App Msg << %s" % msg)
        self.onMessage(message, sessionID)

    def getValue(self, message, field):
        key = field
        message.getField(key)
        return key.getValue()

    def getHeaderValue(self, message, field):
        key = field
        message.getHeader().getField(key)
        return key.getValue()

    def getSide(self, side):
        if side == '1': return "Buy"
        if side == '2': return "Sell"
        if side == '5': return "SellShort"

    def onMessage(self, message, sessionID):
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)
        msgType = msgType.getValue()

        if msgType == fix.MsgType_ExecutionReport:
            # Extract fields from the message here and pass to an upper layer
            client_log.info("Receiving Execution Report")
        elif msgType == fix.MsgType_OrderCancelReject:
            # Extract fields from the message here and pass to an upper layer
            client_log.info("Receiving Cancel Reject")

        ordStatus = self.getValue(message, fix.OrdStatus())
        clOrdID = self.getValue(message, fix.ClOrdID())
        ordID = self.getValue(message, fix.OrderID())
        if ordStatus == fix.ExecType_CANCELED or ordStatus == fix.ExecType_REPLACED:
            clOrdID = self.getValue(message, fix.OrigClOrdID())
            ordID = self.getValue(message, fix.OrigClOrdID())

        senderCompID = self.getHeaderValue(message, fix.SenderCompID())
        targetCompID = self.getHeaderValue(message, fix.TargetCompID())
        report = {
            'clOrdID': clOrdID,
            'ordID': ordID,
            'sender': senderCompID,
            'target': targetCompID,
            'symbol': self.getValue(message, fix.Symbol()),
            'side': self.getSide(self.getValue(message, fix.Side())),
            'price': self.getValue(message, fix.Side()),
            'quantity': self.getValue(message, fix.OrderQty()),
            'ordStatus': ordStatus,
            'execType': self.getValue(message, fix.ExecType()),
            'leavesQty': self.getValue(message, fix.LeavesQty()),
            'text': self.getValue(message, fix.Text())
        }
        print(report)

    def getNextOrderID(self):
        self.lastOrderID += 1
        return self.lastOrderID

    def createOrder(self, order):
        '''
        :param order: Dictionary describing the order to be created. Mandatory fields:
            id:			order ID unique for the session and the day (FIX# 11)
            symbol:		the traded security symbol (FIX# 55)
            side:		side of the order (1 == buy, 2 == sell) (FIX# 54)
            price: 		price (required for limit orders) (FIX# 44)
            quantity:	transaction quantity (FIX# 38)
            type:		order type (1 == market, 2 == limit) (FIX# 40)
        '''
        if not self.connected:
            raise RuntimeError('Application not connected')

        message = fix.Message()
        header = message.getHeader()

        header.setField(fix.BeginString('FIX.4.3'))
        header.setField(fix.MsgType('D'))

        # 11
        message.setField(fix.ClOrdID(str(order['id'])))
        # 55
        message.setField(fix.Symbol(str(order['symbol'])))
        # 60 (current time in UTC)
        message.setField(fix.TransactTime(1))
        # 54 (1 == buy, 2 == sell)
        message.setField(fix.Side(str(order['side'])))
        # 44
        message.setField(fix.Price(float(order['price'])))
        # 38
        message.setField(fix.OrderQty(int(order['quantity'])))
        # 40 (1 == market, 2 == limit)
        message.setField(fix.OrdType(str(order['type'])))

        self.session.sendToTarget(message, self.sessionID)

    def cxlReplace(self, order):
        '''
        :param order: Dictionary describing the order to be created. Mandatory fields:
            id:			order ID unique for the session and the day (FIX# 11)
            symbol:		the traded security symbol (FIX# 55)
            side:		side of the order (1 == buy, 2 == sell) (FIX# 54)
            price: 		price (required for limit orders) (FIX# 44)
            quantity:	transaction quantity (FIX# 38)
            type:		order type (1 == market, 2 == limit) (FIX# 40)
        '''
        if not self.connected:
            raise RuntimeError('Application not connected')

        message = fix.Message()
        header = message.getHeader()
        nextOrdID = self.getNextOrderID()

        header.setField(fix.BeginString('FIX.4.3'))
        header.setField(fix.MsgType('G'))
        # 37
        message.setField(fix.OrigClOrdID(str(order['id'])))
        # 11
        message.setField(fix.ClOrdID(str(nextOrdID)))
        # 55
        message.setField(fix.Symbol(str(order['symbol'])))
        # 60 (current time in UTC)
        message.setField(fix.TransactTime(1))
        # 54 (1 == buy, 2 == sell)
        message.setField(fix.Side(str(order['side'])))
        # 38
        message.setField(fix.OrderQty(int(order['quantity'])))
        # 44
        message.setField(fix.Price(float(order['price'])))
        # 40 (1 == market, 2 == limit)
        message.setField(fix.OrdType(str(order['type'])))

        self.session.sendToTarget(message, self.sessionID)

        return nextOrdID

    def cxlRequest(self, order):

        if not self.connected:
            raise RuntimeError('Application not connected')

        message = fix.Message()
        header = message.getHeader()

        header.setField(fix.BeginString('FIX.4.3'))
        header.setField(fix.MsgType('F'))
        # 37
        message.setField(fix.OrigClOrdID(str(order['id'])))
        # 11
        message.setField(fix.ClOrdID(str(self.getNextOrderID())))
        # 55
        message.setField(fix.Symbol(str(order['symbol'])))
        # 60 (current time in UTC)
        message.setField(fix.TransactTime(1))
        # 54 (1 == buy, 2 == sell)
        message.setField(fix.Side(str(order['side'])))
        # 38
        message.setField(fix.OrderQty(int(order['quantity'])))

        self.session.sendToTarget(message, self.sessionID)

    def run(self):
        """Run"""

        #order = {'id': 1, 'symbol': 'GOOG', 'side': 1, 'price': 1100.01, 'quantity': 200, 'type': 2}
        '''
        count = 1
        while 1:
            time.sleep(10)
            side = count % 2 + 1
            order = {'id': count, 'symbol': 'GOOG', 'side': side, 'price': 1100.01, 'quantity': 200, 'type': 2}
            self.createOrder(order)
            count = count + 1
        '''
        time.sleep(5)
        ordID = self.getNextOrderID()
        order = {'id': ordID, 'symbol': 'GOOG', 'side': 1, 'price': 1100.01, 'quantity': 200, 'type': 2}
        self.createOrder(order)

        time.sleep(5)
        ordID = self.getNextOrderID()
        order = {'id': ordID, 'symbol': 'GOOG', 'side': 2, 'price': 1100.01, 'quantity': 400, 'type': 2}
        self.createOrder(order)

        time.sleep(5)
        ordID = self.getNextOrderID()
        order = {'id': ordID, 'symbol': 'GOOG', 'side': 1, 'price': 1100.01, 'quantity': 400, 'type': 2}
        self.createOrder(order)
        self.cxlRequest(order)

        time.sleep(5)
        ordID = self.getNextOrderID()
        order = {'id': ordID, 'symbol': 'GOOG', 'side': 1, 'price': 1100.01, 'quantity': 200, 'type': 2}
        self.createOrder(order)
        time.sleep(5)
        order = {'id': ordID, 'symbol': 'GOOG', 'side': 1, 'price': 100.01, 'quantity': 200, 'type': 2}
        ordID = self.cxlReplace(order)
        time.sleep(5)
        order = {'id': ordID, 'symbol': 'GOOG', 'side': 1, 'price': 100.01, 'quantity': 1000, 'type': 2}
        ordID = self.cxlReplace(order)
        time.sleep(5)
        order = {'id': ordID, 'symbol': 'GOOG', 'side': 2, 'price': 1001.01, 'quantity': 500, 'type': 2}
        self.cxlReplace(order)
