#!/usr/bin/env python
import os
import logging
import time
from typing import Optional
from confluent_kafka import Producer
from confluent_kafka.cimpl import KafkaException

logger = logging.getLogger(__name__)

producer: Optional[Producer] = None  # global singleton
kafka_connection_last_call = 0.0


def get_kafka_producer() -> Optional[Producer]:
    global producer
    if producer is None:
        if (time.time() - kafka_connection_last_call) > 15:
            init_kafka_producer()
    return producer


def init_kafka_producer() -> None:
    """Initialize the Kafka producer with error handling"""
    global producer, kafka_connection_last_call

    try:
        # Check if we're running in Docker
        kafka_connection_last_call = time.time()
        kafka_host = os.environ.get("KAFKA_HOST", "localhost")
        kafka_port = os.environ.get("KAFKA_PORT", "9092")
        bootstrap_servers = f"{kafka_host}:{kafka_port}"

        logger.info(f"Attempting to connect to Kafka at {bootstrap_servers}")

        # Create producer with a short connection timeout
        producer = Producer(
            {
                "bootstrap.servers": bootstrap_servers,
                "socket.timeout.ms": 5000,  # 5 second timeout
                "message.timeout.ms": 5000,  # 5 second timeout
            }
        )

        # Try to list topics as a connectivity test
        producer.list_topics(timeout=5.0)

        logger.info("Successfully connected to Kafka")
    except KafkaException as e:
        logger.warning(f"Failed to connect to Kafka: {e}")
        producer = None
    except Exception as e:
        logger.exception(f"Unexpected error connecting to Kafka: {e}")
        producer = None


def close_kafka_producer():
    """Safely close the Kafka producer if it exists"""
    global producer
    if producer is not None:
        try:
            producer.flush()
            logger.info("Kafka producer flushed successfully")
        except Exception as e:
            logger.warning(f"Error flushing Kafka producer: {e}")
        producer = None
