import os
import json

from urllib.request import urlopen, Request

PW_AUTH = os.environ['PUSHWOOSH_API_TOKEN']
PW_APPLICATION_CODE = os.environ['PUSHWOOSH_APPLICATION_CODE']


def _pw_call(method, data, verbose=False):
    url = 'https://cp.pushwoosh.com/json/1.3/' + method
    data = json.dumps({'request': data})
    req = Request(url, data.encode('UTF-8'), {'Content-Type': 'application/json'})
    try:
        f = urlopen(req)
        response = json.loads(f.read())
        f.close()

        if response['status_code'] == 200:
            verbose and print('Push sent succesfully.')
        else:
            verbose and print('Pushwoosh request' + str(data))
            verbose and print('Pushwoosh response: ' + str(response))

    except Exception as e:
        print('Error: Unable to send the Pushwoosh request. ' + str(e))


def send_data(users, data, ttl_mins, verbose=False):

    if len(users) == 0:
        print("Error: Tried to push data to an empty list of users.")
        return

    _pw_call('createMessage', {
        'auth': PW_AUTH,
        'application': PW_APPLICATION_CODE,
        'notifications': [
            {
                'send_date': 'now',
                "ignore_user_timezone": True,
                'data': data,
                'users': users,
                "ios_silent": 1,
                "android_silent": 1,
                "ios_ttl": ttl_mins * 60,
                "android_gcm_ttl": ttl_mins * 60,
            }
        ]
    }, verbose)


def send_notification(users, send_date, header, content, ttl_mins=1440, verbose=False):

    if len(users) == 0:
        print("Error: Tried to push data to an empty list of users.")
        return

    _pw_call('createMessage', {
        'auth': PW_AUTH,
        'application': PW_APPLICATION_CODE,
        'notifications': [
            {
                "send_date": send_date.strftime("%Y-%m-%d %H:%M"),
                "ignore_user_timezone": False,
                "users": users,
                "ios_ttl": ttl_mins * 60,
                "android_gcm_ttl": ttl_mins * 60,
                "android_header": header,
                "ios_title": header,
                "content": content,
                "android_priority": 0,
                "android_delivery_priority": "high",
                "android_custom_icon": "https://minoskt.github.io/download/flaas_large_icon.png",
            }
        ]
    }, verbose)
