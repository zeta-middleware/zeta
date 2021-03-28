#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#
import asyncio
import zmq
from random import randrange
from zmq.asyncio import Context
import ctypes

from zeta import IPCPacket, create_base_message

context = Context.instance()


# class FlagStruct(ctypes.LittleEndianStructure):
#     _pack_ = 1
#     _fields_ = [("read", ctypes.c_uint8, 1), ("write", ctypes.c_uint8, 1),
#                 ("erase", ctypes.c_uint8, 1), ("update", ctypes.c_uint8, 1)]

# class REQ(ctypes.LittleEndianStructure):
#     _pack_ = 1
#     _fields_ = [("id", ctypes.c_uint8), ("flag", FlagStruct),
#                 ("data", ctypes.c_uint8 * 32)]

# async def sub_handler():
#     print("Subscriber handler running...")
#     socket = context.socket(zmq.SUB)
#     socket.connect("tcp://localhost:5556")
#     socket.setsockopt(zmq.SUBSCRIBE, b'\x01')
#     while (True):
#         pkt = IPCPacket.from_bytes(await socket.recv())
#         print(
#             f"topic received on channel {pkt.header.channel} and has the value: {pkt.data()}"
#         )
async def pub_handler_ok():
    #  Socket to talk to server
    print("Connecting to hello world server…")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")

    while (True):
        sunlight = ZT_MSG()
        sunlight.SUNLIGHT_LEVEL_MSG.value.level = randrange(0, 65535)
        print("D: generated sunlight_level",
              sunlight.SUNLIGHT_LEVEL_MSG.value.level)
        sunlight.SUNLIGHT_LEVEL_MSG.size = ctypes.sizeof(
            sunlight.SUNLIGHT_LEVEL_MSG.value)
        print("I:", sunlight.SUNLIGHT_LEVEL_MSG.size)
        pkt = IPCPacket().set_header(
            channel=0,
            op=IPCPacket.OP_WRITE,
        ).set_data_with_struct(sunlight)

        print(">>> Request:", pkt)
        await socket.send(pkt.to_bytes())
        #  Get the reply.
        message = await socket.recv()
        print("<<< Reply:", IPCPacket.from_bytes(message))
        await asyncio.sleep(1)

    socket.close()


async def main():
    global ZT_MSG
    ZT_MSG = create_base_message("./zeta.yaml")
    s = ZT_MSG()
    # print("D:", s._fields_)
    # print("D: RESPONSE size", ctypes.sizeof(s.RESPONSE.value))
    # print("D:", type(s.RESPONSE.value))
    # s.REQUEST.value.payload = 65535
    # print("D: REQUEST payload", s.REQUEST.value.payload)
    # s.REQUEST.size = ctypes.sizeof(s.REQUEST.value)
    # print("D:", s.REQUEST.size)
    # print("D:", (s.RESPONSE.value.g.f0))
    # print("D:", (s.RESPONSE.value.g.f1))
    # print("D:", (s.RESPONSE.value.g.f2))
    # print("D:", (s.RESPONSE.value.g.f3))

    await asyncio.gather(pub_handler_ok())


asyncio.run(main())
