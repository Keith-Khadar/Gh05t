#include <BLEDevice.h> // Include library for BLE operations
#include <BLEUtils.h>  // Include library for utility functions
#include <BLEServer.h> // Include library for server functions

// Unique UUID for BLE service
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b" 
// Unique UUID for BLE characteristic
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8" 

const int analogPin1 = A0; // Define analog ch0 to read data from
const int analogPin2 = A1; // Define analog ch1 to read data from
const int analogPin3 = A2; // Define analog ch2 to read data from

// Declare a pointer for BLE characteristic
BLECharacteristic *pCharacteristic; 

void setup() {
  // Initialize the BLE device
  BLEDevice::init("XIAO_ESP32C6"); 
  // Start serial communication at 115200 baud rate
  Serial.begin(115200); 
  // Set ADC resolution to 12 bits for more precise readings
  analogReadResolution(12); 
  // Set 0 dB attenuation for full range (0-3.3V)
  analogSetAttenuation(ADC_0db); 
  Serial.println("BLE starts");

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
  pCharacteristic->setValue("Channel Voltages: 0.00,0.00,0.00"); 
  // Start BLE service
  pService->start(); 

  // Get advertising object
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising(); 
  // Add service UUID to advertising
  pAdvertising->addServiceUUID(SERVICE_UUID); 
  pAdvertising->setScanResponse(true); // Enable scan response for advertising
  // Set preferred connection interval (for iPhone compatibility)
  pAdvertising->setMinPreferred(0x06);  
  pAdvertising->setMinPreferred(0x12);
  pAdvertising->start(); // Start advertising the service

  Serial.println("Characteristic defined, esp32 can now be read!");
}

void loop() {
  float ch0_voltage, ch1_voltage, ch2_voltage; // Variables to store the voltage values
  String voltageString; // String to store all voltages as a single concatenated string

  // Loop to read and update the value 50 times
  for (int i = 0; i < 50; i++) {
    // Read raw ADC values
    int ch0_analogValue = analogRead(analogPin1);
    int ch1_analogValue = analogRead(analogPin2);
    int ch2_analogValue = analogRead(analogPin3);

    // Calculate voltages
    ch0_voltage = (ch0_analogValue * 3.3) / 4095.0;
    ch1_voltage = (ch1_analogValue * 3.3) / 4095.0;
    ch2_voltage = (ch2_analogValue * 3.3) / 4095.0;

    // Concatenate voltage values into a single string
    voltageString = String(ch0_voltage, 2) + "," + String(ch1_voltage, 2) + "," + String(ch2_voltage, 2);

    // Set the BLE characteristic value to the voltage string
    pCharacteristic->setValue(voltageString);
    pCharacteristic->notify(); // Notify connected device (phone) of the updated value

    // Print voltage values to the serial monitor
    Serial.print("Channel Voltages: ");
    Serial.println(voltageString);

    delay(1000); // Delay for 1 second before the next read
  }
}