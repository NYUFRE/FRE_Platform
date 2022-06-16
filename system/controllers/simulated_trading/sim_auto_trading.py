import socket
import threading
import warnings

from flask import flash, render_template
from sqlalchemy.exc import SAWarning

from system.services.sim_trading.client import client_config, wait_for_an_event, quit_connection, send_msg, set_event, \
    join_trading_network, client_receive

warnings.simplefilter(action='ignore', category=SAWarning)

from system.services.sim_trading.network import PacketTypes, Packet

from system.services.utility.config import trading_queue, trading_event


def sim_auto_trading_service(strategy):
    if client_config.server_ready:
        if not client_config.client_thread_started:
            client_config.client_thread_started = True
            client_config.receiver_stop = False

            client_config.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_config.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            status = client_config.client_socket.connect_ex(client_config.ADDR)
            if status != 0:
                print("sim_auto_trading:", str(status))
                # client_config.client_socket.close()
                flash("Failure in server: please restart the program")
                return render_template("error_auto_trading.html")
            client_config.client_up = True
            client_config.orders = []
            client_packet = Packet()
            msg_data = {}

            client_config.client_receiver = threading.Thread(target=client_receive, args=(trading_queue, trading_event))
            client_config.client_thread = threading.Thread(target=join_trading_network,
                                                           args=(trading_queue, trading_event, strategy))

            client_config.client_receiver.start()
            client_config.client_thread.start()

        while not client_config.trade_complete:
            pass

        if client_config.client_up:
            client_config.client_up = False
            client_packet = Packet()
            msg_data = {}
            set_event(trading_event)
            send_msg(quit_connection(client_packet))
            wait_for_an_event(trading_event)
            msg_type, msg_data = trading_queue.get()
            if msg_type != PacketTypes.END_RSP.value:
                client_config.orders.append(msg_data)
                msg_type, msg_data = trading_queue.get()
            trading_queue.task_done()
            print(msg_data)
            client_config.client_thread_started = False
            # client_config.receiver_stop = True
            client_config.trade_complete = False
            client_config.client_socket.close()

        return render_template("sim_auto_trading.html", trading_results=client_config.orders,
                               pnl_results=client_config.ticker_pnl)

    else:
        return render_template("error_auto_trading.html")