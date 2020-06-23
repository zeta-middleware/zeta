#!/usr/bin/python3

import textwrap
import unittest
from collections import namedtuple

MsgType = namedtuple('MsgCode', "statement separator begin end sizable")


class ZetaMessage:
    def __init__(
            self,
            name: str,
            mtype: str = '',
            size: int = 0,
            description: str = "",
            fields: list = None,
            # bitarray_child: bool = False,
            level: int = 0) -> None:
        self.name = name
        self.size = size
        self.description = description
        self.mtype = None
        self.digest_type(mtype)
        self.fields = []
        self.level = level
        if fields is not None:
            for field in fields:
                print(field.items())
                for name, sub_fields in field.items():
                    print(name, sub_fields)
                    self.fields.append(
                        ZetaMessage(name, level=self.level + 1, **sub_fields))

    def digest_type(self, mtype):
        if mtype == 'struct':
            self.mtype = MsgType(
                statement="struct",
                separator="",
                begin="{",
                end="}",
                sizable=f"[{self.size}]" if self.size > 0 else "")
        elif mtype == 'union':
            self.mtype = MsgType(
                statement="union",
                separator="",
                begin="{",
                end="}",
                sizable=f"[{self.size}]" if self.size > 0 else "")
        elif mtype == 'bitarray':
            self.mtype = MsgType(
                statement="struct",
                separator="",
                begin="{",
                end="} __attribute__((packed))",
                sizable=f"[{self.size}]" if self.size > 0 else "")

        elif mtype == 'bits':
            self.mtype = MsgType(
                statement="unsigned int",
                separator="",
                begin="",
                end="",
                sizable=f":{self.size}" if self.size > 0 else "")
        else:
            if mtype in ['u8', 's8', 'u16', 's16', 'u32', 's32', 'u64', 's64']:
                self.mtype = MsgType(
                    statement=mtype + "_t",
                    separator="",
                    begin="",
                    end="",
                    sizable=f"[{self.size}]" if self.size > 0 else "")

    def code(self):
        return textwrap.indent(
            self.mtype.statement + " " + self.mtype.begin +
            self.mtype.separator.join([x.code() for x in self.fields]) +
            self.mtype.end + self.name + self.mtype.sizable + ";",
            prefix="    " * self.level)


class TestStringMethods(unittest.TestCase):
    def test_primitives(self):
        self.assertEqual(
            "unsigned int var:1;",
            ZetaMessage('var', **{
                'mtype': 'bits',
                'size': 1
            }).code())
        self.assertEqual(
            "s8_t vars8b;",
            ZetaMessage('vars8b', **{
                'mtype': 's8',
                'size': 0
            }).code())
        self.assertEqual(
            "u8_t var8b;",
            ZetaMessage('var8b', **{
                'mtype': 'u8',
                'size': 0
            }).code())
        self.assertEqual(
            "s16_t erwoeiruwoeirs16b;",
            ZetaMessage('erwoeiruwoeirs16b', **{
                'mtype': 's16',
                'size': 0
            }).code())
        self.assertEqual(
            "u16_t var16bfff;",
            ZetaMessage('var16bfff', **{
                'mtype': 'u16',
                'size': 0
            }).code())
        self.assertEqual(
            "s32_t erwoeiru32b;",
            ZetaMessage('erwoeiru32b', **{
                'mtype': 's32',
                'size': 0
            }).code())
        self.assertEqual(
            "u32_t var32fdd;",
            ZetaMessage('var32fdd', **{
                'mtype': 'u32',
                'size': 0
            }).code())
        self.assertEqual(
            "s64_t erw64iru32b;",
            ZetaMessage('erw64iru32b', **{
                'mtype': 's64',
                'size': 0
            }).code())

        self.assertEqual(
            "    s64_t erw64iru32b;",
            ZetaMessage('erw64iru32b', **{
                'mtype': 's64',
                'size': 0
            }, level=1).code())
        self.assertEqual(
            "                s64_t erw64iru32b;",
            ZetaMessage('erw64iru32b', **{
                'mtype': 's64',
                'size': 0
            }, level=4).code())

    def test_struct_simple(self):
        self.assertEqual(
            "",
            ZetaMessage(
                'my_struct', **{
                    'mtype': 'struct',
                    'fields': [{
                        'var64bits': {
                            'mtype': 's64'
                        }
                    }]
                }).code())

    def test_union_simple(self):
        pass

    def test_bitarray_simple(self):
        pass

    def test_array_simple(self):
        pass


if __name__ == "__main__":
    unittest.main()
