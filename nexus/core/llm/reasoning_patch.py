"""
Monkey-patch _convert_message_to_dict to propagate reasoning_content
from additional_kwargs to the top-level message dict.

DeepSeek's thinking mode requires reasoning_content from previous
assistant messages to be passed back as a top-level field — but
langchain_litellm's conversion only handles function_call / tool_calls,
silently dropping reasoning_content.
"""
from __future__ import annotations

from typing import Any

import langchain_litellm.chat_models.litellm as _litellm_module
from langchain_core.messages import AIMessage, BaseMessage

_original_convert = _litellm_module._convert_message_to_dict


def _patched_convert_message_to_dict(message: BaseMessage) -> dict[str, Any]:
    message_dict = _original_convert(message)
    if isinstance(message, AIMessage):
        reasoning = (message.additional_kwargs or {}).get("reasoning_content")
        if reasoning:
            message_dict["reasoning_content"] = reasoning
    return message_dict


_litellm_module._convert_message_to_dict = _patched_convert_message_to_dict
