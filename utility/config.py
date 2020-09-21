# Simulated Trading
import queue
import threading
from socket import AF_INET, socket, SOCK_STREAM, IPPROTO_TCP, TCP_NODELAY


class ClientConfig:
    def __init__(self):
        self.client_id = "client1"
        self.HOST = "192.168.1.13"
        self.PORT = 6510
        self.BUF_SIZE = 4096
        self.ADDR = (self.HOST, self.PORT)

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.setsockopt(IPPROTO_TCP, TCP_NODELAY, True)
        self.client_thread = threading.Thread()
        self.client_receiver = threading.Thread()

        self.orders = []

        self.client_thread_started = False
        self.trade_complete = False
        self.client_up = False
        self.client_symbols = "AAPL,XOM"


trading_queue = queue.Queue()
trading_event = threading.Event()
client_config = ClientConfig()
