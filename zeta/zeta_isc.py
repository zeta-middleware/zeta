import asyncio
import serial_asyncio as serial
from libscrc import crc8

import ctypes
from ctypes import c_uint8, c_size_t,\
    c_uint16, c_uint32, c_uint64,\
    c_int8, c_int16, c_int32, c_int64, POINTER, c_char, sizeof, cast

import zmq
from zmq.asyncio import Context

zeta_isc = None
context = Context.instance()


class ZT_MSG_U8(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("size", c_size_t),
        ("value", c_uint8),
    ]


class ZT_MSG_U16(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("size", c_size_t),
        ("value", c_uint16),
    ]


class ZT_MSG_U32(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("size", c_size_t),
        ("value", c_uint32),
    ]


class ZT_MSG_U64(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("size", c_size_t),
        ("value", c_uint64),
    ]


class ZT_MSG_S8(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("size", c_size_t),
        ("value", c_int8),
    ]


class ZT_MSG_S16(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("size", c_size_t),
        ("value", c_int16),
    ]


class ZT_MSG_S32(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("size", c_size_t),
        ("value", c_int32),
    ]


class ZT_MSG_S64(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("size", c_size_t),
        ("value", c_int64),
    ]


class ZT_MSG_BYTES(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("size", c_size_t),
        ("value", c_uint8 * 256),
    ]


class ZT_MSG(ctypes.Union):
    _fields_ = [
        ("s8", ZT_MSG_S8),
        ("u8", ZT_MSG_U8),
        ("s16", ZT_MSG_S16),
        ("u16", ZT_MSG_U16),
        ("s32", ZT_MSG_S32),
        ("u32", ZT_MSG_U32),
        ("s64", ZT_MSG_S64),
        ("u64", ZT_MSG_U64),
        ("bytes", ZT_MSG_BYTES),
    ]


class ZetaISCPacket(ctypes.LittleEndianStructure):
    class ZetaISCHeader(ctypes.LittleEndianStructure):
        """struct zt_isc_header_op {
            uint8_t channel : 8;  /**!> 256 channels available*/
            uint8_t type : 2;     /**!> 0: event, 1: command, 2: response, 3: reserved */
            uint8_t cmd : 5;      /**!> 0: pub, 1: read, 2..: reserved */
            uint8_t has_data : 1; /**!> 0: no data, 1: contains data */
        };
        """
        _pack_ = 1
        _fields_ = [
            ("channel", c_uint8, 8),
            ("type", c_uint8, 2),
            ("cmd", c_uint8, 5),
            ("has_data", c_uint8, 1),
        ]

    class ZetaISCHeaderDataInfo(ctypes.LittleEndianStructure):
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

    _pack_ = 1
    _fields_ = [
        ("header", ZetaISCHeader),
        ("data_info", ZetaISCHeaderDataInfo),
    ]

    def __init__(self):
        self.__data = b''

    def set_data(self, data: bytes):
        self.__data = data
        self.header.has_data = 1
        self.data_info.crc = crc8(data)
        self.data_info.size = len(data)

    def data(self):
        return self.__data

    def set_header(self, data: bytes = 0):
        cast(ctypes.byref(self.header),
             POINTER(c_char * sizeof(self.header))).contents.raw = data

    def set_data_info(self, data: bytes = 0):
        cast(ctypes.byref(self.data_info),
             POINTER(c_char * sizeof(self.data_info))).contents.raw = data

    def raw_header(self):
        return cast(ctypes.byref(self),
                    POINTER(c_char * sizeof(self))).contents.raw

    def __repr__(self):
        representation = "ZetaISCPacket(\n" + \
             f"    type: {self.header.type}\n" + \
             f"    cmd: {self.header.cmd}\n" + \
             f"    channel {self.header.channel}\n" + \
             f"    crc: {self.data_info.crc}\n" + \
             f"    size: {self.data_info.size}\n" + \
             f"    data: {self.__data}\n)"
        return representation


class ZetaChannel:
    def __init__(self, cid, name, data, read_only, size, persistent, flags,
                 sem, subscribers):
        self.__name = name
        self.__cid = cid
        self.__data = data
        self.__read_only = read_only
        self.__size = size
        self.__persistent = persistent
        self.__flags = flags
        self.__subscribers = subscribers


class ZetaHighLevelISC:
    def __init__(self, zeta, channel_changed_queue: asyncio.Queue):
        self.__zeta = zeta
        self.sem = asyncio.Lock()
        self.channel_changed_queue = channel_changed_queue
        self.__channels = [b'\x01', b'\x02', b'\x03']
        self.create_channels()

    def create_channels(self):
        print("Creating channels")

    async def digest_packet(self, pkt: ZetaISCPacket):
        await self.sem.acquire()
        print("digesting pkt")
        self.sem.release()

    async def read_channel(self, cid):
        await self.sem.acquire()
        print("reading channel")
        try:
            return self.__channels[cid]
        except IndexError as exc:
            print(exc)
        self.sem.release()

    async def set_channel(self, cid, msg):
        await self.sem.acquire()
        print("changing channel")
        try:
            if self.__channels[cid] != msg:
                self.__channels[cid] = msg
                await self.channel_changed_queue.put(bytes([cid] + msg))
            return 0
        except IndexError as exc:
            print(exc)
            return 1
        self.sem.release()


