#include <SPI.h>
#include <Arduino.h>
#include "ADS1299.h"
#include "freertos/portmacro.h"

#define synthetic_amplitude_counts (8950L)   					
#define max_int16 (32767)
#define min_int16 (-32767)

typedef long int32;
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
	
void ADS1299::initialize() {
    SPI.begin(SCK, MISO, MOSI, CS);
  	SPI.beginTransaction(SPISettings(2000000, MSBFIRST, SPI_MODE1));
  	pinMode(CS, OUTPUT);
  	pinMode(RESET,OUTPUT);
	pinMode(START, OUTPUT);
	pinMode(led_gpio,OUTPUT);
	pinMode(DRDY, INPUT);
  	digitalWrite(CS, HIGH);
	digitalWrite(START, LOW);
	digitalWrite(led_gpio, HIGH);
	
	   serial_feedback = true;      // When serial_feedback is true, there will be Serial feedback  
  delay(1);
};

void ADS1299::SDATAC()
{
    digitalWrite(CS, LOW);
    transfer(_SDATAC);
    digitalWrite(CS, HIGH);
	delayMicroseconds(3);   	   
}

// Resetting all the ADS1299's settings (stop all data acquisition)
void ADS1299::reset(void)
{
   // Sending RESET command to default all registers
   digitalWrite(CS, LOW);
   transfer(_RESET);
   delayMicroseconds(12);   	
   digitalWrite(CS, HIGH);

  ADS1299::SDATAC();             // Exiting Read Data Continuous mode to communicate with ADS
  
  delay(100);
    
  // Turning off all channels
  for (int chan=1; chan <= NCHAN_PER_BOARD; chan++) {
    deactivateChannel(chan);  
    changeChannelLeadOffDetection(chan,OFF,BOTHCHAN); 
  }
  
  setSRB1(use_SRB1());  		// Setting whether SRB1 is active or not
  setAutoBiasGeneration(true);  // Configuring ADS1299 so that bias is generated based on channel state
};

// Deactivating the given channel
// N is the channel number: 1-8
void ADS1299::deactivateChannel(int N)
{
  uint8_t reg, config;
	
  // Checking the inputs
  if ((N < 1) || (N > NCHAN_PER_BOARD)) return;
  
  ADS1299::SDATAC(); delay(1);      // Exiting Read Data Continuous mode to communicate with ADS

  int N_zeroRef = constrain(N-1,0,NCHAN_PER_BOARD-1);  // Subtracting 1 so that counting begins at 0
  reg = CH1SET+(uint8_t)N_zeroRef;
  config = ADS1299::RREG(reg); delay(1);
  bitSet(config,7);  // Setting left-most bit (bit 7) = 1 so the channel shuts down
  if (use_neg_inputs) bitClear(config,3);  // bit 3 = 0 disconnects SRB2
  ADS1299::WREG(reg,config); delay(1);
  
  alterBiasBasedOnChannelState(N);
}; 
    
//  Activate a channel in single-ended mode, N is 1 through 8
//  GainCode and InputCode are defined in the macros in the header file
void ADS1299::activateChannel(int N,uint8_t gainCode,uint8_t inputCode) 
{
  uint8_t reg, config;
  // Checking the inputs
  if ((N < 1) || (N > NCHAN_PER_BOARD)) return;
  ADS1299::SDATAC(); delay(1);      // Exiting Read Data Continuous mode to communicate with ADS

  // Activating the channel using the given gain and setting MUX for normal operation
  // Refer to ADS1299 datasheet, PDF p44
  N = constrain(N-1,0,NCHAN_PER_BOARD-1);  
  uint8_t configuint8_t = 0b00000000;  			// Left-most zero (bit 7) is to activate the channel
  gainCode = gainCode & 0b01110000;  			// Bitwise AND to get just the bits requiredand set the rest to zero
  configuint8_t = configuint8_t | gainCode; 	// Bitwise OR to set just the gain bits high or low and leave the rest
  inputCode = inputCode & 0b00000111;  			// Bitwise AND to get just the bits we want and set the rest to zero
  configuint8_t = configuint8_t | inputCode; 	// Bitwise OR to set just the gain bits high or low and leave the rest
  if (use_SRB2[N]) configuint8_t |= 0b00001000; // Setting the SRB2 flag
  ADS1299::WREG(CH1SET+(uint8_t)N,configuint8_t); delay(1);

  // Adding this channel to the bias generation
  alterBiasBasedOnChannelState(N);
    
  // Activate SRB1 as the Negative input for all channel
  setSRB1(use_SRB1());

  // Finalizing the bias setup
  ADS1299::WREG(CONFIG3,0b11101100); delay(1); 
};

