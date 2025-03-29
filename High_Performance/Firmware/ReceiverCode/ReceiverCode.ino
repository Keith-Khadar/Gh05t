#include <esp_now.h>
#include <WiFi.h>

#define CHANNEL 1
#define buf_size 25             // Buffer size: start byte (1) + 8 channels * 3 bytes per channel
#define prsd_size 8             // Number of channels
uint8_t buffer[buf_size];       // 8 channels * 3 bytes per channel
uint32_t parsed[prsd_size];     // Buffer to store parsed 24-bit channel data
int ch_no = 0;                  // Index to track received data in buffer
bool frame_start_flag = false;  // Flag to indicate the start of a data frame

void setup() {
  Serial.begin(115200);         // Initializing serial communication
  
  // Setting WiFi to AP mode
  WiFi.mode(WIFI_AP);
  WiFi.softAP("RX_1", "RX_1_Password", CHANNEL, 0);

  // Initializing ESP-NOW protocol
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Registering callback for received data
  esp_now_register_recv_cb(OnDataRecv);
}

void loop() {
  delay(20);
}

// Callback when data is received
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *data, int data_len) {
  if ((*data != 0xA0) & (~frame_start_flag)) {
    return;
  } else {
    frame_start_flag = true; // Marking the start of a frame
  }
  if ((ch_no == buf_size) & (*data != 0xC0) & (frame_start_flag)) {
    Serial.print("End of frame not received: ");
    Serial.println(*data,HEX);
  }
  if ((ch_no < buf_size) & frame_start_flag) {
    buffer[ch_no] = *data;
    ch_no++;
  }
  
  // Storing received data in buffer
  if (ch_no == buf_size){
    for (int u=1,j=1; j<buf_size, u<=prsd_size; j=j+3,u++) {
      parsed[u-1] = ((buffer[j]<<16)|(buffer[j+1]<<8)|(buffer[j+2]));
      Serial.print("0x");  Serial.print(parsed[u-1], HEX); Serial.print("  ");
    }
    Serial.println();
  }

  // Resetting counters and flags after processing a complete frame
  if(ch_no == buf_size) {
    ch_no = 0;
    frame_start_flag = false;
  }  
}
