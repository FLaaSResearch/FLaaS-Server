import pytz

from django.core.management.base import BaseCommand
from api.models import Project, Round

from datetime import timedelta


class Command(BaseCommand):
    help = 'Report begin / end of all projects.'

    def add_arguments(self, parser):
        None

    def handle(self, *args, **options):

        # Spanish Timezone
        TZ = pytz.timezone('Europe/Madrid')

        # get project
        all_projects = Project.objects.all()

        for project in all_projects:

            rounds = Round.objects.filter(project=project).order_by('round_number')
            if len(rounds) > 0:
                begin = rounds.first().create_date.astimezone(TZ).strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]
                end_date = rounds.last().create_date + timedelta(minutes=project.max_training_time)
                end = end_date.astimezone(TZ).strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]

                print("Project %d (%s) \t Begin: %s \t End: %s" % (project.id, project.title, begin, end))
