# LangchainCallbackHandler Methods

## Core Methods
- `__init__`: Initializes the callback handler with Langfuse client and tracking state.
- `on_llm_new_token`: Updates generation completion start time when streaming new tokens.
- `_get_observation_type_from_serialized`: Determines appropriate Langfuse observation type (tool/retriever/generation/agent/chain/span) from LangChain component.
- `get_langchain_run_name`: Extracts run name from serialized data, kwargs, or defaults to "<unknown>".

## Chain Lifecycle
- `on_chain_start`: Creates new chain/agent observation and registers Langfuse prompts.
- `on_chain_end`: Updates chain observation with outputs and ends the observation.
- `on_chain_error`: Handles chain errors by updating status and ending observation.

## LLM Operations
- `on_chat_model_start`: Initiates LLM generation tracking for chat models with message inputs.
- `on_llm_start`: Initiates LLM generation tracking for text completion models with prompt inputs.
- `on_llm_end`: Completes LLM generation with response, usage metrics, and model information.
- `on_llm_error`: Handles LLM errors by updating status message and ending generation.
- `__on_llm_action`: Private method that creates generation observations with model parameters and registered prompts.

## Tool & Retriever Operations
- `on_tool_start`: Creates tool observation for function/API calls with input parameters.
- `on_tool_end`: Completes tool observation with output results.
- `on_tool_error`: Handles tool errors by updating status and ending observation.
- `on_retriever_start`: Creates retriever observation for document search operations.
- `on_retriever_end`: Completes retriever observation with retrieved documents.
- `on_retriever_error`: Handles retriever errors by updating status and ending observation.

## Agent Operations
- `on_agent_action`: Updates agent observation with action details and ends it.
- `on_agent_finish`: Updates agent observation with final results and ends it.

## Prompt Management
- `_register_langfuse_prompt`: Registers Langfuse prompt templates for linking with subsequent generations.
- `_deregister_langfuse_prompt`: Removes prompt registration after linking to prevent reuse.

## Utility Methods
- `_parse_langfuse_trace_attributes_from_metadata`: Extracts session_id, user_id, and tags from metadata.
- `_parse_model_parameters`: Extracts model configuration parameters from invocation params.
- `_parse_model_and_log_errors`: Safely extracts model name with error handling and logging.
- `_log_model_parse_warning`: Logs warning when model name cannot be parsed (only once per instance).
- `__join_tags_and_metadata`: Combines tags and metadata while filtering out Langfuse-specific keys.
- `_convert_message_to_dict`: Converts LangChain message objects to dictionary format.
- `_create_message_dicts`: Batch converts list of messages to dictionary format.
- `_log_debug_event`: Logs debug information for callback events with run IDs.