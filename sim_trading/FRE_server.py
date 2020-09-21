# -*- coding: utf-8 -*-
#!/usr/bin/env python3
#@ Copyright -
import socket
import json
import urllib.request
import sys
import pandas as pd
import random

import struct
from enum import Enum
import threading
import queue

from sqlalchemy import create_engine
from sqlalchemy import MetaData

serverID = "Server1"
engine = create_engine('sqlite:///PairTradingServer.db')
conn = engine.connect()
conn.execute("PRAGMA foreign_keys = ON")

# MetaData is a container object that keeps together many different features of a database 
metadata = MetaData()
metadata.reflect(bind=engine)

class PacketTypes(Enum):
    CONNECTION_NONE = 0
    CONNECTION_REQ = 1
    CONNECTION_RSP = 2
    CLIENT_LIST_REQ = 3
    CLIENT_LIST_RSP = 4
    STOCK_LIST_REQ = 5
    STOCK_LIST_RSP = 6
    STOCK_REQ = 7
    STOCK_RSP = 8
    BOOK_INQUIRY_REQ = 9
    BOOK_INQUIRY_RSP = 10
    NEW_ORDER_REQ = 11
    NEW_ORDER_RSP = 12
    MARKET_STATUS_REQ = 13
    MARKET_STATUS_RSP = 14
    END_REQ = 15
    END_RSP = 16
    SERVER_DOWN_REQ = 17
    SERVER_DOWN_RSP = 18
     
class Packet:
    def __init__(self):
        self.m_type = 0
        self.m_msg_size = 0
        self.m_data_size = 0
        self.m_data = ""
    
    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"
    
    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__) + "\n"
    
    def serialize(self):
        self.m_data_size = 12 + len(self.m_data)
        self.m_msg_size = self.m_data_size
        # TODO Need to handle messages bigger than one packet 
        return self.m_type.to_bytes(4, byteorder='little') + \
                self.m_msg_size.to_bytes(4, byteorder='little') + \
                self.m_data_size.to_bytes(4, byteorder='little') + \
                bytes(self.m_data, 'utf-8')
                
    def deserialize(self, message):
        msg_len = len(message)
        msg_unpack_string = '<iii' + str(msg_len-12) + 's'
        self.m_type, self.m_msg_size, self.m_data_size, msg_data = struct.unpack(msg_unpack_string, message)
        #print("m_msg_size = ", self.m_msg_size, "m_data_size = ", self.m_data_size,)
        #print("self.msg_data:", msg_data[0:self.m_data_size-1], "msg_data", msg_data)
        self.m_data = msg_data[0:self.m_data_size-12].decode('utf-8')
        return message[self.m_data_size:]
    
# https://eodhistoricaldata.com/api/eod/AAPL.US?from=2017-01-05&to=2017-02-10&api_token=OeAFFmMliFG5orCUuwAKQ8l4WWFQ67YX&period=d&fmt=json   
requestURL = "https://eodhistoricaldata.com/api/eod/"
myEodKey = "5ba84ea974ab42.45160048"
defaultStartDate = "2020-01-01"
defaultEndDate = "2020-01-31"
def get_daily_data(symbol, startDate=defaultStartDate, endDate=defaultEndDate, apiKey=myEodKey):
    symbolURL = str(symbol) + ".US?"
    startDateURL = "from=" + str(startDate)
    endDateURL = "to=" + str(endDate)
    apiKeyURL = "api_token=" + apiKey
    completeURL = requestURL + symbolURL + startDateURL + '&' + endDateURL + '&' + apiKeyURL + '&period=d&fmt=json'
    with urllib.request.urlopen(completeURL) as req:
        data = json.load(req)
        return data  
 
def populate_stock_data(tickers, engine, table_name, start_date, end_date):
    column_names = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume']
    price_data = []
    for ticker in tickers:
        stock = get_daily_data(ticker, start_date, end_date)
        for stock_data in stock:
            price_data.append([ticker, stock_data['date'], stock_data['open'], stock_data['high'], stock_data['low'], \
                               stock_data['close'], stock_data['adjusted_close'], stock_data['volume']])
        print(price_data)
    stocks = pd.DataFrame(price_data, columns=column_names)
    stocks.to_sql(table_name, con=engine, if_exists='append', index=False)
    
