# -*- coding: utf-8 -*-
# !/usr/bin/env python3
# @ Copyright -


import os
import sys
import json
import pandas as pd
import random
import numpy as np

import sched, time
import datetime

import pandas_market_calendars as mcal

import threading

from system.services.sim_trading.network import PacketTypes, Packet
from system.services.utility.config import trading_queue, ServerConfig

sys.path.append('../')

from system import EODMarketData
from system import FREDatabase
from typing import Iterable, List, Dict
from collections import defaultdict

server_config = ServerConfig()

#pd.set_option('display.max_rows', 500)
#pd.set_option('display.max_columns', 500)
#pd.set_option('display.width', 1000)

pd.set_option("display.max_rows", None, "display.max_columns", None)

database = FREDatabase()
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

class MarketDates:  
    start_date = None
    end_date = None
    
    @classmethod
    def get_market_periods(cls):
        cls.end_date = datetime.datetime.today()  
        cls.start_date = cls.end_date + datetime.timedelta(-server_config.total_market_days)
        trading_calendar = mcal.get_calendar('NYSE')
        server_config.market_periods = trading_calendar.schedule(
            start_date=cls.start_date.strftime("%Y-%m-%d"),
            end_date=cls.end_date.strftime("%Y-%m-%d")).index.strftime("%Y-%m-%d").tolist()[:-1]      
        server_config.total_market_days = len(server_config.market_periods)
        
        market_period_objects = trading_calendar.schedule(start_date=cls.start_date.strftime("%Y-%m-%d"),
                                                  end_date=cls.end_date.strftime("%Y-%m-%d")).index.tolist()[:-1]
        
        cls.start_date = server_config.market_periods[0]
        cls.end_date = server_config.market_periods[-1]
        print(server_config.market_periods, file=server_config.server_output)
          # Update for remove non-trading days
        return cls.start_date, cls.end_date, market_period_objects
        

def populate_intraday_order_map(symbols: Iterable[str], intraday_data_table: str, market_periods: List[str]) -> Dict[
    str, List]:

    for period in market_periods:
        server_config.intraday_order_map[period] = []

    stock_market_periods = defaultdict(list)
    for symbol in symbols:
        select_st = f"SELECT * FROM {intraday_data_table} WHERE symbol = '{symbol}';"
        result_df = database.execute_sql_statement(select_st)
        for i in range(len(market_periods)):
            if (result_df['datetime'].str.contains(market_periods[i])).any():
                mask = (result_df['datetime'].str.contains(market_periods[i])) & (result_df['symbol'] == symbol)
                result = result_df.loc[mask.values]
                server_config.intraday_order_map[market_periods[i]].append(
                    result[['symbol', 'open', 'high', 'low', 'close', 'volume']])
                stock_market_periods[symbol].append(market_periods[i])

    # print(intraday_order_map, file=intrday_order_file)

    return stock_market_periods


def accept_incoming_connections(q=None):
    while True:
        try:
            client, client_address = server_config.server_socket.accept()
            print("%s:%s has connected." % client_address, file=server_config.server_output)
            client_thread = threading.Thread(target=handle_client, args=(client, q))
            client_thread.setDaemon(True)
            client_thread.start()
        except (KeyError, KeyboardInterrupt, SystemExit, Exception):
            print("Exception in accept_incoming_connections\n", file=server_config.server_output)
            q.put(Exception("accept_incoming_connections"))
            break


def server_receive(client_socket):
    total_client_request = b''
    while True:
        try:
            client_request = client_socket.recv(server_config.buf_size)
            list_client_requests = []
            if len(client_request) > 0:
                total_client_request += client_request
                # print(total_client_request)
                msgSize = len(total_client_request)
                while msgSize > 0:
                    if msgSize > 12:
                        client_packet = Packet()
                        client_request = client_packet.deserialize(total_client_request)
                        # print(client_packet.m_size, msgSize, len(client_request))
                        if client_packet.m_data_size <= msgSize:
                            # data = json.loads(client_packet.m_data)
                            # print(type(data), data)
                            total_client_request = total_client_request[client_packet.m_data_size:]
                            msgSize = len(total_client_request)
                            client_request = b''
                            list_client_requests.append(client_packet)
                    else:
                        client_request = client_socket.recv(server_config.buf_size)
                        total_client_request += client_request
                        msgSize = len(total_client_request)

            return list_client_requests
        except (OSError, Exception):
            del clients[client_socket]
            print("Exception in receive\n", file=server_config.server_output)
            raise Exception('receive')


