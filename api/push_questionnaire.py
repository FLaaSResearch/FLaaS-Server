from datetime import datetime, timedelta, time

from api.models import NotificationSent, User

from django.utils import timezone
from api.libs import pushwoosh_api as push


REGISTRATION_TIME = 6  # in UTC
NOTIFICATION_TIMES = [10, 14, 18]  # local time
NOTIFICATION_MESSAGES = [
    "How was your phone performance until now?",
    "How was your phone performance until now?",
    "Please complete this quick daily survey!",
]


def tick(verbose=False):

    notification_time = time(REGISTRATION_TIME, 00, 00)
    now = timezone.now().time()

    # if time passed for the day
    if (now > notification_time):

        from_date_filter = timezone.now() - timedelta(hours=20)
        notifications = NotificationSent.objects.filter(create_date__gt=from_date_filter)

        if len(notifications) == 0:

            verbose and print("Time to register the notifications!")

            # get users
            usernames = [user.username for user in User.objects.all()]

            for i in range(len(NOTIFICATION_TIMES)):

                # create send_date (in local time) that each user will receive the notification
                send_date = datetime.now().replace(hour=NOTIFICATION_TIMES[i], minute=0, second=0, microsecond=0)

                # send notification
                push.send_notification(
                    usernames,
                    send_date,
                    NOTIFICATION_MESSAGES[i],
                    "It will take you just a minute.")

            # consider it as registered
            NotificationSent.objects.create()
