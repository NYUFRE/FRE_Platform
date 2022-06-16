import os
import socket
import threading
import time
import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

from system.services.sim_trading.client import client_config, wait_for_an_event, server_down, send_msg, set_event, \
    client_receive

warnings.simplefilter(action='ignore', category=SAWarning)

from system import process_list

from system.services.sim_trading.network import PacketTypes, Packet

from system.services.utility.config import trading_queue, trading_event
from system.services.utility.helpers import get_python_pid


def sim_server_down_service():
    if client_config.server_ready:
        try:
            client_config.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_config.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            status = client_config.client_socket.connect_ex(client_config.ADDR)
            if status != 0:
                # TODO: Per Professor, a better clean-up logic needs to be added here
                print("sim_server_down:", str(status))
                client_config.server_tombstone = True
                client_config.server_ready = False
                # Even though connection to server failed such as return code 10016
                # But set server_tomstone to True should get server stop
                # flash("Failure in server: please restart the program")
                return render_template("sim_server_down.html")

            client_config.receiver_stop = False  # TODO Look like it is not used
            client_config.server_tombstone = True

            client_config.client_receiver = threading.Thread(target=client_receive, args=(trading_queue, trading_event))
            client_config.client_receiver.start()

            set_event(trading_event)
            client_packet = Packet()
            send_msg(server_down(client_packet))
            wait_for_an_event(trading_event)
            msg_type, msg_data = trading_queue.get()
            print(msg_data)
            if msg_type == PacketTypes.SERVER_DOWN_RSP.value:
                time.sleep(2)
                print("Server down confirmed!")
                client_config.client_socket.close()

            existing_py_process = get_python_pid()

            for item in existing_py_process:
                if item not in process_list:
                    os.kill(item, 9)

            client_config.server_ready = False
            client_config.client_thread_started = False

        except(OSError, Exception):
            # TODO Need a Web page to indicate we throw an exception and print full stack.
            client_config.server_ready = False
            client_config.server_tombstone = True
            client_config.client_thread_started = False
            return render_template("sim_server_down.html")

    return render_template("sim_server_down.html")