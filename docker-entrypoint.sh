#!/bin/sh -l

cd tests/
rm -rf build
west build -b native_posix
west build -t run
