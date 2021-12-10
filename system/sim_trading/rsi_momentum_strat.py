import os
import sys
from queue import Queue
from typing import Dict
import datetime as dt
from system.database.fre_database import FREDatabase
from system.utility.config import ClientConfig
from system.sim_trading.network import PacketTypes, Packet
import pandas as pd
from system.market_data.fre_market_data import EODMarketData
from system.utility.helpers import usd
from system.sim_trading import sim_demo_model as sdm
from system.sim_trading import client as client

sys.path.append('../')


database = FREDatabase()
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), None) #to only use get_intraday_data() 

#Momentum Strategy
def RSIMomentumStrategy(stkInfo_object, client_config, centerline = 50, upper = 70, lower = 30, OrderIndex = 0, q = None,e = None):
    #Buy when RSI crosses above the centerline, sell if it break above the upper threshold the drops below it again
    #Short if it drops below the centerline and cover if it breaks below the lower threshold and then above it
    K1 = stkInfo_object.k1
    MA = stkInfo_object.ma
    Std = stkInfo_object.std
    RSI = stkInfo_object.rsi_queue[-1]
    Prev_RSI = stkInfo_object.rsi_queue[-2]
    Notional = stkInfo_object.notional
    current_buy = stkInfo_object.current_price_buy
    current_sell = stkInfo_object.current_price_sell

    if stkInfo_object.position == 0:  # not yet open position, could open
        if RSI > centerline and Prev_RSI < centerline:
            stkInfo_object.position = 1
            client_packet = Packet()
            OrderIndex += 1
            client_order_id = client_config.client_id + '_' + str(OrderIndex)
            stkInfo_object.qty = int(Notional / current_sell)
            print(client_order_id)
            client.enter_a_new_order(client_packet, client_order_id, stkInfo_object.ticker, 'Mkt', 'Buy', 100, stkInfo_object.qty)
            print("Open Trade in: ", stkInfo_object.ticker, "With postion: Buy", "at Price:", current_sell, "With Qty:",
                stkInfo_object.qty)
            #print("Because: Price below lower band:", usd(MA - K1 * Std))
            print(stkInfo_object.ticker, "RSI is ", RSI, "Previous RSI is ", Prev_RSI)
            print("Because: RSI crossover the 50 centerline from below")
            client.set_event(e)
            client.send_msg(client_packet)
            client.wait_for_an_event(e)
            print("send",client_packet.m_data)
            # open logic
            response_list = []
            while not q.empty():
                response_data = client.get_response(q)
                response_list.append(response_data)
                client_config.orders.append(response_data)
                print("received", repr(client_config.orders[-1]))
                #                    Trade_object = Trade(stk, response_list)
                #                    stkInfo_object.trade_list.append(Trade_object)
                #stkInfo_object.position_side = "Buy"

          
        #elif current_buy >= MA + K1 * Std:  # above upper band, go short
        elif RSI < centerline and Prev_RSI > centerline :  # above upper band, go short
            stkInfo_object.position = -1
            client_packet = Packet()
            OrderIndex += 1
            client_order_id = client_config.client_id + '_' + str(OrderIndex)
            stkInfo_object.qty = int(Notional / current_buy)
            print(client_order_id)
            client.enter_a_new_order(client_packet, client_order_id, stkInfo_object.ticker, 'Mkt', 'Sell', 100, stkInfo_object.qty)
            print(stkInfo_object.ticker, "RSI is ", RSI, "Previous RSI is ", Prev_RSI)
            print("Open Trade in: ", stkInfo_object.ticker, "With postion: Sell", "at Price:", current_buy, "With Qty: ",
                    stkInfo_object.qty)
            #print("Because: Price above upper band:", usd(MA + K1 * Std))
            print("Because: RSI retracted to the 50 centerline from above")
            client.set_event(e)
            client.send_msg(client_packet)
            client.wait_for_an_event(e)
            print("send",client_packet.m_data)
            # open logic
            response_list = []
            while not q.empty():
                response_data = client.get_response(q)
                response_list.append(response_data)
                client_config.orders.append(response_data)
                print("received", repr(client_config.orders[-1]))
    #                    Trade_object = Trade(stk, response_list)
    #                    stkInfo_object.Tradelist.append(Trade_object)
            #stkInfo_object.position_side = "Sell"

        #Closing the current pos
    elif stkInfo_object.position == 1:  # longing now
        #if current_buy >= MA - 0.75 * K1 * Std:  # above lower bound, sell to close postion
        if RSI > centerline:  # above lower bound, sell to close postion
            if Prev_RSI > upper and RSI < upper: #Check if the price retracted from high
                client_packet = Packet()
                OrderIndex += 1
                client_order_id = client_config.client_id + '_' + str(OrderIndex)
                print(client_order_id)
                client.enter_a_new_order(client_packet, client_order_id, stkInfo_object.ticker, 'Lmt', 'Sell', stkInfo_object.price_queue.queue[-1], stkInfo_object.qty)
                print(stkInfo_object.ticker, "RSI is ",RSI)
                print("Close Trade in: ", stkInfo_object.ticker, "With postion: Limit  Sell", "at Price:", current_buy, "With Qty: ",
                    stkInfo_object.qty)
            #print("Because: Price above lower band:", usd(MA))
                print("Because: RSI just dipped below 70")
                client.set_event(e)
                client.send_msg(client_packet)
                client.wait_for_an_event(e)
                print("send",client_packet.m_data)
            # close trade logic
                response_list = []
                while not q.empty():
                    client.response_data = client.get_response(q)
                    response_list.append(client.response_data)
                    client_config.orders.append(client.response_data)
                    print("received", repr(client_config.orders[-1]))
                    # Trade_object = stkInfo_object.trade_list[-1]
                    # Trade_object.CloseTrade(response_list)
                    # stkInfo_object.pnl_list.append(Trade_object.pnl)
                #TODO donot reset if order rejected
                if client.response_data['Status'] == 'Order Fill':
                    stkInfo_object.position = 0
                    stkInfo_object.qty = 0
                elif client.response_data['Status'] == 'Order Partial Fill':
                    stkInfo_object.qty -= int(client.response_data['Qty'])
            #stkInfo_object.position_side = "null"
        elif RSI < centerline:
            client_packet = Packet()
            OrderIndex += 1
            client_order_id = client_config.client_id + '_' + str(OrderIndex)
            print(client_order_id)
            client.enter_a_new_order(client_packet, client_order_id, stkInfo_object.ticker, 'Lmt', 'Sell', stkInfo_object.price_queue.queue[-1], stkInfo_object.qty)
            print(stkInfo_object.ticker, "RSI is ",RSI)
            print("Close Trade in: ", stkInfo_object.ticker, "With postion: Limit Sell", "at Price:", current_buy, "With Qty: ",
                    stkInfo_object.qty)
            #print("Because: Price above lower band:", usd(MA))
            print("Because: RSI retracted to the 50 centerline")
            client.set_event(e)
            client.send_msg(client_packet)
            client.wait_for_an_event(e)
            print("send",client_packet.m_data)
            # close trade logic
            response_list = []
            while not q.empty():
                response_data = client.get_response(q)
                response_list.append(response_data)
                client_config.orders.append(response_data)
                print("received", repr(client_config.orders[-1]))
                    # Trade_object = stkInfo_object.trade_list[-1]
                    # Trade_object.CloseTrade(response_list)
                    # stkInfo_object.pnl_list.append(Trade_object.pnl)
            #TODO donot reset if order rejected
            if response_data['Status'] == 'Order Fill':
                stkInfo_object.position = 0
                stkInfo_object.qty = 0
            elif response_data['Status'] == 'Order Partial Fill':
                stkInfo_object.qty -= int(response_data['Qty'])
        
        # shorting now
    #for when postion == -1
    else:
        #if current_sell <= MA + 0.75 * K1 * Std:  # below upper bound, buy to close postion
        if  RSI < centerline:  # below upper bound, buy to close postion
            if Prev_RSI < lower and RSI > lower: #check if price has been retraced
                client_packet = Packet()
                OrderIndex += 1
                client_order_id = client_config.client_id + '_' + str(OrderIndex)
                # TODO Check Qty if needs updates
                print(client_order_id)
                client.enter_a_new_order(client_packet, client_order_id, stkInfo_object.ticker, 'Lmt', 'Buy', stkInfo_object.price_queue.queue[-1], stkInfo_object.qty)
                print("Close Trade in: ", stkInfo_object.ticker, "With postion: Limit Buy", "at Price:", current_sell, "With Qty: ",
                    stkInfo_object.qty)
                #print("Because: RSI below upper band:", usd(MA))
                print("Because: RSI crossover 30 from below")
                client.set_event(e)
                client.send_msg(client_packet)
                client.wait_for_an_event(e)
                print("send",client_packet.m_data)
                # close trade logic
                response_list = []
                while not q.empty():
                    response_data = client.get_response(q)
                    response_list.append(response_data)
                    client_config.orders.append(response_data)
                    print("received", repr(client_config.orders[-1]))
                    #Trade_object = stkInfo_object.trade_list[-1]
                    # Trade_object.CloseTrade(response_list)
                    # stkInfo_object.pnl_list.append(Trade_object.pnl)
                #TODO donot reset if order rejected
                
                if response_data['Status'] != 'Order Reject':
                    stkInfo_object.position = 0
                    stkInfo_object.qty = 0
                elif response_data['Status'] == 'Order Partial Fill':
                    stkInfo_object.qty -= int(response_data['Qty'])
                #stkInfo_object.position_side = "null"
        elif RSI > centerline:
            client_packet = Packet()
            OrderIndex += 1
            client_order_id = client_config.client_id + '_' + str(OrderIndex)
            print(client_order_id)
            client.enter_a_new_order(client_packet, client_order_id, stkInfo_object.ticker, 'Lmt', 'Buy', stkInfo_object.price_queue.queue[-1], stkInfo_object.qty)
            print("Close Trade in: ", stkInfo_object.ticker, "With postion: Limit Buy", "at Price:", current_sell, "With Qty: ",
                    stkInfo_object.qty)
                #print("Because: RSI below upper band:", usd(MA))
            print("Because: RSI below upper band:", usd(stkInfo_object.current_price_sell))
            client.set_event(e)
            client.send_msg(client_packet)
            client.wait_for_an_event(e)
            print("send",client_packet.m_data)
                # close trade logic
            response_list = []
            while not q.empty():
                response_data = client.get_response(q)
                response_list.append(response_data)
                client_config.orders.append(response_data)
                print("received", repr(client_config.orders[-1]))
                    #Trade_object = stkInfo_object.trade_list[-1]
                    # Trade_object.CloseTrade(response_list)
                    # stkInfo_object.pnl_list.append(Trade_object.pnl)
            #TODO donot reset if order rejected
            
            if response_data['Status'] != 'Order Reject':
                stkInfo_object.position = 0
                stkInfo_object.qty = 0
            elif response_data['Status'] == 'Order Partial Fill':
                stkInfo_object.qty -= int(response_data['Qty'])
    return OrderIndex