// Determining if channel is active or not
// N here one-referenced (i.e. [1...N]), not [0...N-1]
bool ADS1299::isChannelActive(int N_oneRef) {
	 int N_zeroRef = constrain(N_oneRef-1,0,NCHAN_PER_BOARD-1);  // Subtracting 1 so that counting begins at 0
	 uint8_t reg = CH1SET+(uint8_t)N_zeroRef;
	 uint8_t config = ADS1299::RREG(reg); delay(1);
	 bool chanState = bitRead(config,7);
	 return chanState;
}

void ADS1299::setAutoBiasGeneration(bool state) {
	use_channels_for_bias = state;
	
	// Stepping through the channels are recompute the bias state
	for (int Ichan=1; Ichan<NCHAN_PER_BOARD;Ichan++) {
		alterBiasBasedOnChannelState(Ichan);
	}
}

// N here one-referenced (i.e. [1...N])
void ADS1299::alterBiasBasedOnChannelState(int N_oneRef) {
	 int N_zeroRef = constrain(N_oneRef-1,0,NCHAN_PER_BOARD-1);  // Subtracting 1 so that counting starts at 0
	
	 bool activateBias = false;
	 if ((use_channels_for_bias==true) && (isChannelActive(N_oneRef))) {
	 	 // Activating this channel's bias
	 	 activateBiasForChannel(N_oneRef);
	 } else {
	 	 deactivateBiasForChannel(N_oneRef);
	 }
}
	
void ADS1299::deactivateBiasForChannel(int N_oneRef) {
	int N_zeroRef = constrain(N_oneRef-1,0,NCHAN_PER_BOARD-1); // Subtracting 1 so that counting starts at 0
 	
	// Deactivating this channel's bias
	// Refer ADS1299 datasheet, PDF p44
	uint8_t reg, config;
	for (int I=0;I<2;I++) {
		if (I==0) {
			reg = BIAS_SENSP;
		} else {
			reg = BIAS_SENSN;
		}
		config = ADS1299::RREG(reg); delay(1);// Getting the current bias settings
		bitClear(config,N_zeroRef);           // Clearing this channel's bit to remove from bias generation
		ADS1299::WREG(reg,config); delay(1);  // Sending the modified uint8_t back to the ADS
	}
}
void ADS1299::activateBiasForChannel(int N_oneRef) {
	int N_zeroRef = constrain(N_oneRef-1,0,NCHAN_PER_BOARD-1); 
	uint8_t reg, config;
	int nLoop = 1;  if (use_neg_inputs) nLoop=2;
	for (int i=0; i < nLoop; i++) {
		reg = BIAS_SENSP;
		if (i > 0) reg = BIAS_SENSN;
		config = ADS1299::RREG(reg); 			// Getting the current bias settings
		bitSet(config,N_zeroRef);               // Setting this channel's bit
		ADS1299::WREG(reg,config); delay(1);  	// Sending the modified uint8_t back to the ADS
	}
}	

void ADS1299::changeChannelLeadOffDetection(int N, int code_OFF_ON, int code_P_N_Both)
{
  uint8_t reg, config;
	
  // Checking the inputs
  if ((N < 1) || (N > NCHAN_PER_BOARD)) return;
  N = constrain(N-1,0,NCHAN_PER_BOARD-1);  
  
  ADS1299::SDATAC(); delay(1);      // Exiting Read Data Continuous mode to communicate with ADS

  if ((code_P_N_Both == PCHAN) || (code_P_N_Both == BOTHCHAN)) {
  	  // Shutting the lead-off signal on the positive side
  	  reg = LOFF_SENSP; 
  	  config = ADS1299::RREG(reg); 
  	  if (code_OFF_ON == OFF) {
  	  	  bitClear(config,N);                   
  	  } else {
  	  	  bitSet(config,N); 			  
  	  }
  	  ADS1299::WREG(reg,config); delay(1);  
  }
  
  if ((code_P_N_Both == NCHAN) || (code_P_N_Both == BOTHCHAN)) {
  	  // Shutting the lead-off signal on the negative side
  	  reg = LOFF_SENSN; 
  	  config = ADS1299::RREG(reg); // Getting the current lead-off settings
  	  if (code_OFF_ON == OFF) {
  	  	  bitClear(config,N);                   
  	  } else {
  	  	  bitSet(config,N); 			  
  	  }           
  	  ADS1299::WREG(reg,config); delay(1); 
  }
}; 

