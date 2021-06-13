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
f = open('testing_lims.txt', )
lims_dict = json.load(f)
f.close()

checked_experiements = []
checked_datatypes = []

result_dict = {}

# dir_i = 0
for root, dirs, files in os.walk(results_dir):

    # if dir_i == 0:
    #     saving_path = os.path.join(root, dirs[0] + '_detected')

    # dir_i = 1
    # print(root)
    # print(dirs)
    i = 0
    for file in files:
        if file.endswith('.csv'):
            i += 1

        if i > 1:
            break

    (base_path, data_type) = os.path.split(root)
    (_, experiment_type) = os.path.split(base_path)

    vm_lims = [1000, -1]  # starting [min, max]
    sma_lims = [1000, -1]  # starting [min, max]
    data_type_n = -1
    experiment_type_n = -1

    if i > 1:

        (base_path, data_type) = os.path.split(root)
        (_, experiment_type) = os.path.split(base_path)

        print(experiment_type + "," + data_type)

        # restart_experiment = False

        if experiment_type not in checked_experiements:  # TODO: every set change
            experiment_type_n += 1
            checked_experiements.append(experiment_type)
            # restart_experiment = True
            checked_datatypes = []
            result_dict[experiment_type] = {}
            data_type_n = -1

        if data_type not in checked_datatypes:
            checked_datatypes.append(data_type)

        if data_type == "normal":
            data_type_n = 0

        if data_type == "seizure":
            data_type_n = 1

        if data_type not in result_dict[experiment_type]:
            result_dict[experiment_type][data_type] = {}

        vm_min = lims_dict[experiment_type]['normal'][0][0]
        vm_max = lims_dict[experiment_type]['seizure'][0][1]

        sma_min = lims_dict[experiment_type]['normal'][1][0]
        sma_max = lims_dict[experiment_type]['seizure'][1][1]

        vm_searched_vals = np.linspace(vm_min, vm_max, 10)
        sma_searched_vals = np.linspace(sma_min, sma_max, 10)

        probs_vm = np.zeros((len(combo_set), 2, len(vm_searched_vals), len(sma_searched_vals)))
        probs_sma = np.zeros((len(combo_set), 2, len(vm_searched_vals), len(sma_searched_vals)))

        # TODO: compute grid-search
        for i in range(len(vm_searched_vals)):
            threshold_vm = vm_searched_vals[i]

            for j in range(len(sma_searched_vals)):
                threshold_sma = sma_searched_vals[j]

                n_signals = 0
                for filename in files:
                    n_signals = len(files)

                    # if not restart_experiment:
                    full_dir = os.path.join(root, filename)
                    df = pd.read_csv(full_dir, usecols=['SCR_VM_AVG', 'SCR_SMA_AVG'])
                    df = df[(df >= 0).all(1)]

                    data_arr = df.to_numpy()
                    vm_data_arr = data_arr[:, 0]
                    sma_data_arr = data_arr[:, 1]

                    class_denom = data_arr.shape[0]

                    filt_arr_vm = vm_data_arr[vm_data_arr > threshold_vm]
                    filt_arr_sma = sma_data_arr[sma_data_arr > threshold_sma]

                    vm_correct_num = len(filt_arr_vm)
                    sma_correct_num = len(filt_arr_sma)

                    probs_vm[experiment_type_n, data_type_n, i, j] += vm_correct_num / class_denom
                    probs_sma[experiment_type_n, data_type_n, i, j] += sma_correct_num / class_denom

        # TODO: compute grid-search
        for i in range(len(vm_searched_vals)):
            threshold_vm = vm_searched_vals[i]

            for j in range(len(sma_searched_vals)):
                threshold_sma = sma_searched_vals[j]

                n_signals = 0

                for filename in files:
                    n_signals = len(files)

                    print(data_type_n)
                    result_dict[experiment_type][data_type][str(threshold_vm) + "," + str(threshold_sma)] = [
                        probs_vm[experiment_type_n, data_type_n, i, j] / n_signals, probs_sma[experiment_type_n, data_type_n, i, j] / n_signals]

with open('probs_results_parametric_search_2.txt', 'w') as json_file:
    json.dump(result_dict, json_file)
