from django.utils import timezone

from api.libs import pushwoosh_api as push
from api.models import DeviceTrainRequest, Project, Round


# return all usernames for each device.user belonging to the given project
def _get_user_ids(devices):

    user_ids = [str(device.profile.user.username) for device in devices]
    return user_ids


def send_train_request(project, devices, verbose=False):

    # check if project is started
    if project.status != Project.STATUS_CHOICES[1][0]:
        print("Project status is not 'In Progress'.")
        return

    if len(devices) == 0:
        print("No devices available.")
        return

    # get round model of current round
    round = Round.objects.get(
        project=project,
        round_number=project.current_round)

    # create DeviceTrainRequest object
    request = DeviceTrainRequest.objects.create(
        round=round)

    # now set the devices
    request.devices.set(devices)
    request.save()

    # compute training request validity
    valid_date = int((timezone.now().timestamp() + project.max_training_time * 60) * 1000)

    # build data payload
    data = {
        'type': 'train',
        'validDate': valid_date,
        'request': request.id,
        'project': project.id,
        'round': round.round_number,
        'trainingMode': round.training_mode,
    }

    # get user_ids
    user_ids = _get_user_ids(devices)

    if verbose:
        print("\tusers:" + str(user_ids))
        print("\tdata: " + str(data))

    # send push notification
    ttl = project.max_training_time
    push.send_data(user_ids, data, ttl, verbose)

    return request.id
