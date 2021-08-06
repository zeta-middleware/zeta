import asyncio
import ctypes
import sys

import zmq
from zeta import IPCPacket, create_base_message
from zmq.asyncio import Context

CONTEXT = Context.instance()


async def pub_handler_ok():
    socket = CONTEXT.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")

    sunlight_raw = 20
    signal = 1
    while (True):
        sunlight = ZT_MSG()
        sunlight.SUNLIGHT_LEVEL_MSG.value.level = sunlight_raw
        if sunlight_raw in [0, 20]:
            signal *= -1
        sunlight_raw += signal
        sunlight.SUNLIGHT_LEVEL_MSG.size = ctypes.sizeof(
            sunlight.SUNLIGHT_LEVEL_MSG.value)
        pkt = IPCPacket().set_header(
            channel=0,
            op=IPCPacket.OP_WRITE,
        ).set_data_with_struct(sunlight)

        await socket.send(pkt.to_bytes())
        await socket.recv()
        await asyncio.sleep(0.05)

    socket.close()


async def main():
    global ZT_MSG
    ZT_MSG = create_base_message("./zeta.yaml")
    await asyncio.gather(pub_handler_ok())


try:
    asyncio.run(main())
except KeyboardInterrupt as err:
    sys.exit(1)