def accept_incoming_connections(q=None):
    while True:
        try:
            client, client_address = fre_server.accept()
            print("%s:%s has connected." % client_address)
            client_thread = threading.Thread(target=handle_client, args=(client,q))
            client_thread.setDaemon(True)
            client_thread.start()
        except (KeyError, KeyboardInterrupt, SystemExit, Exception):
        #except (KeyboardInterrupt):
            print("Exception in accept_incoming_connections\n")
            q.put(Exception("accept_incoming_connections"))
            break

def receive(client_socket):
    """Handles receiving of messages."""
    total_client_request =  b''
    client_packet = Packet()
    msgSize = 0
    while True:
        try:
            client_request = client_socket.recv(buf_size)
            if len(client_request) > 0:
                total_client_request += client_request
                #print(total_client_request)
                msgSize += len(total_client_request)
                client_request = client_packet.deserialize(total_client_request)
                #print(client_packet.m_size, msgSize, len(client_request))
                if client_packet.m_data_size <= msgSize:
                    data = json.loads(client_packet.m_data)
                    print(type(data), data)
                    total_client_request = total_client_request[client_packet.m_data_size:]
                    msgSize = 0
                    client_request = b''
                    return client_packet.m_type, data
        except (KeyboardInterrupt):
        #except (OSError, Exception):  
        #except (OSError):  
            print("Exception in receive\n")
            raise Exception('receive')
            
