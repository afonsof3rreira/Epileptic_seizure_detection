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
f = open('probs_results_parametric_combo.txt', )
probs_dict = json.load(f)
f.close()

df_header = ['VM thrs.', 'SMA thrs.', 'precision', 'accuracy']

i = 0
precision = []
accuracy = []
data_final = {}

for experiment, vals in probs_dict.items():

    data_final[experiment] = {}
    print(experiment)
    i = 0
    precision_data = np.zeros(len(vals['normal']))
    accuracy_data = np.zeros(len(vals['normal']))

    true_negatives = np.zeros(len(vals['normal'])) # resetting fro every experiment
    false_negatives = np.zeros(len(vals['normal']))
    true_positives = np.zeros(len(vals['normal'])) # resetting fro every experiment
    false_positives = np.zeros(len(vals['normal'])) # resetting fro every experiment
    print(len(vals['normal']))
    print(len(vals['seizure']))

    max_acc = [[], [0]]
    max_prec = [[], [0]]
                    # param 1, param 2, acc or precision
    curr_exp_data = []

    for data_type, subvals in vals.items():

        i = 0
        for parameter_set, probability_set in subvals.items():

            strings = parameter_set.split(",")
            parameter_set_splt = [[], []]
            parameter_set_splt[0] = strings[0] # VM
            parameter_set_splt[1] = strings[1] # SMA

            if data_type == 'normal':
                false_positives[i] = probability_set[0]
                true_negatives[i] = 1 - probability_set[0]

            if data_type == 'seizure':
                true_positives[i] = probability_set[0]
                false_negatives[i] = 1 - probability_set[0]

                # print(true_positives[i], false_positives[i])
                precision_data[i] = true_positives[i] / (true_positives[i] + false_positives[i] + sys.float_info.epsilon)
                accuracy_data[i] = (true_positives[i] + true_negatives[i]) / (true_positives[i] + true_negatives[i] + false_positives[i] + false_negatives[i] + sys.float_info.epsilon)
                data_final[experiment][parameter_set] = [precision_data[i], accuracy_data[i]]

                if precision_data[i] > max_prec[1]:
                    max_prec[1] = precision_data[i]
                    max_prec[0] = [parameter_set_splt[0], parameter_set_splt[1]]

                if accuracy_data[i] > max_acc[1]:
                    max_acc[1] = accuracy_data[i]
                    max_acc[0] = [parameter_set_splt[0], parameter_set_splt[1]]

                curr_exp_data.append([parameter_set_splt[0], parameter_set_splt[1], precision_data[i], accuracy_data[i]])
            i += 1

    curr_exp_data.append([max_prec[0][0], max_prec[0][1], max_prec[1], -1])
    curr_exp_data.append([max_acc[0][0], max_acc[0][1], -1, max_acc[1]])

    df = pd.DataFrame(curr_exp_data)
    df.to_csv('classification_results/experiment_{}.csv'.format(experiment), sep=",", header=df_header)

# with open('confusion_matrix_results.txt', 'w') as json_file:
#     json.dump(data_final, json_file)
