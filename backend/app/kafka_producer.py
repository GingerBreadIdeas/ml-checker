#!/usr/bin/env python
from confluent_kafka import Producer

producer: Producer = None  # global singleton

def get_kafka_producer() -> Producer:
    global producer
    return producer

def init_kafka_producer():
    global producer
    producer = Producer({
        'bootstrap.servers': 'localhost:9092'
    })

def close_kafka_producer():
    global producer
    if producer is not None:
        producer.flush()