def handle_client(client, q=None):
    while True:
        try:
            list_client_requests = server_receive(client)
            for client_request in list_client_requests:
                msg_data = json.loads(client_request.m_data)
                msg_type = client_request.m_type
                print(msg_data, file=server_config.server_output)
                clientID = msg_data["Client"]
                server_packet = Packet()
                if msg_type == PacketTypes.CONNECTION_REQ.value:
                    server_packet.m_type = PacketTypes.CONNECTION_RSP.value
                    if clientID in clients.values():
                        text = "%s duplicated connection request!" % clientID
                        server_msg = json.dumps(
                            {'Server': server_config.server_id, 'Response': text, 'Status': 'Rejected'})
                    else:
                        client_symbol_list = list(msg_data["Symbol"].split(','))
                        if all(symbol in server_config.symbol_list for symbol in client_symbol_list):
                            text = "Welcome %s!" % clientID
                            server_msg = json.dumps(
                                {'Server': server_config.server_id, 'Response': text, 'Status': 'Ack'})
                            clients[client] = clientID
                        else:
                            text = "%s Not all your symbols are eligible!" % clientID
                            server_msg = json.dumps(
                                {'Server': server_config.server_id, 'Response': text, 'Status': 'Rejected'})
                    server_packet.m_data = server_msg
                    client.send(server_packet.serialize())
                    data = json.loads(server_packet.m_data)
                    print(data, file=server_config.server_output)

                elif msg_type == PacketTypes.END_REQ.value:
                    text = "%s left!" % clientID
                    server_msg = json.dumps({'Server': server_config.server_id, 'Response': text, 'Status': 'Done'})
                    server_packet.m_type = PacketTypes.END_RSP.value
                    server_packet.m_data = server_msg
                    client.send(server_packet.serialize())
                    data = json.loads(server_packet.m_data)
                    print(data, file=server_config.server_output)

                elif msg_type == PacketTypes.CLIENT_LIST_REQ.value:
                    user_list = str('')
                    for clientKey in clients:
                        user_list += clients[clientKey] + str(',')
                        print(clients[clientKey], file=server_config.server_output)
                    server_msg = json.dumps({'Client List': user_list})
                    server_packet.m_type = PacketTypes.CLIENT_LIST_RSP.value
                    server_packet.m_data = server_msg
                    client.send(server_packet.serialize())
                    data = json.loads(server_packet.m_data)
                    print(data, file=server_config.server_output)

                elif msg_type == PacketTypes.STOCK_LIST_REQ.value:
                    stock_list = ','.join(server_config.symbol_list)
                    server_msg = json.dumps({"Stock List": stock_list})
                    server_packet.m_type = PacketTypes.STOCK_LIST_RSP.value
                    server_packet.m_data = server_msg
                    client.send(server_packet.serialize())
                    data = json.loads(server_packet.m_data)
                    print(data, file=server_config.server_output)

                elif msg_type == PacketTypes.SERVER_DOWN_REQ.value:
                    server_msg = json.dumps({'Server': server_config.server_id, 'Status': 'Server Down Confirmed'})
                    server_packet.m_type = PacketTypes.SERVER_DOWN_RSP.value
                    server_packet.m_data = server_msg
                    client.send(server_packet.serialize())
                    data = json.loads(server_packet.m_data)
                    print(data, file=server_config.server_output)

                elif msg_type == PacketTypes.BOOK_INQUIRY_REQ.value:
                    server_packet.m_type = PacketTypes.BOOK_INQUIRY_RSP.value
                    if "Symbol" in msg_data and msg_data["Symbol"] != "":
                        if server_config.order_table.empty:
                            print("Server order book is empty\n", file=server_config.server_output)
                            text = "Server order book is empty"
                            server_msg = json.dumps(
                                {'Server': server_config.server_id, 'Response': text, 'Status': 'Done'})
                        else:
                            server_msg = json.dumps(
                                server_config.order_table.loc[server_config.order_table['Symbol'].isin(
                                    list(msg_data["Symbol"].split(',')))].to_json(orient='table'))
                    else:
                        print("Bad message, missing symbol\n", file=server_config.server_output)
                        text = "Bad message, missing symbol"
                        server_msg = json.dumps({'Server': server_config.server_id, 'Response': text, 'Status': 'Done'})
                    server_packet.m_data = server_msg
                    client.send(server_packet.serialize())
                    data = json.loads(server_packet.m_data)
                    print(data, file=server_config.server_output)

                elif msg_type == PacketTypes.MARKET_STATUS_REQ.value:
                    server_packet.m_type = PacketTypes.MARKET_STATUS_RSP.value
                    server_msg = json.dumps({'Server': server_config.server_id, 'Status': server_config.market_status,
                                             'Market_Period': server_config.market_period, 'Market_End_Date': MarketDates.end_date})
                    server_packet.m_data = server_msg
                    client.send(server_packet.serialize())
                    data = json.loads(server_packet.m_data)
                    print(data, file=server_config.server_output)

                elif msg_type == PacketTypes.NEW_ORDER_REQ.value:
                    server_packet.m_type = PacketTypes.NEW_ORDER_RSP.value

                    if server_config.market_status == "Market Closed":
                        msg_data["Status"] = "Order Reject"
                        server_msg = json.dumps(msg_data)
                        server_packet.m_data = server_msg
                        client.send(server_packet.serialize())
                        data = json.loads(server_packet.m_data)
                        print(data, file=server_config.server_output)

                    server_config.mutex.acquire()

                    if (("Symbol" not in msg_data) or (msg_data["Symbol"] == "")) or \
                            (("Side" not in msg_data) or (msg_data["Side"] == "")) or \
                            (("Type" not in msg_data) or (msg_data["Type"] == "")) or \
                            (("Price" not in msg_data) or (msg_data["Type"] == "Lmt" and msg_data["Price"] == "")) or \
                            (("Qty" not in msg_data) or (msg_data["Qty"] == "") or int(msg_data["Qty"]) < 1):
                        print("Bad message, missing critical data item\n", file=server_config.server_output)
                        text = "Bad message, missing critial item"
                        server_msg = json.dumps({'Server': server_config.server_id, 'Response': text, 'Status': 'Done'})
                        server_packet.m_type = PacketTypes.NEW_ORDER_RSP.value
                        server_packet.m_data = server_msg
                        client.send(server_packet.serialize())
                        data = json.loads(server_packet.m_data)
                        print(data, file=server_config.server_output)

                    if msg_data["Type"] == "Lmt":

                        msg_order_qty = int(msg_data["Qty"])

                        for (index, row) in server_config.order_table.iterrows():
                            if msg_data["Status"] == "Order Fill":
                                break

                            if ((row["Symbol"] == msg_data["Symbol"]) and
                                    (row["Side"] != msg_data["Side"]) and
                                    (row["Price"] <= float(msg_data["Price"]) if msg_data["Side"] == "Buy" else row[
                                                                                                                    "Price"] >= float(
                                        msg_data["Price"])) and
                                    (row["Status"] != "Filled") & (row["Status"] != "Open Trade") & (
                                            int(row["Qty"]) > 0)):
                                order_qty = int(row['Qty'])

                                if order_qty == msg_order_qty:
                                    server_config.order_table.loc[index, 'Qty'] = 0
                                    server_config.order_table.loc[index, 'Status'] = 'Filled'
                                    msg_data["Price"] = round(server_config.order_table.loc[index, 'Price'], 2)
                                    msg_data['Qty'] = str(msg_order_qty)
                                    msg_data["Status"] = "Order Fill"

                                elif (order_qty < msg_order_qty):
                                    server_config.order_table.loc[index, 'Qty'] = 0
                                    server_config.order_table.loc[index, 'Status'] = 'Filled'
                                    msg_data["Price"] = round(server_config.order_table.loc[index, 'Price'], 2)
                                    msg_data['Qty'] = str(order_qty)
                                    msg_data["Status"] = "Order Partial Fill"
                                    msg_order_qty -= order_qty
                                else:
                                    server_config.order_table.loc[index, 'Qty'] -= msg_order_qty
                                    server_config.order_table.loc[index, 'Status'] = 'Partial Filled'
                                    msg_data["Price"] = round(server_config.order_table.loc[index, 'Price'], 2)
                                    msg_data['Qty'] = str(msg_order_qty)
                                    msg_data["Status"] = "Order Fill"

                                msg_data["ServerOrderID"] = server_config.order_table.loc[index, 'OrderIndex']
                                server_msg = json.dumps(msg_data)
                                server_packet.m_type = PacketTypes.NEW_ORDER_RSP.value
                                server_packet.m_data = server_msg
                                client.send(server_packet.serialize())
                                data = json.loads(server_packet.m_data)
                                print(data, file=server_config.server_output)

                        if msg_data["Status"] == "New Order":
                            msg_data["Status"] = "Order Reject"
                            msg_data["Price"] = round(msg_data["Price"], 2)
                            server_msg = json.dumps(msg_data)
                            server_packet.m_type = PacketTypes.NEW_ORDER_RSP.value
                            server_packet.m_data = server_msg
                            client.send(server_packet.serialize())
                            data = json.loads(server_packet.m_data)
                            print(data, file=server_config.server_output)

                    elif msg_data["Type"] == "Mkt":

                        msg_order_qty = int(msg_data["Qty"])

                        while ((server_config.order_table["Symbol"] == msg_data["Symbol"]) &
                               (server_config.order_table["Side"] != msg_data["Side"]) &
                               (server_config.order_table["Status"] != "Filled") & (
                                       server_config.order_table["Status"] != "Open Trade") & \
                               (server_config.order_table['Qty'] != 0)).any():

                            if msg_data["Status"] == "Order Fill":
                                break

                            mask = (server_config.order_table["Symbol"] == msg_data["Symbol"]) & \
                                   (server_config.order_table["Side"] != msg_data["Side"]) & \
                                   (server_config.order_table["Status"] != "Filled") & (
                                           server_config.order_table["Status"] != "Open Trade") & \
                                   (server_config.order_table['Qty'] != 0)

                            index = -1
                            order_qty = 0
                            if msg_data["Side"] == "Sell":
                                index = server_config.order_table.loc[(mask.values), 'Price'].idxmax()
                                order_qty = int(server_config.order_table.loc[index, 'Qty'])
                            else:
                                index = server_config.order_table.loc[(mask.values), 'Price'].idxmin()
                                order_qty = int(server_config.order_table.loc[index, 'Qty'])

                            if (order_qty == msg_order_qty):
                                server_config.order_table.loc[index, 'Qty'] = 0
                                server_config.order_table.loc[index, 'Status'] = 'Filled'
                                msg_data["Price"] = round(server_config.order_table.loc[index, 'Price'], 2)
                                msg_data['Qty'] = str(msg_order_qty)
                                msg_data["Status"] = "Order Fill"

                            elif (order_qty < msg_order_qty):
                                server_config.order_table.loc[index, 'Qty'] = 0
                                server_config.order_table.loc[index, 'Status'] = 'Filled'
                                msg_data['Qty'] = str(order_qty)
                                msg_data["Price"] = round(server_config.order_table.loc[index, 'Price'], 2)
                                msg_data["Status"] = "Order Partial Fill"
                                msg_order_qty -= order_qty
                            else:
                                server_config.order_table.loc[index, 'Qty'] -= msg_order_qty
                                server_config.order_table.loc[index, 'Status'] = 'Partial Filled'
                                msg_data["Price"] = round(server_config.order_table.loc[index, 'Price'], 2)
                                msg_data['Qty'] = str(msg_order_qty)
                                msg_data["Status"] = "Order Fill"

                            msg_data["ServerOrderID"] = server_config.order_table.loc[index, 'OrderIndex']
                            server_msg = json.dumps(msg_data)
                            server_packet.m_type = PacketTypes.NEW_ORDER_RSP.value
                            server_packet.m_data = server_msg
                            client.send(server_packet.serialize())
                            data = json.loads(server_packet.m_data)
                            print(data, file=server_config.server_output)

                        if msg_data["Status"] == "New Order":
                            msg_data["Status"] = "Order Reject"
                            server_msg = json.dumps(msg_data)
                            server_packet.m_type = PacketTypes.NEW_ORDER_RSP.value
                            server_packet.m_data = server_msg
                            client.send(server_packet.serialize())
                            data = json.loads(server_packet.m_data)
                            print(data, file=server_config.server_output)

                    else:
                        msg_data["Status"] = "Order Reject"
                        server_msg = json.dumps(msg_data)
                        server_packet.m_type = PacketTypes.NEW_ORDER_RSP.value
                        server_packet.m_data = server_msg
                        client.send(server_packet.serialize())
                        data = json.loads(server_packet.m_data)
                        print(data, file=server_config.server_output)

                    server_config.mutex.release()

                else:
                    print("Unknown Message from Client\n", file=server_config.server_output)
                    text = "Unknown Message from Client"
                    server_msg = json.dumps({"Server": server_config.server_id, "Response": text, "Status": "Done"})
                    print(server_msg, file=server_config.server_output)
                    server_packet.m_type = PacketTypes.END_RSP.value

                    server_packet.m_data = server_msg
                    client.send(server_packet.serialize())
                    data = json.loads(server_packet.m_data)
                    print(data, file=server_config.server_output)

                # TODO Need a better logic for data['status'] == 'Rejected'
                if (server_packet.m_type == PacketTypes.END_RSP.value or (
                        server_packet.m_type == PacketTypes.CONNECTION_RSP.value and \
                        data['Status'] == "Rejected")):
                    client.close()
                    # del clients[client]
                    if server_packet.m_type == PacketTypes.END_RSP.value:
                        del clients[client]
                    users = ''
                    for clientKey in clients:
                        users += clients[clientKey] + ' '
                        print(users, file=server_config.server_output)
                    return
                elif server_packet.m_type == PacketTypes.SERVER_DOWN_RSP.value:
                    print("Server Down", file=server_config.server_output)
                    time.sleep(1)
                    server_config.server_socket.close()
                    server_config.server_output.close()
                    sys.exit(0)
                    # Exception("Server Down")
        except (KeyboardInterrupt, KeyError, Exception):
            print("Exception in handle client", file=server_config.server_output)
            # q.put(Exception("handle_client"))
            client.close()
            sys.exit(0)
        except json.decoder.JSONDecodeError:
            # q.put(Exception("handle_client"))
            client.close()
            sys.exit(0)


