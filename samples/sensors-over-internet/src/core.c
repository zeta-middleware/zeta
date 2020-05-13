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


void handle_channel_callback(u8_t channel_id)
{
    zt_data_t *data_u8      = ZT_DATA_U8(0);
    zt_data_t *data_u32     = ZT_DATA_U32(0);
    zt_data_t *net_response = ZT_DATA_BYTES(5, 0, 0, 0, 0, 0);
    switch (channel_id) {
    case ZT_SENSOR_A_CHANNEL:
        zt_channel_data_read(channel_id, data_u8);
        ring_data_a[id_a] = data_u8->u8.value;
        id_a              = (id_a + 1) % MAX_RING_SIZE;
        LOG_DBG("Data received from sensor A: %d", data_u8->u8.value);
        break;
    case ZT_SENSOR_B_CHANNEL:
        zt_channel_data_read(channel_id, data_u8);
        ring_data_b[id_b] = data_u8->u8.value;
        id_b              = (id_b + 1) % MAX_RING_SIZE;
        LOG_DBG("Data received from sensor B: %d", data_u8->u8.value);
        break;
    case ZT_SENSOR_C_CHANNEL:
        zt_channel_data_read(channel_id, data_u32);
        ring_data_c[id_c] = data_u32->u32.value;
        id_c              = (id_c + 1) % MAX_RING_SIZE;
        LOG_DBG("Data received from sensor C: %d", data_u32->u32.value);
        break;
    case ZT_NET_ACCESS_CHANNEL:
        zt_channel_data_read(channel_id, data_u8);
        if (data_u8->u8.value == 0xA0) {  // Requesting last A data
            net_response->bytes.value[0] =
                ring_data_a[(id_a == 0) ? MAX_RING_SIZE : id_a - 1];
        } else if (data_u8->u8.value == 0xA1) {  // Requesting last B data
            net_response->bytes.value[0] =
                ring_data_b[(id_b == 0) ? MAX_RING_SIZE : id_b - 1];
        } else if (data_u8->u8.value == 0xA2) {  // Requesting last C data
            memcpy(net_response->bytes.value,
                   &ring_data_c[(id_c == 0) ? MAX_RING_SIZE : id_c - 1], sizeof(u32_t));
        } else if (data_u8->u8.value == 0xA3) {  // Requesting A median
        } else if (data_u8->u8.value == 0xA4) {  // Requesting B median
        } else if (data_u8->u8.value == 0xA5) {  // Requesting C median
        } else if (data_u8->u8.value == 0xA6) {  // Requesting A mean
        } else if (data_u8->u8.value == 0xA7) {  // Requesting B mean
        } else if (data_u8->u8.value == 0xA5) {  // Requesting C mean
        }
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
    LOG_DBG("calling callback...");
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
        handle_channel_callback(channel_id);
    }
}

ZT_SERVICE_INIT(CORE, CORE_task, CORE_service_callback);