class ZetaSerialDataHandler:
    STATE_DIGEST_HEADER_OP = 0
    STATE_DIGEST_HEADER_DATA_INFO = 1
    STATE_DIGEST_BODY = 2

    def __init__(self):
        self.iqueue = asyncio.Queue()
        self.oqueue = asyncio.Queue()
        self.__buffer = bytearray()
        self.__state = self.STATE_DIGEST_HEADER_OP
        self.__current_pkt = None

    async def append(self, data):
        self.__buffer.extend(data)
        await self.digest()

    async def send_command(self, cmd: ZetaISCPacket):
        await self.oqueue.put(cmd.raw_header())
        await self.oqueue.put(cmd.data())

    async def digest(self):
        if self.__state == self.STATE_DIGEST_HEADER_OP:
            if len(self.__buffer) >= 2:
                self.__current_pkt = ZetaISCPacket()
                self.__current_pkt.set_header(self.__buffer[:2])
                self.__buffer = self.__buffer[2:]
                if self.__current_pkt.header.has_data:
                    self.__state = self.STATE_DIGEST_HEADER_DATA_INFO
                else:
                    print("Only a command!")
        if self.__state == self.STATE_DIGEST_HEADER_DATA_INFO:
            if len(self.__buffer) >= 2:
                self.__current_pkt.set_data_info(self.__buffer[:2])
                self.__buffer = self.__buffer[2:]
                self.__state = self.STATE_DIGEST_BODY
        if self.__state == self.STATE_DIGEST_BODY:
            if len(self.__buffer) == self.__current_pkt.data_info.size:
                if crc8(self.__buffer) == self.__current_pkt.data_info.crc:
                    self.__current_pkt.set_data(self.__buffer)
                    print("Pkt assembled: {}".format(self.__current_pkt))
                    await zeta_isc.digest_packet(self.__current_pkt)
                    self.__current_pkt = None
                else:
                    print("CRC error, pkt discarded")
                self.__state = self.STATE_DIGEST_HEADER_OP
                self.__buffer = bytearray()

    async def run(self):
        while (True):
            data = await self.iqueue.get()
            await self.append(data)


async def uart_write_handler(w: asyncio.StreamWriter, oqueue: asyncio.Queue):
    print("Running uart write handler task")
    while True:
        data = await oqueue.get()
        # print(f"Data to be sent: {data}")
        w.write(data)


async def uart_read_handler(r, iqueue: asyncio.Queue):
    print("Running uart read handler task")
    while True:
        data = await r.read(1)
        await iqueue.put(data)


def struct_contents(struct):
    return cast(ctypes.byref(struct),
                POINTER(c_char * sizeof(struct))).contents.raw


def struct_contents_set(struct, raw_data):
    cast(ctypes.byref(struct),
         POINTER(c_char * sizeof(struct))).contents.raw = raw_data


async def callback_handler(channel_changed_queue: asyncio.Queue,
                           zt_data_handler: ZetaSerialDataHandler):
    print("Publisher handler running...")
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5556")
    while (True):
        channel_data = await channel_changed_queue.get()
        pkt = ZetaISCPacket()
        pkt.header.channel = channel_data[0]
        pkt.set_data(channel_data[1:])
        await zt_data_handler.send_command(pkt)
        await socket.send(channel_data)


async def pub_read_handler(channel_changed_queue: asyncio.Queue):
    print("Response handler running...")
    socket = context.socket(zmq.REP)
    # req = REQ(1, FLAG_(0, 1, 1, 0), (c_uint8 * 32)(*range(32)))
    # print(f"{ctypes.sizeof(req)} bytes: {struct_contents(req)}")
    socket.bind("tcp://*:5555")

    while True:
        message = await socket.recv()
        """
        if the message has only one byte it is a read
        """
        if len(message) == 1:
            response_message = await zeta_isc.read_channel(message)
            await socket.send(message + response_message)
        else:
            cid, *msg = message
            response_message = b'\x01'
            if await zeta_isc.set_channel(cid, msg) == 0:
                await channel_changed_queue.put(message)
                response_message = b'\x00'
            await socket.send(response_message)

        print("Received request: %s" % message)

        #  Do some 'work'
        await asyncio.sleep(1)

        #  Send reply back to client
        # await socket.send(b"\x02" + struct_contents(req))


async def isc_run(zeta, port: str = "/dev/ttyACM0", baudrate: int = 115200):
    print("Running main task", zeta)
    global zeta_isc
    channel_changed_queue = asyncio.Queue()
    zeta_isc = ZetaHighLevelISC(zeta, channel_changed_queue)
    zt_data_handler = ZetaSerialDataHandler()
    reader, writer = await serial.open_serial_connection(
        url=port,
        baudrate=baudrate,
    )
    await asyncio.gather(
        uart_write_handler(writer, zt_data_handler.oqueue),
        uart_read_handler(reader, zt_data_handler.iqueue),
        zt_data_handler.run(),
        callback_handler(channel_changed_queue, zt_data_handler),
        pub_read_handler(channel_changed_queue))
