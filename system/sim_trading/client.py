import sys
import time
import random
import json
from system.utility.config import ClientConfig
from system.sim_trading.network import PacketTypes, Packet

sys.path.append('../')

client_config = ClientConfig()


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

        stock_data['Stock List'] = client_config.client_symbols
        while True:
            client_packet = Packet()
            set_event(e)
            send_msg(get_market_status(client_packet))
            wait_for_an_event(e)
            market_status_data = get_response(q)
            market_status = market_status_data["Status"]
            if (market_status != "Market Closed") and (market_status != "Not Open") and (
                    market_status != "Pending Open"):
                break
            time.sleep(1)

        client_packet = Packet()
        set_event(e)
        client_msg = get_order_book(client_packet, stock_data['Stock List'])
        send_msg(client_msg)
        wait_for_an_event(e)
        data = get_response(q)
        book_data = json.loads(data)
        order_book = book_data["data"]
        print(order_book)

        order_index = 0
        for order in order_book:
            print("order:", order)
            client_packet = Packet()
            order_index += 1
            client_order_id = client_config.client_id + '_' + str(order_index)
            if order['Qty'] == 0:
                continue

            enter_a_new_order(client_packet, client_order_id, order['Symbol'],
                              'Lmt' if random.randint(1, 100) % 2 == 0 else 'Mkt',
                              'Buy' if order['Side'] == 'Sell' else 'Sell', float(order['Price']), int(order['Qty']))

            set_event(e)
            send_msg(client_packet)
            wait_for_an_event(e)
            client_config.orders.append(get_response(q))
            while not q.empty():
                client_config.orders.append(get_response(q))

        while not q.empty():
            client_config.orders.append(get_response(q))

        client_config.trade_complete = True

    except(OSError, Exception):
        q.put(PacketTypes.CONNECTION_NONE.value, Exception('join_trading_network'))
        client_config.client_socket.close()
        sys.exit(0)
