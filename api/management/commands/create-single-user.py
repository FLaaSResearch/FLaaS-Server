import random
import string

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a new account with random password.'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1, type=str, help="Username of the user")
        parser.add_argument('samples_index', nargs=1, type=int, help="Sample index of the user")

        # optional
        parser.add_argument('--length', nargs='?', type=int, default=10, help="Password length")

    def handle(self, *args, **options):

        username = options['username'][0]
        samples_index = options['samples_index'][0]
        length = options['length']

        # check if user with giver username exists
        if User.objects.filter(username=username).exists():
            raise CommandError("User '%s' already exists." % username)

        # generate password
        password = self.generate_password(length)

        # create user account
        user = User.objects.create_user(username=username,
                                        password=password)

        # assign dataset
        user.profile.device.samples_index = samples_index
        user.save()

        # report details
        print("Created account with the following details:")
        print("Username: %s" % username)
        print("Password: %s" % password)
        print("Samples Index: %d" % samples_index)

    def generate_password(self, length=10):
        characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(characters) for i in range(length))
        return password
