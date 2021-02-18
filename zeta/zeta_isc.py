import asyncio
import serial_asyncio as serial
from libscrc import crc8

import ctypes
from ctypes import c_uint8, c_size_t,\
    c_uint16, c_uint32, c_uint64,\
    c_int8, c_int16, c_int32, c_int64, POINTER, c_char, sizeof, cast

import zmq
from zmq.asyncio import Context
from zeta import ZetaISCPacket, ZetaISCHeader, ZetaISCHeaderDataInfo

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
        channel_data = None
        try:
            channel_data = self.__channels[cid]
        except IndexError:
            pass
        self.sem.release()
        return channel_data

    async def set_channel(self, cid, msg):
        await self.sem.acquire()
        print("changing channel")
        set_result = 0
        try:
            if self.__channels[cid] != msg:
                self.__channels[cid] = msg
                await self.channel_changed_queue.put(bytes([cid]) + msg)
        except IndexError:
            set_result = 1
        self.sem.release()
        return set_result


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
                if self.__current_pkt.header.has_data != ZetaISCPacket.NO_DATA:
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
        """ The data comes from the channel_changed_queue in the following
        format:

              +------------+---------+
        Bytes |     0      |  1 ...  |
              +------------+---------+
              | channel id | message |
              +------------+---------+
        """
        channel, *message = await channel_changed_queue.get()

        pkt = ZetaISCPacket(header=ZetaISCHeader(
            channel=channel, has_data=ZetaISCPacket.DATA_AVAILABLE),
                            data=bytes(message))
        print("Send packet to subscribers", pkt)
        # await zt_data_handler.send_command(pkt)
        await socket.send(pkt.to_bytes())


async def pub_read_handler(channel_changed_queue: asyncio.Queue):
    print("Response handler running...")
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    while True:
        pkt = ZetaISCPacket.from_bytes(await socket.recv())
        print("Received request: %s" % pkt)
        if pkt.header.op == ZetaISCPacket.OP_COMMAND:
            if pkt.header.otype == ZetaISCPacket.OTYPE_READ:
                pkt.header.op = ZetaISCPacket.OP_RESPONSE
                response_message = await zeta_isc.read_channel(
                    pkt.header.channel)
                if response_message:
                    pkt.header.status = ZetaISCPacket.STATUS_OK
                    pkt.set_data(response_message)
                else:
                    pkt.header.status = ZetaISCPacket.STATUS_FAILED

            elif pkt.header.otype == ZetaISCPacket.OTYPE_WRITE:
                pkt.header.op = ZetaISCPacket.OP_RESPONSE
                op_status = await zeta_isc.set_channel(pkt.header.channel,
                                                       pkt.data())
                if op_status:
                    pkt.header.status = ZetaISCPacket.STATUS_FAILED
                else:
                    pkt.header.status = ZetaISCPacket.STATUS_OK
                pkt.clear_data()

            await socket.send(pkt.to_bytes())


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
