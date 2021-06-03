# -*- coding: utf-8 -*-
import argparse
import collections
import datetime
import itertools
import os
import sys
import time
import timeit
import pandas as pd
import serial
import platform
import numpy as np
import threading
import data_processing.python_code.utilities.data_acquisition as acq


def main(save_data: bool, detect_seizure: bool, result_dir: str, serial_baud_r: int, recording_time: float,
         acquired_signals: list,
         serial_port=None, sf=100, ft_window_s=1, window_overlap=50):
    """Reads the acceleration, pulse and EDA signals acquired from the ESP32 board"""

    global arduino, first_ft_window, temp_window_data, window_overlap_frac, mag_list, abs_fft_list, times_fft
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
    data_ac = acq.data_recorder()
    raw_data = []

    """Receiving data and storing it in a list"""
    # ignoring the first line to avoid the printing error
    arduino.readline()

    print(2)

    print("transmission started...")
    # reading the first line and saving the starting time
    first_read_line = str(arduino.readline())
    data_ac.add_acquisition(first_read_line)

    time_i = acq.get_current_time(first_read_line)
    time_curr = time_i

    interval_mark = 1

    if detect_seizure:
        first_ft_window = True
        temp_window_data = collections.deque([first_read_line])
        window_overlap_frac = 100 // window_overlap
        mag_list = []
        abs_fft_list = []
        times_fft = []

    # recording data until the recording_time stopping criterion is met
    while time_curr - time_i < recording_time * 1000 * 60:  # min to ms
        # start_time = timeit.default_timer()

        read_line_str = str(arduino.readline())

        if save_data:
            data_ac.add_acquisition(read_line_str)

        time_curr = acq.get_current_time(read_line_str)
        if ((time_curr - time_i) * 0.001) % 10 == 0:
            print("{}x10 seconds were recorded".format(interval_mark))
            interval_mark += 1

        # TODO: detection algorithm (every 1 second)
        if detect_seizure:

            # first, we add the next acquired value
            temp_window_data.append(read_line_str)

            # if the first window was recorded, start detection thread and update the temp. window
            if ((time_curr - time_i) * 0.001) == ft_window_s:
                # algorithm itself

                # TODO: until here, we have (sf * ft_window_s) + 1 points = ft_window_s seconds.
                mag_arr, abs_ft_arr = detection_algorithm(temp_window_data)
                times_fft.append(time_curr - time_i)
                mag_list.append(mag_arr)
                abs_fft_list.append(abs_ft_arr)

                # remove the first/left (sf * ft_window_s) / 2 points, resulting in (sf * ft_window_s) + 1 points
                for _ in range(sf * ft_window_s // window_overlap_frac):
                    temp_window_data.popleft()
                first_ft_window = False

                # np.itertools.starmap(temp_window_data.popleft, np.repeat((), 4096))

            # if the next overlapping window was recorded, start detection thread and update the temp. window
            elif ((time_curr - time_i) * 0.001) % (ft_window_s / window_overlap_frac) == 0 and not first_ft_window:
                times_fft.append(time_curr - time_i)
                mag_arr, abs_ft_arr = detection_algorithm(temp_window_data)
                mag_list.append(mag_arr)
                abs_fft_list.append(abs_ft_arr)

                # remove the first/left (sf * ft_window_s) / 2 points, resulting in (sf * ft_window_s) + 1 points
                for _ in range(sf * ft_window_s // window_overlap_frac):
                    temp_window_data.popleft()

            # print(' Time elapsed:', timeit.default_timer() - start_time, 's')
        # TODO: if detection serial.write(beep)

    print("...transmission finished")

    if save_data:
        print("checking on acquired data...")
        data_ac.clean_raw_data(save_delays=True, sf=sf)
        data_ac.print_delays()

        # generate result directory if it does not exist
        os.makedirs(result_dir, exist_ok=True)

        print("saving acquired data...")
        data_ac.save_data_to_csv(result_dir, df_header=acq.getHeaderfromSignals(acquired_signals))

        t = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')  # string with the date of the experiment

        data_fft, header_fft = write_2(times_fft, mag_list, abs_fft_list)
        df_fft = pd.DataFrame(data_fft)

        shape = df_fft.shape
        # print('\nDataFrame Shape :', shape)
        # print('\nNumber of rows :', shape[0])
        # print('\nNumber of columns :', shape[1])

        df_fft.to_csv(os.path.join(result_dir, 'rt_data_fft_windows_{}.csv'.format(t)), header=header_fft,
                      sep=",")  # saving csv file
        # print('FFT data saved as ' + os.path.join(result_dir, 'rt_data_fft_windows_{}.csv'.format(t)))


def detection_algorithm(data_chunk: collections.deque, magnitude=True):
    # implement an algorithm based on the following article https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5375767/ [1]
    # check this one too https://odr.chalmers.se/bitstream/20.500.12380/145997/1/145997.pdf

    # TODO: compute the FFT weights based on a series of seizure vs baseline datasets [1]
    mag_arr = getArrayfromStringList(data_chunk, magnitude=magnitude)

    ft_arr = np.fft.rfft(mag_arr)
    abs_ft_arr = np.abs(ft_arr)
    power_ft_arr = np.square(ft_arr)  # redundant, if every ft is expressed as absolute
    # frequency = np.linspace(0, sampling_rate/2, len(power_spectrum))
    return mag_arr, abs_ft_arr


def write_2(times_fft_l, mag_l, abs_fft_l):
    newl = []
    # time_start: getting the first time measurement to shift time values

    for i in range(len(times_fft_l)):

        temp_l = str(times_fft_l[i])
        mag_arr = np.squeeze(mag_l[i])
        abs_fft_arr = np.squeeze(abs_fft_l[i])

        for j in range(np.size(mag_arr) - 1):  # check dimensions to print 3 values
            temp_l = temp_l + "," + str(mag_arr[j])

        temp_l = temp_l + "," + str(mag_arr[-1])

        for j in range(np.size(abs_fft_arr) - 1):
            temp_l = temp_l + "," + str(abs_fft_arr[j])

        temp_l = temp_l + "," + str(abs_fft_arr[-1])

        temp_l = temp_l.replace(" ", "")
        temp_l = temp_l.split(',')
        newl.append(temp_l)

    header = []

    size_mag = np.size(np.squeeze(mag_l[0]))
    size_abs_fft = np.size(np.squeeze(abs_fft_l[0]))

    header.append('time')
    for i in range(size_mag):
        header.append('mag at point {}'.format(str(i)))
    for i in range(size_abs_fft):
        header.append('fft bin {}'.format(str(i)))
    # print(header)

    return newl, header


def getArrayfromStringList(data_lines: collections.deque, magnitude: bool):
    if magnitude:
        data_arr = np.zeros((1, len(data_lines)))  # [mag_acc_t1, mag_acc_t2, ..., mag_acc_tn]
        for i in range(len(data_lines)):
            temp = data_lines[i].replace(" ", "")
            temp = temp[2:-5].split(',')
            data_arr[0, i] = np.linalg.norm(np.array([float(temp[1]), float(temp[2]), float(temp[3])]))

    else:
        data_arr = np.zeros((3, len(data_lines)))
        for i in range(len(data_lines)):
            temp = data_lines[i].replace(" ", "")
            temp = temp[2:-5].split(',')
            data_arr[0, i] = float(temp[1])
            data_arr[1, i] = float(temp[2])
            data_arr[2, i] = float(temp[3])

    return data_arr

def check_default_port(port_name):
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
        '--detect_seizure',
        type=bool,
        default=True,
        help='Set to True to enable real-time seizure detection'
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
        default=0.5,
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
    main(args.save_data, args.detect_seizure, args.result_dir, args.serial_baud_r, args.recording_time,
         args.acquired_signals,
         args.serial_port)
