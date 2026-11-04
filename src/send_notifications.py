"""Send pending Gov Glance push notifications, then delete the rows that were sent.

By default every message goes to the test topic (TEST_TOPIC). Use --topic to
pick a different test topic name, or --live to send to the real per-branch
topics. --dry-run has FCM validate the messages without delivering them, and
--no-delete delivers without removing the rows, so the same data can be
re-sent while testing.

The API groups pending rows by topic only, so one "Executive" group can hold
posts from several countries. Each group is split by country_schema first, and
every (topic, country) pair gets its own notification on that country's topic.
Countries the app has no notification topics for (for example Australia) are
skipped when live and their rows are kept.

    python send_notifications.py --dry-run                     # validate, test topic
    python send_notifications.py --no-delete                   # deliver to test topic, keep rows
    python send_notifications.py --topic my_test --no-delete   # deliver to a custom test topic
    python send_notifications.py --posts 1 --no-delete         # one post: tap opens the post
    python send_notifications.py --posts 2 --no-delete         # two posts: tap opens the topic page
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
PREVIEW_COUNT = 3  # posts embedded in a multi-post message; the app shows one bubble each
# Only what the app needs from each embedded post, so three fit in FCM's 4KB.
PREVIEW_FIELDS = ("title", "table_id", "table_source_name", "country_schema", "collection_name")


def to_data_value(value):
    """FCM data values must be strings; None becomes an empty string."""
    return "" if value is None else str(value)


def newest_first(results):
    """Sort rows newest first by notification id, which the database assigns in insert order."""
    def key(row):
        try:
            return int(row.get("id"))
        except (TypeError, ValueError):
            return -1
    return sorted(results, key=key, reverse=True)


def split_by_country(payload):
    """Split each topic group into one group per country_schema, newest post first."""
    groups = []
    for item in payload:
        by_schema = {}
        for result in newest_first(item.get("results") or []):
            by_schema.setdefault(result.get("country_schema"), []).append(result)
        for results in by_schema.values():
            groups.append({**item, "results": results})
    return groups


def build_message(item, push_topic):
    """Build the notification for one group's pending results, or None if it has none."""
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

    # "type" tells the app where a tap should go: "item" opens the post's
    # detail page, "topic" opens the topic's home view.
    if total == 1:
        data = {
            "type": "item",
            "topic": first.get("topic"),
            "table": first.get("table_source_name"),
            "schema": first.get("country_schema"),
            "item_id": first.get("table_id"),
        }
        return SendFcmMessage(data=data, **common)

    # Embed a preview of the first few results, dropping entries until the
    # whole message fits under FCM's payload limit.
    preview = [
        {key: to_data_value(result.get(key)) for key in PREVIEW_FIELDS}
        for result in results[:PREVIEW_COUNT]
    ]
    while True:
        data = {
            "type": "topic",
            "topic": item.get("topic"),
            "schema": first.get("country_schema"),
            "results": json.dumps(preview),
        }
        message = SendFcmMessage(data=data, **common)
        if message.payload_size() <= MAX_PAYLOAD_SIZE or not preview:
            return message
        preview.pop()


def send_notifications(groups, topic_override=None, dry_run=False):
    """Send one notification per (topic, country) group. Returns the groups sent successfully.

    With topic_override set, every message goes to that topic instead of the
    real per-branch topic.
    """
    sent = []
    for item in groups:
        results = item.get("results") or []
        if not results:
            log.info("Skipping topic %r: no results", item.get("topic"))
            continue

        schema = results[0].get("country_schema")
        real_topic = build_push_topic(item.get("topic"), schema)

        if topic_override:
            push_topic = topic_override
            log.info(
                "Sending %r (%s, %d post(s)) to %s (when live: %s)",
                item.get("topic"), schema, len(results), push_topic,
                real_topic or "skipped, no topics for this country",
            )
        elif real_topic is None:
            log.warning(
                "Skipping %d %r post(s) from %r: the app has no notification topics "
                "for that country. Rows kept.",
                len(results), item.get("topic"), schema,
            )
            continue
        else:
            push_topic = real_topic

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
    parser.add_argument(
        "--posts",
        type=int,
        default=None,
        help="only use the newest N posts per topic and country: 1 sends an item notification "
        "(opens the post), 2 or more a topic notification (opens the topic page)",
    )
    args = parser.parse_args()
    if args.posts is not None and args.posts < 1:
        parser.error("--posts must be 1 or more")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    InitFirebaseApp()
    api = RequestAPI()

    payload = api.request_notifications()
    if not isinstance(payload, list):
        log.error("Unexpected response from the notifications API: %r", payload)
        return
    if args.limit is not None:
        payload = payload[: args.limit]

    groups = split_by_country(payload)
    if not groups:
        log.info("No notifications to send")
        return

    if args.posts is not None:
        trimmed = []
        for item in groups:
            results = item["results"][: args.posts]
            if len(results) < args.posts:
                log.warning(
                    "Topic %r (%s) has only %d pending post(s); asked for %d",
                    item.get("topic"), results[0].get("country_schema"), len(results), args.posts,
                )
            trimmed.append({**item, "results": results})
        # Only the posts kept here are sent, and only those are deleted afterwards.
        groups = trimmed

    topic_override = None if args.live else args.topic
    sent = send_notifications(groups, topic_override=topic_override, dry_run=args.dry_run)

    if args.dry_run:
        log.info("Dry run: validated %d of %d message(s), nothing deleted", len(sent), len(groups))
        return
    if args.no_delete:
        log.info("Sent %d of %d message(s), rows kept (--no-delete)", len(sent), len(groups))
        return

    # Only rows from groups whose message actually sent are deleted, so a
    # failed or skipped send is retried on the next run.
    for item in sent:
        api.delete_ports_bulk(item["results"])
        log.info(
            "Deleted %d row(s) for topic %r (%s)",
            len(item["results"]), item.get("topic"), item["results"][0].get("country_schema"),
        )


if __name__ == "__main__":
    main()