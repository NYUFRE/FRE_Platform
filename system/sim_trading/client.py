import os
import sys
import csv
import time
import numpy as np
import pandas as pd
import random
import json
from system.utility.config import ClientConfig
from system.sim_trading.network import PacketTypes, Packet
from system.market_data.fre_market_data import EODMarketData
from system.database.fre_database import FREDatabase
from queue import Queue
from system.utility.helpers import usd
from system.sim_trading import sim_demo_model as sdm

sys.path.append('../')

client_config = ClientConfig()

database = FREDatabase()
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), None) #to only use get_intraday_data() 


def client_receive(q=None, e=None):
    total_server_response = b''
    while not client_config.receiver_stop:
        try:
            server_response = client_config.client_socket.recv(client_config.BUF_SIZE)
            total_server_response += server_response
            msgSize = len(total_server_response)
            while msgSize > 0:
                if msgSize > 12:
                    server_packet = Packet()
                    server_packet.deserialize(total_server_response)
                if msgSize > 12 and server_packet.m_data_size <= msgSize:
                    data = json.loads(server_packet.m_data)
                    q.put([server_packet.m_type, data])
                    total_server_response = total_server_response[server_packet.m_data_size:]
                    msgSize = len(total_server_response)
                    if server_packet.m_type == PacketTypes.END_RSP.value or \
                        server_packet.m_type == PacketTypes.SERVER_DOWN_RSP.value:
                        client_config.receiver_stop = True
                else:
                    server_response = client_config.client_socket.recv(client_config.BUF_SIZE)
                    total_server_response += server_response
                    msgSize = len(total_server_response)
            if not q.empty() and e.isSet():
                e.clear()
        except (OSError, Exception):
            print("Client Receiver exited\n")
            sys.exit(0)


def logon(client_packet, symbols):
    client_packet.m_type = PacketTypes.CONNECTION_REQ.value
    client_packet.m_data = json.dumps({'Client': client_config.client_id, 'Status': 'Logon', 'Symbol': symbols})
    return client_packet


def get_client_list(client_packet):
    client_packet.m_type = PacketTypes.CLIENT_LIST_REQ.value
    client_packet.m_data = json.dumps({'Client': client_config.client_id, 'Status': 'Client List'})
    return client_packet


def get_stock_list(client_packet):
    client_packet.m_type = PacketTypes.STOCK_LIST_REQ.value
    client_packet.m_data = json.dumps({'Client': client_config.client_id, 'Status': 'Stock List'})
    return client_packet


def get_market_status(client_packet):
    client_packet.m_type = PacketTypes.MARKET_STATUS_REQ.value
    client_packet.m_data = json.dumps({'Client': client_config.client_id, 'Status': 'Market Status'})
    return client_packet


def get_order_book(client_packet, symbol):
    client_packet.m_type = PacketTypes.BOOK_INQUIRY_REQ.value
    client_packet.m_data = json.dumps({'Client': client_config.client_id, 'Status': 'Book Inquiry', 'Symbol': symbol})
    return client_packet


def enter_a_new_order(client_packet, order_id, symbol, order_type, side, price, qty):
    if order_type == "Mkt":
        price = 0
    client_packet.m_type = PacketTypes.NEW_ORDER_REQ.value
    client_packet.m_data = json.dumps(
        {'Client': client_config.client_id, 'OrderIndex': order_id, 'Status': 'New Order', 'Symbol': symbol,
         'Type': order_type, 'Side': side, 'Price': price, 'Qty': qty})
    return client_packet


def quit_connection(client_packet):
    client_packet.m_type = PacketTypes.END_REQ.value
    client_packet.m_data = json.dumps({'Client': client_config.client_id, 'Status': 'Client Quit'})
    return client_packet


def server_down(client_packet):
    client_packet.m_type = PacketTypes.SERVER_DOWN_REQ.value
    client_packet.m_data = json.dumps({'Client': client_config.client_id, 'Status': 'Server Down'})
    return client_packet


