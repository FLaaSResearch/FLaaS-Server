from django.core.management.base import BaseCommand, CommandError
from api.models import User, DeviceStatusResponse
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Count device status responses per user.'

    def add_arguments(self, parser):
        parser.add_argument('usernames', nargs='*', type=str, help="Usernames to report. If not specified, all registerd users will be reported.")

        # optional
        parser.add_argument('--past-minutes', nargs='?', type=int, default=60, help="Past time in minutes to lookup")
        parser.add_argument('--battery-level', nargs='?', type=float, default=0.0, help="Include power-plugged AND users with >= battery level threshold.")
        parser.add_argument('--plugged-only', action='store_true', help="Only include power-plugged users")

    def handle(self, *args, **options):

        # get arguments
        plugged_only = options['plugged_only']
        battery_level = options['battery_level']
        past_minutes = options['past_minutes']

        if len(options['usernames']) == 0:
            usernames = [user.username for user in User.objects.all()]
        else:
            usernames = options['usernames']

        print("username, responses")
        for username in usernames:

            # check if user with giver username exists
            if not User.objects.filter(username=username).exists():
                raise CommandError("User '%s' does not exist." % username)

            # filter all relevant responses
            responses = self.__query_device_status_responses(username, past_minutes, plugged_only, battery_level)
            print("%s, %d" % (username, len(responses)))

    def __query_device_status_responses(self, username, past_minutes, power_plugged_only, battery_level_threshold):

        # Past X minutes
        from_date_filter = timezone.now() - timedelta(minutes=past_minutes)

        # filter all relevant responses
        responses = DeviceStatusResponse.objects.filter(
            create_date__gt=from_date_filter,
            device__profile__user__username=username).order_by('-create_date')

        # build query based on settings in Project
        if power_plugged_only:

            # power plugged only
            responses = responses.filter(data__battery_status__power_plugged=True)

        else:

            # power plugged OR > battery_level_threshold
            responses = responses.filter(Q(data__battery_status__power_plugged=True) | Q(data__battery_status__level__gte=battery_level_threshold))

        return responses