clients = {}


def get_stock_list():
    symbols = pd.read_csv(server_config.location_of_symbols)
    print(server_config.location_of_symbols, file=server_config.server_output)
    tickers = pd.concat([symbols["Ticker1"], symbols["Ticker2"]], ignore_index=True)
    tickers.drop_duplicates(keep='first', inplace=True)
    tickers.sort_values(axis=0, ascending=True, inplace=True, kind='quicksort')
    return tickers.tolist()


def generate_qty(number_of_qty):
    total_qty = 0
    list_of_qty = []
    for index in range(number_of_qty):
        qty = random.randint(1, 101)
        list_of_qty.append(qty)
        total_qty += qty
    return np.array(list_of_qty) / total_qty


def populate_order_table(symbols, start, end):
    if server_config.market_status == "Open" or server_config.market_status == "Pending Closing":
        return

    symbol_list = ','.join(f"\"{symbol}\"" for symbol in symbols)
    select_st = "SELECT * FROM " + server_config.stock_daily_data + " WHERE date >= " + "\"" + start + "\"" + \
                " AND date <= " + "\"" + end + "\"" + " AND symbol in (" + symbol_list + ");"
    result_df = database.execute_sql_statement(select_st)
    server_config.order_table.drop(server_config.order_table.index, inplace=True)
    list_of_qty_map = {}
    max_number_orders = 0
    for index, stock_data in result_df.iterrows():
        if stock_data['open'] > server_config.high_price_min:
            price_scale = server_config.high_price_scale
        else:
            price_scale = server_config.low_price_scale

        list_of_qty = generate_qty(int((float(stock_data['high']) - float(stock_data['low'])) / price_scale))
        list_of_qty_map[stock_data['symbol']] = list_of_qty
        if max_number_orders < len(list_of_qty):
            max_number_orders = len(list_of_qty)

    if server_config.mutex.locked():
        print("Is locked!", file=server_config.server_output)

    server_config.mutex.acquire()

    server_config.order_table.fillna(0)
    server_config.order_index = 0

    print(list_of_qty_map, file=server_config.server_output)
    print(max_number_orders, file=server_config.server_output)

    for index in range(0, max_number_orders - 1, 2):
        for i, stock_data in result_df.iterrows():
            if index >= len(list_of_qty_map[stock_data['symbol']]):
                continue

            buy_price = float(stock_data['low'])
            sell_price = float(stock_data['high'])
            daily_volume = float(stock_data['volume'])
            open_price = float(stock_data['open'])
            close_price = float(stock_data['close'])

            if stock_data['open'] > server_config.high_price_min:
                price_scale = server_config.high_price_scale
            else:
                price_scale = server_config.low_price_scale

            buy_price = open_price - (index + 1) * price_scale * (
                    random.randint(1, server_config.price_unit) / server_config.price_unit)
            buy_price = round(buy_price, 2)
            qty = float(list_of_qty_map[stock_data['symbol']][index])

            server_config.order_index += 1
            order_qty = int(
                qty * daily_volume * (random.randint(1, server_config.price_unit) / server_config.price_unit))
            if index == 0:
                server_config.order_table.loc[server_config.order_index] = [
                    'Srv_' + server_config.market_period + '_' + str(server_config.order_index),
                    stock_data['symbol'], open_price, close_price,
                    'Buy' if random.randint(1, 11) % 2 == 0 else 'Sell', open_price, 0, order_qty, 'Open Trade']
            else:
                server_config.order_table.loc[server_config.order_index] = [
                    'Srv_' + server_config.market_period + '_' + str(server_config.order_index),
                    stock_data['symbol'], open_price, close_price,
                    'Buy', buy_price, order_qty, order_qty, 'New']

            sell_price = open_price + (index + 1) * price_scale * (
                    random.randint(1, server_config.price_unit) / server_config.price_unit)
            sell_price = round(sell_price, 2)
            qty = float(list_of_qty_map[stock_data['symbol']][index])

            server_config.order_index += 1
            order_qty = int(
                qty * daily_volume * (random.randint(1, server_config.price_unit) / server_config.price_unit))
            server_config.order_table.loc[server_config.order_index] = [
                'Srv_' + server_config.market_period + '_' + str(server_config.order_index),
                stock_data['symbol'], open_price, close_price,
                'Sell', sell_price, order_qty, order_qty, 'New']

    server_config.order_table = server_config.order_table.sort_values(['Side', 'Symbol', 'Price', 'Qty'])

    server_config.mutex.release()

    print(server_config.order_table, file=sys.stdout)
    print(server_config.order_table, file=server_config.server_output)


