# -*- coding: utf-8 -*-
import argparse
import datetime
import os
import sys
import time
import pandas as pd
import serial
import platform


def getHeaderfromSignals(acquired_signals: list):
    avail_time_series = ['time', 'acc', 'pulse', 'eda']
    series_header = []
    for series_i in acquired_signals:
        if series_i in avail_time_series and series_i != 'acc':
            series_header.append(series_i)
        elif series_i in avail_time_series and series_i == 'acc':
            series_header.append('acc_x')
            series_header.append('acc_y')
            series_header.append('acc_z')

    return series_header


def check_default_port(port_name: str):
    port_str = port_name
    default = False
    if platform.system() == 'Windows' and port_name is None:  # for windows OS
        port_str = 'COM3'  # change to default
        default = True
    elif platform.system() == 'Darwin' and port_name is None:  # for MAC OS
        port_str = '/dev/ttyUSB0'  # change to default
        default = True
    elif platform.system() == 'Linux' and port_name is None:  # for GNU/Linux OS
        port_str = '/dev/ttyUSB0'  # change to default
        default = True

    return default, port_str


def clean_time(data_line):
    return data_line[2:]


def clean(L):  # L is a list
    """each row of the raw data is acquired as b'XXXXXXXX\r\n', where XXXXXXXX
    is the readable data (ASCII) of varying length, thus we need to remove first 2 chars + 5 last chars
    """
    newl = []  # initialising the new list
    for i in range(len(L)):
        temp = L[i].replace(" ", "")
        temp = temp[2:-5].split(',')
        newl.append(temp)
    return newl


def write(L):
    file = open("data.txt", mode='w')
    for i in range(len(L)):
        file.write(L[i] + '\n')
    file.close()


def main(save_data: bool, result_dir: str, serial_baud_r: int, recording_time: float, acquired_signals: list,
         serial_port=None):
    """Reads the acceleration, pulse and EDA signals acquired from the ESP32 board"""

    global arduino
    default, port = check_default_port(serial_port)  # the Port name as a string

    # Initializing the serial Port
    printed_str1 = 'Trying to connect to'
    if default:
        printed_str1 += ' default port'
    else:
        printed_str1 += ' custom port'

    printed_str2 = ': ' + str(port) + ' at ' + str(serial_baud_r) + ' BAUD.'
    print(printed_str1 + printed_str2)
    try:
        arduino = serial.Serial(port, serial_baud_r, timeout=4)
        print('Connected to ' + str(port) + ' at ' + str(serial_baud_r) + ' BAUD.')

    except:
        print("Failed to connect with " + str(port) + ' at ' + str(serial_baud_r) + ' BAUD.')

    """Initialising variables"""
    raw_data = []

    """Receiving data and storing it in a list"""
    # ignoring the first line to avoid the printing error
    arduino.readline()

    print("transmission started...")
    # reading the first line and saving the starting time
    first_read_line = str(arduino.readline())
    raw_data.append(first_read_line)
    time_i = int(clean_time(first_read_line.split(", ")[0]))
    time_curr_str = time_i

    interval_mark = 1

    # recording data until the recording_time stopping criterion is met
    while time_curr_str - time_i < recording_time * 1000 * 60:  # min to ms

        read_line_str = str(arduino.readline())

        if save_data:
            raw_data.append(read_line_str)

        time_curr_str = int(clean_time(read_line_str.split(", ")[0]))
        if ((time_curr_str - time_i) * 0.001) % 10 == 0:
            print("{}x10 seconds were recorded".format(interval_mark))
            interval_mark += 1

    print("...transmission finished")

    if save_data:
        cleaned_data = clean(raw_data)
        print(cleaned_data[1])
        # generate result directory if it does not exist
        os.makedirs(result_dir, exist_ok=True)

        df_header = getHeaderfromSignals(acquired_signals)

        df = pd.DataFrame(cleaned_data)  # creating dataframe
        t = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')  # string with the date of the experiment
        df.to_csv(os.path.join(result_dir, 'rt_data_{}.csv'.format(t)), header=df_header, sep=",")  # saving csv file
        print('Data saved as ' + os.path.join(result_dir, 'rt_data_{}.csv'.format(t)))


if __name__ == "__main__":
    """The program's entry point."""

    script_dir = os.path.dirname(sys.argv[0])

    parser = argparse.ArgumentParser(description='Arduino-based acquisition of acceleration, pulse and EDA signals')

    parser.add_argument(
        '--save_data',
        type=bool,
        default=True,
        help='Set to True to save data in a .csv file.'
    )

    parser.add_argument(
        '--result_dir',
        type=str,
        default=os.path.normpath(os.path.join(script_dir, 'data')),
        help='Directory for results (useless if save_data = False).'
    )

    parser.add_argument(
        '--serial_baud_r',
        type=int,
        default=115200,
        help='Baud rate used in the ESP32.'
    )

    parser.add_argument(
        '--recording_time',
        type=float,
        default=0.2,
        help='Time in minutes or fraction of minutes the data acquisition will take.'
    )

    parser.add_argument(
        '--acquired_signals',
        type=list,
        default=['time', 'acc', 'pulse', 'eda'],
        help='Time in minutes or fraction of minutes the data acquisition will take.'
    )

    parser.add_argument(
        '--serial_port',
        type=str,
        default='COM6',
        help='Name of the serial port, depending on the OS and computer itself.'
    )

    args = parser.parse_args()
    main(args.save_data, args.result_dir, args.serial_baud_r, args.recording_time, args.acquired_signals,
         args.serial_port)