#BBand Trading Logic
def BollingerBandStrategy(stkInfo_object,client_config, OrderIndex = None,q = None,e = None):
    #Buy when RSI crosses above the centerline, sell if it break above the upper threshold the drops below it again
    #Short if it drops below the centerline and cover if it breaks below the lower threshold and then above it
    K1 = stkInfo_object.k1
    MA = stkInfo_object.ma
    Std = stkInfo_object.std
    Notional = stkInfo_object.notional
    current_buy = stkInfo_object.current_price_buy
    current_sell = stkInfo_object.current_price_sell

    if stkInfo_object.position == 0:  # not yet open position, could open
        if current_sell <= MA - K1 * Std:
            stkInfo_object.position = 1
            client_packet = Packet()
            OrderIndex += 1
            client_order_id = client_config.client_id + '_' + str(OrderIndex)
            stkInfo_object.qty = int(Notional / current_sell)
            client.enter_a_new_order(client_packet, client_order_id, stkInfo_object.ticker, 'Mkt', 'Buy', 100, stkInfo_object.qty)
            print("Open Trade in: ", stkInfo_object.ticker, "With postion: Buy", "at Price:", current_sell, "With Qty:",
                stkInfo_object.qty)
            print("Because: Price below lower band:", usd(MA - K1 * Std))
            client.set_event(e)
            client.send_msg(client_packet)
            client.wait_for_an_event(e)
            print("send",client_packet.m_data)
            # open logic
            response_list = []
            while not q.empty():
                response_data = client.get_response(q)
                response_list.append(response_data)
                client_config.orders.append(response_data)
                print("received", repr(client_config.orders[-1]))
                #                    Trade_object = Trade(stk, response_list)
                #                    stkInfo_object.trade_list.append(Trade_object)
                #stkInfo_object.position_side = "Buy"

          
        #elif current_buy >= MA + K1 * Std:  # above upper band, go short
        elif current_buy >= MA + K1 * Std:  # above upper band, go short
            stkInfo_object.position = -1
            client_packet = Packet()
            OrderIndex += 1
            client_order_id = client_config.client_id + '_' + str(OrderIndex)
            stkInfo_object.qty = int(Notional / current_buy)
            client.enter_a_new_order(client_packet, client_order_id, stkInfo_object.ticker, 'Mkt', 'Sell', 100, stkInfo_object.qty)
            print("Open Trade in: ", stkInfo_object.ticker, "With postion: Sell", "at Price:", current_buy, "With Qty: ",
                    stkInfo_object.qty)
            print("Because: Price above upper band:", usd(MA + K1 * Std))
            client.set_event(e)
            client.send_msg(client_packet)
            client.wait_for_an_event(e)
            print("send",client_packet.m_data)
            # open logic
            response_list = []
            while not q.empty():
                response_data = client.get_response(q)
                response_list.append(response_data)
                client_config.orders.append(response_data)
                print("received", repr(client_config.orders[-1]))
    #                    Trade_object = Trade(stk, response_list)
    #                    stkInfo_object.Tradelist.append(Trade_object)
            #stkInfo_object.position_side = "Sell"

        #Closing the current pos
    elif stkInfo_object.position == 1:  # longing now
        if current_buy >= MA - 0.75 * K1 * Std:  # above lower bound, sell to close postion
            client_packet = Packet()
            OrderIndex += 1
            client_order_id = client_config.client_id + '_' + str(OrderIndex)
            client.enter_a_new_order(client_packet, client_order_id, stkInfo_object.ticker, 'Lmt', 'Sell', MA, stkInfo_object.qty)
            print("Close Trade in: ", stkInfo_object.ticker, "With postion: Sell", "at Price:", current_buy, "With Qty: ",
                stkInfo_object.qty)
            print("Because: Price above lower band:", usd(MA))
            client.set_event(e)
            client.send_msg(client_packet)
            client.wait_for_an_event(e)
            print("send",client_packet.m_data)
        # close trade logic
            response_list = []
            while not q.empty():
                client.response_data = client.get_response(q)
                response_list.append(client.response_data)
                client_config.orders.append(client.response_data)
                print("received", repr(client_config.orders[-1]))
                # Trade_object = stkInfo_object.trade_list[-1]
                # Trade_object.CloseTrade(response_list)
                # stkInfo_object.pnl_list.append(Trade_object.pnl)
            #TODO donot reset if order rejected
            if client.response_data['Status'] == 'Order Fill':
                stkInfo_object.position = 0
                stkInfo_object.qty = 0
            elif client.response_data['Status'] == 'Order Partial Fill':
                stkInfo_object.qty -= int(client.response_data['Qty'])

        # shorting now
        #for when postion == -1
    else:
        if current_sell <= MA + 0.75 * K1 * Std:  # below upper bound, buy to close postion
            client_packet = Packet()
            OrderIndex += 1
            client_order_id = client_config.client_id + '_' + str(OrderIndex)
            client.enter_a_new_order(client_packet, client_order_id, stkInfo_object.ticker, 'Lmt', 'Buy', MA, stkInfo_object.qty)
            print("Close Trade in: ", stkInfo_object.ticker, "With postion: Buy", "at Price:", current_sell, "With Qty: ",
                stkInfo_object.qty)
            client.set_event(e)
            client.send_msg(client_packet)
            client.wait_for_an_event(e)
            print("send",client_packet.m_data)
            # close trade logic
            response_list = []
            while not q.empty():
                response_data = client.get_response(q)
                response_list.append(response_data)
                client_config.orders.append(response_data)
                print("received", repr(client_config.orders[-1]))
                #Trade_object = stkInfo_object.trade_list[-1]
                # Trade_object.CloseTrade(response_list)
                # stkInfo_object.pnl_list.append(Trade_object.pnl)
            #TODO donot reset if order rejected
            
            if response_data['Status'] != 'Order Reject':
                stkInfo_object.position = 0
                stkInfo_object.qty = 0
            elif response_data['Status'] == 'Order Partial Fill':
                stkInfo_object.qty -= int(response_data['Qty'])
            #stkInfo_object.position_side = "null"
    return OrderIndex

