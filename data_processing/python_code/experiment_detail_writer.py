import os

'''
this script writes a .txt file containing the used training and testing data
'''


def experiment_writer(saving_path: str, training_data: list, testing_data: list, filename: str, experiment_name: str):

    if not os.path.exists(os.path.join(saving_path, filename + '.txt')):

        with open(os.path.join(saving_path, filename + '.txt'), 'w') as outfile:

            outfile.write('=' * 10 + ' Experiment No.' + experiment_name + ' ' + '=' * 10 + '\n\n')

            outfile.write('-' * 10 + ' Training data ' + '-' * 10)
            outfile.write('\n' + '-' * 37 + '\n')

            # getting and writing all used training data
            for train_type in training_data:
                for data in train_type:
                    outfile.write('\n' + '# ' + str(data[:-1]))
                    outfile.write('\n')
            outfile.write('\n' + '-' * 37 + '\n')

            outfile.write('-' * 10 + ' Testing data ' + '-' * 10)
            outfile.write('\n' + '-' * 37 + '\n')

            # getting and writing all used testing data
            for testing_type in testing_data:
                for data in testing_type:
                    outfile.write('\n' + '# ' + str(data[:-1]))
                    outfile.write('\n')
            outfile.write('\n' + '-' * 37 + '\n')
