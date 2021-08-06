import asyncio
import sys

import zmq
from colored import attr, bg
from zeta import IPCPacket, create_base_message
from zmq.asyncio import Context

CONTEXT = Context.instance()
COUNTER = 0


async def sub_handler():
    global COUNTER
    socket = CONTEXT.socket(zmq.SUB)
    socket.connect("tcp://localhost:5556")
    socket.setsockopt(zmq.SUBSCRIBE, b'\x01')

    ZT_MSG = create_base_message("./zeta.yaml")
    msg = ZT_MSG()

    while (True):
        pkt = IPCPacket.from_bytes(await socket.recv())
        pkt.struct_contents_set(msg)
        if msg.LIGHT_STATUS_MSG.value.is_on:
            COUNTER += 1
        print("pub")
        if COUNTER >= 3:
            raise GeneratorExit(int(COUNTER == 0))


async def monitor():
    await asyncio.sleep(60)
    if COUNTER > 0:
        print("Test pass!")
    else:
        print("Test failed!")
    raise GeneratorExit(int(COUNTER == 0))


async def main():
    await asyncio.gather(monitor(), sub_handler())


try:
    asyncio.run(main())
except KeyboardInterrupt:
    sys.exit(0)
except GeneratorExit as err:
    sys.exit(err.args[0])