def handle_client(client, q=None):  # Takes client socket as argument.
    """Handles a single client connection."""
    global symbols
    price_unit = 0.001
    while True:
        try:
            msg_type, msg_data = receive(client)
            print(msg_data) 
            clientID = msg_data["Client"]
            server_packet = Packet()
            if msg_type == PacketTypes.CONNECTION_REQ.value:
                server_packet.m_type = PacketTypes.CONNECTION_RSP.value
                if (clientID in clients.values()):
                    text = "%s duplicated connection request!" % clientID
                    server_msg = json.dumps({'Server': serverID, 'Response': text, 'Status': 'Rejected'})
                else:
                    client_symbols = list(msg_data["Symbol"].split(','))
                    if all(symbol in symbols for symbol in client_symbols):
                        text = "Welcome %s!" % clientID
                        server_msg = json.dumps({'Server': serverID, 'Response': text, 'Status': 'Ack'})
                        clients[client] = clientID
                    else:
                         text = "%s Not all your symbols are eligible!" % clientID
                         server_msg = json.dumps({'Server': serverID, 'Response': text, 'Status': 'Rejected'})
  
            elif msg_type == PacketTypes.END_REQ.value:
                text = "%s left!" % clientID
                server_msg = json.dumps({'Server':serverID, 'Response':text, 'Status':'Done'})
                server_packet.m_type = PacketTypes.END_RSP.value
  
            elif msg_type == PacketTypes.CLIENT_LIST_REQ.value:
                user_list = str('')
                for clientKey in clients:
                    user_list += clients[clientKey] + str(',')
                    print(clients[clientKey])
                server_msg = json.dumps({'Client List':user_list})
                server_packet.m_type = PacketTypes.CLIENT_LIST_RSP.value
                
            elif msg_type == PacketTypes.STOCK_LIST_REQ.value:
                stock_list = ','.join(symbols)
                server_msg = json.dumps({"Stock List":stock_list})
                server_packet.m_type = PacketTypes.STOCK_LIST_RSP.value
            
            elif msg_type == PacketTypes.SERVER_DOWN_REQ.value:
                server_msg = json.dumps({'Server':serverID, 'Status':'Server Down Confirmed'})
                server_packet.m_type = PacketTypes.SERVER_DOWN_RSP.value
            
            elif msg_type == PacketTypes.BOOK_INQUIRY_REQ.value:
                server_packet.m_type = PacketTypes.BOOK_INQUIRY_RSP.value
                if "Symbol" in msg_data and msg_data["Symbol"] != "":
                    server_msg = json.dumps(order_table.loc[order_table['Symbol'].isin(list(msg_data["Symbol"].split(',')))].to_json(orient='table'))
                else:
                    print("Bad message, missing symbol\n")
                    text = "Bad message, missing symbol"
                    server_msg = json.dumps({'Server':serverID, 'Response':text, 'Status':'Done'})
                    
            elif msg_type == PacketTypes.NEW_ORDER_REQ.value:
                server_packet.m_type = PacketTypes.NEW_ORDER_RSP.value
                if (("Symbol" not in msg_data) or ("Symbol" in msg_data and msg_data["Symbol"] == "")) or \
                    (("Side" not in msg_data) or ("Side" in msg_data and msg_data["Side"] == "")) or \
                    (("Price" not in msg_data) or ("Price" in msg_data and msg_data["Price"] == "")) or \
                    (("Qty" not in msg_data) or ("Qty" in msg_data and msg_data["Qty"] == "")):
                    print("Bad message, missing critical data item\n")
                    text = "Bad message, missing critial item"
                    server_msg = json.dumps({'Server':serverID, 'Response':text, 'Status':'Done'})   
                    
                elif ((order_table["Symbol"] == msg_data["Symbol"]) &
                    (order_table["Side"] != msg_data["Side"]) &
                    (abs(order_table["Price"] - float(msg_data["Price"])) < price_unit) &
                    (order_table["Status"] != "Filled")).any():
                    
                    mask = (order_table["Symbol"] == msg_data["Symbol"]) & \
                            (order_table["Side"] != msg_data["Side"]) & \
                            (abs(order_table["Price"] - float(msg_data["Price"])) < price_unit) & \
                            (order_table["Status"] != "Filled")
                   
                    order_qty = order_table.loc[(mask.values), 'Qty']
                    msg_order_qty = int(msg_data["Qty"])
                    if (order_qty.item() == msg_order_qty):
                        order_table.loc[(mask.values), 'Qty'] = 0
                        order_table.loc[(mask.values), 'Status'] = 'Filled'
                        msg_data["Status"] = "Fill"
                    elif (order_qty.item() < msg_order_qty):
                        order_table.loc[(mask.values), 'Qty'] = 0
                        order_table.loc[(mask.values), 'Status'] = 'Filled'
                        msg_data["Status"] = "Order Partial Fill"
                    else:
                        order_table.loc[(mask.values), 'Qty'] -= msg_order_qty
                        order_table.loc[(mask.values), 'Status'] = 'Partial Filled'
                        msg_data["Status"] = "Order Fill"
                    
                    if (order_qty.item() < msg_order_qty):
                        msg_data['Qty'] = str(order_qty.item())
                else:
                    msg_data["Status"] = "Order Reject"     
                    
                server_msg = json.dumps(msg_data)

            else:
                print("Unknown Message from Client\n")
                text = "Unknown Message from Client"
                server_msg = json.dumps({"Server":serverID, "Response":text, "Status":"Done"})
                print(server_msg)
                server_packet.m_type = PacketTypes.END_RSP.value
                
            server_packet.m_data = server_msg
            client.send(server_packet.serialize())
            data = json.loads(server_packet.m_data)
            print(data)
            # TODO Need a better logic for data['status'] == 'Rejected'
            if (server_packet.m_type == PacketTypes.END_RSP.value or (server_packet.m_type == PacketTypes.CONNECTION_RSP.value and \
                data['Status'] == "Rejected")):
                client.close()
                if server_packet.m_type == PacketTypes.END_RSP.value:
                    del clients[client]
                users = ''
                for clientKey in clients:
                    users += clients[clientKey] + ' '
                    print(users)
                return
            elif server_packet.m_type == PacketTypes.SERVER_DOWN_RSP.value:
                    Exception("Server Down")
        #except (KeyboardInterrupt, KeyError, Exception):
        except (KeyboardInterrupt):
            print("Exception in handle client")
            q.put(Exception("handle_client"))
            client.close()
            sys.exit(0) 
        except json.decoder.JSONDecodeError:
            q.put(Exception("handle_client"))
            client.close()
            sys.exit(0)
            
clients = {}

def get_stock_list():
    pairs = pd.read_csv(location_of_pairs)
    tickers = pd.concat([pairs["Ticker1"], pairs["Ticker2"]], ignore_index=True)
    tickers.drop_duplicates(keep='first', inplace=True)
    tickers.sort_values(axis=0, ascending=True, inplace=True, kind='quicksort')
    return tickers.tolist()

def generate_qty(number_of_qty):
    total_qty = 0
    list_of_qty = []
    for index in range(number_of_qty):
        qty = random.randint(1,101)
        list_of_qty.append(qty)
        total_qty += qty
    return (total_qty, list_of_qty)
    
