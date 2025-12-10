#!/usr/bin/env python
import importlib
import logging
from typing import List, Union

import garak.cli
import llm_caller
import ollama
from garak import _config
from garak.generators.base import Generator

runner_logger = logging.getLogger("my.custom.logger")
runner_logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
handler.setFormatter(formatter)

runner_logger.addHandler(handler)
runner_logger.propagate = False  # Optional: prevents double logging to root


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
        runner_logger.info(f"Input: {x}")
        runner_logger.info(f"Chat response: {result}")
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
    runner_logger.debug(f"Running command: {command}")
    garak.cli.main(command.split())
    return (
        "/home/mwm/repositories/GBI/ml-checker/runner/run_output.report.jsonl"
    )