def create_market_interest(symbols):
    while True:
        time.sleep(server_config.order_interval_time)
        if len(server_config.order_table) != 0 and server_config.market_status == 'Open':
            for i in range(len(symbols)):
                # Some stocks may have fewer intraday data than others,
                # it could be empty while other stocks still create intrday orders
                if server_config.intraday_order_map[server_config.market_period][i].empty:
                    continue
                symbol = symbols[i]
                try:
                    server_config.mutex.acquire()

                    ### BUY logic
                    if ((server_config.order_table['Symbol'] == symbol) & (
                            server_config.order_table['Side'] == 'Buy')).any():
                        mask = (server_config.order_table['Symbol'] == symbol) & (
                                server_config.order_table['Side'] == 'Buy')

                        best_buy_index = server_config.order_table.loc[(mask.values), 'Price'].idxmax()
                        close_price = server_config.intraday_order_map[server_config.market_period][i].iloc[0]['close']
                        open_price = server_config.intraday_order_map[server_config.market_period][i].iloc[0]['open']

                        new_buy_price = server_config.intraday_order_map[server_config.market_period][i].iloc[0]['low']
                        new_buy_price = float("{:.2f}".format(new_buy_price))
                        new_buy_qty = server_config.intraday_order_map[server_config.market_period][i].iloc[0][
                                          'volume'] / 2
                        new_buy_qty = int(new_buy_qty * random.uniform(0, 1))
                        server_config.order_index += 1

                        server_config.order_table.loc[server_config.order_index] = [
                            'Srv_' + server_config.market_period + '_' + str(server_config.order_index),
                            symbol, open_price, close_price, 'Buy',
                            new_buy_price, new_buy_qty, new_buy_qty, 'New']

                        print(server_config.order_table.loc[server_config.order_index],
                              file=server_config.server_output)

                    #### Sell
                    if ((server_config.order_table['Symbol'] == symbol) & (
                            server_config.order_table['Side'] == 'Sell')).any():
                        mask = (server_config.order_table['Symbol'] == symbol) & (
                                server_config.order_table['Side'] == 'Sell')

                        best_sell_index = server_config.order_table.loc[(mask.values), 'Price'].idxmin()
                        close_price = server_config.intraday_order_map[server_config.market_period][i].iloc[0]['close']
                        open_price = server_config.intraday_order_map[server_config.market_period][i].iloc[0]['open']

                        new_sell_price = server_config.intraday_order_map[server_config.market_period][i].iloc[0][
                            'high']
                        new_sell_price = float("{:.2f}".format(new_sell_price))
                        new_sell_qty = server_config.intraday_order_map[server_config.market_period][i].iloc[0][
                                           'volume'] / 2
                        new_sell_qty = int(new_sell_qty * random.uniform(0, 1))
                        server_config.order_index += 1

                        server_config.order_table.loc[server_config.order_index] = [
                            'Srv_' + server_config.market_period + '_' + str(server_config.order_index),
                            symbol, open_price, close_price, 'Sell',
                            new_sell_price, new_sell_qty, new_sell_qty, 'New']

                        print(server_config.order_table.loc[server_config.order_index],
                              file=server_config.server_output)

                    server_config.intraday_order_map[server_config.market_period][i].drop(
                        server_config.intraday_order_map[server_config.market_period][i].index[0], inplace=True)

                    while ((server_config.order_table['Symbol'] == symbol) & (
                            server_config.order_table['Qty'] != 0)).any():
                        buy_mask = (server_config.order_table['Symbol'] == symbol) & (
                                server_config.order_table['Qty'] != 0) & (
                                           server_config.order_table['Side'] == 'Buy')
                        sell_mask = (server_config.order_table['Symbol'] == symbol) & (
                                server_config.order_table['Qty'] != 0) & (
                                            server_config.order_table['Side'] == 'Sell')
                        buy_prices = server_config.order_table.loc[buy_mask.values, 'Price']
                        sell_prices = server_config.order_table.loc[sell_mask.values, 'Price']

                        if buy_prices.empty == False and sell_prices.empty == False:
                            best_buy_index = buy_prices.idxmax()
                            best_sell_index = sell_prices.idxmin()
                            best_buy_price = server_config.order_table.loc[best_buy_index, 'Price']
                            best_sell_price = server_config.order_table.loc[best_sell_index, 'Price']
                            # TODO Avoid floating point issue
                            if best_buy_price >= best_sell_price:
                                if server_config.order_table.loc[best_buy_index, 'Qty'] == \
                                        server_config.order_table.loc[best_sell_index, 'Qty']:
                                    server_config.order_table.loc[best_buy_index, 'Qty'] = 0
                                    server_config.order_table.loc[best_buy_index, 'Status'] = 'Filled'
                                    server_config.order_table.loc[best_sell_index, 'Qty'] = 0
                                    server_config.order_table.loc[best_sell_index, 'Status'] = 'Filled'
                                elif server_config.order_table.loc[best_buy_index, 'Qty'] > \
                                        server_config.order_table.loc[best_sell_index, 'Qty']:
                                    server_config.order_table.loc[best_buy_index, 'Qty'] -= \
                                        server_config.order_table.loc[best_sell_index, 'Qty']
                                    server_config.order_table.loc[best_buy_index, 'Status'] = 'Partial Filled'
                                    server_config.order_table.loc[best_sell_index, 'Qty'] = 0
                                    server_config.order_table.loc[best_sell_index, 'Status'] = 'Filled'
                                else:
                                    server_config.order_table.loc[best_sell_index, 'Qty'] -= \
                                        server_config.order_table.loc[best_buy_index, 'Qty']
                                    server_config.order_table.loc[best_sell_index, 'Status'] = 'Partial Filled'
                                    server_config.order_table.loc[best_buy_index, 'Qty'] = 0
                                    server_config.order_table.loc[best_buy_index, 'Status'] = 'Filled'
                            else:
                                server_config.order_table = server_config.order_table.sort_values(
                                    ['Side', 'Symbol', 'Price', 'Qty'])
                                print(server_config.order_table, file=server_config.server_output)
                                break

                        else:
                            server_config.order_table = server_config.order_table.sort_values(
                                ['Side', 'Symbol', 'Price', 'Qty'])
                            print(server_config.order_table, file=server_config.server_output)
                            break

                    server_config.mutex.release()

                except Exception as e:
                    print("Except in create market interest", file=server_config.server_output)
                    print(e, file=server_config.server_output)
                    if server_config.mutex.locked():
                        print("Still locked", file=server_config.server_output)
                        server_config.mutex.release()
                    # sys.exit(0)


