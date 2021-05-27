#include "ICM_20948.h" // Click here to get the library: http://librarymanager/All#SparkFun_ICM_20948_IMU

//#define USE_SPI       // Uncomment this to use SPI

#define SERIAL_PORT Serial

#define SPI_PORT SPI // Your desired SPI port.       Used only when "USE_SPI" is defined
#define CS_PIN 2     // Which pin you connect CS to. Used only when "USE_SPI" is defined

#define WIRE_PORT Wire // Your desired Wire port.      Used when "USE_SPI" is not defined
#define AD0_VAL 1      // The value of the last bit of the I2C address.                \
                       // On the SparkFun 9DoF IMU breakout the default is 1, and when \
                       // the ADR jumper is closed the value becomes 0
                       
#define I2C_SDA 21 // default = 21
#define I2C_SCL 22 // default = 22

#ifdef USE_SPI
ICM_20948_SPI myICM; // If using SPI create an ICM_20948_SPI object
#else
ICM_20948_I2C myICM; // Otherwise create an ICM_20948_I2C object
#endif

// EDA, Pulse and sampling params
// VARIABLES
// Sampling rate [Hz]
unsigned const long s_rate = 100;
// Convertion to sampling period [ms]
unsigned const long sampling_period = ceil(1000 / s_rate);
// Variable to store time
unsigned long post_t = 0;
// Variable to assess the state of the circuit in the previous iteration
int circuitState = 1;
// Pulse sensor pin
int pin_pulse = 36;
// EDA sensor pin
int pin_EDA = 37;


void setup()
{
  SERIAL_PORT.begin(115200);
  while (!SERIAL_PORT)
  {
  };

#ifdef USE_SPI
  SPI_PORT.begin();
#else
  WIRE_PORT.begin();
  WIRE_PORT.setClock(400000);
#endif

  //myICM.enableDebugging(); // Uncomment this line to enable helpful debug messages on Serial

  bool initialized = false;
  while (!initialized)
  {

#ifdef USE_SPI
    myICM.begin(CS_PIN, SPI_PORT);
#else
    myICM.begin(WIRE_PORT, AD0_VAL);
#endif

    SERIAL_PORT.print(F("Initialization of the sensor returned: "));
    SERIAL_PORT.println(myICM.statusString());
    if (myICM.status != ICM_20948_Stat_Ok)
    {
      SERIAL_PORT.println("Trying again...");
      delay(500);
    }
    else
    {
      initialized = true;
    }
  }
}

void loop()
{
  
    // Compute current time
  unsigned long prev_t = millis();
  if (prev_t - post_t >= sampling_period) {

    if (myICM.dataReady())
    {
      myICM.getAGMT();         // The values are only updated when you call 'getAGMT'
                               //    printRawAGMT( myICM.agmt );     // Uncomment this to see the raw values, taken directly from the agmt structure
  
      
        // printScaledAGMT(); // This function takes into account the scale settings from when the measurement was made to calculate the values with units
      printScaledSensorValues(&myICM, pin_pulse, pin_EDA, prev_t);
      //delay(30);
      }
    else
    {
      SERIAL_PORT.println("Waiting for data");
      delay(500);
    }
    post_t = prev_t;
  }


}

// Below here are some helper functions to print the data nicely!

void printPaddedInt16b(int16_t val)
{
  if (val > 0)
  {
    SERIAL_PORT.print(" ");
    if (val < 10000)
    {
      SERIAL_PORT.print("0");
    }
    if (val < 1000)
    {
      SERIAL_PORT.print("0");
    }
    if (val < 100)
    {
      SERIAL_PORT.print("0");
    }
    if (val < 10)
    {
      SERIAL_PORT.print("0");
    }
  }
  else
  {
    SERIAL_PORT.print("-");
    if (abs(val) < 10000)
    {
      SERIAL_PORT.print("0");
    }
    if (abs(val) < 1000)
    {
      SERIAL_PORT.print("0");
    }
    if (abs(val) < 100)
    {
      SERIAL_PORT.print("0");
    }
    if (abs(val) < 10)
    {
      SERIAL_PORT.print("0");
    }
  }
  SERIAL_PORT.print(abs(val));
}

