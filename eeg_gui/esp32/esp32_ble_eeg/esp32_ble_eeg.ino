#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLEAdvertisedDevice.h>
#include <BLEScan.h>

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

void setup() {
  BLEDevice::init("XIAO_ESP32C6"); // Initialize the BLE device
  Serial.begin(115200); // Set baud rate

  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(CHARACTERISTIC_UUID, 
    BLECharacteristic::PROPERTY_READ |
    BLECharacteristic::PROPERTY_WRITE );

  pService->start(); // start BLE service

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);  // add service UUID
  pAdvertising->setScanResponse(true); // enable scan response for advertising
  pAdvertising->setMinPreferred(0x12);
  pAdvertising->start();
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
  delay(1000);
}
