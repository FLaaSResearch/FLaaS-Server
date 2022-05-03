import os

from django.core.files.storage import default_storage

from api.mlmodel import MLModel
from api.mlreport import MLReport
# from api.produce_plots import plot
from api.libs.filemanagement import filecopy, delfolder
from api.libs import consts

import numpy as np


def aggregate_model(round, into_round):

    # get project
    project = round.project

    # init model with zeros (to append weights during aggregation)
    model = MLModel(consts.MODEL_SIZE, "zeros")

    # round level
    round_path = os.path.join(consts.PROJECTS_PATH, str(project.id), str(round.round_number))

    # get all devices that reported data (weights)
    reported_devices = [response.device for response in round.device_train_request.device_train_responses.all()]
    for device in reported_devices:

        # accumulate
        file_path = os.path.join(round_path, str(device.id), consts.MODEL_WEIGHTS_FILENAME)
        model.accumulate_model(file_path)

    # aggregate weights
    model.aggregate()

    # write model into round folder
    file_path = os.path.join(consts.PROJECTS_PATH, str(project.id), str(into_round.round_number), consts.MODEL_WEIGHTS_FILENAME)
    model.write(file_path)

    # TODO: Enable once server-based eval is implemented
    # # compute required list of result filenames (from number of apps)
    # result_filenames_list = []
    # if project.apps > 1:
    #     for i in range(project.apps):
    #         result_filenames_list.append("performance_app_%d_eval_results.csv" % (i + 1))
    # result_filenames_list.append("performance_app_0_eval_results.csv")  # 0 always exists as main model

    # # produce/update round plot
    # path = os.path.join(consts.PROJECTS_PATH, str(project.id))
    # plot(path, result_filenames_list, project.title, consts.RESULTS_FIGURE_FILENAME)


def copy_model(round, into_round):

    # get project
    project = round.project

    original_model = os.path.join(consts.PROJECTS_PATH, str(project.id), str(round.round_number), consts.MODEL_WEIGHTS_FILENAME)
    new_model = os.path.join(consts.PROJECTS_PATH, str(project.id), str(into_round.round_number), consts.MODEL_WEIGHTS_FILENAME)
    filecopy(original_model, new_model)


def delete_project(project):

    # project level
    path = os.path.join(consts.PROJECTS_PATH, str(project.id))

    # delete project folder
    delfolder(path)


def reset_project(project):

    delete_project(project)

    # project level
    path = os.path.join(consts.PROJECTS_PATH, str(project.id))

    # Copy the appropriate model into the project_path
    filecopy(
        os.path.join(consts.MODELS_PATH, project.model + '.bin'),
        os.path.join(path, '0', 'model_weights.bin'))

    # reset counters
    project.current_round = 0
    project.save()


# TODO: Refactor and enable this function
def __report_results(project, round):

    # round level
    path = os.path.join(consts.PROJECTS_PATH, str(project.id), str(round))

    # init empty list
    accuracy_list = []

    # list sessions (folders, not files)
    (sessions, _) = default_storage.listdir(path)
    for session in sessions:

        # build file path
        file_path = os.path.join(path, session, consts.EVAL_RESULTS_FILENAME)

        # report
        report = MLReport(file_path)
        accuracy = report.get_accuracy()
        accuracy_list.append(accuracy)

    np_list = np.array(accuracy_list)

    print("\t>> Round %d accuracy: %.4f (%.4f)" % (project.round_counter, np_list.mean(), np_list.std()))


def __delete_round_models(project, round):

    # round level
    path = os.path.join(consts.PROJECTS_PATH, str(project.id), str(round))

    # list sessions (folders, not files)
    (sessions, _) = default_storage.listdir(path)
    for session in sessions:

        # build session path
        session_path = os.path.join(path, session)

        # delete model if exists
        file_path = os.path.join(session_path, consts.MODEL_WEIGHTS_FILENAME)
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
