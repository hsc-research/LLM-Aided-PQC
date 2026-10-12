"""Optional paid LLM access. Imports and offline commands never create a client."""
import os


def create_client():
    """Require explicit cost opt-in before loading credentials or the SDK."""
    if os.environ.get("PQC_ENABLE_LLM") != "1":
        raise RuntimeError(
            "Paid model calls are disabled. Set PQC_ENABLE_LLM=1 only after "
            "reviewing the model, data sent, and budget; install the [llm] extra.")
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("Optional LLM SDK missing; install this project with [llm].") from exc
    return anthropic.Anthropic()
