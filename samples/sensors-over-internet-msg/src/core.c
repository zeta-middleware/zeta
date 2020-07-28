#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_MSGQ_DEFINE(CORE_callback_msgq, sizeof(u8_t), 30, 4);

#define MAX_RING_SIZE 11

static u8_t ring_data_a[MAX_RING_SIZE];
static u8_t ring_data_b[MAX_RING_SIZE];
static u32_t ring_data_c[MAX_RING_SIZE];
static u8_t id_a;
static u8_t id_b;
static u8_t id_c;

static u16_t sensor_a_mean(void)
{
    u16_t sum = 0;
    int i     = 0;
    for (i = 0; i < MAX_RING_SIZE && ring_data_a[i] != 0; i++) {
        sum += ring_data_a[i];
    }

    LOG_DBG("A Mean -> i: %d, sum: %d, mean: %d", i, sum, sum / i);
    return sum / i;
}

static u16_t sensor_b_mean(void)
{
    u16_t sum = 0;
    int i     = 0;
    for (i = 0; i < MAX_RING_SIZE && ring_data_b[i] != 0; i++) {
        sum += ring_data_b[i];
    }

    LOG_DBG("B Mean -> i: %d, sum: %d, mean: %d", i, sum, sum / i);
    return sum / i;
}

static u32_t sensor_c_mean(void)
{
    u32_t sum = 0;
    int i     = 0;
    for (i = 0; i < MAX_RING_SIZE && ring_data_c[i] != 0; i++) {
        sum += ring_data_c[i];
    }

    LOG_DBG("C Mean -> i: %d, sum: %d, mean: %d", i, sum, sum / i);
    return sum / i;
}

static void core_handle_channel_callback(u8_t channel_id)
{
    zt_data_t *sensors_data = ZT_DATA_SENSORS_MSG(0);
    zt_data_t *net_request  = ZT_DATA_NET_REQUEST_MSG(0);
    zt_data_t *net_response = ZT_DATA_NET_RESPONSE_MSG(0);
    switch (channel_id) {
    case ZT_SENSORS_CHANNEL:
        zt_chan_read(channel_id, sensors_data);
        ring_data_a[id_a] = sensors_data->sensors_msg.value.a;
        id_a              = (id_a + 1) % MAX_RING_SIZE;
        LOG_DBG("Data received from sensor A: %d", sensors_data->sensors_msg.value.a);
        ring_data_b[id_b] = sensors_data->sensors_msg.value.b;
        id_b              = (id_b + 1) % MAX_RING_SIZE;
        LOG_DBG("Data received from sensor B: %d", sensors_data->sensors_msg.value.b);
        ring_data_c[id_c] = sensors_data->sensors_msg.value.c;
        id_c              = (id_c + 1) % MAX_RING_SIZE;
        LOG_DBG("Data received from sensor C: %d", sensors_data->sensors_msg.value.c);
        break;

    case ZT_NET_REQUEST_CHANNEL:
        zt_chan_read(channel_id, net_request);
        net_response->bytes.value[0] = net_request->net_request_msg.value;
        if (net_request->net_request_msg.value == 0xA0) {  // Requesting last A data
            net_response->bytes.value[1] =
                ring_data_a[(id_a == 0) ? MAX_RING_SIZE : id_a - 1];
        } else if (net_request->net_request_msg.value
                   == 0xA1) {  // Requesting last B data
            net_response->bytes.value[1] =
                ring_data_b[(id_b == 0) ? MAX_RING_SIZE : id_b - 1];
        } else if (net_request->net_request_msg.value
                   == 0xA2) {  // Requesting last C data
            memcpy(net_response->bytes.value + 1,
                   &ring_data_c[(id_c == 0) ? MAX_RING_SIZE : id_c - 1], sizeof(u32_t));
        } else if (net_request->net_request_msg.value == 0xA3) {  // Requesting A mean
            u16_t a_mean = sensor_a_mean();
            memcpy(net_response->bytes.value + 1, &a_mean, sizeof(u16_t));
        } else if (net_request->net_request_msg.value == 0xA4) {  // Requesting B mean
            u16_t b_mean = sensor_b_mean();
            memcpy(net_response->bytes.value + 1, &b_mean, sizeof(u16_t));
        } else if (net_request->net_request_msg.value == 0xA5) {  // Requesting C mean
            u32_t c_mean = sensor_c_mean();
            memcpy(net_response->bytes.value + 1, &c_mean, sizeof(u32_t));
        } else {
            LOG_DBG("Net request sent is invalid!");
        }
        LOG_DBG("Net request received with ID: %02X", net_request->net_request_msg.value);
        zt_chan_pub(ZT_NET_RESPONSE_CHANNEL, net_response);
        break;
    default:
        break;
    }
}

/**
 * @brief This is the function used by Zeta to tell the CORE that one(s) of the
 * channels which it is subscribed has changed. This callback will be called passing
 * the channel's id in it.
 *
 * @param id
 */
void CORE_service_callback(zt_channel_e id)
{
    LOG_DBG("Calling CORE Callback...");
    k_msgq_put(&CORE_callback_msgq, &id, K_NO_WAIT);
}

/**
 * @brief This is the task loop responsible to run the CORE thread
 * functionality.
 */
void CORE_task()
{
    LOG_DBG("CORE Service has started...[OK]");
    u8_t channel_id = 0;
    while (1) {
        k_msgq_get(&CORE_callback_msgq, &channel_id, K_FOREVER);
        core_handle_channel_callback(channel_id);
    }
}

ZT_SERVICE_INIT(CORE, CORE_task, CORE_service_callback);
