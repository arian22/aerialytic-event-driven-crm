from django.http import JsonResponse
from django.db import connection
from confluent_kafka import Producer
import os


def health(request):
    # Check DB
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"

    # Check Kafka
    try:
        Producer({"bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS")})
        kafka_status = "ok"
    except Exception:
        kafka_status = "error"

    status = "ok" if db_status == "ok" and kafka_status == "ok" else "error"

    return JsonResponse({
        "status": status,
        "database": db_status,
        "kafka": kafka_status,
    })