# The logic need to be optimized
def close_trades(symbols):
    server_config.mutex.acquire()
    for symbol in symbols:
        side = 'Buy' if random.randint(1, 11) % 2 == 0 else 'Sell'
        if ((server_config.order_table['Symbol'] == symbol) & (server_config.order_table['Side'] == side)).any():
            mask = (server_config.order_table['Symbol'] == symbol) & (server_config.order_table['Side'] == side) & (
                    server_config.order_table['Qty'] != 0)
            if side == 'Buy':
                buy_prices = server_config.order_table.loc[(mask.values), 'Price']
                if not buy_prices.empty:
                    best_buy_index = buy_prices.idxmax()
                    server_config.order_table.loc[best_buy_index, 'Qty'] = 0
                    server_config.order_table.loc[best_buy_index, 'Status'] = 'Close Trade'
                else:
                    open_price = server_config.order_table.loc[server_config.order_index - 1, 'Open']
                    close_price = server_config.order_table.loc[server_config.order_index - 1, 'Close']
                    qty = server_config.order_table.loc[server_config.order_index, 'OrigQty']
                    server_config.order_index += 1
                    server_config.order_table.loc[server_config.order_index] = [
                        'Srv_' + server_config.market_period + '_' + str(server_config.order_index),
                        symbol, open_price, close_price, 'Buy', close_price, 0, qty, 'Close Trade']
            else:
                sell_prices = server_config.order_table.loc[(mask.values), 'Price']
                if not sell_prices.empty:
                    best_sell_index = sell_prices.idxmin()
                    server_config.order_table.loc[best_sell_index, 'Qty'] = 0
                    server_config.order_table.loc[best_sell_index, 'Status'] = 'Close Trade'
                else:
                    open_price = server_config.order_table.loc[server_config.order_index - 1, 'Open']
                    close_price = server_config.order_table.loc[server_config.order_index - 1, 'Close']
                    qty = server_config.order_table.loc[server_config.order_index, 'OrigQty']
                    server_config.order_index += 1
                    server_config.order_table.loc[server_config.order_index] = [
                        'Srv_' + server_config.market_period + '_' + str(server_config.order_index),
                        symbol, open_price, close_price, 'Sell', close_price, 0, qty, 'Close Trade']

        server_config.order_table = server_config.order_table.sort_values(['Side', 'Symbol', 'Price', 'Qty'])
        print(server_config.order_table, file=server_config.server_output)

    server_config.mutex.release()