void ADS1299::configureLeadOffDetection(uint8_t amplitudeCode, uint8_t freqCode)
{
	amplitudeCode &= 0b00001100;  
	freqCode &= 0b00000011;  
	
	uint8_t reg, config;
	reg = LOFF;
	config = ADS1299::RREG(reg); // Getting the current bias settings
	
	// Reconfiguring the uint8_t to get what we want
	config &= 0b11110000;      // Clearing out the last four bits
	config |= amplitudeCode;   // Setting the amplitude
	config |= freqCode;        // Setting the frequency
	
	// Sending the config uint8_t back to the hardware
	ADS1299::WREG(reg,config); delay(1);  // Sending the modified uint8_t back to the ADS
}

void ADS1299::setSRB1(bool desired_state) {
	if (desired_state) {
		ADS1299::WREG(MISC1,0b00100000); delay(1);  //ADS1299 datasheet, PDF p46
	} else {
		ADS1299::WREG(MISC1,0b00000000); delay(1);  //ADS1299 datasheet, PDF p46
	}
}

// Configuring the test signals that can be internally generated by the ADS1299
void ADS1299::configureInternalTestSignal(uint8_t amplitudeCode, uint8_t freqCode)
{
	if (amplitudeCode == ADSTESTSIG_NOCHANGE) amplitudeCode = (ADS1299::RREG(CONFIG2) & (0b00000100));
	if (freqCode == ADSTESTSIG_NOCHANGE) freqCode = (ADS1299::RREG(CONFIG2) & (0b00000011));
	freqCode &= 0b00000011;  
	uint8_t message = 0b11010000 | freqCode | amplitudeCode;  
	
	ADS1299::WREG(CONFIG2,message); delay(1);
}
 
// System Commands
void ADS1299::WAKEUP() {
    digitalWrite(CS, LOW); 
    transfer(_WAKEUP);
    digitalWrite(CS, HIGH); 
    delayMicroseconds(3);  		
}

void ADS1299::STANDBY() {		
    digitalWrite(CS, LOW);
    transfer(_STANDBY);
    digitalWrite(CS, HIGH);
}

// Reading data
void ADS1299::RDATA() {				//  Stopping Read Continuous mode when DRDY goes low
	uint8_t inuint8_t;
	stat_1 = 0;						
	int nchan = 8;
	digitalWrite(CS, LOW);				
	transfer(_RDATA);
	
	for(int i=0; i<3; i++){			
		inuint8_t = transfer(0x00);
		stat_1 = (stat_1<<8) | inuint8_t;				
	}
	
	for(int i = 0; i<8; i++){
		for(int j=0; j<3; j++){	
			inuint8_t = transfer(0x00);
			channelData[i] = (channelData[i]<<8) | inuint8_t;
		}
	}
	
	for(int i=0; i<nchan; i++){			
		if(bitRead(channelData[i],23) == 1){	
			channelData[i] |= 0xFF000000;
		}else{
			channelData[i] &= 0x00FFFFFF;
		}
	}   
}

void ADS1299::RDATAC() {
    digitalWrite(CS, LOW);
    transfer(_RDATAC);
    digitalWrite(CS, HIGH);
	delayMicroseconds(3);   
}

// Starting continuous data acquisition
void ADS1299::start(void)
{
    ADS1299::RDATAC(); delay(1);  
	digitalWrite(CS, LOW);
  transfer(_START);
  digitalWrite(CS, HIGH);
}


// Printing HEX in verbose feedback mode
void ADS1299::printHex(uint8_t _data){
	Serial.print("0x");
  if(_data < 0x10) Serial.print("0");
  Serial.print(_data, HEX);
}

