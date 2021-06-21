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

    """Reads the acceleration, pulse and EDA signals acquired from the ESP32 board

           Args:
               save_data (bool): whether or not to save the acquired signals. Set to False if you only want to detect seizures.
               detect_seizure (bool): set to True if you want to detect seizures.
               result_dir (str): saving path if save_data=True
               serial_baud_r (int): the Baud rate used in the ESP32 for data transmission.
               recording_time (float): time in minutes or fraction of minutes the data acquisition will take.
               acquired_signals (list): a list of the names (str) of the signals needed to be acquired. Edit it if you do not have some sensors.
               serial_port (str): name of the serial port, depending on the OS and computer itself. Specify yours, otherwise it will assume a default one.
               sf (int): the sampling frequency (fixed at 100 Hz for now).
               ft_window_s (int): the size of the real time detection window in seconds.
               window_overlap (int): the percentage of overlap between successive windows.
    """

    global arduino, first_ft_window, temp_window_data, window_overlap_frac, mag_list, abs_fft_vm_list, times_fft, abs_fft_sma_list, detection_window_it, detection_window, scr_vm, scr_sma, scr_vm_sum, scr_sma_sum, vm_weights, sma_weights, SMA_thrs, VM_thrs
    default, port = check_default_port(serial_port)  # the Port name as a string

    """Initialising Serial connection"""

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

    print("transmission started...")
    # reading the first line and saving the starting time
    first_read_line = str(arduino.readline())
    data_ac.add_acquisition(first_read_line)

    time_i = acq.get_current_time(first_read_line)
    time_curr = time_i

    interval_mark = 1

    if detect_seizure:
        # commented for manual threshold input ---------------

        # threshold_param_file = "experiment_a.csv"
        # path_to_thresholds = os.path.join(os.path.dirname(sys.argv[0]), "classification_results", threshold_param_file)
        # path_to_spectral_weights = os.path.join(os.path.dirname(sys.argv[0]), "data", "results", "2021-06-12-22-50-19", "a", "spectral_weights_a.csv")
        #
        # df_thresholds = pd.read_csv(path_to_thresholds, usecols=['VM thrs.', 'SMA thrs.'])
        # max_params = df_thresholds.iloc[[-1]]
        #
        # df_spectral_weights = pd.read_csv(path_to_spectral_weights, index_col=[0])
        # vm_weights = np.transpose(df_spectral_weights['VM weights'].to_numpy())
        # sma_weights = np.transpose(df_spectral_weights['SMA weights'].to_numpy())

        # print(vm_weights)
        # commented for manual threshold input ---------------


        VM_thrs = 1.7065725297694536   # max_params.iloc[0]['VM thrs.'] ,
        SMA_thrs = 1.6968069180073173   # max_params.iloc[0]['SMA thrs.']

        print(VM_thrs)

        first_ft_window = True
        temp_window_data = collections.deque([first_read_line])
        window_overlap_frac = 100 // window_overlap
        mag_list = []
        abs_fft_vm_list = []
        abs_fft_sma_list = []
        times_fft = []
        detection_window = 5  # seconds
        detection_window_it = 0
        scr_vm_sum = 0
        scr_sma_sum = 0
        scr_vm = 0
        scr_sma = 0

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
                abs_ft_vm_arr, abs_ft_sma_arr = detection_algorithm(temp_window_data)
                times_fft.append(time_curr - time_i)
                abs_fft_vm_list.append(abs_ft_vm_arr)
                abs_fft_sma_list.append(abs_ft_sma_arr)
                # print(abs_ft_vm_arr.shape)
                # print(vm_weights.shape)

                vm_num = np.squeeze(np.multiply(abs_ft_vm_arr, vm_weights))
                sma_num = np.squeeze(np.multiply(abs_ft_sma_arr, sma_weights))

                scr_vm = np.divide(np.sum(vm_num, axis=0), np.sum(np.squeeze(abs_ft_vm_arr), axis=0))
                scr_sma = np.divide(np.sum(sma_num, axis=0), np.sum(np.squeeze(abs_ft_sma_arr), axis=0))

                # remove the first/left (sf * ft_window_s) / 2 points, resulting in (sf * ft_window_s) + 1 points
                for _ in range(sf * ft_window_s // window_overlap_frac):
                    temp_window_data.popleft()

                first_ft_window = False
                # print('first')
                # print(scr_vm)

                detection_window_it += 1
                scr_vm_sum += scr_vm
                scr_sma_sum += scr_sma

                # np.itertools.starmap(temp_window_data.popleft, np.repeat((), 4096))

            # if the next overlapping window was recorded, start detection thread and update the temp. window
            elif ((time_curr - time_i) * 0.001) % (ft_window_s / window_overlap_frac) == 0 and not first_ft_window:



                times_fft.append(time_curr - time_i)
                abs_ft_vm_arr, abs_ft_sma_arr = detection_algorithm(temp_window_data)
                abs_fft_vm_list.append(abs_ft_vm_arr)
                abs_fft_sma_list.append(abs_ft_sma_arr)

                vm_num = np.squeeze(np.multiply(abs_ft_vm_arr, vm_weights))
                # print(vm_num)
                sma_num = np.squeeze(np.multiply(abs_ft_sma_arr, sma_weights))


                scr_vm = np.divide(np.sum(vm_num, axis=0), np.sum(np.squeeze(abs_ft_vm_arr), axis=0))
                scr_sma = np.divide(np.sum(sma_num, axis=0), np.sum(np.squeeze(abs_ft_sma_arr), axis=0))
                # print(scr_vm)
                # print('--')
                # print(scr_vm)
                detection_window_it += 1
                # print('next')
                #
                # print(scr_vm)
                scr_vm_sum += scr_vm
                scr_sma_sum += scr_sma

                # remove the first/left (sf * ft_window_s) / 2 points, resulting in (sf * ft_window_s) + 1 points
                for _ in range(sf * ft_window_s // window_overlap_frac):
                    temp_window_data.popleft()


            # print(' Time elapsed:', timeit.default_timer() - start_time, 's')

        # print(detection_window_it)

        if ((time_curr - time_i) * 0.001) % detection_window == 0:
            # print('finish')

            scr_vm_avg = scr_vm_sum / (detection_window_it + 1)
            scr_sma_avg = scr_sma_sum / (detection_window_it + 1)
            # print(scr_vm_avg)

            # print(scr_vm_avg, detection_window_it + 1)
            # print(scr_sma_avg, detection_window_it + 1)
            # print('--')
            # print()

            # print()
            # print(scr_vm_avg)
            # print(VM_thrs)

            if scr_vm_avg > VM_thrs and scr_sma_avg > SMA_thrs:
                arduino.write(b's')
                print('...SEIZURE DETECTED!!!!!!')

            else:
                # arduino.write(b'n')
                print('...normal')


            scr_vm_sum = 0
            scr_sma_sum = 0
            scr_vm_avg = 0
            scr_sma_avg = 0

            detection_window_it = 0



    print("...transmission finished")

    if save_data:
        print("checking on acquired data...")
        data_ac.clean_raw_data(save_delays=True, sf=sf)
        data_ac.print_delays()

        # generate result directory if it does not exist
        os.makedirs(result_dir, exist_ok=True)

        print("saving acquired data...")
        data_ac.save_data_to_csv(result_dir, df_header=acq.getHeaderfromSignals(acquired_signals))

        # t = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')  # string with the date of the experiment

        # data_fft, header_fft = write_2(times_fft, mag_list, abs_fft_list)
        # df_fft = pd.DataFrame(data_fft)

        # shape = df_fft.shape
        # print('\nDataFrame Shape :', shape)
        # print('\nNumber of rows :', shape[0])
        # print('\nNumber of columns :', shape[1])

        # df_fft.to_csv(os.path.join(result_dir, 'rt_data_fft_windows_{}.csv'.format(t)), header=header_fft,
        #              sep=",")  # saving csv file
        # print('FFT data saved as ' + os.path.join(result_dir, 'rt_data_fft_windows_{}.csv'.format(t)))


def detection_algorithm(data_chunk: collections.deque, magnitude=True):
    # implement an algorithm based on the following article https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5375767/ [1]
    # check this one too https://odr.chalmers.se/bitstream/20.500.12380/145997/1/145997.pdf

    # TODO: compute the FFT weights based on a series of seizure vs baseline datasets [1]
    vm_arr, sma_arr = getArrayfromStringList(data_chunk)

    abs_ft_vm_arr = np.abs(np.fft.rfft(vm_arr))
    abs_ft_sma_arr = np.abs(np.fft.rfft(sma_arr))

    return abs_ft_vm_arr, abs_ft_sma_arr


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


def getArrayfromStringList(data_lines: collections.deque):

    data_arr_vm = np.zeros((1, len(data_lines)))  # [mag_acc_t1, mag_acc_t2, ..., mag_acc_tn]
    data_arr_sma = np.zeros((1, len(data_lines)))
    for i in range(len(data_lines)):
        temp = data_lines[i].replace(" ", "")
        temp = temp[2:-5].split(',')
        data_arr_vm[0, i] = np.linalg.norm(np.array([float(temp[1]), float(temp[2]), float(temp[3])]))
        data_arr_sma[0, i] = (abs(float(temp[1])) + abs(float(temp[2])) + abs(float(temp[3]))) / 3

    return data_arr_vm, data_arr_sma

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
        default=1.5,
        help='Time in minutes or fraction of minutes the data acquisition will take.'
    )

    parser.add_argument(
        '--acquired_signals',
        type=list,
        default=['time', 'acc', 'pulse', 'eda'],
        help='A list of the names of the signals needed to be acquired. Edit it if you do not have some sensors.'
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
