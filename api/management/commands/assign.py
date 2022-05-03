from django.core.management.base import BaseCommand, CommandError
from api.models import Project, Profile


class Command(BaseCommand):
    help = 'Query users using a prefix and assign them to a particular project.'

    def add_arguments(self, parser):
        parser.add_argument('project', nargs=1, type=int, help="Project ID")

        # optional
        parser.add_argument('--prefix', nargs='?', type=str, default='user', help="Prefix of users to be assigned to the given project.")

    def handle(self, *args, **options):

        # get project
        try:
            project = Project.objects.get(id=options['project'][0])
        except Project.DoesNotExist:
            raise CommandError("Project with id '%d' does not exist." % options['project'][0])

        prefix = options['prefix']

        # get profiles based on the username prefix
        profiles = Profile.objects.filter(user__username__startswith=prefix)
        if len(profiles) == 0:
            raise CommandError("Could not find any usernames starting with '%s'." % prefix)

        # attach and save
        project.profiles.set(profiles)
        project.save()

        print("%d user(s) assigned succesfully to project '%s'" % (len(profiles), project.title))
