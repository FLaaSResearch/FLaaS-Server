import os
import io

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from api.libs.filemanagement import get_subfolders

matplotlib.use('Agg')


def get_sessions(path, round):

    path = os.path.join(path, str(round))

    # list sessions (folders, not files)
    (sessions, _) = default_storage.listdir(path)

    # convert to int and sort
    sessions = [int(i) for i in sessions]
    sessions.sort()

    return sessions


def produce_plot(data, labels, title, filename):

    plt.figure()

    # plot data per iteration
    for idx, (x, y, yerr) in enumerate(data):
        plt.errorbar(x, y, yerr=yerr, label=labels[idx], alpha=0.5, linewidth=2.0)

    plt.title(title)
    plt.xlabel("FL Rounds")
    plt.ylabel("Test Accuracy")

    if len(labels) > 1:
        plt.legend(loc='lower right')

    # plot into a BytesIO
    plt.tight_layout()
    memory_buffer = io.BytesIO()
    plt.savefig(memory_buffer, format='pdf', dpi=10, bbox_inches="tight")
    memory_buffer.seek(0)
    plt.close()

    # save file
    content = ContentFile(memory_buffer.getvalue())
    default_storage.save(filename, content)


def compute_plot_data(input_path, results_filename):

    rounds = get_subfolders(input_path, intsort=True)

    acc_list = []
    std_list = []

    # iterate through rounds
    for current_round in rounds:

        round_path = os.path.join(input_path, str(current_round))
        sessions = get_subfolders(round_path, intsort=True)

        # init empty list
        accuracy_list = []

        # iterate through sessions
        for session in sessions:
            session_path = os.path.join(round_path, str(session))
            # print(session_path)

            file_path = os.path.join(session_path, results_filename)
            if not default_storage.exists(file_path):
                continue

            url = default_storage.url(file_path)
            df = pd.read_csv(url, index_col=0)

            # report = classification_report(df["y_true"], df["y_pred"])
            acc = accuracy_score(df["y_true"], df["y_pred"])
            accuracy_list.append(acc)

        # mean and std per round
        np_list = np.array(accuracy_list)
        acc_mean = np_list.mean()
        acc_std = np_list.std()

        acc_list.append(acc_mean)
        std_list.append(acc_std)

    # create the plot
    x = list(map(str, rounds))
    return (x, acc_list, std_list)


def plot(path, result_filenames_list, title, output_filename):

    # list the will hold tuples of data (x, acc, std)
    data = []

    # iterate through list and append data
    for results_filename in result_filenames_list:
        x, acc, std = compute_plot_data(path, results_filename)
        data.append((x, acc, std))

    # infer label from filename (e.g., "app_0" from "performance_app_0_eval_results.csv")
    labels = [filename[12:17] for filename in result_filenames_list]
    if len(labels) > 1:
        # replace in case of joined models
        labels = [label.replace('app_0', 'Joined') for label in labels]

    # produce the plot
    output_filename = os.path.join(path, output_filename)
    produce_plot(data, labels=labels, title=title, filename=output_filename)
