"""LLM client module for different providers."""

import os
from typing import Dict, Optional, Any
from dotenv import load_dotenv
from research_radar.llm.client.provider_type import LLMProviderType

load_dotenv()

LLM_PROVIDER = LLMProviderType(os.getenv("LLM_PROVIDER", LLMProviderType.OLLAMA.value))


def _get_base_llm_settings(model_name: str, model_parameters: Optional[Dict]) -> Dict:
    if model_parameters is None:
        model_parameters = {}

    if LLM_PROVIDER == LLMProviderType.OLLAMA:
        parameters = {
            "num_predict": model_parameters.get("max_tokens", 1024),
            "temperature": model_parameters.get("temperature", 0.05),
        }

        return {
            "model": model_name,
            **parameters,
        }

    raise ValueError(f"Incorrect LLM provider: {LLM_PROVIDER}")


def get_chat_llm_client(
    model_name: str = "granite4:micro",
    model_parameters: Optional[Dict] = None,
) -> Any:
    """Get a chat LLM client based on the configured provider.

    Args:
        model_name: The name of the model to use.
        model_parameters: Optional model parameters.

    Returns:
        The LLM client instance.
    """
    if LLM_PROVIDER == LLMProviderType.OLLAMA:
        # pylint: disable=import-outside-toplevel
        from langchain_ollama import ChatOllama

        return ChatOllama(
            **_get_base_llm_settings(
                model_name=model_name, model_parameters=model_parameters
            )
        )

    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")
