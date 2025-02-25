#include <esp_now.h>
#include <WiFi.h>
#include <SPI.h>
#include <Arduino.h>
#include "SenderCode.h"

uint8_t data = 0; uint8_t data1 = 0;
uint8_t fstart = 0xA0; uint8_t fend = 0xC0;
bool start_flag = false;
bool verbose = false;
uint32_t status;
const int SAMPLES = 2;
uint8_t buffers[SAMPLES][27];
uint32_t averagedBuffer[27] = {0};
uint8_t sample = 0;

esp_now_peer_info_t slave;

void sendframe() {
  esp_now_send(slave.peer_addr, &fstart, sizeof(fstart));
  delay(1);
  for (int m = 3; m <12 ; m++) {
    esp_now_send(slave.peer_addr, (const uint8_t*)&averagedBuffer[m], sizeof(uint32_t)); 
    delay(1);
  }
  delay(1);
  esp_now_send(slave.peer_addr, &fend, sizeof(fend));
}

void setup() { 
  Serial.begin(115200);
  disableCore0WDT();
  disableCore1WDT();
  initialize(); 
  verbose = true; // When true there will be serial feedback
  WiFi.mode(WIFI_STA);
  esp_now_init();
  ScanForSlave(); 
  esp_now_add_peer(&slave);
  
  sendCommand(ADS1299_CMD_SDATAC); // Stopping continuous data mode
  delay(1);
  readAllRegisters();
  Serial.print("Updating default config");
  writeRegister(CONFIG1,0xD6); 
  writeRegister(CONFIG2,0xD0); 
  writeRegister(CONFIG3,0xEC); // BIAS buffer, internal BIAS enabled
  writeRegister(CH1SET,0x64);  
  writeRegister(CH2SET,0x64);  
  writeRegister(CH3SET,0x64);  
  writeRegister(CH4SET,0x64);  
  writeRegister(CH5SET,0x64);  
  writeRegister(CH6SET,0x64);  
  writeRegister(CH7SET,0x64);  
  writeRegister(CH8SET,0x64);  
  writeRegister(BIAS_SENSN,0xFF);
  readAllRegisters();
  delay(1);
  
  // Starting continuous data mode
  digitalWrite(CS, LOW);
  sendCommand(ADS1299_CMD_SDATAC);
  delay(1);
  sendCommand(ADS1299_CMD_RDATAC);
  delay(1);
  for (int p = 1; p <50 ; p++) {
     sendframe();
  }
  sendCommand(ADS1299_CMD_START);
  delay(1);
  digitalWrite(CS, HIGH);
  delay(1);
  Serial.print("DRDY Pin State: ");
  Serial.println(digitalRead(DRDY));
}

void loop() {
  if (digitalRead(DRDY) == LOW) {
    readADCData();
  }
  delay(20);
}

void readADCData() {
  digitalWrite(CS, LOW);  
  for (int i = 0; i < 27; i++) {
    buffers[sample][i] = SPI.transfer(0x00);  // Reading one register
  }
  digitalWrite(CS, HIGH);
  if (sample <SAMPLES) {
    sample = sample +1;
    return;
  }
  else{
    sample = 1;
  }
  
  // Averaging the captured data
  for (int i = 3; i < 27; i++) {
    for (int itr = 0; itr < SAMPLES; itr++) {
      averagedBuffer[i] += buffers[itr][i];
    }
    averagedBuffer[i] /= SAMPLES;
  }
  for (int i = 0; i < 3; i++) {
    averagedBuffer[i] = buffers[0][i];
  }
// Processing and printing the averaged data
  status = (averagedBuffer[0] << 16) | (averagedBuffer[1] << 8) | (averagedBuffer[2]);
  Serial.print("Status: 0x"); Serial.print(status, HEX); Serial.print("  ");
  sendframe();

  int32_t channelData;
  float LSB = 2.235e-5;
  float voltage;

for (int channel = 0; channel < 8; channel++) {
    channelData = (averagedBuffer[3 + channel * 3] << 16) | (averagedBuffer[4 + channel * 3] << 8) | averagedBuffer[5 + channel * 3];
    if (channelData & 0x800000) {
      channelData -= 0x1000000;
    } // Sign extension for negative values
    voltage = channelData * LSB; 
    
    if (channel == 4) {
      Serial.println();
    } 
    Serial.print("Ch "); Serial.print(channel + 1); Serial.print(": "); Serial.print(voltage, 2);
    if (channel !=8) Serial.print(", "); 
  }

  Serial.println();
}

