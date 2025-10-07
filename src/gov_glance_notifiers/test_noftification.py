import firebase_admin
from firebase_admin import credentials, messaging,  _messaging_utils, _messaging_encoder
from datetime import datetime, timedelta
startTime = datetime.now()

def notification_push(title, body):
    cred = credentials.Certificate(
        "/Users/santiagosaldivar/Coding/gov_glance/firebase2/gov-glance-firebase-adminsdk-3osxk-6fc6be7677.json")
    firebase_admin.initialize_app(cred)

    topic = "testTopic" # Make sure to use this topic whenever we are testing so other people do not get the notifiacation we are using

    message = messaging.Message(
        notification=messaging.Notification(
            title=title, body=body),
        data={'table': 'congressional_bills',
              'id': '271002'},
        topic=topic,
    )
    res = messaging.send(message)
    print(res)


notification_push(f'Testing Time:{startTime}', 'Testing allUSNews')
# import firebase_admin
# from firebase_admin import credentials, messaging
# firebase_cred = credentials.Certificate(
#     "/Users/santiagosaldivar/Coding/gov_glance/firebase2/gov-glance-firebase-adminsdk-3osxk-6fc6be7677.json")
# firebase_app = firebase_admin.initialize_app(firebase_cred)
# def push_notification():
#     title = "Your title"
#     message = "Your message"
#     ntf_data = {"key": "value"}
#     fcm_token = "your_fcm_token"
#     topic = "your_topic"

#     # apns
#     alert = ApsAlert(title = title, body = message)
#     aps = messaging.Aps(alert = alert, sound = "default")
#     payload = messaging.APNSPayload(aps)

#     # message
#     msg = messaging.Message(
#         notification = messaging.Notification(
#             title = title,
#             body = message
#         ),
#         data = ntf_data,
#         token = fcm_token,
#         topic = topic,
#         apns = messaging.APNSConfig(payload = payload)
#     )

#     # send
#     res = messaging.send(msg)
#     print(res)