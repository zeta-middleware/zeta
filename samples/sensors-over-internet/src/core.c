#include <logging/log.h>
#include <zephyr.h>
#include <zeta.h>

LOG_MODULE_DECLARE(zeta, CONFIG_ZETA_LOG_LEVEL);

K_MSGQ_DEFINE(CORE_callback_msgq, sizeof(uint8_t), 30, 4);

#define MAX_RING_SIZE 11

static uint8_t ring_data_a[MAX_RING_SIZE];
static uint8_t ring_data_b[MAX_RING_SIZE];
static uint32_t ring_data_c[MAX_RING_SIZE];
static uint8_t id_a;
static uint8_t id_b;
static uint8_t id_c;

static uint16_t sensor_a_mean(void)
{
    uint16_t sum = 0;
    int i        = 0;
    for (i = 0; i < MAX_RING_SIZE && ring_data_a[i] != 0; i++) {
        sum += ring_data_a[i];
    }

    LOG_DBG("A Mean -> i: %d, sum: %d, mean: %d", i, sum, sum / i);
    return sum / i;
}

static uint16_t sensor_b_mean(void)
{
    uint16_t sum = 0;
    int i        = 0;
    for (i = 0; i < MAX_RING_SIZE && ring_data_b[i] != 0; i++) {
        sum += ring_data_b[i];
    }

    LOG_DBG("B Mean -> i: %d, sum: %d, mean: %d", i, sum, sum / i);
    return sum / i;
}

static uint32_t sensor_c_mean(void)
{
    uint32_t sum = 0;
    int i        = 0;
    for (i = 0; i < MAX_RING_SIZE && ring_data_c[i] != 0; i++) {
        sum += ring_data_c[i];
    }

    LOG_DBG("C Mean -> i: %d, sum: %d, mean: %d", i, sum, sum / i);
    return sum / i;
}

static void core_handle_channel_callback(uint8_t channel_id)
{
    zt_data_t *data_u8      = ZT_DATA_U8(0);
    zt_data_t *data_u32     = ZT_DATA_U32(0);
    zt_data_t *net_response = ZT_DATA_BYTES(5, 0);
    switch (channel_id) {
    case ZT_SENSOR_A_CHANNEL:
        zt_chan_read(channel_id, data_u8);
        ring_data_a[id_a] = data_u8->u8.value;
        id_a              = (id_a + 1) % MAX_RING_SIZE;
        LOG_DBG("Data received from sensor A: %d", data_u8->u8.value);
        break;
    case ZT_SENSOR_B_CHANNEL:
        zt_chan_read(channel_id, data_u8);
        ring_data_b[id_b] = data_u8->u8.value;
        id_b              = (id_b + 1) % MAX_RING_SIZE;
        LOG_DBG("Data received from sensor B: %d", data_u8->u8.value);
        break;
    case ZT_SENSOR_C_CHANNEL:
        zt_chan_read(channel_id, data_u32);
        ring_data_c[id_c] = data_u32->u32.value;
        id_c              = (id_c + 1) % MAX_RING_SIZE;
        LOG_DBG("Data received from sensor C: %d", data_u32->u32.value);
        break;
    case ZT_NET_REQUEST_CHANNEL:
        zt_chan_read(channel_id, data_u8);
        net_response->bytes.value[0] = data_u8->u8.value;
        if (data_u8->u8.value == 0xA0) {  // Requesting last A data
            net_response->bytes.value[1] =
                ring_data_a[(id_a == 0) ? MAX_RING_SIZE : id_a - 1];
        } else if (data_u8->u8.value == 0xA1) {  // Requesting last B data
            net_response->bytes.value[1] =
                ring_data_b[(id_b == 0) ? MAX_RING_SIZE : id_b - 1];
        } else if (data_u8->u8.value == 0xA2) {  // Requesting last C data
            memcpy(net_response->bytes.value + 1,
                   &ring_data_c[(id_c == 0) ? MAX_RING_SIZE : id_c - 1],
                   sizeof(uint32_t));
        } else if (data_u8->u8.value == 0xA3) {  // Requesting A mean
            uint16_t a_mean = sensor_a_mean();
            memcpy(net_response->bytes.value + 1, &a_mean, sizeof(uint16_t));
        } else if (data_u8->u8.value == 0xA4) {  // Requesting B mean
            uint16_t b_mean = sensor_b_mean();
            memcpy(net_response->bytes.value + 1, &b_mean, sizeof(uint16_t));
        } else if (data_u8->u8.value == 0xA5) {  // Requesting C mean
            uint32_t c_mean = sensor_c_mean();
            memcpy(net_response->bytes.value + 1, &c_mean, sizeof(uint32_t));
        } else {
            LOG_DBG("Net request sent is invalid!");
        }
        LOG_DBG("Net request received with ID: %02X", data_u8->u8.value);
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
    uint8_t channel_id = 0;
    while (1) {
        k_msgq_get(&CORE_callback_msgq, &channel_id, K_FOREVER);
        core_handle_channel_callback(channel_id);
    }
}

ZT_SERVICE_DECLARE(CORE, CORE_task, CORE_service_callback);
