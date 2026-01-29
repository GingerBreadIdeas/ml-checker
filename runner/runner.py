#!/usr/bin/env python

import asyncio
import json
import os
import re
import time
from collections import deque
from typing import Any, Dict, List

import garak.cli
import llm_caller
import ollama
import torch
from loguru import logger
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
from taskiq_pg.asyncpg import AsyncpgBroker
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
)

DB_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ml-checker"
)
broker = AsyncpgBroker(
    dsn=DB_URL,
)

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Use the newer recommended approach to avoid the warning
Base = declarative_base()
JSONPortable = JSON().with_variant(JSONB, "postgresql")

# Batch Processing Configuration
BATCH_SIZE = int(
    os.getenv("METRICS_BATCH_SIZE", "10")
)  # Max messages per batch
BATCH_TIMEOUT = float(
    os.getenv("METRICS_BATCH_TIMEOUT", "5.0")
)  # Max seconds to wait
message_queue: deque = deque()
last_batch_time = time.time()
queue_lock = asyncio.Lock()


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


def calculate_metrics(message: str) -> Dict[str, Any]:
    """
    Calculate comprehensive security and content metrics using multiple models.

    Returns a dictionary with results from various security analysis models:
    - prompt_injection: Detects prompt injection attempts
    - toxicity: Detects toxic/harmful content
    - sentiment: Analyzes sentiment (positive/negative/neutral)
    - jailbreak: Detects jailbreak attempts
    - text_statistics: Basic text analysis metrics
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Running metrics calculation on device: {device}")

    metrics_results: Dict[str, Any] = {}

    # 1. Prompt Injection Detection (ProtectAI DeBERTa model)
    try:
        logger.debug("Running prompt injection detection...")
        pi_tokenizer = AutoTokenizer.from_pretrained(
            "ProtectAI/deberta-v3-base-prompt-injection"
        )
        pi_model = AutoModelForSequenceClassification.from_pretrained(
            "ProtectAI/deberta-v3-base-prompt-injection"
        )
        pi_classifier = pipeline(
            "text-classification",
            model=pi_model,
            tokenizer=pi_tokenizer,
            truncation=True,
            max_length=512,
            device=device,
        )
        pi_result = pi_classifier(message)
        metrics_results["prompt_injection"] = {
            "label": pi_result[0]["label"],
            "score": pi_result[0]["score"],
            "model": "ProtectAI/deberta-v3-base-prompt-injection",
        }
    except Exception as e:
        logger.error(f"Prompt injection detection failed: {e}")
        metrics_results["prompt_injection"] = {"error": str(e)}

    # 2. Toxicity Detection (using unitary/toxic-bert)
    try:
        logger.debug("Running toxicity detection...")
        toxicity_classifier = pipeline(
            "text-classification",
            model="unitary/toxic-bert",
            truncation=True,
            max_length=512,
            device=device,
        )
        toxicity_result = toxicity_classifier(message)
        metrics_results["toxicity"] = {
            "label": toxicity_result[0]["label"],
            "score": toxicity_result[0]["score"],
            "model": "unitary/toxic-bert",
        }
    except Exception as e:
        logger.error(f"Toxicity detection failed: {e}")
        metrics_results["toxicity"] = {"error": str(e)}

    # 3. Sentiment Analysis (using nlptown/bert-base-multilingual-uncased-sentiment)
    try:
        logger.debug("Running sentiment analysis...")
        sentiment_classifier = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            truncation=True,
            max_length=512,
            device=device,
        )
        sentiment_result = sentiment_classifier(message)
        # Convert star rating to sentiment label
        star_label = sentiment_result[0]["label"]
        stars = int(star_label.split()[0])
        if stars <= 2:
            sentiment_label = "negative"
        elif stars == 3:
            sentiment_label = "neutral"
        else:
            sentiment_label = "positive"

        metrics_results["sentiment"] = {
            "label": sentiment_label,
            "stars": stars,
            "score": sentiment_result[0]["score"],
            "model": "nlptown/bert-base-multilingual-uncased-sentiment",
        }
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        metrics_results["sentiment"] = {"error": str(e)}

    # 4. Jailbreak Detection (using jackhhao/jailbreak-classifier)
    try:
        logger.debug("Running jailbreak detection...")
        jailbreak_classifier = pipeline(
            "text-classification",
            model="jackhhao/jailbreak-classifier",
            truncation=True,
            max_length=512,
            device=device,
        )
        jailbreak_result = jailbreak_classifier(message)
        metrics_results["jailbreak"] = {
            "label": jailbreak_result[0]["label"],
            "score": jailbreak_result[0]["score"],
            "model": "jackhhao/jailbreak-classifier",
        }
    except Exception as e:
        logger.error(f"Jailbreak detection failed: {e}")
        metrics_results["jailbreak"] = {"error": str(e)}

    # 5. Text Statistics (no ML model - rule-based analysis)
    try:
        logger.debug("Calculating text statistics...")
        text_stats = calculate_text_statistics(message)
        metrics_results["text_statistics"] = text_stats
    except Exception as e:
        logger.error(f"Text statistics calculation failed: {e}")
        metrics_results["text_statistics"] = {"error": str(e)}

    # 6. Suspicious Patterns Detection (rule-based heuristics)
    try:
        logger.debug("Detecting suspicious patterns...")
        suspicious_patterns = detect_suspicious_patterns(message)
        metrics_results["suspicious_patterns"] = suspicious_patterns
    except Exception as e:
        logger.error(f"Suspicious pattern detection failed: {e}")
        metrics_results["suspicious_patterns"] = {"error": str(e)}

    return metrics_results


def calculate_metrics_batch(messages: List[str]) -> List[Dict[str, Any]]:
    """
    Calculate comprehensive security and content metrics for a batch of messages.
    This is more efficient than processing messages individually as models are loaded once.

    Args:
        messages: List of message strings to analyze

    Returns:
        List of metric dictionaries, one per message in the same order
    """
    if not messages:
        return []

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(
        f"Running batch metrics calculation for {len(messages)} messages on device: {device}"
    )

    batch_results = []

    # Load all models once
    try:
        # 1. Prompt Injection Detection
        logger.debug("Loading prompt injection model...")
        pi_tokenizer = AutoTokenizer.from_pretrained(
            "ProtectAI/deberta-v3-base-prompt-injection"
        )
        pi_model = AutoModelForSequenceClassification.from_pretrained(
            "ProtectAI/deberta-v3-base-prompt-injection"
        )
        pi_classifier = pipeline(
            "text-classification",
            model=pi_model,
            tokenizer=pi_tokenizer,
            truncation=True,
            max_length=512,
            device=device,
        )

        # 2. Toxicity Detection
        logger.debug("Loading toxicity model...")
        toxicity_classifier = pipeline(
            "text-classification",
            model="unitary/toxic-bert",
            truncation=True,
            max_length=512,
            device=device,
        )

        # 3. Sentiment Analysis
        logger.debug("Loading sentiment model...")
        sentiment_classifier = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            truncation=True,
            max_length=512,
            device=device,
        )

        # 4. Jailbreak Detection
        logger.debug("Loading jailbreak model...")
        jailbreak_classifier = pipeline(
            "text-classification",
            model="jackhhao/jailbreak-classifier",
            truncation=True,
            max_length=512,
            device=device,
        )

        # Process all messages through each model in batch
        logger.debug("Processing batch through models...")
        pi_results = pi_classifier(messages)
        toxicity_results = toxicity_classifier(messages)
        sentiment_results = sentiment_classifier(messages)
        jailbreak_results = jailbreak_classifier(messages)

        # Combine results for each message
        for i, message in enumerate(messages):
            metrics_results: Dict[str, Any] = {}

            # Prompt Injection
            try:
                metrics_results["prompt_injection"] = {
                    "label": pi_results[i]["label"],
                    "score": pi_results[i]["score"],
                    "model": "ProtectAI/deberta-v3-base-prompt-injection",
                }
            except Exception as e:
                logger.error(f"Prompt injection failed for message {i}: {e}")
                metrics_results["prompt_injection"] = {"error": str(e)}

            # Toxicity
            try:
                metrics_results["toxicity"] = {
                    "label": toxicity_results[i]["label"],
                    "score": toxicity_results[i]["score"],
                    "model": "unitary/toxic-bert",
                }
            except Exception as e:
                logger.error(f"Toxicity detection failed for message {i}: {e}")
                metrics_results["toxicity"] = {"error": str(e)}

            # Sentiment
            try:
                star_label = sentiment_results[i]["label"]
                stars = int(star_label.split()[0])
                if stars <= 2:
                    sentiment_label = "negative"
                elif stars == 3:
                    sentiment_label = "neutral"
                else:
                    sentiment_label = "positive"

                metrics_results["sentiment"] = {
                    "label": sentiment_label,
                    "stars": stars,
                    "score": sentiment_results[i]["score"],
                    "model": "nlptown/bert-base-multilingual-uncased-sentiment",
                }
            except Exception as e:
                logger.error(f"Sentiment analysis failed for message {i}: {e}")
                metrics_results["sentiment"] = {"error": str(e)}

            # Jailbreak
            try:
                metrics_results["jailbreak"] = {
                    "label": jailbreak_results[i]["label"],
                    "score": jailbreak_results[i]["score"],
                    "model": "jackhhao/jailbreak-classifier",
                }
            except Exception as e:
                logger.error(
                    f"Jailbreak detection failed for message {i}: {e}"
                )
                metrics_results["jailbreak"] = {"error": str(e)}

            # Text Statistics (rule-based)
            try:
                text_stats = calculate_text_statistics(message)
                metrics_results["text_statistics"] = text_stats
            except Exception as e:
                logger.error(f"Text statistics failed for message {i}: {e}")
                metrics_results["text_statistics"] = {"error": str(e)}

            # Suspicious Patterns (rule-based)
            try:
                suspicious_patterns = detect_suspicious_patterns(message)
                metrics_results["suspicious_patterns"] = suspicious_patterns
            except Exception as e:
                logger.error(
                    f"Suspicious patterns failed for message {i}: {e}"
                )
                metrics_results["suspicious_patterns"] = {"error": str(e)}

            batch_results.append(metrics_results)

        logger.info(
            f"Successfully processed batch of {len(messages)} messages"
        )

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        # Fallback to individual processing
        logger.warning("Falling back to individual message processing")
        for message in messages:
            try:
                batch_results.append(calculate_metrics(message))
            except Exception as inner_e:
                logger.error(f"Individual processing also failed: {inner_e}")
                batch_results.append({"error": str(inner_e)})

    return batch_results


def calculate_text_statistics(message: str) -> Dict[str, Any]:
    """
    Calculate basic text statistics useful for anomaly detection.
    """
    words = message.split()
    sentences = re.split(r"[.!?]+", message)
    sentences = [s.strip() for s in sentences if s.strip()]

    return {
        "char_count": len(message),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_word_length": (
            sum(len(w) for w in words) / len(words) if words else 0
        ),
        "avg_sentence_length": (
            len(words) / len(sentences) if sentences else 0
        ),
        "uppercase_ratio": (
            sum(1 for c in message if c.isupper()) / len(message)
            if message
            else 0
        ),
        "special_char_ratio": (
            sum(1 for c in message if not c.isalnum() and not c.isspace())
            / len(message)
            if message
            else 0
        ),
        "digit_ratio": (
            sum(1 for c in message if c.isdigit()) / len(message)
            if message
            else 0
        ),
    }


def detect_suspicious_patterns(message: str) -> Dict[str, Any]:
    """
    Detect suspicious patterns commonly associated with prompt injection
    and jailbreak attempts using rule-based heuristics.
    """
    message_lower = message.lower()

    patterns = {
        # Role-playing/persona manipulation
        "role_manipulation": [
            r"\bignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|rules?|prompts?)\b",
            r"\bignore\s+(previous|above|prior)\s+(all\s+)?(instructions?|rules?|prompts?)\b",
            r"\bdisregard\s+(all\s+)?(previous|above|prior)?\s*(instructions?|rules?|prompts?)\b",
            r"\bforget\s+(everything|all|your)\b",
            r"\byou\s+are\s+(now|no\s+longer)\b",
            r"\bpretend\s+(to\s+be|you\s+are|you\'re)\b",
            r"\bact\s+as\s+(if|a|an)\b",
            r"\broleplay\s+as\b",
            r"\blet\'?s\s+play\s+a\s+game\b",
            r"\bfrom\s+now\s+on\b",
        ],
        # System prompt extraction
        "system_prompt_extraction": [
            r"\brepeat\s+(your|the)\s+(instructions?|prompt|system)\b",
            r"\brepeat\s+(your|the)\s+(initial|original)\s+(instructions?|prompt)\b",
            r"\bshow\s+(me\s+)?(your|the)\s+(original|system|initial)\b",
            r"\bprint\s+(your|the)\s+(instructions?|prompt)\b",
            r"\bwhat\s+(are|were|is)\s+(your|the)\s+(original\s+)?(instructions?|system\s+prompt)\b",
            r"\bdisplay\s+(your|the)\s+prompt\b",
            r"\btell\s+me\s+(your|the)\s+(system\s+)?prompt\b",
            r"\bsystem\s+prompt\b",
            r"\binitial\s+instructions?\b",
            r"\bverbatim\b",
        ],
        # Code injection attempts
        "code_injection": [
            r"<script\b",
            r"\beval\s*\(",
            r"\bexec\s*\(",
            r"\bsystem\s*\(",
            r"\b__import__\b",
            r"\bos\.(system|popen|exec)\b",
            r"\bsubprocess\b",
        ],
        # Delimiter confusion
        "delimiter_confusion": [
            r"```\s*(system|assistant|user)\b",
            r"\[INST\]",
            r"<<SYS>>",
            r"<\|im_start\|>",
            r"<\|system\|>",
            r"###\s*(instruction|response|system)\b",
        ],
        # Encoding tricks
        "encoding_tricks": [
            r"\bbase64\b",
            r"\bhex\s+encode\b",
            r"\brot13\b",
            r"\bunicode\s+escape\b",
            r"\\x[0-9a-fA-F]{2}",
            r"\\u[0-9a-fA-F]{4}",
        ],
        # Authority claims
        "authority_claims": [
            r"\bi\s+am\s+(your|the)\s+(developer|creator|admin)\b",
            r"\bthis\s+is\s+(an?\s+)?(emergency|urgent|critical)\b",
            r"\badmin\s+(mode|override|access)\b",
            r"\bsudo\s+mode\b",
            r"\bdebug\s+mode\b",
        ],
    }

    detected: Dict[str, List[str]] = {}
    total_matches = 0

    for category, pattern_list in patterns.items():
        matches = []
        for pattern in pattern_list:
            if re.search(pattern, message_lower, re.IGNORECASE):
                matches.append(pattern)
        if matches:
            detected[category] = matches
            total_matches += len(matches)

    return {
        "detected_patterns": detected,
        "total_suspicious_matches": total_matches,
        "risk_level": (
            "high"
            if total_matches >= 3
            else "medium" if total_matches >= 1 else "low"
        ),
    }


def save_message_metrics(data):
    """
    Save calculated metrics to the database.

    The metrics structure now contains multiple models' results:
    - prompt_injection: DeBERTa-based prompt injection detection
    - toxicity: Toxic content detection
    - sentiment: Sentiment analysis with star ratings
    - jailbreak: Jailbreak attempt detection
    - text_statistics: Rule-based text analysis
    - suspicious_patterns: Pattern-based heuristic detection
    """
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
            # Compute overall risk assessment
            overall_risk = compute_overall_risk(metrics)
            message.metrics = {
                "metrics": metrics,
                "options": options,
                "overall_risk": overall_risk,
            }
            db.commit()
            logger.info(
                f"Updated message {message_id} with comprehensive metrics"
            )
        else:
            logger.warning(f"No message found with id: {message_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Error saving message results: {e}")
    finally:
        db.close()


def compute_overall_risk(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute an overall risk score based on all metrics.

    Returns a risk assessment with:
    - score: 0.0 to 1.0 (higher = more risky)
    - level: "low", "medium", "high", "critical"
    - flags: List of triggered risk indicators
    """
    risk_score = 0.0
    flags: List[str] = []

    # Check prompt injection (highest weight)
    pi = metrics.get("prompt_injection", {})
    if pi.get("label") == "INJECTION":
        score = pi.get("score", 0)
        risk_score += score * 0.35
        if score > 0.8:
            flags.append("high_confidence_prompt_injection")
        elif score > 0.5:
            flags.append("moderate_prompt_injection")

    # Check jailbreak detection
    jb = metrics.get("jailbreak", {})
    if jb.get("label") == "jailbreak":
        score = jb.get("score", 0)
        risk_score += score * 0.30
        if score > 0.8:
            flags.append("high_confidence_jailbreak")
        elif score > 0.5:
            flags.append("moderate_jailbreak")

    # Check toxicity
    tox = metrics.get("toxicity", {})
    if tox.get("label") == "toxic":
        score = tox.get("score", 0)
        risk_score += score * 0.15
        if score > 0.8:
            flags.append("high_toxicity")
        elif score > 0.5:
            flags.append("moderate_toxicity")

    # Check suspicious patterns
    sp = metrics.get("suspicious_patterns", {})
    if sp.get("risk_level") == "high":
        risk_score += 0.15
        flags.append("multiple_suspicious_patterns")
    elif sp.get("risk_level") == "medium":
        risk_score += 0.05
        flags.append("suspicious_pattern_detected")

    # Check text statistics for anomalies
    ts = metrics.get("text_statistics", {})
    if ts.get("special_char_ratio", 0) > 0.3:
        risk_score += 0.05
        flags.append("high_special_character_ratio")
    if ts.get("uppercase_ratio", 0) > 0.5:
        risk_score += 0.02
        flags.append("excessive_uppercase")

    # Normalize score to 0-1 range
    risk_score = min(risk_score, 1.0)

    # Determine risk level
    if risk_score >= 0.7:
        level = "critical"
    elif risk_score >= 0.4:
        level = "high"
    elif risk_score >= 0.2:
        level = "medium"
    else:
        level = "low"

    return {
        "score": round(risk_score, 4),
        "level": level,
        "flags": flags,
    }


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

    This function now queues messages for batch processing instead of
    processing them immediately. Messages are processed when either:
    1. The batch reaches BATCH_SIZE messages, or
    2. BATCH_TIMEOUT seconds have elapsed since the last batch
    """
    global last_batch_time

    async with queue_lock:
        # Add message to queue
        message_queue.append(
            {
                "id": message_id,
                "content": content,
                "options": options,
            }
        )
        logger.debug(
            f"Queued message {message_id}. Queue size: {len(message_queue)}"
        )

        # Check if we should process the batch
        should_process = (
            len(message_queue) >= BATCH_SIZE
            or (time.time() - last_batch_time) >= BATCH_TIMEOUT
        )

        if should_process and len(message_queue) > 0:
            # Extract batch from queue
            batch = []
            while message_queue and len(batch) < BATCH_SIZE:
                batch.append(message_queue.popleft())

            logger.info(f"Processing batch of {len(batch)} messages")
            last_batch_time = time.time()

            # Process batch outside the lock
            asyncio.create_task(_process_batch(batch))


async def _process_batch(batch: List[Dict[str, Any]]) -> None:
    """
    Internal function to process a batch of messages.
    Runs ML inference on all messages in parallel and saves results.
    """
    try:
        # Extract messages content for batch processing
        messages_content = [msg["content"] for msg in batch]

        # Run batch metrics calculation
        batch_metrics = calculate_metrics_batch(messages_content)

        # Save results for each message
        for i, msg_data in enumerate(batch):
            try:
                message = {
                    "id": msg_data["id"],
                    "metrics": batch_metrics[i],
                    "options": msg_data["options"],
                }
                save_message_metrics(message)
            except Exception as e:
                logger.error(
                    f"Failed to save metrics for message {msg_data['id']}: {e}"
                )

        logger.info(
            f"Successfully processed and saved batch of {len(batch)} messages"
        )

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        # Fallback: process individually
        logger.warning("Falling back to individual processing")
        for msg_data in batch:
            try:
                metrics = calculate_metrics(msg_data["content"])
                message = {
                    "id": msg_data["id"],
                    "metrics": metrics,
                    "options": msg_data["options"],
                }
                save_message_metrics(message)
            except Exception as inner_e:
                logger.error(
                    f"Individual processing failed for message {msg_data['id']}: {inner_e}"
                )


@broker.task(task_name="runner:process_message_metrics_single", max_retries=0)
async def process_message_metrics_single(
    message_id: int, content: str, options: dict
) -> None:
    """
    Legacy single-message processing task for backward compatibility
    or when batch processing is not desired.
    """
    # Run ML inference
    metrics = calculate_metrics(content)

    message = {
        "id": message_id,
        "metrics": metrics,
        "options": options,
    }
    save_message_metrics(message)


@broker.task(task_name="runner:flush_message_queue", max_retries=0)
async def flush_message_queue() -> None:
    """
    Periodic task to flush any remaining messages in the queue.
    Should be called periodically (e.g., every BATCH_TIMEOUT seconds)
    to ensure messages don't wait indefinitely.
    """
    global last_batch_time

    async with queue_lock:
        if len(message_queue) > 0:
            # Extract all remaining messages
            batch = []
            while message_queue:
                batch.append(message_queue.popleft())

            logger.info(
                f"Flushing queue: processing {len(batch)} remaining messages"
            )
            last_batch_time = time.time()

            # Process batch outside the lock
            asyncio.create_task(_process_batch(batch))
