#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b" 
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8" 

BLECharacteristic *pCharacteristic;

#define CHANNELS 8
uint8_t eegData[CHANNELS];
void generateFakeEEGData() {
  for (int i = 0; i < CHANNELS; i++) {
    eegData[i] = random(0, 255);
  }
}

class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    Serial.println("Client connected!");
  }
  void onDisconnect(BLEServer* pServer) {
    Serial.println("Client disconnected!");
  }
};

class MySecurity : public BLESecurityCallbacks {

  uint32_t onPassKeyRequest(){
        ESP_LOGI(LOG_TAG, "PassKeyRequest");
    return 123456;
  }
  void onPassKeyNotify(uint32_t pass_key){
        ESP_LOGI(LOG_TAG, "The passkey Notify number:%d", pass_key);
  }
  bool onConfirmPIN(uint32_t pass_key){
        ESP_LOGI(LOG_TAG, "The passkey YES/NO number:%d", pass_key);
      vTaskDelay(5000);
    return true;
  }
  bool onSecurityRequest(){
      ESP_LOGI(LOG_TAG, "SecurityRequest");
    return true;
  }

  void onAuthenticationComplete(esp_ble_auth_cmpl_t cmpl){
    ESP_LOGI(LOG_TAG, "Starting BLE work!");
  }
};

void setup() {
  BLEDevice::init("XIAO_ESP32C6"); // Initialize the BLE device
  Serial.begin(115200); // Set baud rate
  BLEDevice::setEncryptionLevel(ESP_BLE_SEC_ENCRYPT);
  // BLEDevice::setSecurityCallbacks(new MySecurity());
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(CHARACTERISTIC_UUID, 
    BLECharacteristic::PROPERTY_READ |
    BLECharacteristic::PROPERTY_WRITE |
    BLECharacteristic::PROPERTY_NOTIFY);
  pCharacteristic->addDescriptor(new BLE2902());
  pServer->setCallbacks(new MyServerCallbacks());
  pService->start(); // start BLE service

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);  // add service UUID
  pAdvertising->setScanResponse(true); // enable scan response for advertising
  pAdvertising->setMinPreferred(0x12);
  pAdvertising->start();

  // esp_ble_auth_req_t auth_req = ESP_LE_AUTH_REQ_SC_MITM_BOND;     //bonding with peer device after authentication
  // esp_ble_io_cap_t iocap = ESP_IO_CAP_OUT;           //set the IO capability to No output No input
  // uint8_t key_size = 16;      //the key size should be 7~16 bytes
  // uint8_t init_key = ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK;
  // uint8_t rsp_key = ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK;
  // //set static passkey
  // uint32_t passkey = 123456;
  // uint8_t auth_option = ESP_BLE_ONLY_ACCEPT_SPECIFIED_AUTH_DISABLE;
  // uint8_t oob_support = ESP_BLE_OOB_DISABLE;
  // esp_ble_gap_set_security_param(ESP_BLE_SM_SET_STATIC_PASSKEY, &passkey, sizeof(uint32_t));
  // esp_ble_gap_set_security_param(ESP_BLE_SM_AUTHEN_REQ_MODE, &auth_req, sizeof(uint8_t));
  // esp_ble_gap_set_security_param(ESP_BLE_SM_IOCAP_MODE, &iocap, sizeof(uint8_t));
  // esp_ble_gap_set_security_param(ESP_BLE_SM_MAX_KEY_SIZE, &key_size, sizeof(uint8_t));
  // esp_ble_gap_set_security_param(ESP_BLE_SM_ONLY_ACCEPT_SPECIFIED_SEC_AUTH, &auth_option, sizeof(uint8_t));
  
  // esp_ble_gap_set_security_param(ESP_BLE_SM_SET_INIT_KEY, &init_key, sizeof(uint8_t));
  // esp_ble_gap_set_security_param(ESP_BLE_SM_SET_RSP_KEY, &rsp_key, sizeof(uint8_t));

  Serial.println("BLE advertising started...");
}

void loop() {
  generateFakeEEGData(); // generate random signal

  // Serial.print("EEG Signal: ");
  // for (int i = 0; i < CHANNELS; i++) {
  //   Serial.print(eegData[i]);
  //   if (i < CHANNELS - 1) {
  //     Serial.print(", ");  // Print a comma after each value except the last
  //   }
  // }
  // Serial.println();

  pCharacteristic->setValue(eegData, sizeof(eegData)); // set new value with data
  pCharacteristic->notify(); // notify connected devices
  delay(500);
}
