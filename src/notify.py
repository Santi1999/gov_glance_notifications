"""Firebase Cloud Messaging helpers for Gov Glance push notifications.

Backward compatible with the earlier notify.py: InitFirebaseApp,
SendNotification, SendFcmMessage, get_payload_size and adjust_body_to_fit are
all still available, and send_notification() still raises when a send fails
unless raise_on_error=False is passed.
"""
import json
import os

import firebase_admin
from firebase_admin import credentials, exceptions, messaging

CREDENTIALS_PATH = os.environ.get(
    "FIREBASE_CREDENTIALS",
    "firebase2/gov-glance-firebase-adminsdk-3osxk-6fc6be7677.json",
)
MAX_PAYLOAD_SIZE = 4096  # FCM message payload limit, in bytes
MAX_BODY_LENGTH = 230  # keeps the body readable in the notification shade
TRUNCATE_SUFFIX = "..."


class InitFirebaseApp:
    """Initialize the default Firebase app once. Safe to construct more than once."""

    def __init__(self, credentials_path=CREDENTIALS_PATH):
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(credentials_path))


def is_valid_image_url(value):
    """FCM rejects anything that isn't a real URL, including the string 'None'."""
    return isinstance(value, str) and value.startswith(("https://", "http://"))


class SendNotification:
    """Legacy sender kept unchanged for notifiers that still use it."""

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
        message = messaging.Message(
            notification=messaging.Notification(
                title=notifcation_title,
                body=body),
            data=data,
            topic=self.topic,
        )
        print(message)
        try:
            response = messaging.send(message)
            print(f"Successfully sent message: {response}")
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False


class SendFcmMessage:
    """Build and send one FCM notification to a topic or a condition.

    length_of_values is the total number of posts this notification covers.
    When it is greater than 1, the body ends with "and N more ..." text.
    """

    def __init__(
        self,
        length_of_values=1,
        notification_title=None,
        body=None,
        topic=None,
        image=None,
        data=None,
        condition=None,
        ending_note="",
    ):
        if bool(topic) == bool(condition):
            raise ValueError("Provide exactly one of topic or condition")

        self.length_of_values = max(int(length_of_values or 0), 1)
        self.notification_title = notification_title or ""
        self.topic = topic
        self.condition = condition
        self.image = image if is_valid_image_url(image) else None
        # FCM data payloads must be a flat dict of strings.
        self.data = {str(k): "" if v is None else str(v) for k, v in (data or {}).items()}
        self.ending_note = ending_note or ""
        self.body = self.build_body(body or "")

    def count_suffix(self):
        """Text appended after the body; its length is reserved before truncating."""
        extra = self.length_of_values - 1
        if extra <= 0:
            return self.ending_note
        if extra == 1:
            return " and 1 more post is available to read"
        return f" and {extra} other posts are available to read"

    def build_body(self, body):
        """Truncate the body so body + suffix never exceeds MAX_BODY_LENGTH."""
        body = " ".join(body.split())  # collapse newlines and repeated spaces
        suffix = self.count_suffix()
        limit = MAX_BODY_LENGTH - len(suffix)
        if len(body) > limit:
            body = body[: limit - len(TRUNCATE_SUFFIX)].rstrip() + TRUNCATE_SUFFIX
        return body + suffix

    def adjust_body_to_fit(self):
        """Kept for compatibility. The body is already fitted in __init__, so this does nothing."""

    def payload_size(self):
        """Approximate size of the message in bytes, for checking against MAX_PAYLOAD_SIZE."""
        notification = {"title": self.notification_title, "body": self.body}
        if self.image:
            notification["image"] = self.image
        payload = {"notification": notification, "data": self.data}
        if self.topic:
            payload["topic"] = self.topic
        if self.condition:
            payload["condition"] = self.condition
        return len(json.dumps(payload).encode("utf-8"))

    def get_payload_size(self):
        """Old name for payload_size(), kept for compatibility."""
        return self.payload_size()

    def build_message(self):
        return messaging.Message(
            notification=messaging.Notification(
                title=self.notification_title,
                body=self.body,
                image=self.image,
            ),
            data=self.data or None,
            topic=self.topic,
            condition=self.condition,
        )

    def send_notification(self, dry_run=False, raise_on_error=True):
        """Send the message. With dry_run=True, FCM validates it without delivering.

        By default a failed send raises, like the original version, so callers
        that delete rows after sending never delete rows that weren't sent.
        With raise_on_error=False it returns False instead. Returns True on success.
        """
        target = self.topic or self.condition
        try:
            response = messaging.send(self.build_message(), dry_run=dry_run)
        except (exceptions.FirebaseError, ValueError) as error:
            print(f"Failed to send to {target}: {error}")
            if raise_on_error:
                raise
            return False
        print(f"{'Validated' if dry_run else 'Sent'} to {target}: {response}")
        return True