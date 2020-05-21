import datetime
import sys

import bt2

# Find the `ctf` plugin (shipped with Babeltrace 2).
ctf_plugin = bt2.find_plugin('ctf')

# Get the `source.ctf.fs` component class from the plugin.
fs_cc = ctf_plugin.source_component_classes['fs']

# Create a trace collection message iterator, instantiating a single
# `source.ctf.fs` component class with the `inputs` initialization
# parameter set to open a single CTF trace.
msg_it = bt2.TraceCollectionMessageIterator(
    bt2.ComponentSpec(
        fs_cc,
        {
            # Get the CTF trace path from the first command-line argument.
            'inputs': [sys.argv[1]],
        }))

# Iterate the trace messages.
# for msg in msg_it:
#     # `bt2._EventMessageConst` is the Python type of an event message.
#     if type(msg) is bt2._EventMessageConst:
#         # Print event's name.
#         print(msg.event.name, msg.event.)

# Last event's time (ns from origin).
last_event_ns_from_origin = None
# Iterate the trace messages.
for msg in msg_it:
    # `bt2._EventMessageConst` is the Python type of an event message.
    if type(msg) is bt2._EventMessageConst:
        # Get event message's default clock snapshot's ns from origin
        # value.
        ns_from_origin = msg.default_clock_snapshot.ns_from_origin

        # Compute the time difference since the last event message.
        diff_s = 0

        if last_event_ns_from_origin is not None:
            diff_s = (ns_from_origin - last_event_ns_from_origin) / 1e9

        # Create a `datetime.datetime` object from `ns_from_origin` for
        # presentation. Note that such an object is less accurate than
        # `ns_from_origin` as it holds microseconds, not nanoseconds.
        dt = datetime.datetime.fromtimestamp(ns_from_origin / 1e9)

        # Print line.
        fmt = '{} (+{:.6f} s): {}'
        print(fmt.format(dt, diff_s, msg.event.name))

        # Update last event's time.
        last_event_ns_from_origin = ns_from_origin
