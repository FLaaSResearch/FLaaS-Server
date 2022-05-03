import pytz

from django.core.management.base import BaseCommand, CommandError
from api.models import Project, DeviceStatusResponse
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Query and report device responses for users registered to a project.'

    def add_arguments(self, parser):

        parser.add_argument('project', nargs=1, type=int, help="Project ID")

        parser.add_argument('--past-minutes', nargs='?', type=int, default=60, help="Past time in minutes to lookup")
        parser.add_argument('--battery-level', nargs='?', type=float, default=0.0, help="Include power-plugged AND users with >= battery level threshold.")
        parser.add_argument('--plugged-only', action='store_true', help="Only include power-plugged users")
        parser.add_argument('--show-details', action='store_true', help="Show details for each user's last response")

    def handle(self, *args, **options):

        # Spanish Timezone
        TZ = pytz.timezone('Europe/Madrid')

        # get arguments
        project_id = options['project'][0]
        past_minutes = options['past_minutes']
        plugged_only = options['plugged_only']
        battery_level = options['battery_level']
        show_details = options['show_details']

        # get project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise CommandError("Project with id '%d' does not exist." % options['project'][0])

        # get all relevant responses (unique per device)
        responses = self.__query_device_status_responses(project, past_minutes, plugged_only, battery_level)

        # report
        registered_devices_count = project.profiles.count()
        if registered_devices_count > 0:
            ratio = len(responses) / registered_devices_count
            ratio_str = "%.2f" % ratio
        else:
            ratio_str = "inf"
        print("Project '%s'" % project.title)
        print("Responses: %d. Currently registered: %d (ratio: %s)" % (len(responses), registered_devices_count, ratio_str))

        if show_details:
            for response in responses:
                username = response.device.profile.user.username
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

                print("\t%s - last_reponse: %s - version_code: %d - bucket: %d - power_plugged: %s - battery: %.2f - network: %s (%s)" % (username, timestamp, version_code, bucket, power_plugged, battery, type_name, subtype_name))

    def __keep_last_per_device(self, responses):

        device_responses = {}

        for response in responses:

            # get username
            username = response.device.profile.user.username

            # if device for this user does not exist
            if username not in device_responses.keys():
                device_responses[username] = response

            # OR exists but its older
            elif response.create_date > device_responses[username].create_date:
                device_responses[username] = response

        # convert into a list and return
        return list(device_responses.values())

    def __query_device_status_responses(self, project, past_minutes, power_plugged_only, battery_level_threshold):

        # get all devices registered to this project
        registered_devices = [profile.device for profile in project.profiles.all()]

        # Past X minutes
        from_date_filter = timezone.now() - timedelta(minutes=past_minutes)

        # apply filters
        responses = DeviceStatusResponse.objects.filter(
            create_date__gt=from_date_filter,
            device__in=registered_devices)

        # build query based on settings in Project
        if power_plugged_only:

            # power plugged only
            responses = responses.filter(data__battery_status__power_plugged=True)

        else:

            # power plugged OR > battery_level_threshold
            battery_level_threshold = float(project.battery_level_threshold)
            responses = responses.filter(Q(data__battery_status__power_plugged=True) | Q(data__battery_status__level__gte=battery_level_threshold))

        # only keep the last response per device
        responses = self.__keep_last_per_device(responses)

        return responses
