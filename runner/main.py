import importlib
from typing import List, Union

from garak import _config
from garak.generators.base import Generator

import llm_caller
import garak.generators.function

g = garak.generators.function.Single(name="llm_caller#speak")

"""
The target function is expected to take a string, and return a string. Other arguments passed by garak are forwarded to the target function.

Note that one can import the intended target module into scope and then invoke a garak run via garak’s cli module, using something like:
"""
import garak
import garak.cli
import llm_caller

garak.cli.main("--model_type function --model_name llm_caller#speak --probes encoding.InjectBase32".split())