def populate_order_table(symbols, start, end):
    price_scale = 0.05
    global order_index
    global order_table
    
    symbol_list = ','.join('"' + symbol + '"' for symbol in symbols)
    select_st = "SELECT * FROM FRE_Stocks WHERE date >= " + "\"" + start + "\"" + " AND date <= " + "\"" + end + "\"" + " AND symbol in (" + symbol_list + ");"
    result_set = engine.execute(select_st)
    result_df = pd.DataFrame(result_set.fetchall())
    result_df.columns = result_set.keys()
    order_table.drop(order_table.index, inplace=True)
    for symbol in symbols:
        stock = get_daily_data(symbol, start, end)
        for stock_data in stock:
            (total_qty, list_of_qty) = generate_qty(int((float(stock_data['high'])-float(stock_data['low']))/price_scale))
            buy_price = float(stock_data['low'])
            sell_price = float(stock_data['high'])
            daily_volume = float(stock_data['volume'])
            for index in range(0, len(list_of_qty)-1, 2):
                order_index += 1
                order_table.loc[order_index] = [order_index, symbol, 'Buy', buy_price, int((list_of_qty[index]/total_qty)*daily_volume), 'New']
                buy_price += 0.05
                order_index += 1
                order_table.loc[order_index] = [order_index, symbol, 'Sell', sell_price, int((list_of_qty[index+1]/total_qty)*daily_volume), 'New']
                sell_price -= 0.05
            
    print(order_table)
    #print(market_status, market_period)
    

def create_market_interest(index):
    global market_period
    global symbols
    market_periods = pd.bdate_range('2020-01-01', '2020-01-31').strftime("%Y-%m-%d").tolist()
    #threading.Timer(30, create_market_interest).start()
    #index = random.randint(0, len(market_periods)-1)
    #startDate = market_periods[index][0]
    #endDate = market_periods[index][1]
    startDate = market_periods[index]
    endDate = market_periods[index]
    if len(order_table) == 0 or (market_status != "Market Closed" and market_status != "Pending Closing"):
        #market_period = startDate
        populate_order_table(symbols, startDate, endDate)
    else:
        print(market_status, "No new market interest")

'''
def update_market_status(status, day):
    global market_status
    global order_index
    global order_table
    market_status = status
    create_market_interest(day)
    market_status = 'Open'
    print(market_status)
    time.sleep(30)
    market_status = 'Pending Closing'
    print(market_status)
    time.sleep(5)
    market_status = 'Market Closed'
    print(market_status)
    order_table.fillna(0)
    order_index = 0
    time.sleep(5)
    
def set_market_status(scheduler, time_in_seconds):
    value = datetime.datetime.fromtimestamp(time_in_seconds)
    print(value.strftime('%Y-%m-%d %H:%M:%S'))
    for day in range(total_market_days):
        scheduler.enter(40*day+1,1, update_market_status, argument=('Pending Open',day))
    #scheduler.enter(121,1, update_market_status, argument=('Pending Closing',))
    #scheduler.enter(181,1, update_market_status, argument=('Market Closed',))
    scheduler.run()
'''
   
port = 6510
buf_size = 4096
fre_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(socket.gethostname())
fre_server.bind((socket.gethostbyname(""), port))
location_of_pairs = 'csv/PairTrading.csv'
stock_table_name = "FRE_Stocks"

if __name__ == "__main__":
    
    q = queue.Queue()
    
    #market_status = "Not Open"
    #market_period = "2019-01-01"
    #total_market_days = 30
    order_index = 0
    
    symbols = get_stock_list()
    #symbols = []
    populate_stock_data(symbols, engine, stock_table_name, defaultStartDate, defaultEndDate)
    order_table_columns = ['OrderIndex', 'Symbol', 'Side', 'Price', 'Qty', 'Status']
    order_table = pd.DataFrame(columns=order_table_columns)
    order_table = order_table.fillna(0)
    
    create_market_interest(10)
    
    #print(order_table.loc[order_table['Symbol'] == 'CUK'].to_json(orient='table'))
    
    fre_server.listen(1)
    print("Waiting for client requests")
    try:
        #scheduler = sched.scheduler(time.time, time.sleep)
        #current_time_in_seconds = time.time()
        #scheduler_thread = Thread(target=set_market_status, args=(scheduler, current_time_in_seconds))
        #scheduler_thread.setDaemon(True)
        
        server_thread = threading.Thread(target=accept_incoming_connections, args=(q,))
        server_thread.setDaemon(True)
        
        server_thread.start()
        market_status = "Open"
        
        error = q.get()
        q.task_done()
        if error is not None:
            raise error
            
        #time.sleep(10)
        #scheduler_thread.start()
        
        #scheduler_thread.join()
        #server_thread.join()
    #except (KeyError, KeyboardInterrupt, SystemExit, Exception):
    except (KeyboardInterrupt):
        print("Exception in main\n")
        fre_server.close() 
        sys.exit(0)
#platform_server.close()
