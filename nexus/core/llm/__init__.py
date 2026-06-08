from nexus.core.llm.reasoning_patch import _patched_convert_message_to_dict  # noqa: F401 — monkey-patch applied at import
from nexus.core.llm.factory import get_llm

__all__ = ["get_llm"]
