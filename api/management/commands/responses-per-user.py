import pytz

from django.core.management.base import BaseCommand, CommandError
from api.models import User, DeviceStatusResponse
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Report device status responses per user.'

    def add_arguments(self, parser):
        parser.add_argument('usernames', nargs='*', type=str, help="Usernames to report. If not specified, all registerd users will be reported.")

        # optional
        parser.add_argument('--past-minutes', nargs='?', type=int, default=60, help="Past time in minutes to lookup")
        parser.add_argument('--battery-level', nargs='?', type=float, default=0.0, help="Include power-plugged AND users with >= battery level threshold.")
        parser.add_argument('--plugged-only', action='store_true', help="Only include power-plugged users")

    def handle(self, *args, **options):

        # Spanish Timezone
        TZ = pytz.timezone('Europe/Madrid')

        # get arguments
        plugged_only = options['plugged_only']
        battery_level = options['battery_level']
        past_minutes = options['past_minutes']

        if len(options['usernames']) == 0:
            usernames = [user.username for user in User.objects.all()]
        else:
            usernames = options['usernames']

        missing = 0
        for username in usernames:

            # check if user with giver username exists
            if not User.objects.filter(username=username).exists():
                raise CommandError("User '%s' does not exist." % username)

            # filter all relevant responses
            responses = self.__query_device_status_responses(username, past_minutes, plugged_only, battery_level)

            if len(responses) == 0:
                missing += 1

            else:
                # print stats
                print("Filtered Device Status Responses of user '%s':" % username)

                for response in responses:
                    timestamp = response.create_date.astimezone(TZ).strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]
                    power_plugged = response.data['battery_status']['power_plugged']
                    battery = response.data['battery_status']['level']

                    if 'app_details' in response.data:
                        version_code = response.data['app_details']['version_code']
                    else:
                        version_code = 0

                    if 'usage_stats_details' in response.data:
                        usage_stats_details = response.data['usage_stats_details']
                        bucket = usage_stats_details.get('app_standby_bucket', -1)
                    else:
                        bucket = -1

                    if 'connectivity_status' in response.data:
                        active_network = response.data['connectivity_status']["active_network"]
                        type_name = active_network["type_name"]
                        subtype_name = active_network["subtype_name"]
                    else:
                        type_name = ""
                        subtype_name = ""

                    print("\t%s - version_code: %d - bucket: %d - power_plugged: %s - battery: %.2f - network: %s (%s)" % (timestamp, version_code, bucket, power_plugged, battery, type_name, subtype_name))
                print()

        total = len(usernames) - missing
        print("Total: %d responses (%d users with no relative reponses)." % (total, missing))

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