void printRawAGMT(ICM_20948_AGMT_t agmt)
{
  SERIAL_PORT.print("RAW. Acc [ ");
  printPaddedInt16b(agmt.acc.axes.x);
  SERIAL_PORT.print(", ");
  printPaddedInt16b(agmt.acc.axes.y);
  SERIAL_PORT.print(", ");
  printPaddedInt16b(agmt.acc.axes.z);
  SERIAL_PORT.print(" ], Gyr [ ");
  printPaddedInt16b(agmt.gyr.axes.x);
  SERIAL_PORT.print(", ");
  printPaddedInt16b(agmt.gyr.axes.y);
  SERIAL_PORT.print(", ");
  printPaddedInt16b(agmt.gyr.axes.z);
  SERIAL_PORT.print(" ], Mag [ ");
  printPaddedInt16b(agmt.mag.axes.x);
  SERIAL_PORT.print(", ");
  printPaddedInt16b(agmt.mag.axes.y);
  SERIAL_PORT.print(", ");
  printPaddedInt16b(agmt.mag.axes.z);
  SERIAL_PORT.print(" ], Tmp [ ");
  printPaddedInt16b(agmt.tmp.val);
  SERIAL_PORT.print(" ]");
  SERIAL_PORT.println();
}

void printFormattedFloat_ACC(float val, uint8_t leading, uint8_t decimals)
{
  float aval = abs(val);
  if (val < 0)
  {
    SERIAL_PORT.print("-");
  }
  else
  {
    SERIAL_PORT.print(" ");
  }
  for (uint8_t indi = 0; indi < leading; indi++)
  {
    uint32_t tenpow = 0;
    if (indi < (leading - 1))
    {
      tenpow = 1;
    }
    for (uint8_t c = 0; c < (leading - 1 - indi); c++)
    {
      tenpow *= 10;
    }
    if (aval < tenpow)
    {
      SERIAL_PORT.print("0");
    }
    else
    {
      break;
    }
  }
  if (val < 0)
  {
    SERIAL_PORT.print(-val, decimals);
  }
  else
  {
    SERIAL_PORT.print(val, decimals);
  }
}

#ifdef USE_SPI
void printScaledAGMT(ICM_20948_SPI *sensor)
{
#else
void printScaledAGMT(ICM_20948_I2C *sensor)
{
#endif
  SERIAL_PORT.print("Scaled. Acc (mg) [ ");
  printFormattedFloat_ACC(sensor->accX(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor->accY(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor->accZ(), 5, 2);
  SERIAL_PORT.print(" ], Gyr (DPS) [ ");
  printFormattedFloat_ACC(sensor->gyrX(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor->gyrY(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor->gyrZ(), 5, 2);
  SERIAL_PORT.print(" ], Mag (uT) [ ");
  printFormattedFloat_ACC(sensor->magX(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor->magY(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor->magZ(), 5, 2);
  SERIAL_PORT.print(" ], Tmp (C) [ ");
  printFormattedFloat_ACC(sensor->temp(), 5, 2);
  SERIAL_PORT.print(" ]");
  SERIAL_PORT.println();
}

#ifdef USE_SPI
void printScaledSensorValues(ICM_20948_SPI *sensor_acc, int sensor_pulse, int sensor_eda, unsigned long current_t)
{
#else
void printScaledSensorValues(ICM_20948_I2C *sensor_acc, int sensor_pulse, int sensor_eda, unsigned long current_t)
{
#endif
// [time (ms), accX (mg), accY (mg), accZ (mg), pulse (a.u.), EDA (microS)]
  SERIAL_PORT.print(current_t);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor_acc->accX(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor_acc->accY(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor_acc->accZ(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_Pulse(analogRead(sensor_pulse));
  SERIAL_PORT.print(", ");
  printFormattedFloat_EDA(analogRead(sensor_eda));
  SERIAL_PORT.println();
}

#ifdef USE_SPI
void sendScaledSensorValues(ICM_20948_SPI *sensor_acc, int sensor_pulse, int sensor_eda, unsigned long current_t)
{
#else
void sendScaledSensorValues(ICM_20948_I2C *sensor_acc, int sensor_pulse, int sensor_eda, unsigned long current_t)
{
#endif
// [time (ms), accX (mg), accY (mg), accZ (mg), pulse (a.u.), EDA (microS)]
  SERIAL_PORT.print(current_t);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor_acc->accX(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor_acc->accY(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_ACC(sensor_acc->accZ(), 5, 2);
  SERIAL_PORT.print(", ");
  printFormattedFloat_Pulse(analogRead(sensor_pulse));
  SERIAL_PORT.print(", ");
  printFormattedFloat_EDA(analogRead(sensor_eda));
  SERIAL_PORT.println();
}


void printFormattedFloat_Pulse(int val) // arbitrary unit [0, 1[ (a.u.)
{
  float sensor_val = ((val / 4096.0));
  SERIAL_PORT.print(sensor_val);
}

void printFormattedFloat_EDA(int val) // microS
{
  float sensor_val = (val * 3.3 / 4096.0) / 0.132; 
  SERIAL_PORT.print(sensor_val);
}
