import sys
import argparse
import quickfix as fix
from application import FIXServer

import threading

def help():
    print("Commands are: ")
    print("\tbook                       ## Shows current order book")
    print("\tack [orderID]              ## Sends acknowledgement on orderID")
    print("\tcancel [orderID]           ## Sends cancel ack on orderID")
    print("\tfill [orderID] [quantity]  ## Sends a fill on orderID with quantity")
    print("\torder [orderID]            ## Provides details about the order")
    print("\tremove [orderID]           ## Removes the order from the book")
    print("\treplace [orderID]          ## Sends a ReplaceAck on orderID")
    print("\treplacepend [orderID]      ## Sends a ReplacePending message for orderID")
    print("\texit                       ## Shuts down this server")

def main(config_file):
    try:
        settings     = fix.SessionSettings(config_file)
        server_application  = FIXServer()
        logFactory   = fix.ScreenLogFactory(settings)
        storeFactory = fix.FileStoreFactory(settings)
        acceptor     = fix.SocketAcceptor(server_application, storeFactory, settings)
        fixServer    = threading.Thread(target=acceptor.start())
        fixServer.start()

        while True:
            command = input("--> ")

            if not command: pass

            elif command.lower() == "help": help()

            elif command.lower() == "book": server_application.showOrders()

            elif command.lower()[:6] == "order ":
                orderID = command[6:]
                if not orderID or int(orderID) not in server_application.orders:
                    print("OrderID {} not found in book.  Please try again.".format(orderID))
                    server_application.showOrders()
                else:
                    server_application.getOrderDetails(int(orderID))

            elif command.lower()[:7] == "remove ":
                orderID = command[7:]
                if not orderID or int(orderID) not in server_application.orders:
                    print("OrderID {} not found in book. Please try again".format(orderID))
                    server_application.showOrders()
                else:
                    del server_application.orders[int(orderID)]
                    server_application.showOrders()

            elif command.lower()[:4] == "ack ":
                orderID = command[4:]
                if not orderID or int(orderID) not in server_application.orders:
                    print("OrderID {} not found in book. Please try again".format(orderID))
                    server_application.showOrders()
                else:
                    server_application.sendOrderAck(int(orderID))
                    print("Ack sent for orderID {}".format(orderID))

            elif command.lower()[:7] == "cancel ":
                orderID = command[7:]
                if not orderID or int(orderID) not in server_application.orders:
                    print("OrderID {} not found in book. Please try again".format(orderID))
                    server_application.showOrders()
                else:
                    server_application.sendCancelAck(int(orderID))
                    print("CancelAck sent for orderID {}".format(orderID))

            elif command.lower()[:8] == "replace ":
                orderID = command[8:]
                if not orderID or int(orderID) not in server_application.orders:
                    print("OrderID {} not found in book. Please try again".format(orderID))
                    server_application.showOrders()
                else:
                    server_application.sendReplaceAck(int(orderID))
                    print("ReplaceAck for orderID {}".format(orderID))

            elif command.lower()[:12] == "replacepend ":
                orderID = command[12:]
                if not orderID or int(orderID) not in server_application.orders:
                    print("OrderID {} not found in book. Please try again".format(orderID))
                    server_application.showOrders()
                else:
                    server_application.sendReplacePending(int(orderID))
                    print("ReplacePending for orderID {}".format(orderID))

            elif command.lower()[:5] == "fill ":
                fillCmd = command.lower().split(' ')
                if len(fillCmd) != 3:
                    print("Invalid number of parameters")
                    help()
                    continue
                orderID = fillCmd[1]
                quantity = fillCmd[2]
                if int(orderID) not in server_application.orders:
                    print("OrderID {} not found in book.  Please try again".format(orderID))
                    server_application.showOrders()
                    continue
                try:
                    server_application.sendFill(int(orderID), int(quantity))
                    print("Fill of quantity {} sent for orderID {}".format(quantity, orderID))
                except:
                    print("Quantity '{}' not a valid integer".format(quantity))
                    help()

            elif command.lower() == 'exit':
                acceptor.stop()
                exit(0)

            else:
                print("Command '{}' invalid".format(command))
                help()

    except (KeyError, KeyboardInterrupt, fix.ConfigError, fix.RuntimeError) as e:
        print(e)
        acceptor.stop()
        sys.exit(-1)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='FIX Server')
    parser.add_argument('-cfg', default='./server.cfg', type=str, help='Name of configuration file')
    args = parser.parse_args()
    main(args.cfg)
