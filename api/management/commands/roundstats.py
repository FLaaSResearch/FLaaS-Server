from django.core.management.base import BaseCommand, CommandError
from api.models import Project, Round, DeviceTrainRequest


class Command(BaseCommand):
    help = 'Report joined users per round.'

    def add_arguments(self, parser):
        parser.add_argument('project', nargs=1, type=int, help="Project ID")

    def handle(self, *args, **options):

        # get project
        try:
            project = Project.objects.get(id=options['project'][0])
        except Project.DoesNotExist:
            raise CommandError("Project with id '%d' does not exist." % options['project'][0])

        # get all associated rounds
        all_rounds = Round.objects.filter(project=project).order_by('round_number')

        print("Project '%s'" % project.title)
        print("Registered devices: %d" % project.profiles.count())
        print()
        print("round, status, requested_devices, joined_devices, reported_devices, reported_devices_usernames")
        for round in all_rounds:

            status_label = Round.Status(round.status).label
            requested_devices_count = round.requested_training_devices.count()
            joined_devices = round.joined_devices.all()
            try:
                reported_devices = [response.device for response in round.device_train_request.device_train_responses.all()]
            except DeviceTrainRequest.DoesNotExist:
                reported_devices = []
            usernames = [device.profile.user.username for device in reported_devices]

            print("%d, %s, %d, %d, %d, %s" % (round.round_number, status_label, requested_devices_count, len(joined_devices), len(reported_devices), str(usernames)))
