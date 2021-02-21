import ctypes
from ctypes import c_uint8, sizeof, cast, POINTER, c_char
from libscrc import crc8


class IPCHeader(ctypes.LittleEndianStructure):
    """

    struct zt_isc_header_op {
        uint8_t channel : 8;  /**!> 256 channels available*/
        uint8_t op : 2;     /**!> 0: event, 1: command, 2: response, 3: reserved */
        uint8_t otype : 4;      /**!> 0: pub, 1: read, 2..: reserved */
        uint8_t status : 1;      /**!> 0: ok, 1: failed */
        uint8_t has_data : 1; /**!> 0: no data, 1: contains data */
    };

    """
    _pack_ = 1
    _fields_ = [
        ("channel", c_uint8, 8),
        ("op", c_uint8, 2),
        ("otype", c_uint8, 4),
        ("status", c_uint8, 1),
        ("has_data", c_uint8, 1),
    ]


class IPCHeaderDataInfo(ctypes.LittleEndianStructure):
    """
    struct zt_isc_header_data_info {
        uint8_t crc : 8;  /**!> CCITT 8, polynom 0x07, initial value 0x00 */
        uint8_t size : 8; /**!> data size */
    };

    """
    _pack_ = 1
    _fields_ = [
        ("crc", c_uint8),
        ("size", c_uint8),
    ]


class IPCPacket(ctypes.LittleEndianStructure):
    OP_EVENT = 0
    OP_COMMAND = 1
    OP_RESPONSE = 2

    OTYPE_READ = 0
    OTYPE_WRITE = 1
    OTYPE_CHANGED = 2

    DATA_UNAVALABLE = 0
    DATA_AVAILABLE = 1

    STATUS_OK = 0
    STATUS_FAILED = 1

    _pack_ = 1
    _fields_ = [("header", IPCHeader), ("data_info", IPCHeaderDataInfo)]

    def __init__(self, *args, **kwargs):
        super(IPCPacket, self).__init__(*args, **kwargs)
        if "data" in kwargs.keys():
            self.set_data(kwargs["data"])
        else:
            self.__data = bytes()

    def set_data(self, data: bytes):
        self.header.has_data = self.DATA_AVAILABLE
        self.data_info.crc = crc8(data)
        self.data_info.size = len(data)
        self.__data = data
        return self

    def clear_data(self):
        self.header.has_data = self.DATA_UNAVALABLE
        self.data_info.crc = 0
        self.data_info.size = 0
        self.__data = bytes()

    @classmethod
    def from_bytes(cls, raw_data):
        pkt = cls()
        if len(raw_data) >= 2:
            pkt.set_header_from_bytes(raw_data[:2])
        if len(raw_data) >= 4:
            pkt.set_data_info_from_bytes(raw_data[2:4])
        if len(raw_data) >= 5:
            assert pkt.data_info.size == len(raw_data[4:])
            assert pkt.data_info.crc == crc8(raw_data[4:]), "Invalid CRC"
            pkt.set_data(raw_data[4:])
        return pkt

    def to_bytes(self):
        return (cast(ctypes.byref(self), POINTER(
            c_char * sizeof(self))).contents.raw) + self.__data

    def data(self):
        return self.__data

    def set_header(self,
                   channel: int,
                   op: int,
                   otype: int,
                   status: int = 0,
                   has_data: int = 0):
        self.header.channel = channel
        self.header.op = op
        self.header.otype = otype
        self.header.status = status
        self.header.has_data = has_data
        return self

    def set_data_info(self, crc: int, size: int):
        self.data_info.crc = crc
        self.data_info.size = size
        return self

    def set_header_from_bytes(self, data: bytes = 0):
        cast(ctypes.byref(self.header),
             POINTER(c_char * sizeof(self.header))).contents.raw = data

    def set_data_info_from_bytes(self, data: bytes = 0):
        cast(ctypes.byref(self.data_info),
             POINTER(c_char * sizeof(self.data_info))).contents.raw = data

    def header_to_bytes(self):
        return cast(ctypes.byref(self),
                    POINTER(c_char * sizeof(self))).contents.raw

    def __repr__(self):
        representation = "IPCPacket(\n" + \
             f"    channel {self.header.channel}\n" + \
             f"    op: {self.header.op}\n" + \
             f"    otype: {self.header.otype}\n" + \
             f"    status {self.header.status}\n"
        if self.header.has_data == self.DATA_AVAILABLE:
            representation += f"    crc: {self.data_info.crc}\n" + \
                              f"    size: {self.data_info.size}\n" + \
                              f"    data: {self.__data}"
        return representation + '\n)'


def struct_contents(struct):
    return cast(ctypes.byref(struct),
                POINTER(c_char * sizeof(struct))).contents.raw


def struct_contents_set(struct, raw_data):
    cast(ctypes.byref(struct),
         POINTER(c_char * sizeof(struct))).contents.raw = raw_data