def update_market_status(status, day):
    server_config.market_status = status
    print("day=", day, file=server_config.server_output)
    print(server_config.market_status, server_config.market_periods[day], file=server_config.server_output)
    server_config.market_period = server_config.market_periods[day]

    populate_order_table(server_config.symbol_list, server_config.market_periods[day],
                         server_config.market_periods[day])
    server_config.market_status = 'Open'
    print(server_config.market_status, file=server_config.server_output)
    time.sleep(server_config.market_open_time)
    server_config.market_status = 'Pending Closing'
    print(server_config.market_status, file=server_config.server_output)
    time.sleep(server_config.market_pending_close_time)
    server_config.market_status = 'Market Closed'
    print(server_config.market_status, file=server_config.server_output)
    close_trades(server_config.symbol_list)
    time.sleep(server_config.market_close_time)


def set_market_status(scheduler, time_in_seconds):
    value = datetime.datetime.fromtimestamp(time_in_seconds)
    print(value.strftime('%Y-%m-%d %H:%M:%S'), file=server_config.server_output)
    for day in range(server_config.total_market_days):
        scheduler.enter(
            (server_config.market_close_time + server_config.market_open_time + server_config.market_pending_close_time) * day + 1,
                        1, update_market_status, argument=('Pending Open', day))
    scheduler.run()