def send_msg(client_packet):
    client_config.client_socket.send(client_packet.serialize())
    data = json.loads(client_packet.m_data)
    print(data)
    return data


def get_response(q):
    msg_type, msg_data = q.get()
    print(msg_data)
    if msg_data is not None:
        if msg_type == PacketTypes.END_RSP.value or msg_type == PacketTypes.SERVER_DOWN_RSP.value or \
                (msg_type == PacketTypes.CONNECTION_RSP.value and msg_data["Status"] == "Rejected"):
            client_config.client_socket.close()
            sys.exit(0)
    return msg_data


def set_event(e):
    e.set()


def wait_for_an_event(e):
    while e.isSet():
        continue


def join_trading_network(q, e):
    try:
        client_packet = Packet()
        set_event(e)
        send_msg(logon(client_packet, client_config.client_symbols))
        wait_for_an_event(e)
        get_response(q)

        set_event(e)
        send_msg(get_client_list(client_packet))
        wait_for_an_event(e)
        get_response(q)

        set_event(e)
        send_msg(get_stock_list(client_packet))
        wait_for_an_event(e)
        stock_data = get_response(q)
        market_stock_list = stock_data['Stock List'].split(',')
        # print(market_stock_list)
        
        client_packet = Packet()
        set_event(e)
        send_msg(get_market_status(client_packet))
        wait_for_an_event(e)
        
        mkstatus = get_response(q)
        market_end_date = mkstatus['Market_End_Date']
        current_date = mkstatus['Market_Period']
        # print(market_end_date)
        
        selected_stocks, _ = sdm.BBDmodelStockSelector.select_highvol_stock(pd.to_datetime(current_date), market_stock_list)
        # initialize StkInfo Dict
        StockInfoDict = sdm.BBDmodelStockSelector.bollingerbands_stkinfo_init(selected_stocks)
        # print(StockInfoDict)
        base_filled_orderid = []

        # Get market period same as server side
        # end_date = datetime.datetime.today()

        # # end_date = datetime.datetime.today() - datetime.timedelta(days = 1) # yesterday
        # start_date = end_date + datetime.timedelta(-29)
        
        # trading_calendar = mcal.get_calendar('NYSE')
        # market_periods = trading_calendar.schedule(
        #     start_date=start_date.strftime("%Y-%m-%d"),
        #     end_date=end_date.strftime("%Y-%m-%d")).index.strftime("%Y-%m-%d").tolist()[:-1]
        OrderIndex = 0
        # outer loop
        while True:
            # inner loop
            while True:
                client_packet = Packet()
                set_event(e)
                send_msg(get_market_status(client_packet))
                wait_for_an_event(e)
                # when not empty
                while not q.empty():
                    data = get_response(q)
                    if data['Status'] not in ['Open', 'Pending Closing', 'Market Closed', 'Pending Open', 'Not Open']:
                        client_config.orders.append(data)
                    else:
                        mkt_status = data
                        # print("mkt_status", mkt_status)
                # wait till mkt open
                if mkt_status["Status"] == 'Open' or mkt_status["Status"] == 'Pending Closing':
                    break
                if mkt_status['Market_Period'] == market_end_date and mkt_status["Status"] == "Market Closed":
                    # print('PnL Calculation Logic')
                    pnl_dict = {}
                    for stk in StockInfoDict:
                        stkbuy_order = [order for order in client_config.orders if
                                        (order['Symbol'] == stk) & (order['Side'] == 'Buy')]
                        # print(stkbuy_order)
                        stkbuy_price = [order['Price'] for order in stkbuy_order]
                        # print(stkbuy_price)
                        stkbuy_qty = [int(order['Qty']) for order in stkbuy_order]
                        # print(stkbuy_qty)
                        stksell_order = [order for order in client_config.orders if
                                         (order['Symbol'] == stk) & (order['Side'] == 'Sell')]
                        # print(stksell_order)
                        stksell_price = [order['Price'] for order in stksell_order]
                        # print(stksell_price)
                        stksell_qty = [int(order['Qty']) for order in stksell_order]
                        # print(stksell_qty)
                        stkPnL = sum([P * Q for P, Q in zip(stksell_price, stksell_qty)]) - sum(
                            [P * Q for P, Q in zip(stkbuy_price, stkbuy_qty)])
                        # print(stkPnL)
                        pnl_dict.update({stk: stkPnL})

                    client_config.pnl = sum(pnl_dict.values())
                    client_config.ticker_pnl = {stk: usd(pnl_dict[stk]) for stk in pnl_dict}
                    # complete the sim_trade
                    set_event(e)
                    send_msg(get_market_status(client_packet))
                    wait_for_an_event(e)
                    while not q.empty():
                        get_response(q)
                    client_config.trade_complete = True
                    break
                time.sleep(0.5)
            if client_config.trade_complete:
                break
            # close every day's position in Pending Close
            if mkt_status["Status"] == "Pending Closing":
                for stk in StockInfoDict:
                    stkInfo_object = StockInfoDict[stk]
                    stkInfo_object.ma = 'null'
                    stkInfo_object.std = 'null'
                    stkInfo_object.price_queue = Queue(int(stkInfo_object.h / 5))  # reset the members
                    if stkInfo_object.position != 0:
                        client_packet = Packet()
                        OrderIndex += 1
                        client_order_id = client_config.client_id + '_' + str(OrderIndex)
                        # if longing
                        if stkInfo_object.position > 0:
                            enter_a_new_order(client_packet, client_order_id, stk, 'Mkt', 'Sell', 100, stkInfo_object.qty)
                            print("Close Trade in: ", stk, "With postion: Sell", "With Qty: ", stkInfo_object.qty)
                            print("Because: Close at Pending Close.")
                            set_event(e)
                            send_msg(client_packet)
                            wait_for_an_event(e)
                            # close trade logic
                            response_list = []
                            while not q.empty():
                                response_data = get_response(q)
                                response_list.append(response_data)
                                client_config.orders.append(response_data)
                            stkInfo_object.qty = 0
                            stkInfo_object.position = 0

                        # if shorting
                        else:
                            enter_a_new_order(client_packet, client_order_id, stk, 'Mkt', 'Buy', 100, stkInfo_object.qty)
                            print("Close Trade in: ", stk, "With postion: Buy", "With Qty: ", stkInfo_object.qty)
                            print("Because: Close at Pending Close.")
                            set_event(e)
                            send_msg(client_packet)
                            wait_for_an_event(e)
                            # close trade logic
                            response_list = []
                            while not q.empty():
                                response_data = get_response(q)
                                response_list.append(response_data)
                                client_config.orders.append(response_data)
                            stkInfo_object.qty = 0
                            stkInfo_object.position = 0
                # re-enter into checking "Open" while-loop
                continue

            # BBD Trading Logic
            client_packet = Packet()
            set_event(e)
            client_msg = get_order_book(client_packet, ','.join(selected_stocks))
            send_msg(client_msg)
            wait_for_an_event(e)


            # when not empty or bad message
            while True:
                data = get_response(q)
                if type(data) == dict:
                    if data['Status'] != 'Done':
                        client_config.orders.append(data)
                else:
                    break

            book_data = json.loads(data)
            order_book = book_data["data"]



            filled_order_book = [fill_orders for fill_orders in order_book if fill_orders['Status'] in ['Filled']]
            # print(filled_order_book)
            filled_orderid = [order['OrderIndex'] for order in filled_order_book]
            # print(filled_orderid)
            standing_order_book = [standing_orders for standing_orders in order_book if
                                   standing_orders['Status'] in ['New', 'Partial Filled']]

            #        print(filled_order_book, file = sample)
            #        print(standing_order_book, file = sample)

            # print('test3')
            # print(StockInfoDict)
            for stk in StockInfoDict:
                # print(stk)
                standing_buy_price_list = [order['Price'] for order in standing_order_book if
                                           (order['Symbol'] == stk) & (order['Side'] == 'Buy')]
                standing_sell_price_list = [order['Price'] for order in standing_order_book if
                                            (order['Symbol'] == stk) & (order['Side'] == 'Sell')]
                StockInfoDict[stk].current_price_sell = min(standing_sell_price_list)
                StockInfoDict[stk].current_price_buy = max(standing_buy_price_list)
            # print('test2')
            # store current price in price queue and use it to calculate MA and std
            for stk in StockInfoDict:
                stkInfo_object = StockInfoDict[stk]
                # current price is based on filled_order_book
                if len(base_filled_orderid) == 0:
                    current_price = (stkInfo_object.current_price_buy + stkInfo_object.current_price_sell) / 2
                    base_filled_orderid = filled_orderid
                else:
                    try:
                        newly_filled_orderid = [orderid for orderid in filled_orderid if
                                                orderid not in base_filled_orderid]
                        base_filled_orderid = filled_orderid
                        newly_filled_order = [order for order in filled_order_book if
                                              order['OrderIndex'] in newly_filled_orderid]
                        filled_price_list = [order['Price'] for order in newly_filled_order]
                        filled_qty_list = [int(order['OrigQty']) for order in newly_filled_order]
                        current_price = sum([P * Q for P, Q in zip(filled_price_list, filled_qty_list)]) / sum(
                            filled_qty_list)
                        # print('test1')
                    except:  # when no newly filled
                        # print('test')
                        current_price = (stkInfo_object.current_price_buy + stkInfo_object.current_price_sell) / 2
                #            print("current price for", stk, "P= " current_price)
                if not stkInfo_object.price_queue.full():
                    stkInfo_object.price_queue.put(current_price)
                    if stkInfo_object.price_queue.full():
                        stkInfo_object.ma = np.array(stkInfo_object.price_queue.queue).mean()
                        stkInfo_object.std = np.array(stkInfo_object.price_queue.queue).std() / np.sqrt(5)
                else:  # already full
                    popout = stkInfo_object.price_queue.get()
                    stkInfo_object.price_queue.put(current_price)
                    stkInfo_object.ma = np.array(stkInfo_object.price_queue.queue).mean()
                    stkInfo_object.std = np.array(stkInfo_object.price_queue.queue).std() / np.sqrt(5)

            for stk in StockInfoDict:
                stkInfo_object = StockInfoDict[stk]
                K1 = stkInfo_object.k1
                MA = stkInfo_object.ma
                Std = stkInfo_object.std
                Notional = stkInfo_object.notional
                if MA == 'null':
                    continue
                current_buy = stkInfo_object.current_price_buy
                current_sell = stkInfo_object.current_price_sell
                #            current_p = (current_buy + current_sell) / 2
                #            print("K1: ",K1)
                #            print("MA: ",MA)
                #            print("Std: ",Std)
                #            print("sell p:",current_sell)
                #            print("buy p:",current_buy)
                if stkInfo_object.position == 0:  # not yet open position, could open
                    if current_sell <= MA - K1 * Std:  # below lower band, go long
                        stkInfo_object.position = 1
                        client_packet = Packet()
                        OrderIndex += 1
                        client_order_id = client_config.client_id + '_' + str(OrderIndex)
                        stkInfo_object.qty = int(Notional / current_sell)
                        enter_a_new_order(client_packet, client_order_id, stk, 'Mkt', 'Buy', 100, stkInfo_object.qty)
                        print("Open Trade in: ", stk, "With postion: Buy", "at Price:", current_sell, "With Qty:",
                              stkInfo_object.qty)
                        print("Because: Price below lower band:", usd(MA - K1 * Std))
                        set_event(e)
                        send_msg(client_packet)
                        wait_for_an_event(e)
                        # open logic
                        response_list = []
                        while not q.empty():
                            response_data = get_response(q)
                            response_list.append(response_data)
                            client_config.orders.append(response_data)
                    #                    Trade_object = Trade(stk, response_list)
                    #                    stkInfo_object.Tradelist.append(Trade_object)

                    elif current_buy >= MA + K1 * Std:  # above upper band, go short
                        stkInfo_object.position = -1
                        client_packet = Packet()
                        OrderIndex += 1
                        client_order_id = client_config.client_id + '_' + str(OrderIndex)
                        stkInfo_object.qty = int(Notional / current_buy)
                        enter_a_new_order(client_packet, client_order_id, stk, 'Mkt', 'Sell', 100, stkInfo_object.qty)
                        print("Open Trade in: ", stk, "With postion: Sell", "at Price:", current_buy, "With Qty: ",
                              stkInfo_object.qty)
                        print("Because: Price above upper band:", usd(MA + K1 * Std))
                        set_event(e)
                        send_msg(client_packet)
                        wait_for_an_event(e)
                        # open logic
                        response_list = []
                        while not q.empty():
                            response_data = get_response(q)
                            response_list.append(response_data)
                            client_config.orders.append(response_data)
                #                    Trade_object = Trade(stk, response_list)
                #                    stkInfo_object.Tradelist.append(Trade_object)

                elif stkInfo_object.position == 1:  # longing now
                    if current_buy >= MA:  # above lower bound, sell to close postion
                        client_packet = Packet()
                        OrderIndex += 1
                        client_order_id = client_config.client_id + '_' + str(OrderIndex)
                        enter_a_new_order(client_packet, client_order_id, stk, 'Mkt', 'Sell', 100, stkInfo_object.qty)
                        print("Close Trade in: ", stk, "With postion: Sell", "at Price:", current_buy, "With Qty: ",
                              stkInfo_object.qty)
                        print("Because: Price above lower band:", usd(MA))
                        set_event(e)
                        send_msg(client_packet)
                        wait_for_an_event(e)
                        # close trade logic
                        response_list = []
                        while not q.empty():
                            response_data = get_response(q)
                            response_list.append(response_data)
                            client_config.orders.append(response_data)
                        #                    Trade_object = stkInfo_object.Tradelist[-1]
                        #                    Trade_object.CloseTrade(response_list)
                        #                    stkInfo_object.PnLlist.append(Trade_object.PnL)
                        stkInfo_object.qty = 0
                        stkInfo_object.position = 0

                # shorting now
                else:
                    if current_sell <= MA:  # below upper bound, buy to close postion
                        client_packet = Packet()
                        OrderIndex += 1
                        client_order_id = client_config.client_id + '_' + str(OrderIndex)
                        enter_a_new_order(client_packet, client_order_id, stk, 'Mkt', 'Buy', 100, stkInfo_object.qty)
                        print("Close Trade in: ", stk, "With postion: Buy", "at Price:", current_sell, "With Qty: ",
                              stkInfo_object.qty)
                        print("Because: Price below upper band:", usd(MA))
                        set_event(e)
                        send_msg(client_packet)
                        wait_for_an_event(e)
                        # close trade logic
                        response_list = []
                        while not q.empty():
                            response_data = get_response(q)
                            response_list.append(response_data)
                            client_config.orders.append(response_data)
                        #                    Trade_object = stkInfo_object.Tradelist[-1]
                        #                    Trade_object.CloseTrade(response_list)
                        #                    stkInfo_object.PnLlist.append(Trade_object.PnL)
                        stkInfo_object.qty = 0
                        stkInfo_object.position = 0

            time.sleep(1)  # request order book every sec

    except(OSError, Exception):
        q.put(PacketTypes.CONNECTION_NONE.value, Exception('join_trading_network'))
        client_config.client_socket.close()
        sys.exit(0)
