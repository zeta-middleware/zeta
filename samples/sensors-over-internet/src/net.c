#include <logging/log.h>
#include <stdlib.h>
#include <zephyr.h>
#include <zeta.h>

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_MSGQ_DEFINE(NET_callback_msgq, sizeof(uint8_t), 30, 4);

uint8_t generate_random_number(uint8_t lower, uint8_t upper)
{
    static int counter = 0;
    counter++;
    return (counter % (upper - lower + 1)) + lower;
}

static void handle_net_requests(void)
{
    uint8_t num               = generate_random_number(1, 36);
    zt_data_t *packet_request = ZT_DATA_U8(0);
    if (num <= 6) {
        packet_request->u8.value = 0xA0;
    } else if (num <= 12) {
        packet_request->u8.value = 0xA1;
    } else if (num <= 18) {
        packet_request->u8.value = 0xA2;
    } else if (num <= 24) {
        packet_request->u8.value = 0xA3;
    } else if (num <= 30) {
        packet_request->u8.value = 0xA4;
    } else if (num <= 36) {
        packet_request->u8.value = 0xA5;
    }

    LOG_DBG("Getting a virtual packet request from net with id: %02X",
            packet_request->u8.value);
    LOG_DBG("Sending a net packet request to NET_REQUEST channel...");
    zt_chan_pub(ZT_NET_REQUEST_CHANNEL, packet_request);
}

static void net_handle_channel_callback(uint8_t channel_id)
{
    zt_data_t *net_response = ZT_DATA_BYTES(5, 0);
    switch (channel_id) {
    case ZT_NET_RESPONSE_CHANNEL:
        zt_chan_read(channel_id, net_response);
        LOG_DBG("Net response received: %02X", net_response->bytes.value[0]);
        if (net_response->bytes.value[0] == 0xA0) {  // Requesting last A data
            LOG_DBG("Last sensor A data saved: %d", net_response->bytes.value[1]);
        } else if (net_response->bytes.value[0] == 0xA1) {  // Requesting last B data
            LOG_DBG("Last sensor B data saved: %d", net_response->bytes.value[1]);
        } else if (net_response->bytes.value[0] == 0xA2) {  // Requesting last C data
            uint32_t c_value = 0;
            memcpy(&c_value, net_response->bytes.value + 1, sizeof(uint32_t));
            LOG_DBG("Last sensor C data saved: %d", c_value);
        } else if (net_response->bytes.value[0] == 0xA3) {  // Requesting A mean
            uint16_t a_mean = 0;
            memcpy(&a_mean, net_response->bytes.value + 1, sizeof(uint16_t));
            LOG_DBG("Current A mean: %d", a_mean);
        } else if (net_response->bytes.value[0] == 0xA4) {  // Requesting B mean
            uint16_t b_mean = 0;
            memcpy(&b_mean, net_response->bytes.value + 1, sizeof(uint16_t));
            LOG_DBG("Current B mean: %d", b_mean);
        } else if (net_response->bytes.value[0] == 0xA5) {  // Requesting C mean
            uint32_t c_mean = 0;
            memcpy(&c_mean, net_response->bytes.value + 1, sizeof(uint32_t));
            LOG_DBG("Current C mean: %d", c_mean);
        } else {
            LOG_DBG("Net response sent is invalid!");
        }
        break;
    default:
        break;
    }
}

/**
 * @brief This is the function used by Zeta to tell the NET that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing the
 * channel's id in it.
 *
 * @param id
 */
void NET_service_callback(zt_channel_e id)
{
    LOG_DBG("Calling NET Callback...");
    k_msgq_put(&NET_callback_msgq, &id, K_NO_WAIT);
}

/**
 * @brief This is the task loop responsible to run the NET thread
 * functionality.
 */
void NET_task()
{
    LOG_DBG("NET Service has started...[OK]");
    uint8_t channel_id = 0;
    while (1) {
        k_msgq_get(&NET_callback_msgq, &channel_id, K_NO_WAIT);
        net_handle_channel_callback(channel_id);
        handle_net_requests();
        k_sleep(K_SECONDS(10));
#if defined(CONFIG_TRACING)
        uint32_t per = cpu_stats_non_idle_and_sched_get_percent();
        LOG_WRN("CPU usage: %u%%\n", per);
        cpu_stats_reset_counters();
#endif
    }
}

ZT_SERVICE_DECLARE(NET, NET_task, NET_service_callback);
