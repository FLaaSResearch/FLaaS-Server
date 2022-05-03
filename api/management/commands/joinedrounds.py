from django.core.management.base import BaseCommand, CommandError
from api.models import Project, Device


class Command(BaseCommand):
    help = 'Report number of joined rounds per user.'

    def add_arguments(self, parser):
        parser.add_argument('project', nargs=1, type=int, help="Project ID")

    def handle(self, *args, **options):

        # get project
        try:
            project = Project.objects.get(id=options['project'][0])
        except Project.DoesNotExist:
            raise CommandError("Project with id '%d' does not exist." % options['project'][0])

        print("Project '%s'" % project.title)

        # get all devices registered in the system
        all_devices = Device.objects.all().order_by('profile__user__username')

        excluded = []
        print("username, joined_rounds")
        for device in all_devices:

            username = device.profile.user.username
            joined_rounds_count = device.joined_rounds.filter(project=project).count()
            if joined_rounds_count != 0:
                print("%s, %d" % (username, joined_rounds_count))
            else:
                excluded.append(username)

        print("Excluded %d users with zero joined rounds: %s" % (len(excluded), excluded))
