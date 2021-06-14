import datetime
import os
import pandas as pd
import numpy as np
import json


class fft_training:
    def __init__(self, sf: int, window_size: float, overlap=50):
        """Initializes a new instance of the fft training class.

        Args:
            sf (int) sampling frequency in Hertz.
            window_size (int): the window size in milliseconds for feature extraction.
            overlap (float): the window overlap as a percentage of the window size between consecutive extractions.
        """
        self.sf = sf
        self.window_size = int((window_size * sf) / 1000)  # keeps the integer part (floor)
        print(self.window_size)
        assert 0 <= overlap < 100
        self.stride = int(np.ceil(((100 - overlap) / 100) * self.window_size))
        self.raw_data = {}
        self.feature_data = {}
        self.computed_sample_order = []

        # If n is even, the length of the transformed axis is (n / 2) + 1.
        # If n is odd, the length is (n + 1) / 2. (fft.rfft function)
        if self.window_size % 2 == 0:
            self.fft_size = (self.window_size // 2) + 1
        else:
            self.fft_size = (self.window_size // 2) + 2

        self.spectral_weights = None

    def set_and_save_acc_features(self, preprocessed_data_dir: str, output_folder_dir: str):
        print('...extracting and saving acceleration features')

        activities_rel_path = os.path.join('normal', 'activities')
        still_motion_rel_path = os.path.join('normal', 'still_motions')
        seizure_rel_path = 'seizure'

        data_sub_dirs = [[os.path.join(preprocessed_data_dir, activities_rel_path),
                          os.path.join(preprocessed_data_dir, still_motion_rel_path)],
                         [os.path.join(preprocessed_data_dir, seizure_rel_path)]]

        # searching, cropping and adding acceleration data as numpy arrays to the raw_data list
        for folder_set in data_sub_dirs:

            if os.path.basename(folder_set[0]) == 'seizure':
                series_type = 'seizure'
                print('...retrieving \"seizure\" data')
            else:
                series_type = 'normal'
                print('...retrieving \"normal\" data')

            sub_raw_data = {}  # list containing numpy arrays of a class of time-series
            searched_filename_order = []

            for folder_dir in folder_set:

                if os.path.basename(folder_dir) == 'activities':
                    saving_path = os.path.join(output_folder_dir, activities_rel_path)

                elif os.path.basename(folder_dir) == 'still_motions':
                    saving_path = os.path.join(output_folder_dir, still_motion_rel_path)

                else:
                    saving_path = os.path.join(output_folder_dir, seizure_rel_path)

                for filename in os.listdir(folder_dir):
                    if filename.endswith(".csv"):

                        print('   -> ' + filename + ' signal')

                        full_dir = os.path.join(folder_dir, filename)
                        df = pd.read_csv(full_dir, index_col=[0])  # to ignore reading the index column

                        vm_vals, sma_vals = [], []
                        for index, row in df.iterrows():
                            mag_arr = np.array([row["acc_x"], row["acc_y"], row["acc_z"]])

                            vm_vals.append(np.linalg.norm(mag_arr))
                            sma_vals.append((abs(mag_arr[0]) + abs(mag_arr[1]) + abs(mag_arr[2])) / 3)

                        # Using DataFrame.insert() to add a column
                        df.insert(6, "VM", vm_vals, True)
                        df.insert(7, "SMA", sma_vals, True)
                        df.to_csv(os.path.join(saving_path, filename), sep=",")  # saving csv file

                        sub_raw_data.update({filename: df.to_numpy()})
                        searched_filename_order.append(filename)

            # each key is given by the folder name containing files of each type of time series
            self.raw_data.update({series_type: sub_raw_data})
            self.computed_sample_order.append(searched_filename_order)

    def set_acc_features(self, input_data_folder_dir: str):
        print('...retrieving saved acceleration features')

        activities_rel_path = os.path.join('normal', 'activities')
        still_motion_rel_path = os.path.join('normal', 'still_motions')
        seizure_rel_path = 'seizure'

        data_sub_dirs = [[os.path.join(input_data_folder_dir, activities_rel_path),
                          os.path.join(input_data_folder_dir, still_motion_rel_path)],
                         [os.path.join(input_data_folder_dir, seizure_rel_path)]]

        # searching, cropping and adding acceleration data as numpy arrays to the raw_data list
        for folder_set in data_sub_dirs:

            if os.path.basename(folder_set[0]) == 'seizure':
                series_type = 'seizure'
                print('...retrieving \"seizure\" data')
            else:
                series_type = 'normal'
                print('...retrieving \"normal\" data')

            sub_raw_data = {}  # list containing numpy arrays of a class of time-series
            searched_filename_order = []

            for folder_dir in folder_set:

                if os.path.basename(folder_dir) == 'activities':
                    retrieving_path = os.path.join(input_data_folder_dir, activities_rel_path)

                elif os.path.basename(folder_dir) == 'still_motions':
                    retrieving_path = os.path.join(input_data_folder_dir, still_motion_rel_path)

                else:
                    retrieving_path = os.path.join(input_data_folder_dir, seizure_rel_path)

                for filename in os.listdir(folder_dir):
                    if filename.endswith(".csv"):
                        print('   -> ' + filename + ' signal')

                        full_dir = os.path.join(folder_dir, filename)
                        df = pd.read_csv(full_dir, index_col=[0])  # to ignore reading the index column
                        sub_raw_data.update({filename: df.to_numpy()})

                        searched_filename_order.append(filename)

            # each key is given by the folder name containing files of each type of time series
            self.raw_data.update({series_type: sub_raw_data})
            self.computed_sample_order.append(searched_filename_order)

    def set_acc_data(self, folder_dirs: list):
        """previous non-saving version.
        """

        # if columns is None:
        #     columns = ["time", "acc_x", "acc_y", "acc_z"]

        # searching, cropping and adding acceleration data as numpy arrays to the raw_data list
        for folder_dir in folder_dirs:
            print('...retrieving \"' + os.path.basename(folder_dir) + '\" data')
            sub_raw_data = []  # list containing numpy arrays of a class of time-series

            searched_filename_order = []
            for filename in os.listdir(folder_dir):
                if filename.endswith(".csv"):
                    print('   -> ' + filename + ' signal')

                    full_dir = os.path.join(folder_dir, filename)
                    df = pd.read_csv(full_dir, index_col=[0])  # to ignore reading the index column

                    vm_vals, sma_vals = [], []
                    for index, row in df.iterrows():
                        mag_arr = np.array([row["acc_x"], row["acc_y"], row["acc_z"]])

                        vm_vals.append(np.linalg.norm(mag_arr))
                        sma_vals.append((abs(mag_arr[0]) + abs(mag_arr[1]) + abs(mag_arr[2])) / 3)

                    # Using DataFrame.insert() to add a column
                    df.insert(6, "VM", vm_vals, True)
                    df.insert(7, "SMA", sma_vals, True)

                    sub_raw_data.append(df.to_numpy())
                    searched_filename_order.append(filename)

            # each key is given by the folder name containing files of each type of time series
            self.raw_data.update({os.path.basename(folder_dir): sub_raw_data})
            # self.raw_data[os.path.basename(folder_dir)] = sub_raw_data

            self.computed_sample_order.append(searched_filename_order)

    def spectral_weights_extractor(self):

        print('Computing spectral weights...')

        fft_data = []
        found_order = []

        for data_type, data_list in self.raw_data.items():
            print(data_type)

            found_order.append(data_type)

            # If n is even, the length of the transformed axis is (n / 2) + 1.
            # If n is odd, the length is (n + 1) / 2. (fft.rfft function)
            if self.window_size % 2 == 0:
                fft_size = (self.window_size // 2) + 1
            else:
                fft_size = (self.window_size // 2) + 2

            fft_concat_tot_vm = np.zeros((1, fft_size))
            fft_concat_tot_sma = np.zeros((1, fft_size))

            for filename, data_arr in data_list.items():
                fft_concat_vm = np.zeros(fft_size)
                fft_concat_sma = np.zeros(fft_size)

                sample_size = data_arr.shape[0]
                n_windows = int(np.floor((sample_size - self.window_size) / self.stride)) + 1

                # iterating through every window's initial index
                ind_initial = 0
                for i in range(n_windows):
                    # ["time", "acc_x", "acc_y", "acc_z", "VM", SMA"] = [0, 1, 2, 3, 4, 5]
                    # temp_window = data_arr[ind_initial:ind_initial + self.window_size, :]
                    # temp_feature_window = np.zeros((self.window_size, 2))

                    ft_window_vm = np.abs(
                        np.fft.rfft(data_arr[int(ind_initial):ind_initial + self.window_size, 6]))
                    ft_window_sma = np.abs(
                        np.fft.rfft(data_arr[ind_initial:ind_initial + self.window_size, 7]))

                    # summing the magnitudes along each frequency
                    fft_concat_vm = np.sum([fft_concat_vm, ft_window_vm], axis=0)
                    fft_concat_sma = np.sum([fft_concat_sma, ft_window_sma], axis=0)

                    ind_initial += self.stride

                # normalizing every frequency bin
                fft_concat_vm = np.divide(fft_concat_vm, np.sum([fft_concat_vm], axis=1))
                fft_concat_sma = np.divide(fft_concat_sma, np.sum([fft_concat_sma], axis=1))

                fft_concat_tot_vm = np.sum([fft_concat_tot_vm, fft_concat_vm])
                fft_concat_tot_sma = np.sum([fft_concat_tot_sma, fft_concat_sma])

            fft_concat_tot_vm = np.squeeze(np.divide(fft_concat_tot_vm, len(data_list)))
            fft_concat_tot_sma = np.squeeze(np.divide(fft_concat_tot_sma, len(data_list)))

            fft_data.append([fft_concat_tot_vm, fft_concat_tot_sma])

        ind_num = 0
        ind_denom = 1

        if found_order[0] == "normal" and found_order[1] == "seizure":
            ind_num = 1
            ind_denom = 0

        self.spectral_weights = np.transpose(
            np.squeeze(np.array([[np.divide(fft_data[ind_num][0], fft_data[ind_denom][0])],
                                 [np.divide(fft_data[ind_num][1], fft_data[ind_denom][1])]])))

    def spectral_weights_extractor_v2(self, training_data: list):
        # [training_data_normal, training_data_seizure]

        print('Computing spectral weights...')

        fft_data = []

        for data_type in training_data:
            fft_concat_tot_vm = np.zeros((1, self.fft_size))
            fft_concat_tot_sma = np.zeros((1, self.fft_size))

            for training_signal in data_type:
                data_arr = training_signal[-1]

                fft_concat_vm = np.zeros(self.fft_size)
                fft_concat_sma = np.zeros(self.fft_size)

                sample_size = data_arr.shape[0]
                n_windows = int(np.floor((sample_size - self.window_size) / self.stride)) + 1

                # iterating through every window's initial index
                ind_initial = 0
                for i in range(n_windows):
                    ft_window_vm = np.abs(
                        np.fft.rfft(data_arr[int(ind_initial):ind_initial + self.window_size, 6]))
                    ft_window_sma = np.abs(
                        np.fft.rfft(data_arr[ind_initial:ind_initial + self.window_size, 7]))

                    # summing the magnitudes along each frequency
                    fft_concat_vm = np.sum([fft_concat_vm, ft_window_vm], axis=0)
                    fft_concat_sma = np.sum([fft_concat_sma, ft_window_sma], axis=0)

                    ind_initial += self.stride

                # normalizing every frequency bin
                fft_concat_vm = np.divide(fft_concat_vm, np.sum([fft_concat_vm], axis=1))
                fft_concat_sma = np.divide(fft_concat_sma, np.sum([fft_concat_sma], axis=1))

                fft_concat_tot_vm = np.sum([fft_concat_tot_vm, fft_concat_vm])
                fft_concat_tot_sma = np.sum([fft_concat_tot_sma, fft_concat_sma])

            fft_concat_tot_vm = np.squeeze(np.divide(fft_concat_tot_vm, len(data_type)))
            fft_concat_tot_sma = np.squeeze(np.divide(fft_concat_tot_sma, len(data_type)))

            fft_data.append([fft_concat_tot_vm, fft_concat_tot_sma])

        ind_num = 1
        ind_denom = 0

        return np.transpose(np.squeeze(np.array([[np.divide(fft_data[ind_num][0], fft_data[ind_denom][0])],
                                                 [np.divide(fft_data[ind_num][1], fft_data[ind_denom][1])]])))

    def select_data_partition(self, datatypes: dict, partition_combo: list, frac_train_test: float):

        print('...generating partition')
        training_data_normal, training_data_seizure = [], []
        testing_data_normal, testing_data_seizure = [], []

        for key, val in datatypes.items():
            if key == 'normal':
                test_current_whole_motion = False
                for motion, activities in val.items():

                    if motion in partition_combo:  # TODO:
                        test_current_whole_motion = True

                    for sub_activities, rel_path_list in activities.items():

                        if test_current_whole_motion or sub_activities in partition_combo:

                            # generating a random partition for a searched group of target data
                            sub_s_size = len(rel_path_list)
                            vec = np.arange(sub_s_size)
                            round_s_size = int(np.floor(sub_s_size * frac_train_test))
                            np.random.shuffle(vec)
                            train_ind_vec = vec[0: round_s_size]

                            i = 0
                            for rel_path in rel_path_list:
                                if i in train_ind_vec:
                                    training_data_normal.append(
                                        [key, motion, sub_activities, os.path.basename(rel_path),
                                         self.raw_data[key][os.path.basename(rel_path)]])
                                else:
                                    testing_data_normal.append([key, motion, sub_activities, os.path.basename(rel_path),
                                                                self.raw_data[key][os.path.basename(rel_path)]])
                                i += 1

            elif key == 'seizure':

                # generating a random partition for a searched group of target data
                sub_s_size = len(val)
                vec = np.arange(sub_s_size + 1)
                round_s_size = int(np.floor(sub_s_size * frac_train_test))
                np.random.shuffle(vec)
                train_ind_vec = vec[0: round_s_size]
                i = 0

                for rel_path in val:
                    if i in train_ind_vec:
                        training_data_seizure.append([key, ' ', ' ', os.path.basename(rel_path),
                                                      self.raw_data[key][os.path.basename(rel_path)]])
                    else:
                        testing_data_seizure.append([key, ' ', ' ', os.path.basename(rel_path),
                                                     self.raw_data[key][os.path.basename(rel_path)]])
                    i += 1

        return [training_data_normal, training_data_seizure], [testing_data_normal, testing_data_seizure]

    def seizure_detection(self, n_avg: int, testing_data: list, spectral_weights: np.ndarray):

        # signal_list_training = [["normal", "signal name.csv"], ["seizure", "signal name"], ...]
        # signal_list_testing = [["normal", "signal name.csv"], ["seizure", "signal name"], ...]

        spectral_weight_vm = np.transpose(spectral_weights[:, 0])
        spectral_weight_sma = np.transpose(spectral_weights[:, 1])

        print('testing...')

        tested_signal_types_detected = []

        for signal_type in testing_data:

            sub_tested_signals_detected = []

            for signal in signal_type:

                signal_info = signal[:-1]
                signal_data = signal[-1]
                new_shape = (signal_data.shape[0], signal_data.shape[1] + 4)  # adding another column for detection

                signal_detected_data = np.multiply(np.ones(new_shape), -1)
                signal_detected_data[:, :signal_data.shape[1]] = signal_data

                sample_size = signal_data.shape[0]

                n_windows = int(np.floor((sample_size - self.window_size) / self.stride)) + 1

                ind_initial = 0
                n_avg_i = 0
                scr_vm_sum = 0
                scr_sma_sum = 0

                for i in range(n_windows):

                    fft_temp_vm = np.abs(
                        np.fft.rfft(signal_data[int(ind_initial):ind_initial + self.window_size, 6]))
                    fft_temp_sma = np.abs(
                        np.fft.rfft(signal_data[ind_initial:ind_initial + self.window_size, 7]))

                    vm_num = np.multiply(fft_temp_vm, spectral_weight_vm)
                    sma_num = np.multiply(fft_temp_sma, spectral_weight_sma)

                    scr_vm = np.divide(np.sum(vm_num, axis=0), np.sum(fft_temp_vm, axis=0))
                    scr_sma = np.divide(np.sum(sma_num, axis=0), np.sum(fft_temp_sma, axis=0))

                    signal_detected_data[ind_initial + self.window_size, -4] = scr_vm
                    signal_detected_data[ind_initial + self.window_size, -3] = scr_sma

                    scr_vm_sum += scr_vm
                    scr_sma_sum += scr_sma

                    if n_avg_i == n_avg - 1:
                        signal_detected_data[ind_initial + self.window_size, -2] = scr_vm_sum / n_avg
                        signal_detected_data[ind_initial + self.window_size, -1] = scr_sma_sum / n_avg
                        scr_vm_sum = 0
                        scr_sma_sum = 0
                        n_avg_i = 0
                    else:
                        n_avg_i += 1

                    ind_initial += self.stride

                signal_detected = signal_info
                signal_detected.append(signal_detected_data)
                sub_tested_signals_detected.append(signal_detected)

            tested_signal_types_detected.append(sub_tested_signals_detected)

        return tested_signal_types_detected

    def save_weights_to_csv(self, output_path: str, df_header=None, filename=None):
        if df_header is None:
            df_header = ["VM weights", "SMA weights"]

        df = pd.DataFrame(self.spectral_weights)  # creating dataframe
        if filename is None:
            name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')  # string with the date of the experiment
        else:
            name = filename
        df.to_csv(os.path.join(output_path, 'spectral_weights_{}.csv'.format(name)), header=df_header,
                  sep=",")  # saving csv file
        print('Trained data saved as ' + os.path.join(output_path, 'spectral_weights_{}.csv'.format(name)))


def save_weights_to_csv_v2(spectral_weights, output_path: str, df_header=None, filename=None):
    if df_header is None:
        df_header = ["VM weights", "SMA weights"]

    df = pd.DataFrame(spectral_weights)  # creating dataframe
    if filename is None:
        name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')  # string with the date of the experiment
    else:
        name = filename
    df.to_csv(os.path.join(output_path, 'spectral_weights_{}.csv'.format(name)), header=df_header,
              sep=",")  # saving csv file
    print('Trained data saved as ' + os.path.join(output_path, 'spectral_weights_{}.csv'.format(name)))


def get_header_info(folder_dir: str, filename: str):
    return list(pd.read_csv(os.path.join(folder_dir, filename)).columns.values)


def save_acc_features(preprocessed_data_dir: str, output_folder_dir: str):
    print('...extracting and saving acceleration features')

    activities_rel_path = os.path.join('normal', 'activities')
    still_motion_rel_path = os.path.join('normal', 'still_motions')
    seizure_rel_path = 'seizure'

    data_sub_dirs = [[os.path.join(preprocessed_data_dir, activities_rel_path),
                      os.path.join(preprocessed_data_dir, still_motion_rel_path)],
                     [os.path.join(preprocessed_data_dir, seizure_rel_path)]]

    # searching, cropping and adding acceleration data as numpy arrays to the raw_data list
    for folder_set in data_sub_dirs:

        if os.path.basename(folder_set[0]) == 'seizure':
            print('...retrieving \"seizure\" data')
        else:
            print('...retrieving \"normal\" data')

        for folder_dir in folder_set:

            if os.path.basename(folder_dir) == 'activities':
                saving_path = os.path.join(output_folder_dir, activities_rel_path)

            elif os.path.basename(folder_dir) == 'still_motions':
                saving_path = os.path.join(output_folder_dir, still_motion_rel_path)

            else:
                saving_path = os.path.join(output_folder_dir, seizure_rel_path)

            for filename in os.listdir(folder_dir):
                if filename.endswith(".csv"):

                    print('   -> ' + filename + ' signal')

                    full_dir = os.path.join(folder_dir, filename)
                    df = pd.read_csv(full_dir, index_col=[0])  # to ignore reading the index column

                    vm_vals, sma_vals = [], []
                    for index, row in df.iterrows():
                        mag_arr = np.array([row["acc_x"], row["acc_y"], row["acc_z"]])

                        vm_vals.append(np.linalg.norm(mag_arr))
                        sma_vals.append((abs(mag_arr[0]) + abs(mag_arr[1]) + abs(mag_arr[2])) / 3)

                    # Using DataFrame.insert() to add a column
                    df.insert(6, "VM", vm_vals, True)
                    df.insert(7, "SMA", sma_vals, True)
                    df.to_csv(os.path.join(saving_path, filename), sep=",")  # saving csv file


def save_detected_signals(tested_data: str, output_folder_dir: str):
    global saving_path
    print('...saving tested signals')

    normal_data = tested_data[0]
    seizure_data = tested_data[1]

    normal_dir = os.path.join(output_folder_dir, 'normal')
    seizure_dir = os.path.join(output_folder_dir, 'seizure')

    os.makedirs(normal_dir, exist_ok=True)
    os.makedirs(seizure_dir, exist_ok=True)

    header = ['time', 'acc_x', 'acc_y', 'acc_z', 'pulse', 'eda', 'VM', 'SMA', 'SCR_VM', 'SCR_SMA', 'SCR_VM_AVG',
              'SCR_SMA_AVG']

    for tested_type in tested_data:
        for tested_signal in tested_type:
            df = pd.DataFrame(tested_signal[-1], columns=header)

            if tested_signal[0] == 'normal':
                saving_path = os.path.join(normal_dir, tested_signal[3])

            elif tested_signal[0] == 'seizure':
                saving_path = os.path.join(seizure_dir, tested_signal[3])
            df.to_csv(saving_path, sep=",")  # saving csv file
