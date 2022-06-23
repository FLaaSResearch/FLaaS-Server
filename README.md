# FLaaS-Server

This is the centralized service component of our FLaaS system. It is designed to be hosted under [heroku](https://heroku.com/) cloud platform, but it should be easily adaptable to other platforms. It provides a REST API for incoming communication from mobile devices. For outgoing communications it relies on [Pushwoosh](https://www.pushwoosh.com/) push notification service (provided for free if requested as a [heroku add-on](https://elements.heroku.com/addons/pushwoosh)). It also uses the free
[Heroku Scheduler addon](https://elements.heroku.com/addons/scheduler) for scheduling actions on 10 mins intervals. Finally, it uses Amazon's S3 for storing the model parameters, performance metrics and website's static files. All client devices are authenticated using Java Web Token (JWT).

For more information about our system, please read the following publications:
- [FLaaS: Enabling Practical Federated Learning on Mobile Environments](http://arxiv.org/abs/2206.10963)
- [FLaaS: Federated Learning as a Service](https://arxiv.org/abs/2011.09359)
- [Demo: FLaaS - Practical Federated Learning as a Service for Mobile Applications](https://dl.acm.org/doi/pdf/10.1145/3508396.3517074)


## Overview of the REST API

- `/api/get-samples/<:dataset_type>/<:app>/` - Get samples dedicated for specific application and dataset 
- `/api/project/` - List of projects (GET, POST)
- `/api/project/:project_id/` - Details of a project with ID (GET, PUT, DELETE)
- `/api/project/:project_id/get-model/<:round>/` - Download model from project ID and for a given FL round (GET)
- `/api/project/:project_id/join-round/<:round>/` - Join project with ID and specific FL round
- `/api/report-availability` - Report Device Availability for project with ID (POST)
- `/api/project/:project_id/submit-results/:round/:filename` - Submit ML evaluation results for project with ID and FL round (POST)
- `/api/project/:project_id/submit-model/:round/:filename` - Submit local ML model for project with ID and FL round (POST)
- `/api/token` - Obtain authentication token (for new or rejoining users) (POST)
- `/api/token/refresh` - Refresh authentication token (for existing users) (POST)


## Configuration

- Create two Amazon S3 storages for storing the model data and static files.

- Create a new heroku app with the following add-ons:
  * Heroku Postgres (or, optionally, use an external PostgreSQL server)
  * Pushwoosh
  * Heroku Scheduler

- Configure the following environmental parameters:
  * AWS_ACCESS_KEY_ID
  * AWS_REGION
  * AWS_S3_BUCKET_NAME
  * AWS_S3_BUCKET_NAME_STATIC
  * AWS_SECRET_ACCESS_KEY
  * PUSHWOOSH_API_TOKEN
  * PUSHWOOSH_APPLICATION_CODE

- Push the repository into Heroku.

- Configure Heroku Scheduler with the following command: `python manage.py tick`.


You should be now able to access and configure the admin interface through `<host>/admin` url.


## Server commands

We extended Django's `manage.py` commands to provide server control functionality. The following is a list of the supported commands:

```
python manage.py -h

Type 'manage.py help <subcommand>' for help on a specific subcommand.

Available subcommands:

[api]
    assign
    countresponses
    create-single-user
    createusers
    extract-device-status-responses
    extract-projects-start
    extract-train-responses
    joinedrounds
    performance
    performance_multirounds
    projectresponses
    responses-per-user
    roundstats
    tick
```

In case of heroku instance, use `heroku run` as a prefix in the following commands (or `heroku run bash` to get access to a bash terminal).

### Create user accounts with random passwords.

Command:
`python manage.py createusers 5 --prefix test_user`

Output:
```
username, password, samples_index
test_user1, FUA3ByyLAP, 0
test_user2, M5UJfEjit4, 1
test_user3, uxOlcxrHZi, 2
test_user4, nVJYSxsWEq, 3
test_user5, M5peA7ZzHc, 4
```

Details:
```
Create users accounts with random passwords.

positional arguments:
  accounts              Number of accounts

optional arguments:
  -h, --help            show this help message and exit
  --prefix [PREFIX]     Prefix that will be used in the usernames
  --length [LENGTH]     Password length
  --samples-index-start [SAMPLES_INDEX_START]
                        Sample index start that will increment per user
```


### Assign users to a project

Command:
`python manage.py assign 1 --prefix test_user`

Output:
```
5 user(s) assigned succesfully to project 'Project 1'
```

Details:
```
Query users using a prefix and assign them to a particular project.

positional arguments:
  project               Project ID

optional arguments:
  -h, --help            show this help message and exit
  --prefix [PREFIX]     Prefix of users to be assigned to the given project.
```


### Joined rounds per user

Command:
`python manage.py joinedrounds 1`

Output:
```
username, joined_rounds
test_user1, 16
test_user2, 12
test_user3, 15
```

Details:
```
Report number of joined rounds per user.

positional arguments:
  project               Project ID

optional arguments:
  -h, --help            show this help message and exit
```


### Round performance

Command:
`python manage.py performance 1 --round 1`

Output:
```
Project: Test Baseline IID
Rounds completed: 18/20 (plus 0 invalid)
Round 1 Test Accuracy: TBD
Round 1 Loss: 0.31 (0.01)
```

Details:
```
Report round performance of a project. If a round is not specified, the last one will be used.

positional arguments:
  project               Project ID

optional arguments:
  -h, --help            show this help message and exit
  --round [ROUND]       Round to be evaluated. If not defined, last completed round will be used.
```


### Project responses

Command:
`python manage.py projectresponses 1 --show-details`

Output:
```
Project responses: 4/4 (ratio: 1.00)
    test_user1 - last_reponse: 05/11/2021 16:25:14.761 - version_code: 12 - bucket: 30 - power_plugged: True - battery: 1.00
    test_user2 - last_reponse: 05/11/2021 16:24:55.484 - version_code: 12 - bucket: 30 - power_plugged: True - battery: 1.00
    test_user3 - last_reponse: 05/11/2021 16:24:58.886 - version_code: 12 - bucket: 40 - power_plugged: True - battery: 1.00
    test_user4 - last_reponse: 05/11/2021 16:28:07.406 - version_code: 12 - bucket: 10 - power_plugged: True - battery: 1.00
```

Details:
```
Query and report device responses for users registered to a project.

positional arguments:
  project               Project ID

optional arguments:
  -h, --help            show this help message and exit
  --past-minutes [PAST_MINUTES]
                        Past time in minutes to lookup
  --battery-level [BATTERY_LEVEL]
                        Include power-plugged AND users with >= battery level threshold.
  --plugged-only        Only include power-plugged users
  --show-details        Show details for each user's last response
```


### Responses per user

Command:
`python manage.py responses-per-user`

Output:
```
Filtered Device Status Responses of user 'test_user1':
    05/11/2021 14:47:47.172 - version_code: 12 - bucket: 30 - power_plugged: False - battery: 1.00
    05/11/2021 14:44:04.430 - version_code: 12 - bucket: 30 - power_plugged: True - battery: 1.00
    05/11/2021 14:35:58.184 - version_code: 12 - bucket: 30 - power_plugged: True - battery: 1.00

Filtered Device Status Responses of user 'test_user2':
    05/11/2021 14:43:46.010 - version_code: 12 - bucket: 30 - power_plugged: True - battery: 1.00
    05/11/2021 14:35:40.389 - version_code: 12 - bucket: 10 - power_plugged: True - battery: 1.00

Filtered Device Status Responses of user 'test_user3':
    05/11/2021 14:55:02.405 - version_code: 12 - bucket: 30 - power_plugged: True - battery: 1.00
    05/11/2021 14:49:23.924 - version_code: 12 - bucket: 10 - power_plugged: True - battery: 1.00
    05/11/2021 14:43:49.177 - version_code: 12 - bucket: 10 - power_plugged: True - battery: 1.00
    05/11/2021 14:35:42.836 - version_code: 12 - bucket: 10 - power_plugged: True - battery: 1.00

Filtered Device Status Responses of user 'test_user4':
    05/11/2021 15:12:06.894 - version_code: 12 - bucket: 10 - power_plugged: True - battery: 1.00
    05/11/2021 15:03:10.347 - version_code: 12 - bucket: 10 - power_plugged: True - battery: 1.00
    05/11/2021 14:48:09.845 - version_code: 12 - bucket: 10 - power_plugged: True - battery: 1.00
```

Details:
```
Report device status responses per user.

positional arguments:
  usernames             Usernames to report. If not specified, all registerd users will be reported.

optional arguments:
  -h, --help            show this help message and exit
  --past-minutes [PAST_MINUTES]
                        Past time in minutes to lookup
  --battery-level [BATTERY_LEVEL]
                        Include power-plugged AND users with >= battery level threshold.
  --plugged-only        Only include power-plugged users
```


### Round statistics

Command:
`python manage.py roundstats 1`

Output:
```
round, status, joined_devices_ratio, usernames
0, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
1, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
2, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
3, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
4, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
5, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
6, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
7, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
8, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
9, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
10, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
11, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
12, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
13, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
14, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
15, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
16, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
17, complete, 0.75, ['test_user2', 'test_user3', 'test_user1']
18, complete, 1.00, ['test_user2', 'test_user4', 'test_user3', 'test_user1']
19, training, 1.00, ['test_user2', 'test_user4', 'test_user3', 'test_user1']
```

Details:
```
Report joined users per round.

positional arguments:
  project               Project ID

optional arguments:
  -h, --help            show this help message and exit
```
