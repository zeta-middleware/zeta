#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt


def plot():
    xs = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
    ys = [14, 19, 23, 28, 33, 38, 42, 47, 52, 57]
    plt.bar(xs, ys)  #, color=(0.4, 0.4, 0.4, 1.0))
    for x, y in zip(xs, ys):
        plt.text(x, y + 1, r"{0}".format(y), horizontalalignment='center')

    plt.ylim([0, 60])
    plt.yticks([])
    plt.ylabel(r'Latency ($\mu$s)')
    plt.xlabel('Number of subscribers')
    plt.title("Publish-callback one-to-n Latency")
    plt.savefig("channel_latency_o2n.png")


if __name__ == "__main__":
    plot()
