/* Referenced to https://github.com/chipaudette/OpenBCI Arduino Uno Example and adapted to ESP32
  This example uses the ADS1299 Arduino Library, a software bridge between the ADS1299 chip and 
  Arduino. See http://www.ti.com/product/ads1299 for more information about the device and the README
  folder in the ADS1299 directory for more information about the library.
  
  // ------- FIREBEETLE ESP32 Pin Assignments ------- //
  // SCK = GPIO 18
  // MISO [DOUT] = GPIO 19
  // MOSI [DIN] = GPIO 23
  // CS = GPIO 13 // chip select pin
  // DRDY = GPIO 16 // data ready pin
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

unsigned long startTime;
unsigned long currentTime;

// NMLS Filtering
#define FILTER_ORDER 10
#define MU 0.1f
#define EPS 1e-6f

typedef struct {
    float weights[FILTER_ORDER];
    float buffer[FILTER_ORDER];
    int bufferIndex;
} NLMSFilter;
NLMSFilter nlmsFilters[8];

void initNLMSFilters() {
    for (int ch = 0; ch < 8; ch++) {
        NLMSFilter* filter = &nlmsFilters[ch];
        filter->bufferIndex = 0;
        
        // Initialize weights to zeros (or small random values)
        for (int i = 0; i < FILTER_ORDER; i++) {
            filter->weights[i] = 0.0f;
            filter->buffer[i] = 0.0f;
        }
    }
}

float applyNLMS(NLMSFilter* filter, float noisySample) {
    filter->buffer[filter->bufferIndex] = noisySample;
    
    float y_hat = 0.0f;
    for (int i = 0; i < FILTER_ORDER; i++) {
        int idx = (filter->bufferIndex + i) % FILTER_ORDER;
        y_hat += filter->weights[i] * filter->buffer[idx];
    }
    
    // Compute error
    float e = noisySample - y_hat;
    
    float x_pow = 0.0f;
    for (int i = 0; i < FILTER_ORDER; i++) {
        int idx = (filter->bufferIndex + i) % FILTER_ORDER;
        x_pow += filter->buffer[idx] * filter->buffer[idx];
    }
    
    float mu_eff = MU / (x_pow + EPS);
    
    for (int i = 0; i < FILTER_ORDER; i++) {
        int idx = (filter->bufferIndex + i) % FILTER_ORDER;
        filter->weights[i] += mu_eff * e * filter->buffer[idx];
    }
    
    // Update buffer index
    filter->bufferIndex = (filter->bufferIndex + 1) % FILTER_ORDER;
    
    return e;
}

void setup() {
  // --- FIREBEETLE ESP32 Dev ADS Configurations ---
  // ADS.initialize(16,2,5,2,0);          // (DRDY pin, RST pin, CS pin, SCK frequency in MHz, isDaisy bool);
  ADS.initialize(16, 2, 13, 1.5, 0);      // (DRDY, RST, CS, 1.5MHz)
  // --- ESP32 S3 XIAO SEEED ADS Configurations ---
  // ADS.initialize(3,2,44,2,0);
  
  delay(1000);                            // Give time for USB to stabilize

  Serial.begin(115200);
  Serial.println("ADS1299-ESP32"); 
  delay(1000);

  // Digital Inputs/Outputs Setup for FIREBEETLE
	pinMode(25, INPUT); // GPIO4
  pinMode(26, INPUT); // GPIO3
  pinMode(27, INPUT); // GPIO2
  pinMode(9, INPUT); // GPIO1
  pinMode(10, OUTPUT); // START

  // SETUP DEVICE (Datasheet pg. 62)
  ADS.verbose = true;                     // when verbose is true, there will be Serial feedback 
  ADS.RESET();                            // all registers set to default
  ADS.SDATAC();                           // stop Read Data Continuous mode to communicate with ADS
  ADS.getDeviceID();                      // Confirm register ID                                    
  
  // --- Initialize BLE ---
  BLEDevice::init("ADS1299_BLE");
  BLEDevice::setEncryptionLevel(ESP_BLE_SEC_ENCRYPT);
  BLEDevice::setMTU(517);                 // set max MTU size
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

  // --- SANITY CHECK - Internal Test Signal (Square Wave) ---
  // Config2 Register - Setup test Signal
  // Bit 4 (INT_CAL) = 1 → Enables the internal test signal
  // Bit 2 (CAL_AMP) = 0 or 1 → Choose test signal amplitude
  // Bits 1:0 (CAL_FREQ) = 01 → Selects test signal frequency (fCLK / 2²⁰)
  // ADS.WREG(CONFIG1,0xD6);               // 0b11010110 - 250 SPS
  // ADS.RREG(CONFIG1);                    // verify write
  // ADS.WREG(CONFIG2, 0xD1);              // 0b11010001
  // ADS.RREG(CONFIG2);                    // verify write
  // ADS.WREG(CONFIG3, 0xEC);              // 0b11101100
  // ADS.RREG(CONFIG3);                    // verify write
  // for(byte i=CH1SET; i<=CH8SET; i++){   // set up to modify the 8 channel setting registers
  //   ADS.regData[i] = 0b00000101;        // the regData array mirrors the ADS1299 register addresses
  // }                                  
  // ADS.WREGS(CH1SET,7);                  // write new channel settings
  // ADS.RREGS(CH1SET,7);                  // read out what we just did to verify the write
  
  // --- ELECTRODE READING ---
  ADS.WREG(CONFIG1,0xD6);            // 0b11010110 - 250 SPS
  ADS.RREG(CONFIG1);                 // verify write
  ADS.WREG(CONFIG2,0xC2);            // 0b11000010
  ADS.RREG(CONFIG2);                 // verify write
  ADS.WREG(CONFIG3,0xEC);            // 0b11100100 (external bias) or 0b11101100 (internal bias)
  ADS.RREG(CONFIG3);                 // verify write
  ADS.WREG(MISC1, 0x00);             // closed for SRB1 connection to CHxN - single ended
  // ADS.WREG(MISC1, 0x20);          // closed for SRB1 connection to CHxN - single ended
  ADS.WREG(BIAS_SENSP,0xFF);         // bias derivation for each positive channel
  // ADS.WREG(BIAS_SENSN,0xFF);      // bias derivation for each negative channel

  for(byte i=CH1SET; i<=CH8SET; i++){// set up to modify the 8 channel setting registers
    if (i < CH2SET) {
      ADS.regData[i] = 0x60;         // 0b01100000
    } else {
      ADS.regData[i] = 0xE9;         // 0b11101001 - power down channels
    }
  }
  ADS.WREGS(CH1SET,7);               // write new channel settings
  ADS.RREGS(CH1SET,7); 

  // initNLMSFilters();                 // Apply NLMS Filtering

  digitalWrite(10, HIGH);               // START = 1
  ADS.RDATAC();

  unsigned long startTime = millis();
}

void loop() {
  if (deviceConnected) {
    DataPacket dataPacket;
    unsigned long currentTime = millis();
    dataPacket.timestamp = currentTime-startTime; // capture time in miliseconds
    if (digitalRead(16) == 0) { // DRDY low
      ADS.RDATA(); // Read data from each channel
      float sample = 0.0;

      for (int i = 0; i < 8; i++) {
        // // applying nlms filtering - noise reduction
        // sample = (float)ADS.channelData[i];
        // // // apply NMLS filtering
        // float filteredSample = applyNLMS(&nlmsFilters[i], sample);
        // // // Copy back into channeldata
        // dataPacket.channelData[i] = (int32_t)filteredSample;

        dataPacket.channelData[i] = ADS.channelData[i];
      }

      // Send channel data over BLE
      pCharacteristic->setValue((uint8_t*)&dataPacket, sizeof(DataPacket));
      pCharacteristic->notify();

      Serial.println("===============");
      Serial.print("Timestamp: ");
      Serial.println(dataPacket.timestamp/1000); // convert to seconds
      Serial.print(" Channel Data: ");
      Serial.print(dataPacket.channelData[0]);
      Serial.println();

      // for (int i = 0; i < 8; i++) {
      // int32_t signed24BitData = dataPacket.channelData[i] & 0x00FFFFFF;

      //   // Check if the sign bit (bit 23) is set
      //   if (signed24BitData & 0x00800000) {
      //       // If the sign bit is set, extend the sign to 32 bits
      //       signed24BitData |= 0xFF000000;
      //   }

        // Print the meaningful signed 24-bit data
        // Serial.print("Channel ");
        // Serial.print(i);
        // Serial.print(": ");
        // Serial.println(signed24BitData);
    }
  }
}