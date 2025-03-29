#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "hardware/adc.h"
#include "hardware/dma.h"
#include "lwip/tcp.h"
#include "pico/cyw43_arch.h"
#include "pico/stdlib.h"

#define WIFI_SSID "Ghost"
#define WIFI_PASSWORD "eegdatapls"
#define TCP_PORT 4242
#define SAMPLES_PER_PACKET 8
#define BUF_SIZE \
  (SAMPLES_PER_PACKET * sizeof(uint16_t))  // 16 bytes for 8 uint16_t values
#define POLL_TIME_MS 1

typedef struct {
  struct tcp_pcb *pcb;
  uint16_t buffer[SAMPLES_PER_PACKET];  // Buffer for uint16_t values
  bool sending;
  absolute_time_t last_send;
} tcp_server_state_t;

static tcp_server_state_t *server_state = NULL;

// Forward declarations
static err_t tcp_server_sent(void *arg, struct tcp_pcb *tpcb, u16_t len);
static err_t tcp_server_poll(void *arg, struct tcp_pcb *tpcb);
static void tcp_server_err(void *arg, err_t err);

// Called when data has been sent
static err_t tcp_server_sent(void *arg, struct tcp_pcb *tpcb, u16_t len) {
  tcp_server_state_t *state = (tcp_server_state_t *)arg;
  state->sending = false;
  return ERR_OK;
}

// Optimized ADC reading function
static inline void fast_read_adc(uint16_t *buffer, size_t count) {
  for (size_t i = 0; i < count; i++) {
    // Read full 12-bit ADC value
    buffer[i] = adc_read();
  }
}

// Called periodically to check connection and send data
static err_t tcp_server_poll(void *arg, struct tcp_pcb *tpcb) {
  tcp_server_state_t *state = (tcp_server_state_t *)arg;

  // Only send if we're not currently sending and enough time has passed
  if (!state->sending &&
      absolute_time_diff_us(state->last_send, get_absolute_time()) >= 1000) {
    // Read new ADC data
    fast_read_adc(state->buffer, SAMPLES_PER_PACKET);

    // Send the data
    err_t err = tcp_write(tpcb, state->buffer, BUF_SIZE, TCP_WRITE_FLAG_COPY);
    if (err == ERR_OK) {
      state->sending = true;
      state->last_send = get_absolute_time();
      tcp_output(tpcb);
    } else if (err != ERR_MEM) {
      printf("Failed to send data: %d\n", err);
      tcp_close(tpcb);
      return ERR_ABRT;
    }
  }

  return ERR_OK;
}

// Error callback
static void tcp_server_err(void *arg, err_t err) {
  tcp_server_state_t *state = (tcp_server_state_t *)arg;
  if (state) {
    printf("TCP error: %d\n", err);
    free(state);
    server_state = NULL;
  }
}

// Accept callback for new connections
static err_t tcp_server_accept(void *arg, struct tcp_pcb *newpcb, err_t err) {
  if (err != ERR_OK || newpcb == NULL) {
    return ERR_VAL;
  }

  if (server_state != NULL) {
    printf("Connection rejected - server busy\n");
    return ERR_MEM;
  }

  tcp_nagle_disable(newpcb);
  tcp_setprio(newpcb, TCP_PRIO_MAX);

  printf("Client connected!\n");

  server_state = calloc(1, sizeof(tcp_server_state_t));
  if (!server_state) {
    printf("Failed to allocate server state\n");
    return ERR_MEM;
  }

  server_state->pcb = newpcb;
  server_state->sending = false;
  server_state->last_send = get_absolute_time();

  tcp_arg(newpcb, server_state);
  tcp_sent(newpcb, tcp_server_sent);
  tcp_poll(newpcb, tcp_server_poll, POLL_TIME_MS);
  tcp_err(newpcb, tcp_server_err);

  return ERR_OK;
}

int main() {
  stdio_init_all();
  sleep_ms(2000);

  printf("Starting High-Speed TCP Server (16-bit ADC)...\n");

  if (cyw43_arch_init()) {
    printf("WiFi initialization failed!\n");
    return 1;
  }

  cyw43_arch_enable_sta_mode();

  printf("Connecting to WiFi: %s\n", WIFI_SSID);
  if (cyw43_arch_wifi_connect_timeout_ms(WIFI_SSID, WIFI_PASSWORD,
                                         CYW43_AUTH_WPA2_AES_PSK, 30000)) {
    printf("Failed to connect to WiFi\n");
    return 1;
  }
  printf("Connected to WiFi!\n");

  const ip4_addr_t *ip = &cyw43_state.netif[0].ip_addr;
  printf("Assigned IP Address: %s\n", ip4addr_ntoa(ip));

  // Initialize ADC at maximum speed
  adc_init();
  adc_gpio_init(26);
  adc_set_clkdiv(0);

  struct tcp_pcb *pcb = tcp_new();
  if (!pcb) {
    printf("Failed to create PCB\n");
    return 1;
  }

  if (tcp_bind(pcb, IP_ADDR_ANY, TCP_PORT) != ERR_OK) {
    printf("Failed to bind TCP server\n");
    return 1;
  }

  pcb = tcp_listen(pcb);
  tcp_accept(pcb, tcp_server_accept);
  printf("TCP server listening on port %d (sending 16-bit values)\n", TCP_PORT);

  while (true) {
    cyw43_arch_poll();
    sleep_us(100);
  }

  return 0;
}
