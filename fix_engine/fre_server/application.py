import sys
sys.path.append('../')

import quickfix as fix
import logging
import time
import texttable

from model import field
from model.message import Base, Types, __SOH__
from model.logger import setup_logger

setup_logger('logfix', 'Logs/message.log')
logfix = logging.getLogger('logfix')

class FIXServer(fix.Application):
    def onCreate(self, session):
        targetCompID = session.getTargetCompID().getValue()
        try:
            self.sessions[targetCompID] = {}
        except AttributeError:
            # We're here if this is the first connected session, so we initialize everything.
            # I wouldn't have to do this wonky crap if quickfix.Application didn't hijack __init__()
            self.lastOrderID            = 0
            self.sessions               = {}
            self.orders                 = {}
            self.sessions[targetCompID] = {}

        self.sessions[targetCompID]['session']   = session
        self.sessions[targetCompID]['connected'] = False
        self.sessions[targetCompID]['exchID']    = 0
        self.sessions[targetCompID]['execID']    = 0

    def onLogon(self, session):
        targetCompID                             = session.getTargetCompID().getValue()
        self.sessions[targetCompID]['connected'] = True
        print("\nClient {} has logged in\n--> ".format(targetCompID),)

    def onLogout(self, session):
        targetCompID                             = session.getTargetCompID().getValue()
        self.sessions[targetCompID]['connected'] = False
        print("\nClient {} has logged out\n--> ".format(targetCompID),)

    def onMessage(self, message, sessionID):
        """Processing application message here"""
        pass

    def toAdmin(self, session, message):
        msg = message.toString().replace(__SOH__, "|")
        logfix.debug("S >> %s" % msg)
        return

    def fromAdmin(self, session, message):
        msg = message.toString().replace(__SOH__, "|")
        logfix.debug("R << %s" % msg)
        self.onMessage(message, session)
        return

    def toApp(self, session, message):
        msg = message.toString().replace(__SOH__, "|")
        logfix.debug("S >> %s" % msg)
        return

    def run(self):
        """Run"""
        while 1:
            time.sleep(2)

    def fromApp(self, message, session):
        clientOrderID = self.getValue(message, fix.ClOrdID())
        targetCompID  = session.getTargetCompID().getValue()
        details       = {'session'  : session,
                         'clOrdID'  : clientOrderID,
                         'target'   : targetCompID,
                         'symbol'   : self.getValue(message, fix.Symbol()),
                         'side'     : self.getValue(message,  fix.Side()),
                         'sideStr'  : self.getSide(self.getValue(message,  fix.Side())),
                         'quantity' : self.getValue(message, fix.OrderQty()),
                         'leaves'   : self.getValue(message,  fix.OrderQty())}

        if self.getHeaderValue(message,  fix.MsgType()) ==  fix.MsgType_NewOrderSingle:
            ## Received new order from client
            orderID = self.getNextOrderID()
            print("\nNewOrder {} received\n--> ".format(orderID),)
            details['ordType'] = self.getValue(message,  fix.OrdType())
            details['state']   = 'PendingAck'

            if (self.getValue(message, fix.OrdType()) == fix.OrdType_LIMIT or
                    self.getValue(message, fix.OrdType()) == fix.OrdType_LIMIT_ON_CLOSE):
                # Limit orders will have a price, Market order will not.
                details['price'] = self.getValue(message, fix.Price())

            self.orders[orderID] = details
            self.sessions[targetCompID][clientOrderID] = orderID

            self.sendOrderAck(orderID)

            #TODO! No self trade prevention for now
            for key, value in self.orders.items():
                if value['symbol'] == details['symbol'] and int(value['leaves']) > 0 and \
                   value['side'] != details['side'] and key != orderID:
                    lvsQty = value['leaves']
                    ordQty = details['leaves']
                    self.sendFill(key, ordQty)
                    #time.sleep(10)
                    self.sendFill(orderID, lvsQty)

        if self.getHeaderValue(message, fix.MsgType()) == fix.MsgType_OrderCancelRequest:
            origClientOrderID      = self.getValue(message, fix.OrigClOrdID())
            details['origClOrdID'] = origClientOrderID
            details['cxlClOrdID']  = clientOrderID

            if origClientOrderID not in self.sessions[targetCompID]:
                # A cancel request has come in for an order we don't have in the book
                # So let's create that order in the book based on what we know
                orderID                                        = self.getNextOrderID()
                self.orders[orderID]                           = details
                self.sessions[targetCompID][origClientOrderID] = orderID
            else:
                ## We have the order in the book
                orderID = self.sessions[targetCompID][origClientOrderID]
                self.orders[orderID]['cxlClOrdID']   = clientOrderID

            self.orders[orderID]['state']      = 'PendingCancel'
            print("\nCancelRequest for OrderID {} received\n--> ".format(orderID),)

            self.sendCancelAck(orderID)

        if self.getHeaderValue(message, fix.MsgType()) == fix.MsgType_OrderCancelReplaceRequest:
            origClientOrderID = self.getValue(message, fix.OrigClOrdID())

            if origClientOrderID not in self.sessions[targetCompID]:
                ## A replace request has come in for an order we don't have in the book
                orderID                                        = self.getNextOrderID()
                self.orders[orderID]                           = details
                self.sessions[targetCompID][origClientOrderID] = orderID

            else:
                ## We have the original order in the book
                orderID = self.sessions[targetCompID][origClientOrderID]

            self.orders[orderID]['rplClOrdID'] = clientOrderID
            self.orders[orderID]['state']      = 'PendingReplace'

            newOrderID = self.getNextOrderID()
            self.orders[newOrderID]                = details
            self.orders[newOrderID]['origClOrdID'] = origClientOrderID
            self.orders[newOrderID]['origOrdID']   = orderID
            self.orders[newOrderID]['state']    = 'PendingNew'
            self.sessions[targetCompID][clientOrderID] = newOrderID
            print("OrderID {} to replace OrderID {} received\n--> ".format(newOrderID, orderID),)

            self.sendReplaceAck(newOrderID)

    def getNextOrderID(self):
        self.lastOrderID += 1
        return self.lastOrderID

    def getNextExecID(self, targetCompID):
        self.sessions[targetCompID]['execID'] += 1
        return "{}_{}".format(targetCompID, self.sessions[targetCompID]['execID'])

    #def getNextExchangeID(self, targetCompID):
    #    self.sessions[targetCompID]['exchID'] += 1
    #    return "{}_{}".format(targetCompID, self.sessions[targetCompID]['exchID'])

    def startFIXString(self, orderID):
        message = fix.Message()
        message.getHeader().setField(fix.BeginString(fix.BeginString_FIX43))
        message.getHeader().setField(fix.MsgType(fix.MsgType_ExecutionReport))
        message.getHeader().setField(fix.SendingTime())
        message.getHeader().setField(fix.TransactTime())
        message.setField(fix.ClOrdID(self.orders[orderID]['clOrdID']))
        message.setField(fix.OrderQty(self.orders[orderID]['quantity']))
        message.setField(fix.Symbol(self.orders[orderID]['symbol']))
        message.setField(fix.Side(self.orders[orderID]['side']))
        message.setField(fix.ExecID(str(self.getNextExecID(self.orders[orderID]['target']))))
        #if 'exchangeID' not in self.orders[orderID]:
        #    self.orders[orderID]['exchangeID'] = self.getNextExchangeID(self.orders[orderID]['target'])
        message.setField(fix.OrderID(str(self.orders[orderID]['clOrdID'])))
        return message

    def sendOrderAck(self, orderID):

        message = self.startFIXString(orderID)
        message.setField(fix.ExecType(fix.ExecType_NEW))
        #message.setField(fix.ExecTransType(fix.ExecTransType_NEW))
        message.setField(fix.OrdStatus(fix.ExecType_NEW))
        message.setField(fix.LeavesQty(self.orders[orderID]['leaves']))
        self.orders[orderID]['state'] = 'New'
        message.setField(fix.Text(self.orders[orderID]['state']))
        fix.Session.sendToTarget(message, self.orders[orderID]['session'])

        #print(message)

    def sendCancelAck(self, orderID):
        message = self.startFIXString(orderID)
        message.setField(fix.OrderQty(self.orders[orderID]['leaves']))
        message.setField(fix.ExecType(fix.ExecType_CANCELED))
        message.setField(fix.OrdStatus(fix.ExecType_CANCELED))
        if 'cxlClOrdID' in self.orders[orderID]:
            message.setField(fix.ClOrdID(self.orders[orderID]['cxlClOrdID']))
        if 'origClOrdID' in self.orders[orderID]:
            message.setField(fix.OrigClOrdID(self.orders[orderID]['origClOrdID']))
        else:
            message.setField(fix.OrigClOrdID(self.orders[orderID]['clOrdID']))
        self.orders[orderID]['leaves'] = 0
        self.orders[orderID]['state'] = 'Canceled'
        message.setField(fix.Text(self.orders[orderID]['state']))
        message.setField(fix.LeavesQty(self.orders[orderID]['leaves']))
        fix.Session.sendToTarget(message, self.orders[orderID]['session'])


    def sendReplaceAck(self, orderID):
        origOrdID         = self.orders[orderID]['origOrdID']
        origClientOrderID = self.orders[orderID]['origClOrdID']
        message = self.startFIXString(orderID)
        message.setField(fix.OrderQty(self.orders[orderID]['quantity']))
        message.setField(fix.ExecType(fix.ExecType_REPLACED))
        message.setField(fix.OrdStatus(fix.ExecType_REPLACED))
        #message.setField(fix.ExecTransType(fix.ExecTransType_NEW))
        message.setField(fix.OrigClOrdID(origClientOrderID))
        self.orders[orderID]['leaves'] = self.orders[orderID]['quantity']
        self.orders[origOrdID]['leaves'] = 0
        self.orders[orderID]['state'] = 'New'
        self.orders[origOrdID]['state'] = 'Replaced'
        message.setField(fix.Text(self.orders[origOrdID]['state']))
        message.setField(fix.LeavesQty(self.orders[orderID]['leaves']))
        fix.Session.sendToTarget(message, self.orders[orderID]['session'])

    def sendReplacePending(self, orderID):
        origClientOrderID = self.orders[orderID]['origClOrdID']
        message = self.startFIXString(orderID)
        message.setField(fix.OrderQty(self.orders[orderID]['quantity']))
        message.setField(fix.ExecType(fix.ExecType_PENDING_REPLACE))
        message.setField(fix.OrigClOrdID(origClientOrderID))

        fix.Session.sendToTarget(message, self.orders[orderID]['session'])

    def sendFill(self, orderID, quantity):
        message = self.startFIXString(orderID)
        if self.orders[orderID]['leaves'] <= quantity:
            message.setField(fix.OrdStatus(fix.OrdStatus_FILLED))
            message.setField(fix.ExecType(fix.ExecType_FILL))
            message.setField(fix.LastShares(self.orders[orderID]['leaves']))
            self.orders[orderID]['state'] = 'Filled'
            message.setField(fix.Text(self.orders[orderID]['state']))
            self.orders[orderID]['leaves'] = 0

        else:
            message.setField(fix.OrdStatus(fix.OrdStatus_PARTIALLY_FILLED))
            message.setField(fix.ExecType(fix.ExecType_PARTIAL_FILL))
            message.setField(fix.LastShares(quantity))
            self.orders[orderID]['state'] = 'Partially Filled'
            message.setField(fix.Text(self.orders[orderID]['state']))
            self.orders[orderID]['leaves'] -= quantity

        if 'price' in self.orders[orderID]:
            message.setField(fix.LastPx(self.orders[orderID]['price']))
        else:
            message.setField(fix.LastPx(1.00))

        message.setField(fix.LeavesQty(self.orders[orderID]['leaves']))
        fix.Session.sendToTarget(message, self.orders[orderID]['session'])

        print(message)

    def getHeaderValue(self, message, field):
        key = field
        message.getHeader().getField(key)
        return key.getValue()

    def getValue(self, message, field):
        key = field
        message.getField(key)
        return key.getValue()

    def getFooterValue(self, message, field):
        key = field
        message.getTrailer().getField(key)
        return key.getValue()

    def showOrders(self):
        if len(self.orders) > 0:
            table = texttable.Texttable()
            table.header(['OrderID', 'Client', 'ClOrdID', 'Side', 'OrdQty', 'Leaves', 'Symbol', 'State'])
            table.set_cols_width([8, 12, 16, 8, 12, 12, 12, 32])
            for order in self.orders:
                table.add_row([order,
                               self.orders[order]['target'],
                               self.orders[order]['clOrdID'],
                               self.orders[order]['sideStr'],
                               self.orders[order]['quantity'],
                               self.orders[order]['leaves'],
                               self.orders[order]['symbol'],
                               self.orders[order]['state']])
            print(table.draw())
        else:
            print("The order book is currently empty")

    def getSide(self, side):
        if side == '1': return "Buy"
        if side == '2': return "Sell"
        if side == '5': return "SellShort"

    def getOrderDetails(self, orderID):
        table = texttable.Texttable()
        table.set_cols_width([16, 32])
        for key in self.orders[orderID]:
            table.add_row([key, self.orders[orderID][key]])
        print(table.draw())