// IMPORTING LIBRARIES
#include <FirebaseESP32.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include "ICM_20948.h" // Click here to get the library: http://librarymanager/All#SparkFun_ICM_20948_IMU
#include "time.h"

// WIFI CONFIGURATION
const char * networkName = "MEO-59E8C0"; //AndroidAP.D
const char * networkPswd = "7b04aebe7b"; //otla9444
const int hostPort       = 80;
const int LED_PIN        = 5;

// FIREBASE HOST NAME AND AUTHENTICATION KEY
#define FIREBASE_HOST "esp32wifitest-4f0ee-default-rtdb.europe-west1.firebasedatabase.app/"
#define FIREBASE_AUTH "jBNwA2QGBe88wTUwwupLSuutDkSFI50ssutFKWrh"
FirebaseData firebaseData;     

// JSON OBJECT TO SEND TO FIREBASE
FirebaseJson json;
FirebaseJsonArray jsonArr;
int data_block = 1;

// NETWORK TIME PROTOCOL SERVER CONFIGURATION
const char* ntpServer = "pool.ntp.org";  // pool.ntp.org is a cluster of timeservers to request the time.
const long gmtOffset_sec = 0;            // Offset in seconds between the time zone and GMT (Portugal -> 0)
const int daylightOffset_sec = 3600;     // Offset in seconds for daylight saving time. Generally it is one hour (3600 seconds)
char time_begin[20];                     // Store begin YYYY-MM-DD_HH:MM:SS

// VARIABLES
// Sampling
  unsigned const long s_rate = 100;               // Sampling rate [Hz]
  unsigned const long Ts = ceil(1000/s_rate);     // Convertion to sampling period [ms] 
  float post_t           = 0;                 // Variable to store time   

// Sensors
  // PPG
  int PPGpin             = 36;                // Pulse sensor pin
  float PPGval;                               // Store analogRead PPG value
  // ---
  
  // EDA
  int EDApin             = 39;                // EDA pin
  float EDAval;                               // Store analogRead EDA value
  const float EDAconv    = (3.3/4096.0)/0.132;// Conversion factor for EDA
  // ---
  
  // IMU
  #define I2C_SDA 21                          // IMU SDA pin (default = 21)
  #define I2C_SCL 22                          // IMU SCL pin (default = 22)
  //#define USE_SPI                           // Uncomment this to use SPI
  #define SERIAL_PORT Serial
  #define SPI_PORT SPI                        // Your desired SPI port.       Used only when "USE_SPI" is defined
  #define CS_PIN 2                            // Which pin you connect CS to. Used only when "USE_SPI" is defined
  #define WIRE_PORT Wire                      // Your desired Wire port.      Used when "USE_SPI" is not defined
  #define AD0_VAL 1                           // The value of the last bit of the I2C address.                      
  #ifdef USE_SPI
  ICM_20948_SPI myICM; // If using SPI create an ICM_20948_SPI object
  #else
  ICM_20948_I2C myICM; // Otherwise create an ICM_20948_I2C object
  #endif
  float IMUx;
  float IMUy;
  float IMUz;
  // ---

// Initialize string with data to send to Firebase
String data_send;
int q;
const int maxsize = 200;
int sendd         = 0; 

// BUZZER
const int buzzer = 17;
byte ONoff        = 0;
byte seizure      = 0;
int nrbeep       = 0;
char input;


// FUNCTIONS - WIFI CONNECTION
void connectToWiFi(const char * ssid, const char * pwd)
{
  int ledState = 0;

  printLine();
  Serial.println("Connecting to WiFi network: " + String(ssid));
  WiFi.begin(ssid, pwd);
  WiFi.setTxPower(WIFI_POWER_2dBm);
  
  while (WiFi.status() != WL_CONNECTED) 
  {
    // Blink LED while we're connecting:
    WiFi.begin(ssid, pwd);
    digitalWrite(LED_PIN, ledState);
    ledState = (ledState + 1) % 2; // Flip ledState
    delay(5000);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void printLine()
{
  Serial.println();  
  for (int i=0; i<30; i++)
    Serial.print("-");  
  Serial.println();
}

void requestURL(const char * host, uint8_t port)
{
  printLine();
  Serial.println("Connecting to domain: " + String(host));

  // Use WiFiClient class to create TCP connections
  WiFiClient client;
  if (!client.connect(host, port))
  {
    Serial.println("connection failed");
    return;
  }
  Serial.println("Connected!");
  printLine();

  // This will send the request to the server
  client.print((String)"GET / HTTP/1.1\r\n" +
               "Host: " + String(host) + "\r\n" +
               "Connection: close\r\n\r\n");
  unsigned long timeout = millis();
  while (client.available() == 0) 
  {
    if (millis() - timeout > 5000) 
    {
      Serial.println(">>> Client Timeout !");
      client.stop();
      return;
    }
  }

  // Read all the lines of the reply from server and print them to Serial
  while (client.available()) 
  {
    String line = client.readStringUntil('\r');
    Serial.print(line);
  }

  Serial.println();
  Serial.println("closing connection");
  client.stop();
}

/*
#ifdef USE_SPI
void printScaledSensorValues(ICM_20948_SPI *sensor_acc, int sensor_pulse, int sensor_eda, float current_t)
{
#else
void printScaledSensorValues(ICM_20948_I2C *sensor_acc, int sensor_pulse, int sensor_eda, float current_t)
{
#endif

  printFormattedFloat_ACC(sensor_acc->accX(), 5, 2);
  //printFormattedFloat_ACC(sensor_acc->accY(), 5, 2, FirebaseData firebaseData);
  //printFormattedFloat_ACC(sensor_acc->accZ(), 5, 2, FirebaseData firebaseData);
  printFormattedFloat_Pulse(analogRead(sensor_pulse));
  printFormattedFloat_EDA(analogRead(sensor_eda));
}
*/

//#ifdef USE_SPI
//void readIMU(float val, uint8_t leading, uint8_t decimals) // void printScaledSensorValues(ICM_20948_SPI *sensor_acc, int sensor_pulse, int sensor_eda, float current_t)
//{
//#else
float readIMU(float val, uint8_t leading, uint8_t decimals) // void printScaledSensorValues(ICM_20948_I2C *sensor_acc, int sensor_pulse, int sensor_eda, float current_t)
{
  float aval = abs(val);
  String res;
  if (val < 0)
  {
    //SERIAL_PORT.print("-");
    res = res + String("-");
  }
  else
  {
    //SERIAL_PORT.print(" ");
    res = res + String(" ");
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
      //SERIAL_PORT.print("0");
      res = res + String("0");
    }
    else
    {
      break;
    }
  }
  if (val < 0)
  {
    //SERIAL_PORT.print(-val, decimals);
    res = res + String(-val);
  }
  else
  {
    //SERIAL_PORT.print(val, decimals);
    res = res + String(val);
  }
  return res.toFloat();
}


// SETUP
void setup()
{  
  // Initialize Serial communication at 115200 bps
  Serial.begin(115200);

  // SETUP WIFI
  pinMode(LED_PIN, OUTPUT);
  connectToWiFi(networkName, networkPswd);
  digitalWrite(LED_PIN, LOW); // LED off
  Serial.print("Press button 0 to connect to ");

  // SETUP FIREBASE
  Serial.println(FIREBASE_HOST);
  Firebase.begin(FIREBASE_HOST, FIREBASE_AUTH);
  Firebase.reconnectWiFi(true);
  FirebaseData firebaseData;

  // TIME
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer); // Configure time with the previous settings
  struct tm timeinfo;                      // Time structure containing all the details about the time (min, sec, hour, etc…)
  getLocalTime(&timeinfo);
  strftime(time_begin,20, "%F_%X", &timeinfo);

  // SENSOR PIN INITIALIZATION
  pinMode(PPGpin, INPUT);
  pinMode(EDApin, INPUT);

  // SETUP IMU
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

  // BUZZER
  //pinMode(buzzer, OUTPUT);
  ledcSetup(0, 1000, 12);
  ledcAttachPin(buzzer, 0);
}

