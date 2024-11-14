import firebase_admin
from firebase_admin import credentials, messaging


class InitFirebaseApp:
    def __init__(self):
        cred = credentials.Certificate(
            f"firebase2/gov-glance-firebase-adminsdk-3osxk-6fc6be7677.json")
        firebase_admin.initialize_app(cred)

class SendNotification:

    def __init__(self, topic: str):
        self.topic = topic

    def message(self, list_items, recent_value):

        if len(list_items) == 1:
            title = recent_value['title'].split("'")[0].upper() + "'" + recent_value['title'].split("'")[1].lower()
            notification_message = f'{title} is available to read'
        else:
            notification_message = f'{recent_value[:80]}... and {len(list_items)-1} more are available to read!'
        return notification_message

    def notification_push(self, notifcation_title, body, data={}):
        topic = self.topic

        message = messaging.Message(
            notification=messaging.Notification(
                title=notifcation_title, 
                body=body),
                data = data,
            topic=topic
        )
        # print(message)
        messaging.send(message)