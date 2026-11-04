"""Send pending Gov Glance push notifications, then delete the rows that were sent.

By default every message goes to the test topic (TEST_TOPIC). Use --topic to
pick a different test topic name, or --live to send to the real per-branch
topics. --dry-run has FCM validate the messages without delivering them, and
--no-delete delivers without removing the rows, so the same data can be
re-sent while testing.

    python send_notifications.py --dry-run                     # validate, test topic
    python send_notifications.py --no-delete                   # deliver to test topic, keep rows
    python send_notifications.py --topic my_test --no-delete   # deliver to a custom test topic
    python send_notifications.py --live --dry-run              # validate real topic names
    python send_notifications.py --live                        # production
"""
import argparse
import json
import logging

from notify import MAX_PAYLOAD_SIZE, InitFirebaseApp, SendFcmMessage
from push_topics import build_push_topic
from response import RequestAPI

log = logging.getLogger(__name__)

# Must match TEST_TOPIC_OVERRIDE in the app's notificationTopics.js while testing.
TEST_TOPIC = "3.6.2_test"
PREVIEW_COUNT = 2  # results embedded in a multi-item message's data payload


def to_data_value(value):
    """FCM data values must be strings; None becomes an empty string."""
    return "" if value is None else str(value)


def build_message(item, push_topic):
    """Build the notification for one topic's pending results, or None if it has none."""
    results = item.get("results") or []
    if not results:
        return None

    first = results[0]
    total = len(results)
    common = {
        "length_of_values": total,
        "notification_title": first.get("collection_name") or "Gov Glance",
        "body": first.get("title") or "",
        "image": first.get("image_url"),
        "topic": push_topic,
    }

    if total == 1:
        data = {
            "topic": first.get("topic"),
            "table": first.get("table_source_name"),
            "schema": first.get("country_schema"),
            "item_id": first.get("table_id"),
        }
        return SendFcmMessage(data=data, **common)

    # Embed a preview of the first few results, dropping entries until the
    # whole message fits under FCM's payload limit.
    preview = [
        {key: to_data_value(value) for key, value in result.items()}
        for result in results[:PREVIEW_COUNT]
    ]
    while True:
        data = {"topic": item.get("topic"), "results": json.dumps(preview)}
        message = SendFcmMessage(data=data, **common)
        if message.payload_size() <= MAX_PAYLOAD_SIZE or not preview:
            return message
        preview.pop()


def send_notifications(payload, topic_override=None, dry_run=False):
    """Send one notification per topic. Returns the items that were sent successfully.

    With topic_override set, every message goes to that topic instead of the
    real per-branch topic.
    """
    sent = []
    for item in payload:
        results = item.get("results") or []
        if not results:
            log.info("Skipping topic %r: no results", item.get("topic"))
            continue

        real_topic = build_push_topic(item.get("topic"), results[0].get("country_schema"))
        push_topic = topic_override or real_topic
        if topic_override:
            log.info("Sending %r to %s (would go to %s when live)", item.get("topic"), push_topic, real_topic)

        message = build_message(item, push_topic)
        if message.send_notification(dry_run=dry_run, raise_on_error=False):
            sent.append(item)
    return sent


def main():
    parser = argparse.ArgumentParser(description="Send pending Gov Glance push notifications.")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--topic", default=TEST_TOPIC, help=f"test topic to send to (default: {TEST_TOPIC})")
    target.add_argument("--live", action="store_true", help="send to the real per-branch topics")
    parser.add_argument("--dry-run", action="store_true", help="validate with FCM without delivering or deleting")
    parser.add_argument("--no-delete", action="store_true", help="deliver but keep the rows, so they can be re-sent")
    parser.add_argument("--limit", type=int, default=None, help="only process the first N topics")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    InitFirebaseApp()
    api = RequestAPI()

    payload = api.request_notifications() or []
    if args.limit is not None:
        payload = payload[: args.limit]
    if not payload:
        log.info("No notifications to send")
        return

    topic_override = None if args.live else args.topic
    sent = send_notifications(payload, topic_override=topic_override, dry_run=args.dry_run)

    if args.dry_run:
        log.info("Dry run: validated %d of %d message(s), nothing deleted", len(sent), len(payload))
        return
    if args.no_delete:
        log.info("Sent %d of %d message(s), rows kept (--no-delete)", len(sent), len(payload))
        return

    # Only rows from topics whose message actually sent are deleted, so a
    # failed send is retried on the next run.
    for item in sent:
        api.delete_ports_bulk(item["results"])
        log.info("Deleted %d row(s) for topic %r", len(item["results"]), item.get("topic"))


if __name__ == "__main__":
    main()