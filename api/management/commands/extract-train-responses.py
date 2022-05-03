import os
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from api.models import Project, Round


class Command(BaseCommand):
    help = 'Extract train reponses into a json file.'

    def add_arguments(self, parser):
        parser.add_argument('project', nargs=1, type=int, help="Project ID")
        parser.add_argument('filename', nargs=1, type=str, help="Output filename (requires a .json extension)")

        type_choices = ['available', 'joined', 'replied']
        parser.add_argument('--type', choices=type_choices, default=type_choices[2], help="Choose the type of responses to be included.")

    def handle(self, *args, **options):

        # get project
        try:
            project = Project.objects.get(id=options['project'][0])
        except Project.DoesNotExist:
            raise CommandError("Project with id '%d' does not exist." % options['project'][0])

        # get properties
        responses_type = options['type']

        # init output list
        output_list = []

        # iterate through all complete rounds (also include TRAINING to include last round)
        rounds = Round.objects.filter(Q(status=Round.Status.COMPLETE) | Q(status=Round.Status.TRAINING), project=project).order_by('round_number')
        for round in rounds:

            # get related responses based on type
            if responses_type == "replied":
                device_train_responses = round.device_train_request.device_train_responses.all()
                devices = [reponse.device for reponse in device_train_responses]

            elif responses_type == "joined":
                devices = round.joined_devices.all()

            elif responses_type == "available":
                devices = round.requested_training_devices.all()

            else:
                raise CommandError("Unknown type %s." % responses_type)

            # build the dict entry
            entry = [{
                "username": device.profile.user.username,
                "samples_index": device.samples_index,
            } for device in devices]

            # Old code, enable if round is needed
            # # add to entry
            # entry = {
            #     "round": round.round_number,
            #     "devices": devices_entry,
            # }

            # append to list
            output_list.append(entry)

        # save output into a file
        content = ContentFile(json.dumps(output_list, indent=4))
        filename = options['filename'][0]
        default_storage.save(os.path.join("results", "distributions", filename), content)
