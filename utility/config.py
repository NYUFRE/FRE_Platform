import queue
import threading
import pandas as pd
import socket
#from socket import AF_INET, socket, SOCK_STREAM, IPPROTO_TCP, TCP_NODELAY, gethostbyname


class ClientConfig:
    def __init__(self):
        self.client_id = "client1"
        self.HOST = "127.0.0.1"
        self.PORT = 6510
        self.BUF_SIZE = 4096
        self.ADDR = (self.HOST, self.PORT)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.client_thread = threading.Thread()
        self.client_receiver = threading.Thread()
        self.server_ready = False
        
        self.orders = []

        self.client_thread_started = False
        self.trade_complete = False
        self.receiver_stop = False
        self.client_up = False
        self.client_symbols = "AAPL,XOM"


class ServerConfig:
    def __init__(self):
        self.server_id = "server"
        self.port = 6510
        self.buf_size = 4096
        self.server_thread_started = False

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.server_socket.bind((socket.gethostbyname(""), self.port))
        self.mutex = threading.Lock()

        #TODO! will remove later
        self.location_of_pairs = 'csv/PairTrading.csv'
        
        self.stock_daily_data = "server_daily_data"
        self.stock_intraday_data = "server_intraday_data"

        self.market_open_time = 50
        self.market_pending_close_time = 10
        self.market_close_time = 10
        self.order_interval_time = 5
        self.low_price_scale = 0.05
        self.high_price_scale = 5
        self.high_price_min = 1000
        self.price_unit = 100
        self.intraday_order_map = {}
        self.market_periods = []
        self.market_period_seconds = []
        self.total_market_days = 29
        self.market_status = "Not Open"
        self.server_output = "server_output.txt"
        self.order_index = 0
        self.symbols = []

        self.market_period = ""

        order_table_columns = ['OrderIndex', 'Symbol', 'Open', 'Close', 'Side', 'Price', 'Qty', 'OrigQty', 'Status']
        self.order_table = pd.DataFrame(columns=order_table_columns)
        self.order_table = self.order_table.fillna(0)
        self.order_table['Price'] = self.order_table['Price'].astype(float)
        self.order_table['Open'] = self.order_table['Open'].astype(float)
        self.order_table['Close'] = self.order_table['Close'].astype(float)
        self.order_table['Qty'] = self.order_table['Qty'].astype(int)
        self.order_table['OrigQty'] = self.order_table['OrigQty'].astype(int)


trading_queue = queue.Queue()
trading_event = threading.Event()