void sendCommand(uint8_t cmd) {
  digitalWrite(CS, LOW);
  SPI.transfer(cmd);
  digitalWrite(CS, HIGH);
}
  
void start(void)
{
  sendCommand(ADS1299_CMD_RDATAC);
  delayMicroseconds(1);
  sendCommand(ADS1299_CMD_START);
  delayMicroseconds(1);
}

void readAllRegisters() {
  for (int i = 0; i < NUM_REGISTERS; i++) {
    uint8_t regValue = readRegister(i);
    if ((i == 8) | (i== 16) ){
      Serial.println();
    }
  }
  Serial.println();
}

uint8_t readRegister(uint8_t reg) {
  digitalWrite(CS, LOW);
  SPI.transfer(ADS1299_CMD_RREG | reg);
  SPI.transfer(0x00);  // Reading one register
  uint8_t value = SPI.transfer(0x00);
  digitalWrite(CS, HIGH);
  if (verbose) {
  Serial.print("Register 0x"); Serial.print(reg, HEX); Serial.print(": 0x"); Serial.print(value, HEX); Serial.print(" ");
  }
  return value;
}

void writeRegister(uint8_t reg, uint8_t value) {
  digitalWrite(CS, LOW);
  // Sending the command to write to a register
  SPI.transfer(ADS1299_CMD_WREG | reg);  // Setting the write register command (WREG)
  SPI.transfer(0x00);                    // Number of registers to write (in this case, 1)
  SPI.transfer(value);  
  digitalWrite(CS, HIGH);
  if (verbose) {
    Serial.print("Write Register 0x");
    Serial.print(reg, HEX);
    Serial.print(": 0x");
    Serial.println(value, HEX);
  }
}

void initialize() {
  SPI.begin(SCK, MISO, MOSI, CS);
  SPI.beginTransaction(SPISettings(2000000, MSBFIRST, SPI_MODE1));
  pinMode(CS, OUTPUT);
  pinMode(RESET,OUTPUT);
	pinMode(START, OUTPUT);
	pinMode(led_gpio,OUTPUT);
	pinMode(DRDY, INPUT);
  digitalWrite(CS, HIGH);
  digitalWrite(RESET, HIGH);
	digitalWrite(START, LOW);
	digitalWrite(led_gpio, HIGH);
  // Reseting the ADS1299
  digitalWrite(RESET, LOW);
  delayMicroseconds(10);
  digitalWrite(RESET, HIGH);
  delay(1);            // Waiting for reset to complete
	verbose = true;      // When verbose1 is true, there will be serial feedback 
};

/** Scanning for slaves in AP mode and adding as peer if found **/
void ScanForSlave() {
  int8_t scanResults = WiFi.scanNetworks();

  for (int i = 0; i < scanResults; ++i) {
    String SSID = WiFi.SSID(i);
    String BSSIDstr = WiFi.BSSIDstr(i);

    if (SSID.indexOf("RX_1") == 0) {

      int mac[6];
      if ( 6 == sscanf(BSSIDstr.c_str(), "%x:%x:%x:%x:%x:%x",  &mac[0], &mac[1], &mac[2], &mac[3], &mac[4], &mac[5] ) ) {
        for (int ii = 0; ii < 6; ++ii ) {
          slave.peer_addr[ii] = (uint8_t) mac[ii];
        }
      }

      slave.channel = CHANNEL; // Selecting a channel
      slave.encrypt = 0; // No encryption
      break;
    }
  }
}