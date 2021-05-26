# _Epileptic Seizure Detection: IASB project, Instituto Superior Técnico_ 

[![](https://www.ejp-eurad.eu/sites/default/files/2019-11/ist_logo.png)](https://tecnico.ulisboa.pt/en/)

This is an Arduino/Android project for a device that detects epilepsy attacks based on biosignal acquisition. This project was part of the [IASB](https://fenix.tecnico.ulisboa.pt/disciplinas/IAS511132646/2020-2021/2-semestre) course of the 1st year/2nd semester of the [Master in Biomedical Engineering](https://fenix.tecnico.ulisboa.pt/cursos/mebiom) at [Instituto Superior Técnico, Universidade de Lisboa](https://tecnico.ulisboa.pt/en/).

###### The group members of this project are: 
 - **[Afonso Ferreira]**
 - **[Diogo Vieira]**

## Setup: ESP32 COM to Arduino IDE

1. **Install all the required packages for ESP32 either through your IDE or manually**
2. **Install drivers for the COMx PORT**
3. **Compile and Run!**

## Setup: Android App (...)

1. **...**


### Troubleshooting "Flash memory exceeded" after sending code from computer to ESP32

1. **Install PIP on your OS. To check if PIP is installed on windows, run this on the cmd**
```batch
pip help
```
2. **After PIP is installed, run on terminal/cmd:**
```batch
pip install esptool
```
3. **To reset flash memory, run on terminal/cmd (change x for PORT number in COMx)**
```batch
esptool.py --chip esp32 --port COMx erase_flash
```


[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen.)

   [Afonso Ferreira]: <https://github.com/afonsof3rreira>
   [Diogo Vieira]: <https://github.com/dunvvich>
