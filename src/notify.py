import firebase_admin
from firebase_admin import credentials, messaging
import json


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

    def notification_push(self, notifcation_title, body, data: dict):
        topic = self.topic

        message = messaging.Message(
            notification=messaging.Notification(
                title=notifcation_title, 
                body=body),
                data = data,
            topic=topic
        )
        print(message)
        try:
            # Send message
            response = messaging.send(message)
            print(f"Successfully sent message: {response}")
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

class SendFcmMessage:
    

    def __init__(self, length_of_values: int = 0, notification_title:str = None, body: str = None, topic: str = None, image = None, data: dict = None, condition: str = None, ending_note:str = ''): 

        '''
        We are going currently going to take a list of values since we are not using the yield keyword but once this class gets added to the scrapy project the code will be adjusted.
        '''
        self.notification_title = notification_title
        self.length_of_values = length_of_values
        self.body = body
        self.topic = topic
        self.image = image
        self.data = data if data else {}
        self.condition = condition
        # Track and adjust size
        self.MAX_PAYLOAD_SIZE = 4096 # Firebase limit
        self.TRUNCATE_SUFFIX = '...'
        self.ENDING_NOTE = ending_note
        self.MAX_BODY_LENGTH = 230 - len(self.TRUNCATE_SUFFIX) - len(self.ENDING_NOTE)
        self.adjust_body_to_fit()

    def get_payload_size(self):
        """
        Calculate the current size of the payload in bytes
        """

        payload = {
            "notification": {
                "title": self.notification_title,
                "body": self.body
            },
            "data": self.data
        }
        if self.topic:
            payload["topic"] = self.topic
        if self.image:
            payload["notification"]["image"] = self.image
        if self.condition:
            payload["condition"] = self.condition
        return len(json.dumps(payload).encode("utf-8"))

    def adjust_body_to_fit(self):
        """Ensure the body stays within Firebase’s 1000-character and 4096-byte limits."""
        # Step 1: Ensure the body doesn't exceed 1000 characters
        # if len(self.body) > self.MAX_BODY_LENGTH:
        #     self.body = self.body[:self.MAX_BODY_LENGTH - len(self.TRUNCATE_SUFFIX)] + self.TRUNCATE_SUFFIX

        # # Step 2: Ensure the total payload fits within 4096 bytes

        if len(self.body):
            if len(self.body) > self.MAX_BODY_LENGTH:

                while len(self.body) > self.MAX_BODY_LENGTH:
                    self.body = self.body[:-1]  # Trim one character at a time


                if self.body is not self.body.endswith(self.TRUNCATE_SUFFIX):
                    self.body = self.body + self.TRUNCATE_SUFFIX

                if self.length_of_values == 1:
                    self.body += self.ENDING_NOTE
                elif 2 >= self.length_of_values > 1:
                    self.body += f'.. and {self.length_of_values - 1} more post is available to read'
                else:
                    self.body += f'.. and {self.length_of_values - 1} other posts are available to read'

                
            else:
                if self.length_of_values == 1:
                    self.body += self.ENDING_NOTE
                elif 2 >= self.length_of_values > 1:
                    self.body += f'.. and {self.length_of_values - 1} more post is available to read'
                else:
                    self.body += f'.. and {self.length_of_values - 1} other posts are available to read'

                

    def send_notification(self):

        message = messaging.Message(
            notification=messaging.Notification(
                    title=self.notification_title, 
                    body=self.body ,
                    image=self.image),
            topic=self.topic,
            data=self.data,
            condition=self.condition
        )
        print(messaging.send(message))