import requests
from langchain_core.callbacks import BaseCallbackHandler

d = """
__init__/LangchainCallbackHandler
on_llm_new_token/LangchainCallbackHandler
_get_observation_type_from_serialized/LangchainCallbackHandl
get_langchain_run_name/LangchainCallbackHandler
on_retriever_error/LangchainCallbackHandler
_parse_langfuse_trace_attributes_from_metadata/LangchainCall
on_chain_start/LangchainCallbackHandler
_register_langfuse_prompt/LangchainCallbackHandler
_deregister_langfuse_prompt/LangchainCallbackHandler
on_agent_action/LangchainCallbackHandler
on_agent_finish/LangchainCallbackHandler
on_chain_end/LangchainCallbackHandler
on_chain_error/LangchainCallbackHandler
on_chat_model_start/LangchainCallbackHandler
on_llm_start/LangchainCallbackHandler
on_tool_start/LangchainCallbackHandler
on_retriever_start/LangchainCallbackHandler
on_retriever_end/LangchainCallbackHandler
on_tool_end/LangchainCallbackHandler
on_tool_error/LangchainCallbackHandler
__on_llm_action/LangchainCallbackHandler
_parse_model_parameters/LangchainCallbackHandler
_parse_model_and_log_errors/LangchainCallbackHandler
_log_model_parse_warning/LangchainCallbackHandler
on_llm_end/LangchainCallbackHandler
on_llm_error/LangchainCallbackHandler
__join_tags_and_metadata/LangchainCallbackHandler
_convert_message_to_dict/LangchainCallbackHandler
_create_message_dicts/LangchainCallbackHandler
_log_debug_event/LangchainCallbackHandler
"""


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


class Client:
    def __init__(self, token):
        self.token = token


class CheckerCallbackHandler(BaseCallbackHandler):
    def __init__(self, *, token, update_trace: bool = False) -> None:
        self.client = Client(token)

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(f"My custom handler, token: {token}")
