from taskiq.brokers.shared_broker import async_shared_broker

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
    """Stub for runner task - queues message for ML metrics computation (batched)"""
    pass


@async_shared_broker.task(task_name="runner:process_message_metrics_single")
async def process_message_metrics_single(
    message_id: int, content: str, options: dict
) -> None:
    """Stub for runner task - queues single message for immediate ML metrics computation"""
    pass


@async_shared_broker.task(task_name="runner:flush_message_queue")
async def flush_message_queue() -> None:
    """Stub for runner task - flushes any remaining messages in the batch queue"""
    pass
