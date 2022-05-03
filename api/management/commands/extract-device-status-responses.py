import os
import json
import pytz

from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.timezone import make_aware

from api.models import DeviceStatusResponse


class Command(BaseCommand):
    help = 'Extract device status responses (event only) of each user.'

    def add_arguments(self, parser):
        parser.add_argument('start', nargs=1, type=str, help="Date start.")
        parser.add_argument('end', nargs=1, type=str, help="Date end.")
        parser.add_argument('filename', nargs=1, type=str, help="Output filename (requires a .json extension)")

    def handle(self, *args, **options):

        # Spanish Timezone
        TZ = pytz.timezone('Europe/Madrid')

        # get dates and set server timezone
        from_date_filter = datetime.strptime(options['start'][0], "%Y-%m-%d")
        from_date_filter = make_aware(from_date_filter)
        to_date_filter = datetime.strptime(options['end'][0], "%Y-%m-%d")
        to_date_filter = make_aware(to_date_filter)

        # filter all relevant responses.
        # device_train_request should be null as we want to ingore reports from training tasks.
        responses = DeviceStatusResponse.objects.filter(
            create_date__gt=from_date_filter,
            create_date__lt=to_date_filter,
            device_train_request__isnull=True).order_by('-create_date').iterator()

        # init output list
        output_list = []

        # append responses (events only: timestamp and username)
        for response in responses:
            output_list.append({
                "timestamp": response.create_date.astimezone(TZ).strftime("%Y-%m-%dT%H:%M:%S"),
                "username": response.device.profile.user.username
            })

        # save output into a file
        content = ContentFile(json.dumps(output_list, indent=4))
        filename = options['filename'][0]
        default_storage.save(os.path.join("results", "responses", filename), content)
