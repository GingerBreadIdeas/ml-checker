import json
import os

import torch
from confluent_kafka import Consumer, Producer
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
)

from runner import work


def send_results_to_kafka(producer, jsonl_filepath, original_data):
    """Send JSONL file contents and original data to Kafka"""
    # Read the JSONL file
    try:
        with open(jsonl_filepath, "r") as f:
            jsonl_contents = f.read()

        # Create the message with both results and original data
        message = {"original_data": original_data, "results": jsonl_contents}

        # Send to Kafka
        print(f"Sending results to save_prompt_check topic")
        producer.produce(
            "save_prompt_check",
            key=None,
            value=json.dumps(message).encode("utf-8"),
        )
        producer.flush()
        print("Results sent successfully")
    except Exception as e:
        print(f"Error sending results to Kafka: {e}")


def process_prompt_check(msg):
    data = json.loads(msg.value().decode("utf-8"))
    if not data.get("init", False):
        print("Received JSON:", data)
        prompt_check_data = data["prompt_check_data"]
        jsonl_filepath = work(prompt_check_data)
        if os.path.exists(jsonl_filepath):
            send_results_to_kafka(producer, jsonl_filepath, data)
        else:
            print(f"Warning: Result file {jsonl_filepath} not found")


def upload_metrics(msg: dict, metrics: dict):
    try:
        message = {
            "id": msg["id"],
            "metrics": metrics,
            "options": msg["options"],
        }
        print(f"Sending results to save_message_metrics")
        producer.produce(
            "save_message_metrics",
            key=None,
            value=json.dumps(message).encode("utf-8"),
        )
        producer.flush()
        print("Results sent successfully")
    except Exception as e:
        print(f"Error sending results to Kafka: {e}")


def calculate_metrics(message) -> dict:
    """
     Respones:
    {'label': 'INJECTION', 'score': 0.9999992847442627}
    """

    tokenizer = AutoTokenizer.from_pretrained(
        "ProtectAI/deberta-v3-base-prompt-injection"
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        "ProtectAI/deberta-v3-base-prompt-injection"
    )

    classifier = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        truncation=True,
        max_length=512,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    )
    result = classifier(message)
    return result[0]


def process_compute_message_metrics(msg):
    metrics = calculate_metrics(msg.content)
    upload_metrics(msg, metrics)


if __name__ == "__main__":
    # Get Kafka connection details from environment or use defaults
    kafka_host = os.environ.get("KAFKA_HOST", "localhost")
    kafka_port = os.environ.get("KAFKA_PORT", "9092")
    bootstrap_servers = f"{kafka_host}:{kafka_port}"

    print(f"Connecting to Kafka at {bootstrap_servers}")

    # Create a Kafka producer
    producer = Producer({"bootstrap.servers": bootstrap_servers})

    # Create the topics we need
    producer.produce(
        "prompt_check",
        key=None,
        value=json.dumps({"init": True}).encode("utf-8"),
    )
    producer.produce(
        "save_prompt_check",
        key=None,
        value=json.dumps({"init": True}).encode("utf-8"),
    )
    producer.produce(
        "save_message_metrics",
        key=None,
        value=json.dumps({"init": True}).encode("utf-8"),
    )
    producer.flush(5)

    # Now set up the consumer
    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap_servers,
            "group.id": "json-consumer",
            "auto.offset.reset": "earliest",
        }
    )

    consumer.subscribe(["prompt_check"])
    print("Subscribed to topic: prompt_check")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Error:", msg.error())
            else:
                match msg.topic():
                    case "prompt_check":
                        process_prompt_check(msg)
                    case "compute_message_metrics":
                        process_compute_message_metrics(msg)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
