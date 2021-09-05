#include <inttypes.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

struct metadata {
    char *name;
    bool persistent;
    bool on_changed;
    uint16_t flags;
    uint16_t channel_size;
    uint8_t *channel;
};

struct machine_msg {
    int a;
    int b;
};

struct oven_msg {
    char x;
    bool y;
};

// #define ZT_CHANNEL(name, type)            \
//     struct {                              \
//         struct metadata __zt_meta_##name; \
//         type name;                        \
//     };

#define ZT_CHANNEL(name, type) name, type

#define ZT_CHAN(name, type) name

#define FOR_EACH(macro, ...) __VA_OPT__(EXPAND(FOR_EACH_HELPER(macro, __VA_ARGS__)))
#define FOR_EACH_HELPER(macro, a1, ...) \
    macro(a1) __VA_OPT__(FOR_EACH_AGAIN PARENS(macro, __VA_ARGS__))
#define FOR_EACH_AGAIN() FOR_EACH_HELPER

#define ZT_CHANNELS_DEFINE(channel, ...) \
    struct __zt_channels {               \
        ZT_CHAN(channel) __VA_ARGS__     \
    } channels = {channel, __VA_ARGS__};

/*! The result of the macro usage is:
ZT_CHANNELS_DEFINE(ZT_CHANNEL(machine, struct machine_msg), ZT_CHANNEL(oven, struct
oven_msg));

Result:
struct channels {
    struct {
        struct metadata __zt_meta_machine;
        struct machine_msg machine;
    };
    struct {
        struct metadata __zt_meta_oven;
        struct oven_msg oven;
    };
};
*/

ZT_CHANNELS_DEFINE(ZT_CHANNEL(machine, struct machine_msg),
                   ZT_CHANNEL(oven, struct oven_msg))
channels = {.__zt_meta_machine = {"MACHINE", false, true, 10, sizeof(struct machine_msg),
                                  (uint8_t *) &channels.machine}};
#define CHANNEL_PUB(chan, val)   \
    printf("Size of type %lu\n", \
           sizeof(typeof(((char *) &channels) + offsetof(struct channels, chan))));

#define ZT_CHANNEL_GET(chan) &channels.chan

#define ZT_CHANNEL_METADATA_GET(chan) ((struct metadata *) &channels.__zt_meta_##chan)


#define zt_chan_pub(chan, value)                                                         \
    ({                                                                                   \
        {                                                                                \
            typeof(channels.chan) chan##__aux__;                                         \
            typeof(value) value##__aux__;                                                \
            (void) (&chan##__aux__ == &value##__aux__);                                  \
        }                                                                                \
        __zt_chan_pub(ZT_CHANNEL_METADATA_GET(chan), (uint8_t *) &value, sizeof(value)); \
    })

int __zt_chan_pub(struct metadata *meta, uint8_t *data, size_t data_size)
{
    if (meta->channel == NULL || data == NULL) {
        return -1;
    }
    if (meta->channel_size != data_size) {
        return -2;
    }
    memcpy(meta->channel, data, meta->channel_size);
    meta->on_changed = true;
    return 0;
}


#define zt_chan_read(chan, value)                                         \
    ({                                                                    \
        {                                                                 \
            typeof(channels.chan) chan##__aux__;                          \
            typeof(value) value##__aux__;                                 \
            (void) (&chan##__aux__ == &value##__aux__);                   \
        }                                                                 \
        __zt_chan_read(ZT_CHANNEL_METADATA_GET(chan), (uint8_t *) &value, \
                       sizeof(value));                                    \
    })

int __zt_chan_read(struct metadata *meta, uint8_t *data, size_t data_size)
{
    if (meta->channel == NULL || data == NULL) {
        return -1;
    }
    if (meta->channel_size != data_size) {
        return -2;
    }
    memcpy(data, meta->channel, meta->channel_size);
    return 0;
}

int main()
{
    // struct channels channels = {
    //     .__zt_meta_machine = {"MACHINE", false, true, 10, sizeof(struct
    //     machine_msg)},
    //     .__zt_meta_oven    = {"OVEN", true, true, 20, sizeof(struct oven_msg)}};
    channels.__zt_meta_machine.channel = (uint8_t *) &channels.machine;
    // channels.__zt_meta_oven.channel    = (uint8_t *) &channels.oven;
    // channels.machine.b                 = 10;
    // printf("base = %p, machine = %p, offset = %lu\n", &channels,
    // &(channels.machine),
    //        offsetof(struct channels, machine));
    // printf("Channel ptr = %p, right meta ptr = %p, meta ptr = %p\n%s\n",
    //        ZT_CHANNEL_GET(machine), &channels.__zt_meta_machine,
    //        ZT_CHANNEL_METADATA_GET(machine),
    //        ZT_CHANNEL_METADATA_GET(machine)->name);
    // printf("Sizeof meta %lu\n", sizeof(struct metadata));
    // printf("base = %p, oven = %p, offset = %lu\n", &channels, &(channels.oven),
    //        offsetof(struct channels, oven));
    // printf("Channel ptr = %p, right meta ptr = %p, meta ptr = %p\n%s\n",
    //        ZT_CHANNEL_GET(oven), &channels.__zt_meta_oven,
    //        ZT_CHANNEL_METADATA_GET(oven), ZT_CHANNEL_METADATA_GET(oven)->name);
    // printf("Sizeof meta %lu\n", sizeof(struct metadata));

    printf("Before writing machine channel value = {.a=%d, .b=%d}\n", channels.machine.a,
           channels.machine.b);
    struct machine_msg msg = {5, 10};
    zt_chan_pub(machine, msg);
    printf("After writing machine channel value = {.a=%d, .b=%d}\n", channels.machine.a,
           channels.machine.b);

    struct machine_msg msg_read = {0};
    printf("Before reading machine channel value = {.a=%d, .b=%d}\n", msg_read.a,
           msg_read.b);
    zt_chan_read(machine, msg_read);
    printf("After reading machine channel value = {.a=%d, .b=%d}\n", channels.machine.a,
           channels.machine.b);

    return (0);
}
