from taskiq.brokers.shared_broker import async_shared_broker
import numpy as np

# Task stubs - actual implementations are in runner and processing workers
# These allow the backend to queue tasks


@async_shared_broker.task(task_name="runner:process_prompt_check")
async def process_prompt_check(
    prompt_id: int,
    model_supplier: str,
    model_id: str,
    prompt_text: str,
    probe: str,
) -> None:
    """Stub for runner task - queues prompt for Garak security check"""
    pass


@async_shared_broker.task(task_name="runner:process_message_metrics")
async def process_message_metrics(
    message_id: int, content: str, options: dict
) -> None:
    """Stub for runner task - queues message for ML metrics computation"""
    pass


@async_shared_broker.task(task_name="runner:create_embeddings")
async def create_embeddings(
    texts: list[str],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> np.ndarray:
    """Stub for runner task - queues message for ML metrics computation"""
    pass


@async_shared_broker.task(task_name="runner:reduce_to_2d")
async def reduce_to_2d(embeddings: np.ndarray, random_state: int = 42) -> np.ndarray:
    pass
