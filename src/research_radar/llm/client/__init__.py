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
    
    if LLM_PROVIDER == LLMProviderType.GOOGLE:
        return {
            "model_name": model_name,  
            "temperature": model_parameters.get("temperature", 0.0),
            "max_output_tokens": model_parameters.get("max_tokens", 8192),
        }

    raise ValueError(f"Incorrect LLM provider: {LLM_PROVIDER}")


def get_chat_llm_client(
    model_name: Optional[str] = None,
    model_parameters: Optional[Dict] = None,
) -> Any:
    """Get a chat LLM client based on the configured provider.

    Args:
        model_name: The name of the model to use.
        model_parameters: Optional model parameters.

    Returns:
        The LLM client instance.
    """
    if model_name is None:
        # Default to a safe generic if .env is missing
        model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")
        
    if LLM_PROVIDER == LLMProviderType.OLLAMA:
        from langchain_ollama import (
            ChatOllama,
        )  

        if "gemini" in model_name:
             model_name = "llama3.2" 

        return ChatOllama(
            **_get_base_llm_settings(
                model_name=model_name, model_parameters=model_parameters
            )
        )

    if LLM_PROVIDER == LLMProviderType.GOOGLE:
        from langchain_google_vertexai import (
            ChatVertexAI
        ) 
        
        if model_name == "granite4:micro" or "granite" in model_name:
            model_name = "gemini-1.5-flash"

        return ChatVertexAI(
            **_get_base_llm_settings(
                model_name=model_name, model_parameters=model_parameters
            )
        )

    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")
