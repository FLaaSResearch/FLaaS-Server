import os

from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.db.models import JSONField

from django.db import models
from api.libs.filemanagement import filecopy
from api import server_control as sc


MODELS_PATH = 'models'
PROJECTS_PATH = 'projects'


class Project(models.Model):

    STATUS_CHOICES = (
        # value, text
        ('Stopped', 'Stopped'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    )

    MODEL_CHOICES = (
        # value, text
        ('CIFAR10_B20', 'CIFAR-10 - B20'),
    )

    DATASET_CHOICES = (
        # value, text
        ('CIFAR10', 'CIFAR-10'),
    )

    DATASET_TYPE = (
        # value, text
        ('IID', 'IID'),
        ('NonIID', 'Non-IID'),
    )

    TRAINING_MODE_TYPE = (
        # value, text
        ('BASELINE', 'Baseline'),
        ('JOINT_SAMPLES', 'Joint Samples'),
        ('JOINT_MODELS', 'Joint Models'),
    )

    create_date = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=30, unique=True)
    description = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0], help_text='Project State.')

    model = models.CharField(max_length=30, choices=MODEL_CHOICES, default=MODEL_CHOICES[0][0], help_text='Model type.')
    dataset = models.CharField(max_length=30, choices=DATASET_CHOICES, default=DATASET_CHOICES[0][0], help_text='Training dataset.')
    dataset_type = models.CharField(max_length=30, choices=DATASET_TYPE)
    training_mode = models.CharField(max_length=30, choices=TRAINING_MODE_TYPE)

    number_of_rounds = models.PositiveIntegerField(default=20, help_text='Max number of succesfull FL rounds until the project is complete.')
    number_of_apps = models.PositiveIntegerField(default=3, help_text='Number of apps per device.')
    number_of_samples = models.PositiveIntegerField(default=150, help_text='Number of samples per app.')
    number_of_epochs = models.PositiveIntegerField(default=20, help_text='Number of epochs per device.')

    # scheduler fields
    responses_ratio_threshold = models.DecimalField(default=0.80, help_text='Ratio of valid devices that needs to be fulfilled for running a trainning round.', max_digits=3, decimal_places=2)
    max_training_time = models.PositiveIntegerField(default=60, help_text='Max training time (in minutes) for a round to wait for incoming training responses.')
    valid_round_training_threshold = models.DecimalField(default=0.70, help_text='A round will only be considered as valid if the given ratio of device responses is fulfilled.', max_digits=3, decimal_places=2)
    power_plugged_only = models.BooleanField(default=True, help_text='Only allow device training when power plugged.')
    battery_level_threshold = models.DecimalField(default=0.60, help_text='Only devices greater or equal to this threshold will be considered as valid for training. (not relevant if Power Plugged Only setting is enabled)', max_digits=3, decimal_places=2)

    seed = models.PositiveIntegerField(default=42524235, null=True, blank=True, help_text='Seed to be used when training. Empty for random.')

    # read-only fields
    current_round = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


@receiver(post_save, sender=Project)
def save_project_hook(sender, instance, created, **kwargs):

    # if 'In Progress' and a round doesn't exist
    if instance.status == Project.STATUS_CHOICES[1][0] and instance.rounds.count() == 0:

        # create a Round (by copying all needed fields from Project)
        Round.objects.create(
            round_number=0,
            number_of_samples=instance.number_of_samples,
            number_of_epochs=instance.number_of_epochs,
            seed=instance.seed,
            project=instance
        )

    # NOTE: It assumes that model type never changes!
    # If we ever support more models this needs to be adapted
    if created:
        filecopy(
            os.path.join(MODELS_PATH, instance.model + '.bin'),
            os.path.join(PROJECTS_PATH, str(instance.id), '0', 'model_weights.bin'))


@receiver(post_delete, sender=Project)
def delete_project_hook(sender, instance, using, **kwargs):

    # delete all relevant files in S3
    sc.delete_project(instance)


class Round(models.Model):

    class Status(models.IntegerChoices):
        WAIT = 1, ('wait')
        TRAINING = 2, ('training')
        COMPLETE = 3, ('complete')
        INVALID = 4, ('invalid')

    create_date = models.DateTimeField(auto_now_add=True)

    # Copy of current_round when Round is created
    round_number = models.PositiveIntegerField()

    status = models.IntegerField(choices=Status.choices, default=Status.WAIT)

    start_training_date = models.DateTimeField(null=True, blank=True)
    stop_training_date = models.DateTimeField(null=True, blank=True)

    # these fields are simple copies from Project
    number_of_samples = models.PositiveIntegerField()
    number_of_epochs = models.PositiveIntegerField()
    seed = models.PositiveIntegerField()

    # each project has multiple rounds
    project = models.ForeignKey(Project, related_name='rounds', blank=True, null=True, on_delete=models.CASCADE)

    @property
    def model(self):
        return self.project.model

    @property
    def dataset(self):
        return self.project.dataset

    @property
    def dataset_type(self):
        return self.project.dataset_type

    @property
    def training_mode(self):
        return self.project.training_mode

    @property
    def number_of_apps(self):
        return self.project.number_of_apps

    # @receiver(post_save, sender=Project)
    # def create_first_round(sender, instance, created, **kwargs):
    #     if created:
    #         Round.objects.create(
    #             round_number=1,
    #             project=instance)

    # @receiver(post_save, sender=Project)
    # def save_first_round(sender, instance, **kwargs):
    #     instance.project.save()


