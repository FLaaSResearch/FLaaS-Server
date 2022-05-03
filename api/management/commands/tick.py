from django.core.management.base import BaseCommand  # , CommandError
from api import scheduling
from api import push_questionnaire


class Command(BaseCommand):
    help = 'Periodic Tick called from an external clock.'

    def handle(self, *args, **options):
        scheduling.tick(verbose=True)
        push_questionnaire.tick(verbose=True)
