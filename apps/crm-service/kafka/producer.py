from confluent_kafka import Producer
import json
import os

producer = Producer({
    "bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
})


def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def publish_event(topic: str, data: dict):
    producer.produce(
        topic=topic,
        value=json.dumps(data),
        callback=delivery_report
    )
    producer.poll(0)
    producer.flush()