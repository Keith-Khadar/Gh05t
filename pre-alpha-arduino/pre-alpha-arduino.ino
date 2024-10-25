///////////////////////////// SETTINGS /////////////////////////////

// Debug
#define DEBUG true // Comment out when in operation
#define SERIAL_BAUD 115200
#if (DEBUG)
    #define DebugPrint(x) Serial.print(x)
#else
    #define DebugPrint(x)
#endif

// Options
#define SAMPLE_RATE 500


/////////////////////////////// PINS ///////////////////////////////

// DIGITAL PINS

// ANALOG PINS
#define INPUT_PIN A0

///////////////////////// GLOBAL VARIABLES /////////////////////////


//////////////////////////////////////////////////////////////////

void setup()
{
    #if (DEBUG)
        Serial.begin(SERIAL_BAUD);
        while(!Serial) {}
        DebugPrint(F("\nDEBUG MODE\n\n"));
    #endif

    pinMode(INPUT_PIN, INPUT);
}

void loop() {

	// Calculate elapsed time
	static unsigned long past = 0;
	unsigned long present = micros();
	unsigned long interval = present - past;
	past = present;

	// Run timer
	static long timer = 0;
	timer -= interval;

	// Sample
	if(timer < 0){
		timer += 1000000 / SAMPLE_RATE;
		int sensor_value = analogRead(INPUT_PIN);
		Serial.println(sensor_value);
	}
}