class Profile(models.Model):
    # One-to-one with Django's User model (each user is connected with one profile)
    # Info: https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
    # Authentication will take place on the User level (not profile)
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)

    # TODO: add more profile related info in case are needed
    # ...

    # one project is assigned to multiple users (profiles)
    project = models.ForeignKey(Project, related_name='profiles', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return "%s's profile" % (self.user.username)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Device(models.Model):

    OS_CHOICES = (
        # value, text
        ('Android', 'Android'),
        ('iOS', 'iOS'),
    )

    # one device is assigned to one profile
    profile = models.OneToOneField(Profile, related_name='device', on_delete=models.CASCADE)

    # device details (will be set from client side)
    os = models.CharField(max_length=10, choices=OS_CHOICES, default=OS_CHOICES[0][0], verbose_name="OS", help_text='OS.')
    model = models.CharField(max_length=30, null=True, blank=True, help_text='Model name.')
    manufacturer = models.CharField(max_length=30, null=True, blank=True, help_text="The manufacturer of the device.")
    brand = models.CharField(max_length=30, null=True, blank=True, help_text="The consumer-visible brand.")
    build_type = models.CharField(max_length=30, null=True, blank=True, help_text="The type of build, like 'user' or 'eng' (Android only).")
    incremental = models.CharField(max_length=30, null=True, blank=True, help_text="Incremental (Android only).")
    os_version = models.CharField(max_length=10, null=True, blank=True, verbose_name="OS version", help_text="OS version.")
    security_patch = models.CharField(max_length=15, null=True, blank=True, help_text="Security Patch (Android only).")

    # dataset
    samples_index = models.PositiveIntegerField(default=0, help_text='Index of sample file to be downloaded.')
    samples_downloaded = models.BooleanField(default=False, help_text='Has the device downloaded the samples?')

    # a device can join many rounds. A round is joined by many devices (same for requested_training_rounds)
    joined_rounds = models.ManyToManyField(Round, through='JoinedRounds', related_name='joined_devices')
    requested_training_rounds = models.ManyToManyField(Round, through='RequestedTrainingRounds', related_name='requested_training_devices')

    def __str__(self):
        if self.profile is not None:
            return "%s's device" % (self.profile.user.username)


@receiver(post_save, sender=Profile)
def create_user_device(sender, instance, created, **kwargs):
    if created:
        Device.objects.create(profile=instance)


@receiver(post_save, sender=Profile)
def save_user_device(sender, instance, **kwargs):
    instance.device.save()


class JoinedRounds(models.Model):

    class Status(models.IntegerChoices):
        JOIN_ROUND = 1, ('join')
        DOWNLOAD_MODEL = 2, ('download_model')
        TRAIN = 3, ('train')
        MERGE_MODELS = 4, ('merge_models')
        SUBMIT_RESULTS = 5, ('submit_results')
        COMPLETE = 6, ('complete')

    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, default=Status.JOIN_ROUND)

    date_joined = models.DateTimeField(auto_now_add=True)
    date_last_state = models.DateTimeField(auto_now_add=True)


class RequestedTrainingRounds(models.Model):

    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)

    date_requested = models.DateTimeField(auto_now_add=True)


class DeviceTrainRequest(models.Model):

    create_date = models.DateTimeField(auto_now_add=True)

    # devices the this request was sent
    devices = models.ManyToManyField(Device, related_name='device_train_requests')

    # one Round has multiple device control requests
    round = models.OneToOneField(Round, related_name='device_train_request', on_delete=models.CASCADE)


class DeviceStatusResponse(models.Model):

    create_date = models.DateTimeField(auto_now_add=True)
    data = JSONField(default=dict)

    # one device with many responses
    device = models.ForeignKey(Device, related_name='device_status_responses', on_delete=models.CASCADE)

    # only one response
    device_train_request = models.ForeignKey(DeviceTrainRequest, related_name='device_train_responses', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return "%s: %s" % (self.device, self.create_date)


class NotificationSent(models.Model):

    create_date = models.DateTimeField(auto_now_add=True)
