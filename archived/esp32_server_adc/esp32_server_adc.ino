#include <BLEDevice.h> // Include library for BLE operations
#include <BLEUtils.h>  // Include library for utility functions
#include <BLEServer.h> // Include library for server functions

// Unique UUID for BLE service
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b" 
// Unique UUID for BLE characteristic
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8" 

// Define analog pin to read data from
const int analogPin = A0; 

// Declare a pointer for BLE characteristic
BLECharacteristic *pCharacteristic; 

void setup() {
  // Start serial communication at 115200 baud rate
  Serial.begin(115200);
  // Set ADC resolution to 12 bits for more precise readings
  analogReadResolution(12);
  Serial.println("BLE starts");

  // Initialize the BLE device
  BLEDevice::init("XIAO_ESP32C6");
  // Create BLE server
  BLEServer *pServer = BLEDevice::createServer();
  // Create BLE service with UUID
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Set characteristic properties to read and write
  pCharacteristic = pService->createCharacteristic(
                                         CHARACTERISTIC_UUID,
                                         BLECharacteristic::PROPERTY_READ |
                                         BLECharacteristic::PROPERTY_WRITE
                                       );
  // Set permissions for read and write access
  pCharacteristic->setAccessPermissions(ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE);
  // Set initial characteristic value
  pCharacteristic->setValue("Hello from ESP32C6");
  // Start BLE service
  pService->start();

  // Get advertising object
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  // Add service UUID to advertising
  pAdvertising->addServiceUUID(SERVICE_UUID);
  // Enable scan response for advertising
  pAdvertising->setScanResponse(true);
  // Set preferred connection interval (for iPhone compatibility)
  pAdvertising->setMinPreferred(0x06);  
  pAdvertising->setMinPreferred(0x12);
  // Start advertising the service
  pAdvertising->start();
  Serial.println("Characteristic defined, it can now be read in your phone!");
}

void loop() {
  // Array to store the converted analog value as a string
  char value[8];
  // Variable to store the raw analog value
  int analogValue;
  // Loop to read and update the value 50 times
  for (int i=0; i<50; i++) {
    // Read the analog value from the pin
    analogValue = analogRead(analogPin);
    // Convert the integer analog value to a string
    sprintf(value, "%d", analogValue);
    // Set the BLE characteristic value to the string
    pCharacteristic->setValue(value);
    // Notify connected device (phone) of the updated value
    pCharacteristic->notify();
    // Print analog value to the serial monitor
    Serial.printf("ADC analog value = %d\n", analogValue);
    // Delay for 2 seconds before next read
    delay(2000);
  }
}