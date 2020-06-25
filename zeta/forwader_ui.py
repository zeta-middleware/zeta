#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import base64
from datetime import datetime
from functools import partial
from pathlib import Path

from serial.tools import list_ports

import hexdump
import serial_asyncio
import urwid

from .zeta import Zeta


class ZetaCLIEventListWalker(urwid.ListWalker):
    def __init__(self, event_list=[]):
        urwid.ListWalker.__init__(self)
        self.event_list = event_list
        self.table_rows = []
        self.focus = 0
        self.table_title = None
        self.data_viewer = None

    def __create_table_header(self):
        return urwid.AttrMap(urwid.Columns([
            (8, urwid.Text("Msg", align='center')),
            (1, urwid.Divider(' ')),
            (12, urwid.Text("Timestamp", align='center')),
            (1, urwid.Divider(' ')),
            (4, urwid.Text("Type", align='center')),
            (1, urwid.Divider(' ')),
            ('weight', 16, urwid.Text("Service", align='center')),
            (1, urwid.Divider(' ')),
            ('weight', 21, urwid.Text("Channel", align='center')),
            (1, urwid.Divider(' ')),
            ('weight', 35, urwid.Text('Data', align='center')),
        ]),
                             attr_map='key,head')

    def create_table(self, title="[0/0]"):
        listbox = urwid.ListBox(self)
        self.table_title = urwid.LineBox(urwid.Frame(
            header=self.__create_table_header(), body=listbox),
                                         title,
                                         title_align='right')
        return self.table_title

    def __len__(self):
        return len(self.event_list)

    def append(self, item):
        index = len(self.event_list)
        self.event_list.append(item)
        self.table_rows.append(
            urwid.AttrMap(urwid.Columns([
                (8,
                 urwid.Button("{:0>4}".format(self.event_list[index]['id']))),
                (1, urwid.Divider('│')),
                (12,
                 urwid.Text(self.event_list[index]['timestamp'].strftime(
                     "%H:%M:%S.%f")[:-3],
                            align='center')),
                (1, urwid.Divider('│')),
                (4,
                 urwid.Text(self.event_list[index]['type'],
                            align='center',
                            wrap='ellipsis')),
                (1, urwid.Divider('│')),
                ('weight', 16,
                 urwid.Text(self.event_list[index]['service'],
                            wrap='ellipsis')),
                (1, urwid.Divider('│')),
                ('weight', 21,
                 urwid.Text(self.event_list[index]['channel'],
                            wrap='ellipsis')),
                (1, urwid.Divider('│')),
                ('weight', 35,
                 urwid.Text(hexdump.dump(self.event_list[index]['message']),
                            wrap='ellipsis')),
            ]),
                          attr_map='cell' if index % 2 else "cell2",
                          focus_map='selected'))

        self.create_data_viewer()
        if self.focus == index - 1:
            self.focus = index
            self.data_viewer.set_text(
                hexdump.hexdump(self.event_list[index]['message'],
                                result='return'))
        self.table_title.set_title(f"[{self.focus+1}/{len(self.event_list)}]")
        self._modified()

    def create_data_viewer(self):
        if self.data_viewer is None:
            self.data_viewer = urwid.Text("")
        return self.data_viewer

    def __getitem__(self, index):
        if index > (len(self.event_list) - 1):
            raise IndexError("Event list index out of range")
        return self.table_rows[index]

    def set_modified_callback(self, callback):
        """
        This function inherited from MonitoredList is not
        implemented in SimpleFocusListWalker.
        Use connect_signal(list_walker, "modified", ...) instead.
        """
        raise NotImplementedError('Use connect_signal('
                                  'list_walker, "modified", ...) instead.')

    def set_focus(self, position):
        """Set focus position."""
        self.focus = position
        self.table_title.set_title(f"[{self.focus+1}/{len(self.event_list)}]")

        self.data_viewer.set_text(
            hexdump.hexdump(self.event_list[position]['message'],
                            result='return'))
        self._modified()

    def next_position(self, position):
        """
        Return position after start_from.
        """
        if len(self) - 1 <= position:
            raise IndexError
        return position + 1

    def prev_position(self, position):
        """
        Return position before start_from.
        """
        if position <= 0:
            raise IndexError
        return position - 1

    def positions(self, reverse=False):
        """
        Optional method for returning an iterable of positions.
        """
        if reverse:
            return range(len(self) - 1, -1, -1)
        return range(len(self))


class ZetaSerialMonitor(asyncio.Protocol):
    def __init__(self, event_list, logging_widget):
        super().__init__()
        self.event_list = event_list
        self.logging_ui = logging_widget
        self.line_buffer = bytearray()
        zeta_yaml_path = Path('./zeta.yaml')
        if zeta_yaml_path.exists():
            with zeta_yaml_path.open() as zeta_yaml:
                self.zeta = Zeta(zeta_yaml)

    def connection_made(self, transport):
        self.transport = transport
        print('port opened', transport)
        # asyncio.ensure_future(self.send())
        #transport.serial.rts = False  # You can manipulate Serial object via transport
        # transport.write(b'Hello, World!\n')  # Write serial data via transport

    def digest_isc_message(self, msg):
        msg_raw = base64.b64decode(msg[7:])

        mtype = ["READ", "PUBL", "CLBK", "STRG"]
        try:
            self.event_list.append({
                "id":
                int.from_bytes(msg_raw[:4], byteorder='little'),
                "timestamp":
                datetime.now(),  # current_time,
                "service":
                self.zeta.services[msg_raw[4]].name
                if msg_raw[4] < len(self.zeta.services) else "ZT_STORAGE",
                "channel":
                self.zeta.channels[msg_raw[5]].name,
                "type":
                mtype[msg_raw[6]],
                "message":
                msg_raw[8:8 + msg_raw[7]]
            })
        except IndexError:
            pass  # Invalid packet


