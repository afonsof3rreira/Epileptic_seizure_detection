import os
import sys
import json
import pandas as pd
import numpy as np

results_dir = os.path.join(os.path.dirname(sys.argv[0]), 'data', 'results')

# Opening JSON file
f = open('combos.json', )
combo_set = json.load(f)
f.close()

# Opening JSON file
f = open('probs_results_parametric_combo_vf_20_20_min_max.txt', )
probs_dict = json.load(f)
f.close()

df_header = ['experiment name', 'data type', 'target param.', 'VM', 'SMA', 'P. normal', 'P. seizure']
i = 0
data_list = []

for experiment, vals in probs_dict.items():
    set_of_vals = []

    for data_type, subvals in vals.items():


        max_vals_normal = [[], []]
        min_vals_normal = [[], []]

        max_vals_seizure = [[], []]
        min_vals_seizure = [[], []]

        max_prob_seizure = [0, 0]  # VM, SMA
        max_prob_normal = [0, 0]  # VM, SMA

        min_prob_seizure = [1000, 1000]  # VM, SMA
        min_prob_normal = [1000, 1000]  # VM, SMA

        for parameter_set, probability_set in subvals.items():
            strings = parameter_set.split(",")
            print(strings)
            parameter_set_splt = [[], []]
            parameter_set_splt[0] = strings[0]
            parameter_set_splt[1] = strings[1]

            if data_type == 'normal':

                if probability_set[0] > max_prob_normal[0]:
                    max_vals_normal[0] = [experiment, data_type, 'max VM', parameter_set_splt[0], parameter_set_splt[1],
                                          probability_set[0], probability_set[1]]
                    max_prob_normal[0] = probability_set[0]

                if probability_set[1] > max_prob_normal[1]:
                    max_vals_normal[1] = [experiment, data_type, 'max SMA', parameter_set_splt[0], parameter_set_splt[1],
                                          probability_set[0], probability_set[1]]
                    max_prob_normal[1] = probability_set[1]

                if probability_set[0] < min_prob_normal[0]:
                    min_vals_normal[0] = [experiment, data_type, 'min VM', parameter_set_splt[0], parameter_set_splt[1],
                                          probability_set[0], probability_set[1]]
                    min_prob_normal[0] = probability_set[0]

                if probability_set[1] < min_prob_normal[1]:
                    min_vals_normal[1] = [experiment, data_type, 'min SMA', parameter_set_splt[0], parameter_set_splt[1],
                                          probability_set[0], probability_set[1]]
                    min_prob_normal[1] = probability_set[1]

            if data_type == 'seizure':

                if probability_set[0] > max_prob_seizure[0]:
                    max_vals_seizure[0] = [experiment, data_type, 'max VM', parameter_set_splt[0], parameter_set_splt[1],
                                           probability_set[0], probability_set[1]]
                    max_prob_seizure[0] = probability_set[0]

                if probability_set[1] > max_prob_seizure[1]:
                    max_vals_seizure[1] = [experiment, data_type, 'max SMA', parameter_set_splt[0], parameter_set_splt[1],
                                           probability_set[0], probability_set[1]]
                    max_prob_seizure[1] = probability_set[1]

                if probability_set[0] < min_prob_seizure[0]:
                    min_vals_seizure[0] = [experiment, data_type, 'min VM', parameter_set_splt[0], parameter_set_splt[1],
                                           probability_set[0], probability_set[1]]
                    min_prob_seizure[0] = probability_set[0]

                if probability_set[1] < min_prob_seizure[1]:
                    min_vals_seizure[1] = [experiment, data_type, 'min SMA', parameter_set_splt[0], parameter_set_splt[1],
                                           probability_set[0], probability_set[1]]
                    min_prob_seizure[1] = probability_set[1]

        print(min_vals_normal[0])
        data_list.append(min_vals_normal[0])
        data_list.append(max_vals_seizure[0])
        data_list.append(min_vals_normal[1])
        data_list.append(max_vals_seizure[1])
        data_list.append(max_vals_normal[0])
        data_list.append(min_vals_seizure[0])
        data_list.append(max_vals_normal[1])
        data_list.append(min_vals_seizure[1])

df = pd.DataFrame(data_list)

df.to_csv('resuts_parametric_search_vf.csv', sep=",", header=df_header)