// String-uint8_t converters for RREG and WREG
void ADS1299::printRegisterName(uint8_t _address) {
    if(_address == ID){
        Serial.print(F("ID, ")); // Loading the string directly from Flash memory
    }
    else if(_address == CONFIG1){
        Serial.print(F("CONFIG1, "));
    }
    else if(_address == CONFIG2){
        Serial.print(F("CONFIG2, "));
    }
    else if(_address == CONFIG3){
        Serial.print(F("CONFIG3, "));
    }
    else if(_address == LOFF){
        Serial.print(F("LOFF, "));
    }
    else if(_address == CH1SET){
        Serial.print(F("CH1SET, "));
    }
    else if(_address == CH2SET){
        Serial.print(F("CH2SET, "));
    }
    else if(_address == CH3SET){
        Serial.print(F("CH3SET, "));
    }
    else if(_address == CH4SET){
        Serial.print(F("CH4SET, "));
    }
    else if(_address == CH5SET){
        Serial.print(F("CH5SET, "));
    }
    else if(_address == CH6SET){
        Serial.print(F("CH6SET, "));
    }
    else if(_address == CH7SET){
        Serial.print(F("CH7SET, "));
    }
    else if(_address == CH8SET){
        Serial.print(F("CH8SET, "));
    }
    else if(_address == BIAS_SENSP){
        Serial.print(F("BIAS_SENSP, "));
    }
    else if(_address == BIAS_SENSN){
        Serial.print(F("BIAS_SENSN, "));
    }
    else if(_address == LOFF_SENSP){
        Serial.print(F("LOFF_SENSP, "));
    }
    else if(_address == LOFF_SENSN){
        Serial.print(F("LOFF_SENSN, "));
    }
    else if(_address == LOFF_FLIP){
        Serial.print(F("LOFF_FLIP, "));
    }
    else if(_address == LOFF_STATP){
        Serial.print(F("LOFF_STATP, "));
    }
    else if(_address == LOFF_STATN){
        Serial.print(F("LOFF_STATN, "));
    }
    else if(_address == GPIO){
        Serial.print(F("GPIO, "));
    }
    else if(_address == MISC1){
        Serial.print(F("MISC1, "));
    }
    else if(_address == MISC2){
        Serial.print(F("MISC2, "));
    }
    else if(_address == CONFIG4){
        Serial.print(F("CONFIG4, "));
    }
}

// Querying to see if data is available from the ADS1299
int ADS1299::isDataAvailable(void)
{
  return (!(digitalRead(DRDY)));
}
  
// Stopping the continuous data acquisition
void ADS1299::stop(void)
{
	// Stopping data conversion
    digitalWrite(CS, LOW);
    transfer(_STOP);
    digitalWrite(CS, HIGH);
    delay(1);
    ADS1299::SDATAC(); delay(1);  // Exiting Read Data Continuous mode to communicate with ADS
}

uint8_t ADS1299::transfer(uint8_t _data) {
    portENTER_CRITICAL(&mux); // Disabling interrupts on this core
    digitalWrite(CS, LOW);    // Selecting the SPI device
    SPI.transfer(_data);      // Performing SPI transfer
    digitalWrite(CS, HIGH);   // Deselecting the SPI device
    SPI.endTransaction();
    portEXIT_CRITICAL(&mux);  // Re-enabling interrupts on this core
}



// Reading more than one register starting at _address
void ADS1299::RREGS(uint8_t _address, uint8_t _numRegistersMinusOne) {
    uint8_t opcode1 = _address + 0x24; 	
    digitalWrite(CS, LOW); 				//  Opening SPI
    transfer(opcode1); 					//  Opcode1
    transfer(_numRegistersMinusOne);	//  Opcode2
    for(int i = 0; i <= _numRegistersMinusOne; i++){
        regData[_address + i] = transfer(0x00); 	//  Adding register uint8_t to mirror array
		}
    digitalWrite(CS, HIGH); 			//  Closing SPI
	if(serial_feedback){				
		for(int i = 0; i<= _numRegistersMinusOne; i++){
			printRegisterName(_address + i);
			printHex(_address + i);
			Serial.print(", ");
			printHex(regData[_address + i]);
			Serial.print(", ");
			for(int j = 0; j<8; j++){
				Serial.print(bitRead(regData[_address + i], 7-j));
				if(j!=7) Serial.print(", ");
			}
			Serial.println();
		}
    }
}

void ADS1299::WREG(uint8_t _address, uint8_t _value) {	//  Writing one register at _address
    uint8_t opcode1 = _address + 0x40; 	//  WREG expects 010rrrrr where rrrrr = _address
    digitalWrite(CS, LOW); 				//  Opening SPI
    transfer(opcode1);					//  Sending WREG command & address
    transfer(0x00);						//	Sending number of registers to read -1	
    transfer(_value);					//  Writing the value to the register
    digitalWrite(CS, HIGH); 			//  Closing SPI
	regData[_address] = _value;		
	if(serial_feedback){			
		Serial.print(F("Register "));
		printHex(_address);
		Serial.println(F(" modified."));
	}
}

