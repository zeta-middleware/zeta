#!/bin/sh -l

# Removing old dist folder
rm -rf dist/;
rm -rf zeta_cli.egg-info/;

# Installing current Zeta-cli and running tests
python3 setup.py sdist bdist_wheel &&   \
    cd dist/ &&                         \
    pip3 install *.whl &&               \
    cd ../tests/ &&                     \
    rm -rf build &&                     \
    west build -b native_posix &&       \
    west build -t run
