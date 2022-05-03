import random
import string

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create users accounts with random passwords.'

    def add_arguments(self, parser):
        parser.add_argument('accounts', nargs=1, type=int, help="Number of accounts")

        # optional
        parser.add_argument('--prefix', nargs='?', type=str, default='user', help="Prefix that will be used in the usernames")
        parser.add_argument('--length', nargs='?', type=int, default=10, help="Password length")
        parser.add_argument('--samples-index-start', nargs='?', type=int, default=0, help="Sample index start that will increment per user")

    def handle(self, *args, **options):

        print("username, password, samples_index")
        for i in range(options['accounts'][0]):

            username = "%s%d" % (options['prefix'], i + 1)

            # check if user with giver username exists
            if User.objects.filter(username=username).exists():
                raise CommandError("User '%s' already exists." % username)

            # generate password
            length = options['length']
            password = self.generate_password(length)

            # create user account
            user = User.objects.create_user(username=username,
                                            password=password)

            # assign dataset
            samples_index = options['samples_index_start'] + i
            user.profile.device.samples_index = samples_index
            user.save()

            # report details
            print("%s, %s, %d" % (username, password, samples_index))

    def generate_password(self, length=10):
        characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(characters) for i in range(length))
        return password
