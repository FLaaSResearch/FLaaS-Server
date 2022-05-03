import os
import json

import numpy as np

from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from api.models import Project, Round

from api.libs import consts


class Command(BaseCommand):
    help = 'Report round performance of a project. If a round is not specified, the last one will be used.'

    def add_arguments(self, parser):
        parser.add_argument('project', nargs=1, type=int, help="Project ID")

        parser.add_argument('--round', nargs='?', type=int, default=None, help="Round to be evaluated. If not defined, last completed round will be used.")

    def handle(self, *args, **options):

        # get arguments
        project_id = options['project'][0]
        round_number = options['round']

        # get project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise CommandError("Project with id '%d' does not exist." % project_id)

        print("Project: %s" % project.title)

        # if round_number is not defined, get last completed round
        if round_number is None:
            round = Round.objects.filter(project=project, status=Round.Status.COMPLETE).last()
            print("Exact round was not specified, using last completed round '%d'" % round.round_number)

        # else, get the round
        else:
            try:
                round = Round.objects.get(project=project, round_number=round_number)
            except Round.DoesNotExist:
                raise CommandError("Round %d does not exist in project with id '%d'." % (round_number, project_id))

        completed_rounds = self.__count_rounds(project, Round.Status.COMPLETE)
        invalid_rounds = self.__count_rounds(project, Round.Status.INVALID)
        print("Rounds completed: %d/%d (plus %d invalid)" % (completed_rounds, project.number_of_rounds, invalid_rounds))

        print("Round %d Test Accuracy: TBD" % (round.round_number))

        loss_mean, loss_sd = self.__get_loss(round)
        print("Round %d Loss: %.2f (%.2f)" % (round.round_number, loss_mean, loss_sd))

    def __count_rounds(self, project, status):
        return Round.objects.filter(project=project, status=status).count()

    def __get_sessions(self, path):

        # list sessions (folders, not files)
        (sessions, _) = default_storage.listdir(path)

        return sessions

    def __get_loss(self, round):

        project_id = round.project.id
        round_number = round.round_number

        round_path = os.path.join(consts.PROJECTS_PATH, str(project_id), str(round_number))

        # query round joined devices
        sessions = self.__get_sessions(round_path)

        # append losses
        losses = []
        for session in sessions:

            # get losses
            performance_file = os.path.join(round_path, session, consts.PERFORMANCE_FILENAME)
            if default_storage.exists(performance_file):

                # read json as dict
                data = default_storage.open(performance_file).read()
                data = json.loads(data)

                # if Baseline or Joint Samples
                if data['local_training_worker'].get('epochs'):
                    losses.append(data['local_training_worker']['epochs'][-1])

                # else, Joint Models
                else:
                    # add RGB losses
                    app_losses = []
                    app_losses.append(data['local_training_worker']['Red']['epochs'][-1])
                    app_losses.append(data['local_training_worker']['Green']['epochs'][-1])
                    app_losses.append(data['local_training_worker']['Blue']['epochs'][-1])

                    # mean of all three losses
                    losses.append(np.mean(app_losses))

        # return mean and std
        return np.mean(losses, axis=0), np.std(losses, axis=0)
