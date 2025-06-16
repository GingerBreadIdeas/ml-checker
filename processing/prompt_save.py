#!/usr/bin/env python

import json
import sys
import os
from pathlib import Path
import time
from confluent_kafka import Consumer
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# Database configuration
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'ml-checker')

print(f"Starting prompt_save script with DB configuration:")
print(f"DB_HOST: {DB_HOST}, DB_PORT: {DB_PORT}, DB_NAME: {DB_NAME}")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Use the newer recommended approach to avoid the warning
Base = declarative_base()

# Define Prompt model directly in this file
class Prompt(Base):
    __tablename__ = "prompt_check"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    created_at = Column(DateTime(timezone=True))
    content = Column(JSONB)
    check_results = Column(JSONB, nullable=True)
    checked = Column(Boolean, default=False)


def save_prompt_results(prompt_data, results_data):
    db = SessionLocal()
    try:
        # Get the prompt by ID from the original data
        prompt_id = prompt_data.get('id')
        if not prompt_id:
            print("Error: No prompt ID found in data")
            return
            
        # Query by ID explicitly
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if prompt:
            prompt.check_results = results_data
            prompt.checked = True
            db.commit()
            print(f"Updated prompt with id: {prompt_id}")
        else:
            print(f"No prompt found with id: {prompt_id}")
        
    except Exception as e:
        db.rollback()
        print(f"Error saving prompt results: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    # Kafka configuration
    kafka_host = os.environ.get('KAFKA_HOST', 'localhost')
    kafka_port = os.environ.get('KAFKA_PORT', '9092')
    bootstrap_servers = f"{kafka_host}:{kafka_port}"
    
    print(f"All environment variables:")
    for key, value in sorted(os.environ.items()):
        print(f"  {key}: {value}")
    
    print(f"Connecting to Kafka at {bootstrap_servers}")
    print(f"Using database at {DATABASE_URL}")
    
    # Attempt to resolve Kafka hostname for debugging
    try:
        import socket
        print(f"Attempting to resolve {kafka_host}...")
        ip_address = socket.gethostbyname(kafka_host)
        print(f"Resolved {kafka_host} to {ip_address}")
    except Exception as e:
        print(f"Unable to resolve {kafka_host}: {e}")
    
    # Create Kafka consumer with improved settings for Docker networking
    consumer_config = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': 'prompt-save-consumer',
        'auto.offset.reset': 'earliest',
        'socket.timeout.ms': 30000,  # 30 second timeout
        'session.timeout.ms': 45000,  # 45 second timeout
        'request.timeout.ms': 60000,  # 60 second timeout
        'max.poll.interval.ms': 300000,  # 5 minutes
        'heartbeat.interval.ms': 15000,  # 15 seconds
        'reconnect.backoff.ms': 1000,  # 1 second initial backoff
        'reconnect.backoff.max.ms': 10000,  # 10 seconds maximum backoff
        'retry.backoff.ms': 500  # 500ms retry backoff
    }
    print(f"Consumer config: {consumer_config}")
    
    # Retry loop for creating consumer
    max_retries = 5
    retry_delay = 10  # seconds
    for attempt in range(max_retries):
        try:
            print(f"Creating Kafka consumer (attempt {attempt+1}/{max_retries})...")
            consumer = Consumer(consumer_config)
            print("Consumer created successfully")
            break
        except Exception as e:
            print(f"Error creating consumer: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                import time
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Max retries reached. Exiting.")
                sys.exit(1)

    # Subscribe to the save_prompt_check topic
    consumer.subscribe(['save_prompt_check'])
    print("Subscribed to topic: save_prompt_check")
    print("Waiting for messages...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Error:", msg.error())
            else:
                try:
                    # Parse the message
                    data = json.loads(msg.value().decode('utf-8'))
                    
                    # Skip initialization messages
                    if data.get("init", False):
                        continue
                        
                    print("Received results to save")
                    
                    # Extract original data and results
                    original_data = data.get("original_data")
                    results = data.get("results")
                    
                    if original_data and results:
                        # Convert results string to JSON if needed
                        try:
                            results_data = json.loads(results)
                        except json.JSONDecodeError:
                            # If it's not valid JSON, store as a string in a JSON object
                            results_data = {"raw_results": results}
                            
                        # Save to database
                        save_prompt_results(original_data, results_data)
                    else:
                        print("Missing data in message")
                        
                except json.JSONDecodeError:
                    print(f"Received non-JSON message, ignoring")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        consumer.close()
        print("Consumer closed")
