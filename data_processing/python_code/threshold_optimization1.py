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

lims_dict = {}
results_dict = {}

for root, dirs, files in os.walk(results_dir):

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

    if i > 1:

        (base_path, data_type) = os.path.split(root)
        (_, experiment_type) = os.path.split(base_path)

        print(experiment_type, data_type)

        restart_experiment = False

        if experiment_type not in lims_dict:  # TODO: every set change
            lims_dict[experiment_type] = {}
            results_dict[experiment_type] = {}
            restart_experiment = True

        if 'normal' not in lims_dict[experiment_type] and data_type == 'normal':
            lims_dict[experiment_type]['normal'] = {}
            vm_lims = [1000, -1]  # starting [min, max]
            sma_lims = [1000, -1]  # starting [min, max]
            # print('restarting vals for normal')

        if 'seizure' not in lims_dict[experiment_type] and data_type == 'seizure':
            lims_dict[experiment_type]['seizure'] = {}
            vm_lims = [1000, -1]  # starting [min, max]
            sma_lims = [1000, -1]  # starting [min, max]
            # print('restarting vals for seizure')

        for filename in files:

            full_dir = os.path.join(root, filename)
            df = pd.read_csv(full_dir, usecols=['SCR_VM_AVG', 'SCR_SMA_AVG'])
            df = df[(df >= 0).all(1)]

            min_df = df.min(axis=0).to_numpy()  # return minimum value detected
            max_df = df.max(axis=0).to_numpy()

            if max_df[0] > vm_lims[1]:
                vm_lims[1] = max_df[0]

            if max_df[1] > sma_lims[1]:
                sma_lims[1] = max_df[1]

            if min_df[0] < sma_lims[0]:
                sma_lims[0] = min_df[0]

            if min_df[1] < vm_lims[0]:
                vm_lims[0] = min_df[1]

        if data_type == "normal":
            lims_dict[experiment_type]['normal'] = [vm_lims, sma_lims]

        if data_type == "seizure":
            lims_dict[experiment_type]['seizure'] = [vm_lims, sma_lims]

        # if not restart_experiment: # TODO: compute grid-search
        #     vm_searched_vals = np.linspace(lims_dict[experiment_type]['normal'])
        #     print('compute grid search')

for exp, vals in lims_dict.items():
    result = []

    if vals["normal"][0][1] > vals["seizure"][0][0]:
        result.append(-1)

    else:
        result.append(vals["seizure"][0][0] - vals["normal"][0][1])

    if vals["normal"][1][1] > vals["seizure"][1][0]:
        result.append(-1)

    else:
        result.append(vals["seizure"][0][0] - vals["normal"][0][1])

    results_dict[exp] = result



# with open('testing_lims_filt.txt', 'w') as json_file1:
#     json.dump(results_dict, json_file1)

# with open('testing_lims.txt', 'w') as json_file:
#     json.dump(lims_dict, json_file)





