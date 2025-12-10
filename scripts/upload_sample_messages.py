#!/usr/bin/env python3
"""
Script to upload sample messages to the ML-Checker API using the deepset/prompt-injections dataset.

Usage:
    python upload_sample_messages.py --token YOUR_PROJECT_TOKEN [--url API_URL]

Example:
    python upload_sample_messages.py --token proj_1234567890abcdef...

Note: Use a project API token (not a user JWT token). Generate one from the Settings page.
"""

import argparse
import random
import time

import pandas as pd
import requests
from datasets import load_dataset


def parse_args():
    parser = argparse.ArgumentParser(
        description="Upload sample messages to the ML-Checker API"
    )
    parser.add_argument(
        "--token", required=True, help="Project API token for authentication"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/v1",
        help="Base URL for the API",
    )
    return parser.parse_args()


def upload_message(
    api_url, token, content, is_prompt_injection, session_id="default"
):
    """Upload a single message to the API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    data = {
        "content": content,
        "is_prompt_injection": is_prompt_injection,
        "session_id": session_id,
    }

    try:
        response = requests.post(
            f"{api_url}/chat/messages", json=data, headers=headers
        )

        if response.status_code == 200:
            message = response.json()
            print(f"Created message ID: {message['id']}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False


def main():
    args = parse_args()

    print(f"Loading prompt-injections dataset from Hugging Face...")

    # Load the dataset
    try:
        dataset = load_dataset("deepset/prompt-injections")
        train_data = dataset["train"].to_pandas()
    except Exception as e:
        print(f"Error loading dataset: {e}")
        print("Falling back to pandas read_csv from parquet URL...")
        try:
            # Alternative: directly download the parquet file
            url = "https://huggingface.co/datasets/deepset/prompt-injections/resolve/main/data/train-00000-of-00001.parquet"
            train_data = pd.read_parquet(url)
        except Exception as e2:
            print(f"Failed to load dataset: {e2}")
            return

    # Verify the data has the expected columns
    if "text" not in train_data.columns or "label" not in train_data.columns:
        print(f"Dataset missing expected columns. Found: {train_data.columns}")
        return

    # Split into normal and injection messages
    normal_messages = train_data[train_data["label"] == 0]["text"].tolist()
    injection_messages = train_data[train_data["label"] == 1]["text"].tolist()

    print(
        f"Found {len(normal_messages)} normal messages and {len(injection_messages)} injection messages"
    )
    print(f"Using project API token for authentication")

    # Sample the required number of messages
    normal_sample = random.sample(
        normal_messages, min(30, len(normal_messages))
    )
    injection_sample = random.sample(
        injection_messages, min(10, len(injection_messages))
    )

    print(
        f"Will upload {len(normal_sample)} normal messages and {len(injection_sample)} prompt injection messages"
    )

    # Upload normal messages
    success_count = 0
    for i, msg in enumerate(normal_sample):
        print(f"Uploading normal message {i+1}/{len(normal_sample)}...")

        # Truncate long messages
        if len(msg) > 1000:
            msg = msg[:997] + "..."

        if upload_message(args.url, args.token, msg, False):
            success_count += 1

        # Add a small delay to avoid overwhelming the API
        time.sleep(0.2)

    print(
        f"Successfully uploaded {success_count}/{len(normal_sample)} normal messages"
    )

    # Upload injection messages
    injection_success = 0
    for i, msg in enumerate(injection_sample):
        print(f"Uploading injection message {i+1}/{len(injection_sample)}...")

        # Truncate long messages
        if len(msg) > 1000:
            msg = msg[:997] + "..."

        if upload_message(args.url, args.token, msg, True):
            injection_success += 1

        # Add a small delay to avoid overwhelming the API
        time.sleep(0.2)

    print(
        f"Successfully uploaded {injection_success}/{len(injection_sample)} injection messages"
    )
    print(
        f"Total: {success_count + injection_success}/{len(normal_sample) + len(injection_sample)} messages uploaded"
    )


if __name__ == "__main__":
    main()