void ADS1299::WREGS(uint8_t _address, uint8_t _numRegistersMinusOne) {
    uint8_t opcode1 = _address + 0x40;		//  WREG expects 010rrrrr where rrrrr = _address
    digitalWrite(CS, LOW); 					//  Opening SPI
    transfer(opcode1);						//  Sending WREG command & address
    transfer(_numRegistersMinusOne);		//	Sending number of registers to read -1	
	for (int i=_address; i <=(_address + _numRegistersMinusOne); i++){
		transfer(regData[i]);				//  Writing to the registers
	}	
	digitalWrite(CS,HIGH);					//  Closing SPI
	if(serial_feedback){
		Serial.print(F("Registers "));
		printHex(_address); Serial.print(F(" to "));
		printHex(_address + _numRegistersMinusOne);
		Serial.println(F(" modified"));
	}
}

// Printing as text each channel's data
void ADS1299::printChannelDataAsText(int N, long int sampleNumber)
{
	if ((N < 1) || (N > NCHAN_PER_BOARD)) return;
	
	if (sampleNumber > 0) {
		Serial.print(sampleNumber);
		Serial.print(", ");
	}

	for (int chan = 0; chan < N; chan++ )
	{
		Serial.print(channelData[chan]);
		Serial.print(", ");
	}
	
	Serial.println();
};

// Writing as binary each channel's data
// Printing channels 1-N (where N is 1-8)
int32 val;
uint8_t *val_ptr = (uint8_t *)(&val);
void ADS1299::writeChannelDataAsBinary(int N, long sampleNumber){
	ADS1299::writeChannelDataAsBinary(N,sampleNumber,false,0,false);
}
void ADS1299::writeChannelDataAsBinary(int N, long sampleNumber,bool useSyntheticData){
	ADS1299::writeChannelDataAsBinary(N,sampleNumber,false,0,useSyntheticData);
}
void ADS1299::writeChannelDataAsBinary(int N, long sampleNumber,long int auxValue){
	ADS1299::writeChannelDataAsBinary(N,sampleNumber,true,auxValue,false);
}
void ADS1299::writeChannelDataAsBinary(int N, long sampleNumber,long int auxValue, bool useSyntheticData){
	ADS1299::writeChannelDataAsBinary(N,sampleNumber,true,auxValue,useSyntheticData);
}
void ADS1299::writeChannelDataAsBinary(int N, long sampleNumber,bool sendAuxValue, 
	long int auxValue, bool useSyntheticData)
{
	if ((N < 1) || (N > NCHAN_PER_BOARD)) return;
	
	Serial.write( (uint8_t) PCKT_START);

	uint8_t payloaduint8_ts = (uint8_t)((1+N)*4);    // Length of data payload, uint8_ts
	if (sendAuxValue) payloaduint8_ts+= (uint8_t)4;  // Adding four more uint8_ts for the aux value
	Serial.write(payloaduint8_ts);  				 // Writing the payload length

	// Writing the sample number
	val = sampleNumber;
	Serial.write(val_ptr,4); 
	
	// Writing each channel
	for (int chan = 0; chan < N; chan++ )
	{
		// Getting this channel's data
		if (useSyntheticData) {
			val = makeSyntheticSample(sampleNumber,chan);
		} else {
			// Getting the real EEG data for this channel
			val = channelData[chan];
		}
		Serial.write(val_ptr,4); 
	}
	
	// Writing the AUX value
	if (sendAuxValue) {
		val = auxValue;
		Serial.write(val_ptr,4); 
	}
	
	// Write footer
	Serial.write((uint8_t)PCKT_END);	
};

