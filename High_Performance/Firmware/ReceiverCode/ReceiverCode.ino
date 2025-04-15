#include <esp_now.h>
#include <WiFi.h>

#define CHANNEL 1
#define buf_size 25      // Buffer size: start byte (1) + 8 channels * 3 bytes per channel 
#define buf1_size 8	 // Number of channels
#define DATA_SIZE 1998

uint8_t buffer[buf_size];          
uint32_t buffer1[buf1_size];       
uint32_t buffer2[DATA_SIZE];       
volatile int ch_no = 0;
volatile bool frame_start_flag = false;
volatile int index1 = 0;

void setup() {
  Serial.begin(115200); // Initializing serial communication

  // Setting WiFi to AP mode
  WiFi.mode(WIFI_AP);
  WiFi.softAP("RX_1", "RX_1_Password", CHANNEL, 0);

  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  esp_now_register_recv_cb(OnDataRecv);
}

void loop() {
}

// Callback for received ESP-NOW data
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *data, int data_len) {
  if ((*data != 0xA0) && (!frame_start_flag)) {
    return;
  } else {
    frame_start_flag = true;
  }

  if ((ch_no == buf_size) && (*data != 0xC0) && (frame_start_flag)) {
    Serial.print("End of frame not received: ");
    Serial.println(*data, HEX);
  }

  if ((ch_no < buf_size) && frame_start_flag) {
    buffer[ch_no] = *data;
    ch_no++;
  }

  if (ch_no == buf_size) {
    for (int u = 1, j = 1; j < buf_size && u <= buf1_size; j += 3, u++) {
      buffer1[u - 1] = ((buffer[j] << 16) | (buffer[j + 1] << 8) | (buffer[j + 2]));
    }

    if (index1 <= DATA_SIZE - buf1_size - 1) {
      uint32_t ms = millis(); // Use full timestamp in milliseconds

      buffer2[index1++] = 0xFEEDFACE; // Frame marker
      buffer2[index1++] = ms;         // Timestamp


      memcpy(buffer2 + index1, buffer1, buf1_size * sizeof(uint32_t));
      index1 += buf1_size;
    } else {
      Serial.write((uint8_t*)buffer2, DATA_SIZE * sizeof(uint32_t));
      index1 = 0;
    }

    ch_no = 0;
    frame_start_flag = false;
  }
}