def launch_server():
    server_config.server_output = open("server_output.txt", "w")
    # server_config.server_output = sys.stderr
    # server_config.server_output = sys.stdout

    server_config.symbol_list = get_stock_list()
    # print(server_config.symbol_list)

    start_date, end_date, market_period_objects = MarketDates.get_market_periods()
    # print(server_config.market_periods)

    for i in range(len(market_period_objects)):
        server_config.market_period_seconds.append(
            int(time.mktime(market_period_objects[i].timetuple())))  # As timestamp is 12am of each day
    server_config.market_period_seconds.append(int(time.mktime(
        market_period_objects[len(market_period_objects) - 1].timetuple())) + 24 * 3600)  # For last day intraday data
    # print(market_period_objects, file=server_config.server_output)

    # TODO! probably it is better to harden delete table function and use it here
    # database.drop_table(server_config.stock_intraday_data)
    eod_market_data.populate_intraday_stock_data(server_config.symbol_list, server_config.stock_intraday_data,
                                                 server_config.market_period_seconds[0],
                                                 server_config.market_period_seconds[
                                                     len(server_config.market_period_seconds) - 1],
                                                 category='US', action='replace',
                                                 output_file=server_config.server_output)

    stock_market_periods = populate_intraday_order_map(server_config.symbol_list,
                                                       server_config.stock_intraday_data,
                                                       server_config.market_periods)

    print(server_config.intraday_order_map, file=server_config.server_output)

    print(stock_market_periods, file=server_config.server_output)
    for value in stock_market_periods.values():
        if server_config.total_market_days > len(value):
            server_config.total_market_days = len(value)
            server_config.market_periods = value

    print(server_config.market_periods, file=server_config.server_output)

    # TODO! probably it is better to harden delete table function and use it here
    # database.drop_table(server_config.stock_daily_data)
    eod_market_data.populate_stock_data(server_config.symbol_list,
                                        server_config.stock_daily_data,
                                        server_config.market_periods[0],
                                        server_config.market_periods[len(server_config.market_periods) - 1],
                                        category='US', action='replace', output_file=server_config.server_output)

    try:
        scheduler = sched.scheduler(time.time, time.sleep)
        current_time_in_seconds = time.time()
        scheduler_thread = threading.Thread(target=set_market_status, args=(scheduler, current_time_in_seconds))
        # scheduler_thread.setDaemon(True)

        accept_client_thread = threading.Thread(target=accept_incoming_connections, args=(trading_queue,))
        create_market_thread = threading.Thread(target=create_market_interest, args=(server_config.symbol_list,))
        # server_thread.setDaemon(True)

        server_config.server_socket.listen(1)
        print("Waiting for client requests", file=server_config.server_output)

        scheduler_thread.start()
        accept_client_thread.start()
        create_market_thread.start()

        # scheduler_thread.join()
        accept_client_thread.join()

        server_config.server_socket.close()
        server_config.server_output.close()
        sys.exit(0)

    except (KeyError, KeyboardInterrupt, SystemExit, Exception):
        print("Exception in main\n", file=server_config.server_output)
        server_config.server_socket.close()
        server_config.server_output.close()
        sys.exit(0)


if __name__ == "__main__":
    launch_server()
    print("Server is up", file=server_config.server_output)
    sys.exit(0)
