"""Embeddings provider type enumeration."""

from enum import Enum


class EmbeddingsProvider(Enum):
    """Supported embeddings provider types."""

    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    WATSONX = "watsonx"
    GOOGLE = "google"
