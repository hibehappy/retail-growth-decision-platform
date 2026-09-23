# ============================================================
# Retail Growth — Kafka event producer
#
# Purpose:
# Publish synthetic purchase-like events to Kafka.
#
# Usage:
#
# python streaming/produce_events.py --mode base
#
# python streaming/produce_events.py --mode retry
# ============================================================

import argparse
import json

from confluent_kafka import Producer

from events import (
    base_events,
    retry_event,
)


BOOTSTRAP_SERVERS = "localhost:9092"

TOPIC = "retail-growth-events"


# ------------------------------------------------------------
# Delivery callback
#
# Kafka production is asynchronous.
# This callback tells us whether an event was acknowledged
# by the broker or failed.
# ------------------------------------------------------------

def delivery_report(error, message):

    if error is not None:

        print(
            f"FAILED: {error}"
        )

        return

    print(
        "DELIVERED:",
        f"partition={message.partition()}",
        f"offset={message.offset()}",
        f"key={message.key().decode('utf-8')}",
    )


def publish(events):

    producer = Producer(
        {
            "bootstrap.servers":
                BOOTSTRAP_SERVERS,
        }
    )

    for event in events:

        payload = json.dumps(
            event
        ).encode("utf-8")

        # event_id becomes the Kafka message key.
        #
        # Kafka uses the key when deciding which partition
        # should receive the event.
        producer.produce(
            topic=TOPIC,
            key=event["event_id"],
            value=payload,
            callback=delivery_report,
        )

        # Serve any completed callbacks.
        producer.poll(0)

    # Wait until all queued messages have been delivered.
    producer.flush()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=[
            "base",
            "retry",
        ],
        default="base",
    )

    args = parser.parse_args()

    if args.mode == "base":

        events = base_events()

    else:

        events = [
            retry_event()
        ]

    publish(events)

    print(
        f"Published {len(events)} event(s)."
    )