// Writing channel data using binary format of ModularEEG so that it can be used by BrainBay (P2 protocol)
void ADS1299::writeChannelDataAsOpenEEG_P2(long sampleNumber) {
	ADS1299::writeChannelDataAsOpenEEG_P2(sampleNumber,false);
}
void ADS1299::writeChannelDataAsOpenEEG_P2(long sampleNumber,bool useSyntheticData) {
	static int count = -1;
	uint8_t sync0 = 0xA5;
	uint8_t sync1 = 0x5A;
	uint8_t version = 2;
	
	Serial.write(sync0);
	Serial.write(sync1);
	Serial.write(version);
	uint8_t foo = (uint8_t)sampleNumber;
	if (foo == sync0) foo--;
	Serial.write(foo);
	
	long val32; 
	int val_i16;  
	unsigned int val_u16;  
	uint8_t *val16_ptr = (uint8_t *)(&val_u16);  // Pointing to the memory for the variable above
	for (int chan = 0; chan < 6; chan++ )
	{
		// Getting this channel's data
		if (useSyntheticData) {
			val32 = makeSyntheticSample(sampleNumber,chan) + 127L + 256L*2L;  
		} else {
			// Getting the real EEG data for this channel
			val32 = channelData[chan];
		}			
						
		// Preparing the value for transmission
		val32 = val32 / (32);  // Shrinking to fit within a 16-bit number
		val32 = constrain(val32,min_int16,max_int16); 
		val_u16 = (unsigned int) (val32 & (0x0000FFFF));  
		if (val_u16 > 1023) val_u16 = 1023;
		foo = (uint8_t)((val_u16 >> 8) & 0x00FF); 
		if (foo == sync0) foo--;
		Serial.write(foo);
		foo = (uint8_t)(val_u16 & 0x00FF); 
		if (foo == sync0) foo--;
		Serial.write(foo);		
	}
	uint8_t switches = 0x07;
	count++; if (count >= 18) count=0;
	if (count >= 9) {
		switches = 0x0F;
	}	
	Serial.write(switches);
}

uint8_t ADS1299::RREG(uint8_t _address) {		//  Reading ONE register at _address
    uint8_t opcode1 = _address + 0x20; 			//  RREG expects 001rrrrr where rrrrr = _address
    digitalWrite(CS, LOW); 						//  Opening SPI
    transfer(opcode1); 							//  Opcode1
    transfer(0x00); 							//  Opcode2
    regData[_address] = transfer(0x00);			//  Updating mirror location with returned uint8_t
    digitalWrite(CS, HIGH); 					//  Closing SPI	
	if (serial_feedback){						
		printRegisterName(_address);
		printHex(_address);
		Serial.print(", ");
		printHex(regData[_address]);
		Serial.print(", ");
		for(uint8_t j = 0; j<8; j++){
			Serial.print(bitRead(regData[_address], 7-j));
			if(j!=7) Serial.print(", ");
		}
		
		Serial.println();
	}
	return regData[_address];					// Returning requested register value
}

void ADS1299::updateChannelData(){
	uint8_t inuint8_t;
	int nchan=8;            // 8 channel
	digitalWrite(CS, LOW);	// Opening SPI
	
	for(int i=0; i<3; i++){			//  Reading 3 uint8_t status register from ADS 
		inuint8_t = transfer(0x00);
		stat_1 = (stat_1<<8) | inuint8_t;				
	}
	
	for(int i = 0; i<8; i++){
		for(int j=0; j<3; j++){		//  Reading 24 bits of channel data from 1st ADS
			inuint8_t = transfer(0x00);
			channelData[i] = (channelData[i]<<8) | inuint8_t;
		}
	}
		
	digitalWrite(CS, HIGH);				//  Closing SPI
	
	// Reformatting the numbers
	for(int i=0; i<nchan; i++){			// Converting 3 uint8_t 2's compliment to 4 uint8_t 2's compliment	
		if(bitRead(channelData[i],23) == 1){	
			channelData[i] |= 0xFF000000;
		}else{
			channelData[i] &= 0x00FFFFFF;
		}
	}
}

long int ADS1299::makeSyntheticSample(long sampleNumber,int chan) {
	long time_samp_255 = (long)((sampleNumber) & (0x000000FF));  
	time_samp_255 = (long)((time_samp_255*(long)(chan+1)) & (0x000000FF)); 
	time_samp_255 -= 127L;
	return (synthetic_amplitude_counts * time_samp_255) / 255L; // Scaled zero-mean ramp 
};

// Printing the state of all the control registers
void ADS1299::printAllRegisters(void)   
{
	bool prevVerboseState = serial_feedback;
	
        serial_feedback = true;
        ADS1299::RREGS(0x00,0x10);       // Writing the first registers
        delay(100);  					 // Stalling to let all that data get read
        ADS1299::RREGS(0x11,0x17-0x11);  // Writing the rest
        serial_feedback = prevVerboseState;
}

// Only use SRB1 if all use_SRB2 are set to false
bool ADS1299::use_SRB1(void) {
	for (int Ichan=0; Ichan < NCHAN_PER_BOARD; Ichan++) {
		if (use_SRB2[Ichan]) {
			return false;
		}
	}
	return true;
}
