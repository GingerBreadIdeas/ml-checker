#!/usr/bin/env python

import asyncio
import importlib
import json
import os
from typing import List, Union, tuple

import garak.cli
import llm_caller
import ollama
import torch
from garak import _config
from garak.generators.base import Generator
from loguru import logger
from taskiq_pg.asyncpg import AsyncpgBroker
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
)
from sklearn.manifold import TSNE
import numpy as np

DB_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ml-checker"
)
broker = AsyncpgBroker(
    dsn=DB_URL,
)


from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Use the newer recommended approach to avoid the warning
Base = declarative_base()
JSONPortable = JSON().with_variant(JSONB, "postgresql")


# Define Prompt model directly in this file
class Prompt(Base):
    __tablename__ = "prompt_check"

    id = Column(Integer, primary_key=True, index=True)
    # ForeignKey omitted because we don't load the projects table metadata here
    project_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content = Column(JSONPortable)
    check_results = Column(JSONPortable, nullable=True)
    checked = Column(Boolean, default=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=True)
    project_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    is_prompt_injection = Column(Boolean, default=False)
    metrics = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def prepare_function(data):
    ollama.create(
        model="tested", from_=data["model_id"], system=data["prompt"]
    )
    from ollama import ChatResponse, chat

    def speak(x):
        response: ChatResponse = chat(
            model="tested",
            messages=[
                {
                    "role": "user",
                    "content": f"{x}",
                },
            ],
        )
        result = [response.message.content]
        logger.info(f"Input: {x}")
        logger.info(f"Chat response: {result}")
        print(result)
        return result

    return speak


def work(data):
    source_data = data.copy()
    speak_func = prepare_function(data)
    llm_caller.speak = speak_func
    probes = ""
    probe_list = [
        # "encoding.InjectBase32",
        # "promptinject.HijackHateHumansMini",
        source_data["probe"]
    ]
    for probe in probe_list:
        probes += f" --probes {probe}"
    command = f"""--model_type function --model_name llm_caller#speak
    --config garak_config.yaml -P probes.json --generations 1 {probes}
    """
    logger.debug(f"Running command: {command}")
    garak.cli.main(command.split())
    return (
        "/home/mwm/repositories/GBI/ml-checker/runner/run_output.report.jsonl"
    )


def save_prompt_results(prompt_id, results_data):
    db = SessionLocal()
    try:
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
        logger.debug("saved prompt correctly")
        db.close()


def calculate_metrics(message) -> dict:
    """
     Responses:
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


def save_message_metrics(data):
    db = SessionLocal()
    try:
        message_id = data.get("id")
        metrics = data.get("metrics")
        options = data.get("options")
        if not message_id:
            print("Error: No message ID found in data")
            return

        # Query by ID explicitly
        message = (
            db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        )
        if message:
            message.metrics = {"metrics": metrics, "options": options}
            db.commit()
            print(f"Updated message with id: {message_id}")
        else:
            print(f"No message found with id: {message_id}")

    except Exception as e:
        db.rollback()
        print(f"Error saving message results: {e}")
    finally:
        db.close()


@broker.task(task_name="runner:process_prompt_check", max_retries=0)
async def process_prompt_check(
    prompt_id: int,
    model_supplier: str,
    model_id: str,
    prompt_text: str,
    probe: str,
) -> None:
    """
    Replaces Kafka topic: prompt_check
    Step 1 of 2-step workflow
    """

    logger.debug("running prompt job")
    # Run Garak scan (returns JSONL filepath)
    prompt_check_data = {
        "model_supplier": model_supplier,
        "model_id": model_id,
        "prompt": prompt_text,
        "probe": probe,
    }
    jsonl_filepath = work(prompt_check_data)

    # Read results file and parse JSONL
    results_list = []
    with open(jsonl_filepath, "r") as f:
        for line in f:
            if line.strip():
                results_list.append(json.loads(line))

    save_prompt_results(
        prompt_id=prompt_id, results_data={"results": results_list}
    )


@broker.task(task_name="runner:process_message_metrics", max_retries=0)
async def process_message_metrics(
    message_id: int, content: str, options: dict
) -> None:
    """
    Replaces Kafka topic: compute_message_metrics
    Step 1 of 2-step workflow
    """
    # Run ML inference
    metrics = calculate_metrics(content)

    message = {
        "id": message_id,
        "metrics": metrics,
        "options": options,
    }
    save_message_metrics(message)



@async_shared_broker.task(task_name="runner:create_embeddings")
def create_embeddings(
    texts: List[str],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> np.ndarray:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    embeddings = []
    batch_size = 32

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]

        # Tokenize batch
        encoded_inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(device)

        # Compute token embeddings
        with torch.no_grad():
            model_output = model(**encoded_inputs)

        # Use mean pooling to get sentence embeddings
        attention_mask = encoded_inputs["attention_mask"]
        token_embeddings = model_output.last_hidden_state

        # Mask the padding tokens and compute mean of token embeddings
        input_mask_expanded = (
            attention_mask.unsqueeze(-1)
            .expand(token_embeddings.size())
            .float()
        )
        sentence_embeddings = torch.sum(
            token_embeddings * input_mask_expanded, 1
        ) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

        # Add batch embeddings to results
        embeddings.append(sentence_embeddings.cpu().numpy())

    # Concatenate all batch embeddings
    embeddings = np.vstack(embeddings)
    return embeddings


def reduce_to_2d(embeddings: np.ndarray, random_state: int = 42) -> np.ndarray:
    tsne = TSNE(
        n_components=2,
        random_state=random_state,
        perplexity=min(30, max(5, len(embeddings) // 10)),
    )
    return tsne.fit_transform(embeddings)
