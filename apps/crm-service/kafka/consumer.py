import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

import django
from confluent_kafka import Consumer
import time
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from leads.models import Lead

bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")

consumer = Consumer({
    "bootstrap.servers": bootstrap_servers,
    "group.id": "crm-group",
    "auto.offset.reset": "earliest",
})

consumer.subscribe(["lead.created"])


while True:
    time.sleep(1)
    msg = consumer.poll(3.0)

    if msg is None:
        print("No message yet")
        continue

    if msg.error():
        print("Consumer error:", msg.error())
        continue

    print("Message received!")
    data = json.loads(msg.value().decode("utf-8"))
    print("Received event:", data)

    lead_id = data.get("lead_id")

    try:
        lead = Lead.objects.get(id=lead_id, status="NEW")
        if lead.status == "QUALIFIED":
            print("Lead already qualified. Skipping.")
            continue

        lead.status = "QUALIFIED"
        lead.save()
        print(f"Lead {lead_id} updated to QUALIFIED")
    except Lead.DoesNotExist:
        print("Lead not found:", lead_id)