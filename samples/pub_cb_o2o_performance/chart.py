#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt


def channel_latency_ping():
    xs = ['1', '2', '4', '8', '16', '32', '64', '128', '255']
    ys = [13, 13, 14, 14, 15, 17, 20, 27, 22]
    plt.bar(xs, ys)
    for x, y in zip(xs, ys):
        plt.text(x, y + 1, r"{0}".format(y), horizontalalignment='center')

    plt.ylim([0, 50])
    plt.yticks([])
    plt.ylabel(r'Latency ($\mu$s)')
    plt.xlabel('Channel size (bytes)')
    plt.title("Publish-callback one-to-one Latency")
    plt.savefig("channel_latency.png")


if __name__ == "__main__":
    channel_latency_ping()
