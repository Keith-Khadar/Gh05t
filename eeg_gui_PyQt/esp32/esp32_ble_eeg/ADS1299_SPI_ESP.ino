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
  // GND to both AGND, AVSS, and DGND

  // ------- XIAO ESP32-C6 Pin Assignments ------- //
  // SCK = GPIO 19 or D8
  // MISO [DOUT] = GPIO 20 or D9
  // MOSI [DIN] = GPIO 18 or D10
  // CS = GPIO 21 or D3 // chip select pin
  // DRDY = GPIO 1 or D1 // data ready pin
  // RST = GPIO 2 or D2

  // VCC supplies 5V/AVDD while plugged via usb
  // 3.3V supplies DVDD
  // GND to both AGND, AVSS, and DGND

    // ------- XIAO ESP32-S3 Pin Assignments ------- //
  // SCK = GPIO 7 or D8
  // MISO [DOUT] = GPIO 8 or D9
  // MOSI [DIN] = GPIO 9 or D10
  // CS = GPIO 44 or D7 // chip select pin
  // DRDY = GPIO 3 or D2 // data ready pin
  // RST = GPIO 2 or D1

  // VCC supplies 5V/AVDD while plugged via usb
  // 3.3V supplies DVDD
  // GND to both AGND, AVSS, and DGND

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
bool deviceConnected = false;

#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b" 
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8" 
#define CONFIG_ESP_CONSOLE_USB_CDC 0

struct DataPacket {
    unsigned long timestamp;
    int32_t channelData[8];  // Assuming 8 channels
};

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
  // FIREBEETLE ESP32 Dev
  ADS.initialize(4,2,5,4,0);        // (DRDY pin, RST pin, CS pin, SCK frequency in MHz, isDaisy bool);
  // ESP32 S3 XIAO SEEED
  // ADS.initialize(3,2,44,2,0);
  delay(1000); // Give time for USB to stabilize
  // Serial.setTxTimeoutMs(100);

  Serial.begin(115200); //SERIAL_8E1
  Serial.println("ADS1299-ESP32"); 
  delay(1000);        

  ADS.verbose = true;               // when verbose is true, there will be Serial feedback 
  ADS.RESET();                      // all registers set to default
  ADS.SDATAC();                     // stop Read Data Continuous mode to communicate with ADS
  ADS.getDeviceID();                // Confirm register ID    
  ADS.WREG(CONFIG1,0xD6);           // 0b11010110 - 250 SPS
  ADS.WREG(CONFIG2,0xC2);           // 0b11000010
  // ADS.RREGS(0x00,0x17);             // read ADS registers starting at 0x00 and ending at 0x17
  ADS.WREG(CONFIG3,0xEC);           // 0b11101100
  ADS.RREG(CONFIG3);                // verify write
  // ADS.WREG(BIAS_SENSP,0xFF);        // bias derivation for each positive channel
  // ADS.WREG(BIAS_SENSN,0xFF);        // bias derivation for each negative channel
  // ADS.WREG(MISC1, 0x20);            // enabling SRB1
  for(byte i=CH1SET; i<=CH8SET; i++){   // set up to modify the 8 channel setting registers
    ADS.regData[i] = 0x60;           // 0b01100100 - temperature sensor?
  }                                  
  ADS.WREGS(CH1SET,7);               // write new channel settings
  ADS.RREGS(CH1SET,7);               // read out what we just did to verify the write
  ADS.RDATAC();                      // enter Read Data Continuous mode
  
  // Initialize BLE
  BLEDevice::init("ADS1299_BLE");
  BLEDevice::setEncryptionLevel(ESP_BLE_SEC_ENCRYPT);
  BLEDevice::setMTU(517);           // set max MTU size
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

  // ----- SANITY CHECK - read from internal test signal -----
  // Bit 4 (INT_CAL) = 1 → Enables the internal test signal
  // Bit 2 (CAL_AMP) = 0 or 1 → Choose test signal amplitude
  // Bits 1:0 (CAL_FREQ) = 01 → Selects test signal frequency (fCLK / 2²⁰)
  ADS.SDATAC();
  ADS.WREG(CONFIG2, 0xD1);              // 110 1 0 0 01
  ADS.RREG(CONFIG2);
  ADS.WREG(CONFIG3, 0xEC);              // 1 11 0 1 1 0 0
  ADS.RREG(CONFIG3);
  for(byte i=CH1SET; i<=CH8SET; i++){   // set up to modify the 8 channel setting registers
    ADS.regData[i] = 0b00000101;        // the regData array mirrors the ADS1299 register addresses
  }                                  
  ADS.WREGS(CH1SET,7);               // write new channel settings
  ADS.RREGS(CH1SET,7);               // read out what we just did to verify the write
  ADS.RDATAC();
}

void loop() {
  if (deviceConnected) {
    DataPacket dataPacket;
    dataPacket.timestamp = millis(); // capture time in miliseconds
    ADS.RDATA(); // Read data from each channel

    for (int i = 0; i < 8; i++) {
      dataPacket.channelData[i] = ADS.channelData[i];
    }

    // Send channel data over BLE
    pCharacteristic->setValue((uint8_t*)&dataPacket, sizeof(DataPacket));
    pCharacteristic->notify();

    Serial.print("Timestamp: ");
    Serial.print(dataPacket.timestamp);
    // Serial.print(" Channel Data: ");
    // Serial.print(dataPacket.channelData[1]);
    // Serial.println();
    // Serial.print(" Channel Data: ");
    // Serial.println();

    for (int i = 0; i < 8; i++) {
    int32_t signed24BitData = dataPacket.channelData[i] & 0x00FFFFFF;

      // Check if the sign bit (bit 23) is set
      if (signed24BitData & 0x00800000) {
          // If the sign bit is set, extend the sign to 32 bits
          signed24BitData |= 0xFF000000;
      }

      // Print the meaningful signed 24-bit data
      Serial.print("Channel ");
      Serial.print(i);
      Serial.print(": ");
      Serial.println(signed24BitData);
    }

    delay(50);
  }
}