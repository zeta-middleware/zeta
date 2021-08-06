import asyncio
import ctypes
from random import randrange

import zmq
from colored import attr, bg, fg
from zeta import IPCPacket, create_base_message
from zmq.asyncio import Context

context = Context.instance()


async def pub_handler_ok():

    #  Socket to talk to server
    print("\nConnecting to zeta host IPC…", end="")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")
    print("[OK]\n")

    sunlight_raw = 20
    signal = 1
    while (True):
        sunlight = ZT_MSG()
        sunlight.SUNLIGHT_LEVEL_MSG.value.level = sunlight_raw
        print('\r SUNLIGHT LEVEL ({:02}):{}|{}{}       {}|'.format(
            sunlight.SUNLIGHT_LEVEL_MSG.value.level, fg(255 - sunlight_raw),
            bg(235 + sunlight_raw), attr(1), attr(0)),
              end="")
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
        #  Get the reply.
        await socket.recv()
        await asyncio.sleep(0.25)

    socket.close()


async def main():
    global ZT_MSG
    ZT_MSG = create_base_message("./zeta.yaml")
    # s = ZT_MSG()
    await asyncio.gather(pub_handler_ok())


try:
    asyncio.run(main())
except KeyboardInterrupt as err:
    exit(1)
