#!/usr/bin/python3

import textwrap
import unittest
from collections import namedtuple

MsgType = namedtuple('MsgCode', "statement separator begin end sizable")


class ZetaMessage:
    def __init__(self,
                 name: str,
                 mtype: str = '',
                 size: int = 0,
                 description: str = "",
                 fields: list = None,
                 parent: object = None,
                 level: int = 0) -> None:
        self.name = name.lower()
        self.size = size
        self.level = level
        self.description = description
        self.parent = parent
        self.mtype_obj = None
        if "bitarray" in mtype:  # mtype here must be bitarray_u32 for example
            self.mtype, self.mtype_base_type = mtype.lower().split("_")
        else:
            self.mtype = mtype.lower()
            # used by the children of an bitarray
            self.mtype_base_type = "u32"
        if self.size > 0 and self.mtype not in [
                'bits', 'u8', 's8', 'u16', 's16', 'u32', 's32', 'u64', 's64'
        ]:
            assert self.level > 0, "Invalid size for root objects"
        self.digest_type()
        self.fields = []
        if fields is not None:
            for field in fields:
                print(field.items())
                for item_name, sub_fields in field.items():
                    print(item_name, sub_fields)
                    self.fields.append(
                        ZetaMessage(item_name,
                                    level=self.level + 1,
                                    parent=self,
                                    **sub_fields))

    def digest_type(self):
        if self.mtype == 'struct':
            self.mtype_obj = MsgType(
                statement="struct"
                if self.level > 0 else f"struct {self.name}",
                separator="\n",
                begin="{\n",
                end="\n}",
                sizable=f"[{self.size}]" if self.size > 0 else "")
            self.name = "" if self.level == 0 else " " + self.name
        elif self.mtype == 'union':
            self.mtype_obj = MsgType(
                statement="union" if self.level > 0 else f"union {self.name}",
                separator="\n",
                begin="{\n",
                end="\n}",
                sizable=f"[{self.size}]" if self.size > 0 else "")
            self.name = "" if self.level == 0 else " " + self.name
        elif self.mtype == "bitarray":
            self.mtype_obj = MsgType(
                statement="struct"
                if self.level > 0 else f"struct {self.name}",
                separator="\n",
                begin="{\n",
                end="\n}",
                sizable=f"[{self.size}]" if self.size > 0 else "")
            self.name = "" if self.level == 0 else " " + self.name

        elif self.mtype == "bits":
            self.mtype_obj = MsgType(
                statement=self.parent.mtype_base_type +
                "_t" if self.parent else "u32_t",
                separator="",
                begin="",
                end="",
                sizable=f":{self.size}" if self.size > 0 else "")
        else:
            if self.mtype in [
                    'u8', 's8', 'u16', 's16', 'u32', 's32', 'u64', 's64'
            ]:
                self.mtype_obj = MsgType(
                    statement=self.mtype + "_t",
                    separator="",
                    begin="",
                    end="",
                    sizable=f"[{self.size}]" if self.size > 0 else "")

    def code(self):
        return textwrap.indent(
            f"{self.mtype_obj.statement} {self.mtype_obj.begin}{self.mtype_obj.separator.join([x.code() for x in self.fields])}{self.mtype_obj.end}{self.name}{self.mtype_obj.sizable};",
            prefix="    " * (1 if self.level > 0 else 0))