void loop()
{
  // OBTAIN CURRENT TIME
  float prev_t = millis();

  // READ SENSOR VALUES WITHIN SAMPLING PERIOD  
  if (prev_t - post_t >= Ts) { //if (prev_t - post_t >= Ts && myICM.dataReady()) {
    // IMU
    myICM.getAGMT();         // The values are only updated when you call 'getAGMT'
                               //    printRawAGMT( myICM.agmt );     // Uncomment this to see the raw values, taken directly from the agmt structure
  
      
        // printScaledAGMT(); // This function takes into account the scale settings from when the measurement was made to calculate the values with units

    
    #ifdef USE_SPI
    ICM_20948_SPI *sensor_acc = &myICM;
    #else
    ICM_20948_I2C *sensor_acc = &myICM;
    #endif
    
    
    /*
    #ifdef USE_SPI
    myICM = ICM_20948_SPI *myICM
    #else
    sensor_acc = ICM_20948_I2C *myICM
    #endif
    */
    
    //printScaledSensorValues(&myICM, PPGpin, EDApin, prev_t);

    // READ ANALOG SENSOR VALUES
    PPGval = analogRead(PPGpin);
    EDAval = analogRead(EDApin) * EDAconv;
    IMUx   = readIMU(sensor_acc->accX(), 5, 2);
    IMUy   = readIMU(sensor_acc->accY(), 5, 2);
    IMUz   = readIMU(sensor_acc->accZ(), 5, 2);


    // SERIAL_PORT.print(sensor_val); ??
 
    // GATHER DATA INTO STRING
    data_send = String(prev_t)+String(",")+String(IMUx)+String(",")+String(IMUy)+String(",")+String(IMUz)+String(",")+String(PPGval)+String(",")+String(EDAval);

    // ADD DATA TO ARRAY
    jsonArr.add(data_send);
    q = q + 1;

    // IF THE ARRAY IS FULL, SEND TO FIREBASE 
    if (q == maxsize) {
        sendd = 1;
      }

    // PUT THIS INSIDE TASK1CODE
    if (sendd == 1){
      // ADD DATA ARRAY TO JSON 
      json.add("Data",jsonArr);

      // SEND JSON TO FIREBASE
      String path = String(time_begin) + String("/") + String(data_block);
      Firebase.setJSON(firebaseData, path, json);

      // CLEAR AND RE-INITIALIZE VARIABLES
      json.clear();
      jsonArr.clear();
      q = 0;
      sendd = 0;

      // UPDATE DATA ID TO SEND TO FIREBASE
      data_block = data_block + 1; 
    }
   
    // PRINT TO SERIAL MONITOR
    Serial.print(data_send);
    Serial.print(",");
    Serial.println(q); 

    // INCREASE TIME
    post_t += Ts;
  }
  

  // IF A SEIZURE HAS BEEN DETECTED, ACTIVATE BUZZER
  if (Serial.available() > 0 ) { 
    input = Serial.read();  
    if (input == 's') {
      seizure = 1;     
    }
  }

  // ACTIVATE THE BUZZER TO BEEP  
  if (prev_t - post_t >= 10000 && seizure == 1) {
      if (ONoff == 0) {
        ledcWriteTone(0,1000); 
        ONoff = 1;
      }
      if (ONoff == 1) {
        ledcWriteTone(0,0);
        ONoff = 0;
        seizure = 0;
      }
    }
}
