/* Referenced to https://github.com/chipaudette/OpenBCI Arduino Uno Example and adapted to ESP32
  This example uses the ADS1299 Arduino Library, a software bridge between the ADS1299 chip and 
  Arduino. See http://www.ti.com/product/ads1299 for more information about the device and the README
  folder in the ADS1299 directory for more information about the library.
  
  // ------- FIREBEETLE ESP32 Pin Assignments ------- //
  // SCK = GPIO 18
  // MISO [DOUT] = GPIO 19
  // MOSI [DIN] = GPIO 23
  // CS = GPIO 5 // chip select pin
  // DRDY = GPIO 4 // data ready pin
  // RST = GPIO 2

  // VCC supplies 5V/AVDD while plugged via usb
  // 3.3V supplies DVDD

  // ------- XIAO ESP32-C6 Pin Assignments ------- //
  // SCK = 
  // MISO [DOUT] = 
  // MOSI [DIN] = 
  // CS = GPIO  // chip select pin
  // DRDY =  // data ready pin
  // RST = 

  // VCC supplies 5V/AVDD while plugged via usb
  // 3.3V supplies DVDD
*/

#include <ADS1299.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

ADS1299 ADS;
BLECharacteristic *pCharacteristic;
BLEServer* pServer = nullptr;
BLEService* pService = nullptr;
BLECharacteristic* pCharacteristic = nullptr;
bool deviceConnected = false;

#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b" 
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8" 

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("Client connected!");
    };

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("Client disconnected!");
    }
};

void setup() {
  ADS.initialize(4,2,5,4,0);        // (DRDY pin, RST pin, CS pin, SCK frequency in MHz);

  Serial.begin(115200);
  Serial.println("ADS1299-ESP32"); 
  delay(1000);            

  ADS.verbose = true;               // when verbose is true, there will be Serial feedback 
  ADS.RESET();                      // all registers set to default
  ADS.SDATAC();                     // stop Read Data Continuous mode to communicate with ADS
  ADS.RREGS(0x00,0x17);             // read ADS registers starting at 0x00 and ending at 0x17
  ADS.WREG(CONFIG3,0xE0);           // enable internal reference buffer
  ADS.RREG(CONFIG3);                // verify write
  for(byte i=CH1SET; i<=CH8SET; i++){   // set up to modify the 8 channel setting registers
    ADS.regData[i] = 0x60;           // the regData array mirrors the ADS1299 register addresses
  }                                  
  ADS.WREGS(CH1SET,7);               // write new channel settings
  ADS.RREGS(CH1SET,7);               // read out what we just did to verify the write
  ADS.RDATAC();                      // enter Read Data Continuous mode
  
    // Initialize BLE
    BLEDevice::init("ADS1299_BLE");
    BLEDevice::setEncryptionLevel(ESP_BLE_SEC_ENCRYPT);
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    pService = pServer->createService(SERVICE_UUID);

    pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_READ |
        BLECharacteristic::PROPERTY_WRITE |
        BLECharacteristic::PROPERTY_NOTIFY
    );
    pCharacteristic->addDescriptor(new BLE2902());
    pService->start();                    // start BLE service

    BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);  // enable scan response for advertising
    pAdvertising->setMinPreferred(0x12);
    pAdvertising->start();
    Serial.println("Waiting for a client connection to notify...");

}

void loop() {
    if (deviceConnected) {
        int32_t channelData[8];
        for (int i = 0; i < 8; i++) {
            channelData[i] = ADS.RDATA(i); // Read data from each channel
        }

        // Send channel data over BLE
        pCharacteristic->setValue((uint8_t*)channelData, sizeof(channelData));
        pCharacteristic->notify();

        delay(100);
    }
}