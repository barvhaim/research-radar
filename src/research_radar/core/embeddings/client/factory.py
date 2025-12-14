import os
import logging
from typing import Dict, Any
from research_radar.core.embeddings.client.provider_type import EmbeddingsProvider

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    pass
try:
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    pass
try:
    from langchain_ibm import WatsonxEmbeddings
except ImportError:
    pass

logger = logging.getLogger(__name__)


def _get_base_llm_settings(model_name: str, provider: EmbeddingsProvider) -> Dict:
    """
    Organizes connection details
    """
    if provider == EmbeddingsProvider.OLLAMA:
        return {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "model": model_name,
        }
    if provider == EmbeddingsProvider.WATSONX:
        return {
            "model_id": model_name,
            "url": os.getenv(
                "WATSONX_API_ENDPOINT", "https://us-south.ml.cloud.ibm.com"
            ),
            "project_id": os.getenv("WATSONX_PROJECT_ID"),
            "apikey": os.getenv("WATSONX_API_KEY"),
            "params": {
                "truncate_input_tokens": int(
                    os.getenv("WATSONX_TRUNCATE_INPUT_TOKENS", "3")
                ),
                "return_options": {"input_text": True},
            },
        }
    return {}


def get_embeddings_client() -> Any:
    """
    Picks tool, need to be changed in .env:
        - EMBEDDINGS_PROVIDER=huggingface
        - EMBEDDINGS_PROVIDER=ollama
        - EMBEDDINGS_PROVIDER=watsonx
    """
    provider_str = os.getenv("EMBEDDINGS_PROVIDER", "huggingface").lower()

    try:
        provider = EmbeddingsProvider(provider_str)
    except ValueError:
        logger.warning(
            "Unknown provider '%s', defaulting to HuggingFace.", provider_str
        )
        provider = EmbeddingsProvider.HUGGINGFACE

    logger.info("Initializing Embeddings Provider: %s", provider.name)

    if provider == EmbeddingsProvider.HUGGINGFACE:
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    if provider == EmbeddingsProvider.OLLAMA:
        model_name = os.getenv("EMBEDDINGS_MODEL_NAME", "mxbai-embed-large")
        settings = _get_base_llm_settings(model_name, provider)
        return OllamaEmbeddings(**settings)

    elif provider == EmbeddingsProvider.WATSONX:
        model_name = os.getenv(
            "EMBEDDINGS_MODEL_NAME", "ibm/granite-embedding-107m-multilingual"
        )

        settings = _get_base_llm_settings(model_name, provider)
        return WatsonxEmbeddings(
            model_id=settings["model_id"],
            url=settings["url"],
            apikey=settings["apikey"],
            project_id=settings["project_id"],
            params=settings["params"],
        )

    raise ValueError(f"Unsupported embeddings provider: {provider}")
