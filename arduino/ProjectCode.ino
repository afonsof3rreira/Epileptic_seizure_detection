// IMPORTING LIBRARIES
#include <FirebaseESP32.h>
#include <WiFi.h>
#include <ArduinoJson.h>

// FIREBASE HOST NAME AND AUTHENTICATION KEY
#define FIREBASE_HOST "esp32wifitest-4f0ee-default-rtdb.europe-west1.firebasedatabase.app/" //Do not include https in FIREBASE_HOST
#define FIREBASE_AUTH "jBNwA2QGBe88wTUwwupLSuutDkSFI50ssutFKWrh"

// WIFI NETWORK NAME AND PASSWORD
const char * networkName = "MEO-59E8C0";
const char * networkPswd = "7b04aebe7b";

const int hostPort = 80;
const int BUTTON_PIN = 36;
const int LED_PIN = 5;

void connectToWiFi(const char * ssid, const char * pwd)
{
  int ledState = 0;

  printLine();
  Serial.println("Connecting to WiFi network: " + String(ssid));

  WiFi.begin(ssid, pwd);
  
  while (WiFi.status() != WL_CONNECTED) 
  {
    
    // Blink LED while we're connecting:
    digitalWrite(LED_PIN, ledState);
    ledState = (ledState + 1) % 2; // Flip ledState
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
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

void printLine()
{
  Serial.println();  
  for (int i=0; i<30; i++)
    Serial.print("-");  
  Serial.println();
}

// SENSOR VARIABLES
unsigned long s_rate = 50;                                // Sampling rate [Hz]
unsigned const long sampling_period = ceil(1000/s_rate); // Convertion to sampling period [ms] 
//unsigned long post_t = 0;                              // Variable to store time
float post_t = 0;                                        // Variable to store time
int sensorValueR;                                        // Variable to store a value measured by a pin related to the resistance
int sensorValueT;                                        // Variable to store a value measured by a pin related to the temperature
char input;                                              // Variable to store what is read in the Serial monitor
int circuitState = 1;                                    // Variable to assess the state of the circuit in the previous iteration   
int PPGpin = 36;                                         // Pulse sensor pin
float PPGval;
float EDAval;
float IMUval;

FirebaseData firebaseData;

void setup()
{
  
  // Initilize hardware:
  Serial.begin(115200);
  pinMode(37, INPUT);
  pinMode(LED_PIN, OUTPUT);

  // Connect to the WiFi network (see function below loop)
  connectToWiFi(networkName, networkPswd);

  digitalWrite(LED_PIN, LOW); // LED off
  Serial.print("Press button 0 to connect to ");
  Serial.println(FIREBASE_HOST);

  // Firebase
  Firebase.begin(FIREBASE_HOST, FIREBASE_AUTH);
  Firebase.reconnectWiFi(true);
  //String path = "/ESP32_Test";
  String path = "/test";
  String jsonStr;

  FirebaseData firebaseData;

  /*
  Serial.println("------------------------------------");
  Serial.println("Path exist test...");
  if (Firebase.pathExist(firebaseData, path))
  {
    Serial.println("Path " + path + " exists");
  }
  else
  {
    Serial.println("Path " + path + " is not exist");
  }
  Serial.println("------------------------------------");
  Serial.println();

  //Quit Firebase and release all resources
  Firebase.end(firebaseData);
  */

  // SENSOR PIN INITIALIZATION
  pinMode(PPGpin, INPUT);
  //pinMode(EDApin, INPUT);
  //pinMode(IMUpin, INPUT);
}

void loop()
{
  // Compute current time
  float prev_t = millis();

  // Read sensor values if the circuit is on within the sampling period
  if (circuitState == 1) {  
    if (prev_t - post_t >= sampling_period) {
      PPGval = analogRead(PPGpin);
      //EDAval = analogRead(EDApin);
      //IMUval = analogRead(IMUpin);
      
      // SERIAL MONITOR
      Serial.print(prev_t);
      Serial.print(',');
      Serial.print(PPGval); 
      Serial.print(',');
      Serial.print(2*PPGval); 
      Serial.print(',');
      Serial.println(3*PPGval); 
      
      // FIREBASE
      Firebase.pushFloat(firebaseData,"/Time/Value", prev_t); 
      Firebase.pushFloat(firebaseData,"/PPG/Value", PPGval); 
      Firebase.pushFloat(firebaseData,"/EDA/Value", 2*PPGval);
      Firebase.pushFloat(firebaseData,"/IMU/Value", 3*PPGval);
      
      // Increase time
      post_t += sampling_period;
    }
  }
 
  // If something was written in the serial monitor...
  if (Serial.available() > 0 ) { 
    input = Serial.read();  // ...we read the input
    if (input == 's') {     // If the input is 's', we turn on the circuit
      circuitState = 1;
    }
    if (input == 'n') {     // If the input is 'n', we turn off the circuit
      circuitState = 0;
    }
  }
}
