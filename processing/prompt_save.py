#!/usr/bin/env python

import json
import sys
import os
from pathlib import Path
from confluent_kafka import Consumer
from sqlalchemy import create_engine, Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB

# Database configuration
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'mlechker')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Define a simplified Prompt model without foreign keys
class Prompt(Base):
    __tablename__ = "prompt_check"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # Removed foreign key constraint
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
    
    print(f"Connecting to Kafka at {bootstrap_servers}")
    print(f"Using database at {DATABASE_URL}")
    
    # Create Kafka consumer
    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': 'prompt-save-consumer',
        'auto.offset.reset': 'earliest'
    })

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