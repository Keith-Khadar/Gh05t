//  SenderCode.h
//  Inspired by Chip Audette.

#ifndef ____ADS1299__
#define ____ADS1299__

#define NCHAN_PER_BOARD (8)       // Number of EEG channels
#define SCK_MHZ (2)
#define SPI_DATA_MODE 0x04        // CPOL = 0; CPHA = 1
#define SPI_MODE_MASK 0x0D        // Mask of CPOL and CPHA  on SPCR
#define SPI_CLOCK_MASK 0x05       // SPR1 = bit 1, SPR0 = bit 0 on SPCR
#define SPI_2XCLOCK_MASK 0x01     // SPI2X = bit 0 on SPSR
#define SPI_CLOCK_DIV_2 0X04	    // 8MHz SPI SCK
#define SPI_CLOCK_DIV_4 0X00	    // 4MHz SPI SCK
#define SPI_CLOCK_DIV_16 0x01     // 1MHz SPI SCK

// Define SPI pins
#define MISO 11
#define SCK 12
#define MOSI 13
#define CS 21
#define RESET 48
#define START 49
#define DRDY 14

#define CHANNEL 1
const byte led_gpio = 38;
// ADS1299 commands
#define ADS1299_CMD_RREG 0x20
#define ADS1299_CMD_WREG 0x40
#define ADS1299_CMD_START 0x08
#define ADS1299_CMD_STOP 0x0B
#define ADS1299_CMD_RDATAC 0x10
#define ADS1299_CMD_SDATAC 0x11
#define ADS1299_CMD_RDATA 0x12
// Number of registers to read
#define NUM_REGISTERS 24

#define _WAKEUP 0x02      
#define _STANDBY 0x04    
#define _RESET 0x06       
#define _START 0x0A       // Starting and synchronizing conversions
#define _STOP 0x08        // Stopping conversion
#define _RDATAC 0x11      // Enabling read data continuous mode
#define _SDATAC 0x12      // Stopping read data continuous mode
#define _RDATA 0x13       

// Register addresses
#define ID 0x00
#define CONFIG1 0x01
#define CONFIG2 0x02
#define CONFIG3 0x03
#define LOFF 0x04
#define CH1SET 0x05
#define CH2SET 0x06
#define CH3SET 0x07
#define CH4SET 0x08
#define CH5SET 0x09
#define CH6SET 0x0A
#define CH7SET 0x0B
#define CH8SET 0x0C
#define BIAS_SENSN 0x0D
#define BIAS_SENSP 0x0E
#define LOFF_SENSN 0x0F
#define LOFF_SENSP 0x10
#define LOFF_FLIP 0x11
#define LOFF_STATN 0x12
#define LOFF_STATP 0x13
#define MISC1 0x14
#define MISC2 0x15
#define GPIO 0x16
#define CONFIG4 0x17

// GainCode choices
#define ADS_GAIN01 (0b00000000)
#define ADS_GAIN02 (0b00010000)
#define ADS_GAIN04 (0b00100000)
#define ADS_GAIN06 (0b00110000)
#define ADS_GAIN08 (0b01000000)
#define ADS_GAIN12 (0b01010000)
#define ADS_GAIN24 (0b01100000)

// InputCode choices
#define ADSINPUT_NORMAL (0b00000000)
#define ADSINPUT_SHORTED (0b00000001)
#define ADSINPUT_TESTSIG (0b00000101)

// Test signal choices
#define ADSTESTSIG_AMP_1X (0b00000000)
#define ADSTESTSIG_AMP_2X (0b00000100)
#define ADSTESTSIG_PULSE_SLOW (0b00000000)
#define ADSTESTSIG_PULSE_FAST (0b00000001)
#define ADSTESTSIG_DCSIG (0b00000011)
#define ADSTESTSIG_NOCHANGE (0b11111111)

// Lead-off signal choices
#define LOFF_MAG_6NA (0b00000000)
#define LOFF_MAG_24NA (0b00000100)
#define LOFF_MAG_6UA (0b00001000)
#define LOFF_MAG_24UA (0b00001100)
#define LOFF_FREQ_DC (0b00000000)
#define LOFF_FREQ_7p8HZ (0b00000001)
#define LOFF_FREQ_31p2HZ (0b00000010)
#define LOFF_FREQ_FS_4 (0b00000011)
#define PCHAN (1)
#define NCHAN (2)
#define BOTHCHAN (3)

#define OFF (0)
#define ON (1)

// Binary communication codes for each packet
#define PCKT_START 0xA0
#define PCKT_END 0xC0

class ADS1299 {
  public:
    void initialize(); // Initializing the ADS1299 controller
    // Data Read Commands
    void SDATAC();
    void RDATAC();
    void WAKEUP();
    void STANDBY();
    void RDATA();
    void reset(void);          
    void printRegisterName(uint8_t _address);
    void printHex(uint8_t _data);
    // Register Read/Write Commands
    uint8_t RREG(uint8_t _address);
    void updateChannelData();
    // SPI Transfer function
    uint8_t transfer(uint8_t _data);
    void RREGS(uint8_t _address, uint8_t _numRegistersMinusOne); 
    void WREG(uint8_t _address, uint8_t _value); 
    void WREGS(uint8_t _address, uint8_t _numRegistersMinusOne); 

    bool isChannelActive(int N_oneRef);
    void activateChannel(int N_oneRef, uint8_t gainCode,uint8_t inputCode);               // Setting channel 1-8
    void deactivateChannel(int N_oneRef);                                                 // Disabling given channel 1-8
    void configureLeadOffDetection(uint8_t amplitudeCode, uint8_t freqCode);              // Configuring the lead-off detection signal parameters
    void changeChannelLeadOffDetection(int N_oneRef, int code_OFF_ON, int code_P_N_Both);
    void configureInternalTestSignal(uint8_t amplitudeCode, uint8_t freqCode);            // Configuring the test signal parameters
    void start(void);
    void stop(void);
    int isDataAvailable(void);
    void printChannelDataAsText(int N, long int sampleNumber);
    void writeChannelDataAsBinary(int N, long int sampleNumber);
    void writeChannelDataAsBinary(int N, long int sampleNumber, bool useSyntheticData);
    void writeChannelDataAsBinary(int N, long int sampleNumber, long int auxValue);
    void writeChannelDataAsBinary(int N, long int sampleNumber, long int auxValue, bool useSyntheticData);
    void writeChannelDataAsBinary(int N, long int sampleNumber, bool sendAuxValue,long int auxValue, bool useSyntheticData);
    void writeChannelDataAsOpenEEG_P2(long int sampleNumber);
    void writeChannelDataAsOpenEEG_P2(long int sampleNumber, bool useSyntheticData);
    void printAllRegisters(void);
    void setSRB1(bool desired_state);
    void alterBiasBasedOnChannelState(int N_oneRef);
    void deactivateBiasForChannel(int N_oneRef);
    void activateBiasForChannel(int N_oneRef);
    void setAutoBiasGeneration(bool state);
    
    int DIVIDER;		        // Selecting SPI SCK frequency
    int stat_1;    	        // Used to hold the status register for boards 1 and 2
    uint8_t regData [24];	  // Array is used to mirror register data
    long channelData [8];	  // Array used when reading channel data board 1+2
    bool verbose1;		      // Turning on/off Serial feedback
    bool isDaisy;		        

  private:
    bool use_neg_inputs;
    bool use_SRB2[NCHAN_PER_BOARD];
    bool use_channels_for_bias;
    bool use_SRB1(void);
    long int makeSyntheticSample(long sampleNumber,int chan);
};

#endif