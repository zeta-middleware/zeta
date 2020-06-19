#!/usr/bin/python3

# import textwrap


class ZetaMessage:
    def __init__(self, fields):
        if fields is None:
            raise "Error"  #TODO: use ZetaError correctly
        self.fields = fields

    def __repr__(self):
        raise NotImplementedError(
            "This function must be implemented  by the child.")