class TestStringMethods(unittest.TestCase):
    def test_primitives(self):
        self.assertEqual(
            "u32_t var:1;",
            ZetaMessage('var', **{
                'mtype': 'bits',
                'size': 1
            }).code())
        self.assertEqual(
            "u32_t var:10;",
            ZetaMessage('var', **{
                'mtype': 'bits',
                'size': 10
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
            "    s64_t erw64iru32b;",
            ZetaMessage('erw64iru32b', **{
                'mtype': 's64',
                'size': 0
            }, level=4).code())

    def test_struct_simple(self):
        self.assertEqual(
            "struct my_struct {\n\n};",
            ZetaMessage('my_struct', **{
                'mtype': 'struct',
                'fields': []
            }).code())
        self.assertEqual(
            "struct my_struct {\n    s64_t var64bits;\n};",
            ZetaMessage(
                'my_struct', **{
                    'mtype': 'struct',
                    'fields': [{
                        'var64bits': {
                            'mtype': 's64'
                        }
                    }]
                }).code())
        self.assertEqual(
            "struct my_struct {\n    s64_t var64bits;\n    u32_t var32;\n    s16_t var16s;\n};",
            ZetaMessage(
                'my_struct', **{
                    'mtype':
                    'struct',
                    'fields': [{
                        'var64bits': {
                            'mtype': 's64'
                        },
                        'var32': {
                            'mtype': 'u32'
                        },
                        'var16s': {
                            'mtype': 's16'
                        }
                    }]
                }).code())
        self.assertEqual(
            textwrap.indent(
                "struct {\n    s64_t var64bits;\n    u32_t var32;\n    s16_t var16s;\n} my_struct;",
                prefix="    "),
            ZetaMessage('my_struct',
                        level=1,
                        **{
                            'mtype':
                            'struct',
                            'fields': [{
                                'var64bits': {
                                    'mtype': 's64'
                                },
                                'var32': {
                                    'mtype': 'u32'
                                },
                                'var16s': {
                                    'mtype': 's16'
                                }
                            }]
                        }).code())
        self.assertEqual(
            textwrap.indent(
                "struct {\n    s64_t var64bits;\n    u32_t var32;\n    s16_t var16s;\n} my_struct[128];",
                prefix="    "),
            ZetaMessage('my_struct',
                        level=1,
                        **{
                            'mtype':
                            'struct',
                            'size':
                            128,
                            'fields': [{
                                'var64bits': {
                                    'mtype': 's64'
                                },
                                'var32': {
                                    'mtype': 'u32'
                                },
                                'var16s': {
                                    'mtype': 's16'
                                }
                            }]
                        }).code())

    def test_union_simple(self):
        self.assertEqual(
            "union my_union {\n\n};",
            ZetaMessage('my_union', **{
                'mtype': 'union',
                'fields': []
            }).code())
        self.assertEqual(
            "union my_union {\n    s64_t v64s;\n};",
            ZetaMessage(
                'my_union', **{
                    'mtype': 'union',
                    'fields': [{
                        'v64s': {
                            'mtype': 's64'
                        }
                    }]
                }).code())
        self.assertEqual(
            "union my_union {\n    s64_t v64s;\n    u32_t v32;\n};",
            ZetaMessage(
                'my_union', **{
                    'mtype': 'union',
                    'fields': [{
                        'v64s': {
                            'mtype': 's64'
                        },
                        'v32': {
                            'mtype': 'u32'
                        }
                    }]
                }).code())
        self.assertEqual(
            textwrap.indent("union {\n    s64_t v64s;\n} my_union;",
                            prefix="    "),
            ZetaMessage(
                'my_union', **{
                    'level': 1,
                    'mtype': 'union',
                    'fields': [{
                        'v64s': {
                            'mtype': 's64'
                        }
                    }]
                }).code())
        self.assertEqual(
            textwrap.indent(
                "union {\n    s64_t v64s;\n    u32_t v32;\n} my_union;",
                prefix="    "),
            ZetaMessage(
                'my_union', **{
                    'level': 1,
                    'mtype': 'union',
                    'fields': [{
                        'v64s': {
                            'mtype': 's64'
                        },
                        'v32': {
                            'mtype': 'u32'
                        }
                    }]
                }).code())

    def test_bitarray_simple(self):
        self.assertEqual(
            "struct my_bitarray {\n\n};",
            ZetaMessage('my_bitarray', **{
                'mtype': 'bitarray_u32',
                'fields': []
            }).code())
        self.assertEqual(
            "struct my_bitarray {\n    u32_t b2:2;\n};",
            ZetaMessage(
                'my_bitarray', **{
                    'mtype': 'bitarray_u32',
                    'fields': [{
                        'b2': {
                            'mtype': 'bits',
                            'size': 2
                        }
                    }]
                }).code())
        self.assertEqual(
            "struct my_bitarray {\n    u32_t b2:2;\n    u32_t b8:8;\n};",
            ZetaMessage(
                'my_bitarray', **{
                    'mtype':
                    'bitarray_u32',
                    'fields': [{
                        'b2': {
                            'mtype': 'bits',
                            'size': 2
                        },
                        'b8': {
                            'mtype': 'bits',
                            'size': 8
                        }
                    }]
                }).code())
        self.assertEqual(
            textwrap.indent(
                "struct {\n    u32_t b2:2;\n    u32_t b8:8;\n} my_bitarray;",
                prefix="    "),
            ZetaMessage('my_bitarray',
                        level=1,
                        **{
                            'mtype':
                            'bitarray_u32',
                            'fields': [{
                                'b2': {
                                    'mtype': 'bits',
                                    'size': 2
                                },
                                'b8': {
                                    'mtype': 'bits',
                                    'size': 8
                                }
                            }]
                        }).code())
        self.assertEqual(
            textwrap.indent(
                "struct {\n    u32_t b2:2;\n    u32_t b8:8;\n} my_bitarray[64];",
                prefix="    "),
            ZetaMessage('my_bitarray',
                        level=1,
                        size=64,
                        **{
                            'mtype':
                            'bitarray_u32',
                            'fields': [{
                                'b2': {
                                    'mtype': 'bits',
                                    'size': 2
                                },
                                'b8': {
                                    'mtype': 'bits',
                                    'size': 8
                                }
                            }]
                        }).code())

    def test_array_simple(self):
        self.assertEqual(
            "s8_t vars8b[1];",
            ZetaMessage('vars8b', **{
                'mtype': 's8',
                'size': 1
            }).code())
        self.assertEqual(
            "u8_t var8b[10];",
            ZetaMessage('var8b', **{
                'mtype': 'u8',
                'size': 10
            }).code())
        self.assertEqual(
            "s16_t erwoeiruwoeirs16b[128];",
            ZetaMessage('erwoeiruwoeirs16b', **{
                'mtype': 's16',
                'size': 128
            }).code())
        self.assertEqual(
            "    u16_t var16bfff[1000];",
            ZetaMessage('var16bfff', level=5, **{
                'mtype': 'u16',
                'size': 1000
            }).code())
        self.assertEqual(
            "s32_t erwoeiru32b[7];",
            ZetaMessage('erwoeiru32b', **{
                'mtype': 's32',
                'size': 7
            }).code())
        self.assertEqual(
            "u32_t var32fdd[35];",
            ZetaMessage('var32fdd', **{
                'mtype': 'u32',
                'size': 35
            }).code())
        self.assertEqual(
            "s64_t erw64iru32b[44];",
            ZetaMessage('erw64iru32b', **{
                'mtype': 's64',
                'size': 44
            }).code())

        self.assertEqual(
            "    s64_t erw64iru32b[9999];",
            ZetaMessage('erw64iru32b',
                        **{
                            'mtype': 's64',
                            'size': 9999
                        },
                        level=1).code())
        self.assertEqual(
            "    s64_t erw64iru32b[157869];",
            ZetaMessage('erw64iru32b',
                        **{
                            'mtype': 's64',
                            'size': 157869
                        },
                        level=4).code())

    def test_complex_message(self):
        self.assertEqual(
            textwrap.indent("", prefix="    "),
            ZetaMessage('req',
                        level=0,
                        **{
                            'mtype':
                            'struct',
                            'fields': [{
                                'id': {
                                    'mtype': 'u32'
                                },
                                'flag': {
                                    'mtype':
                                    'bitarray_u8',
                                    'fields': [{
                                        'read': {
                                            'mtype': 'bits',
                                            'size': 1
                                        }
                                    }, {
                                        'write': {
                                            'mtype': 'bits',
                                            'size': 1
                                        }
                                    }, {
                                        'erase': {
                                            'mtype': 'bits',
                                            'size': 1
                                        }
                                    }, {
                                        'update': {
                                            'mtype': 'bits',
                                            'size': 1
                                        }
                                    }]
                                },
                                'bytes': {
                                    'mtype': 'u8',
                                    'size': 32
                                },
                                'complex': {
                                    'mtype':
                                    'union',
                                    'fields': [{
                                        'arr': {
                                            'mtype': 'u32',
                                            'size': 128,
                                        },
                                        'st': {
                                            'mtype':
                                            'struct',
                                            'size':
                                            4,
                                            'fields': [{
                                                'number': {
                                                    'mtype': 's64',
                                                    'size': 32
                                                }
                                            }]
                                        }
                                    }]
                                }
                            }]
                        }).code())
        self.assertEqual(
            textwrap.indent("", prefix="    "),
            ZetaMessage(
                'req', **{
                    'mtype':
                    'struct',
                    'fields': [{
                        'id': {
                            'mtype': 'u32'
                        },
                        'flag': {
                            'mtype':
                            'bitarray_u8',
                            'fields': [{
                                'read': {
                                    'mtype': 'bits',
                                    'size': 1
                                },
                                'write': {
                                    'mtype': 'bits',
                                    'size': 1
                                },
                                'erase': {
                                    'mtype': 'bits',
                                    'size': 1
                                },
                                'update': {
                                    'mtype': 'bits',
                                    'size': 1
                                }
                            }]
                        },
                        'bytes': {
                            'mtype': 'u8',
                            'size': 32
                        }
                    }]
                }).code())


if __name__ == "__main__":
    unittest.main()
