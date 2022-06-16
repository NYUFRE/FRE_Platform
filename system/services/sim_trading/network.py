from enum import Enum
import struct


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
        return self.m_type.to_bytes(4, byteorder='little') + self.m_msg_size.to_bytes(4, byteorder='little') + \
               self.m_data_size.to_bytes(4, byteorder='little') + bytes(self.m_data, 'utf-8')

    def deserialize(self, message):
        msg_len = len(message)
        msg_unpack_string = '<iii' + str(msg_len - 12) + 's'
        self.m_type, self.m_msg_size, self.m_data_size, msg_data = struct.unpack(msg_unpack_string, message)
        self.m_data = msg_data[0:self.m_data_size - 12].decode('utf-8')
        return message[self.m_data_size:]