# struct zt_isc_packet {
#     u32_t id;
#     u8_t service_id;
#     u8_t channel_id;
#     u8_t op;
#     u8_t size;
#     u8_t message[$max_channel_size];
# } __attribute__((packed));

    def data_received(self, data):
        for c in data:
            if c != 0x0d and c != 0x0a:
                self.line_buffer.append(c)
            if c == 0x0d:
                if self.line_buffer.find(b"@ZT_ISC:") == 0:
                    self.digest_isc_message(self.line_buffer)
                else:
                    self.logging_ui.body.append(
                        urwid.AttrMap(urwid.Text(
                            self.line_buffer.decode("utf-8")),
                                      attr_map='log',
                                      focus_map='selected'))
                    self.logging_ui.body.focus = len(self.logging_ui.body) - 1

                self.line_buffer = bytearray()

    def connection_lost(self, exc):
        print('port closed')
        self.transport.loop.stop()

    def pause_writing(self):
        print('pause writing')
        print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        print(self.transport.get_write_buffer_size())
        print('resume writing')

    async def send(self):
        """Send four newline-terminated messages, one byte at a time.
        """
        message = b'foo\nbar\nbaz\nqux\n'
        for b in message:
            # await asyncio.sleep(0.5)
            self.transport.serial.write(bytes([b]))
            print(f'Writer sent: {bytes([b])}')
        self.transport.close()


def main(serial_port="", baudrate=115200):
    # palette = [
    #     ('body', 'black', 'dark green', 'standout'),
    #     ('foot', 'light gray', 'black'),
    #     ('key', 'light green', 'black', 'underline'),
    #     ('selected', 'black', 'light blue'),
    #     ('cell', 'black', 'light green', 'underline'),
    #     ('cell2', 'black', 'dark green', 'underline'),
    #     ('title', 'white', 'black'),
    # ]
    palette_dark = [
        ('body', '', 'black', 'standout'),
        ('foot', 'light gray', 'black'),
        ('key', 'light green', 'black', 'underline'),
        ('selected', 'black', 'light green'),
        ('cell', 'dark blue', 'black', 'standout'),
        ('cell2', 'dark magenta', 'black', 'standout'),
        ('title', 'white', 'black'),
        ('log', 'dark cyan', 'black'),
    ]

    footer_text = [
        ('title', "Zeta-CLI ISC sniffer"),
        "    ",
        ('key', "UP"),
        ", ",
        ('key', "DOWN"),
        ", ",
        ('key', "PAGE UP"),
        " and ",
        ('key', "PAGE DOWN"),
        " move view    ",
        # ('key', "D"),
        # " change uart device   ",
        # ('key', "F"),
        # " Focus on new msg   ",
        ('key', "Q"),
        " exits",
    ]

    def handle_key(input):
        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        # if input in ('d', 'D'):
        #     print("D")

    event_list = ZetaCLIEventListWalker([])

    uart_device_header = urwid.Padding(
        urwid.Columns([('weight', 70, urwid.Text(footer_text)),
                       ('weight', 30,
                        urwid.Text(["Serial device: ", ('key', serial_port)],
                                   align='right'))]),
        left=1,
        right=1,
    )
    logging = urwid.ListBox(urwid.SimpleFocusListWalker([]))
    body = urwid.Columns([
        ('weight', 50, event_list.create_table()),
        ('weight', 50,
         urwid.Pile([('weight', 10,
                      urwid.LineBox(title="Raw data",
                                    title_align='left',
                                    original_widget=urwid.Filler(
                                        event_list.create_data_viewer(),
                                        valign='top'))),
                     ('weight', 60,
                      urwid.LineBox(
                          original_widget=logging,
                          title="Device log",
                          title_align='left',
                      ))]))
    ])

    aloop = asyncio.get_event_loop()
    monitor = partial(ZetaSerialMonitor, event_list, logging)
    coro = serial_asyncio.create_serial_connection(aloop, monitor, serial_port,
                                                   baudrate)
    aloop.run_until_complete(coro)

    u_event_loop = urwid.AsyncioEventLoop(loop=aloop)
    view = urwid.Frame(urwid.AttrWrap(body, 'body'),
                       footer=urwid.AttrMap(uart_device_header, 'foot'))
    loop = urwid.MainLoop(view,
                          palette_dark,
                          unhandled_input=handle_key,
                          event_loop=u_event_loop)
    loop.run()


def terminal_ui():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('serial_port', help='an integer for the accumulator')
    parser.add_argument('baudrate',
                        help='sum the integers (default: find the max)')
    args = parser.parse_args()
    print(args)
    main(serial_port=args.serial_port, baudrate=args.baudrate)


if __name__ == "__main__":
    terminal_ui()
