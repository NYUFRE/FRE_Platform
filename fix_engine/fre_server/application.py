import sys
sys.path.append('../')

import quickfix as fix
import logging
import time
from model import field
from model.message import Base, Types, __SOH__
from model.logger import setup_logger

setup_logger('logfix', 'Logs/message.log')
logfix = logging.getLogger('logfix')

class Application(fix.Application):

    sessionID = None
    orderID = 0

    def onCreate(self, sessionID):
        """onCreate"""
        return

    def onLogon(self, sessionID):
        self.sessionID = sessionID
        """onLogon"""
        return

    def onLogout(self, sessionID):
        """onLogout"""
        return

    def toAdmin(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        logfix.debug("S >> %s" % msg)
        return

    def fromAdmin(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        logfix.debug("R << %s" % msg)
        return

    def toApp(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        logfix.debug("S >> %s" % msg)
        return

    def fromApp(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        logfix.debug("R << %s" % msg)
        self.onMessage(message, sessionID)
        return
    

    def onMessage(self, message, sessionID):
        """Processing application message here"""
        pass

    def run(self):
        """Run"""
        while 1:
            time.sleep(2)
