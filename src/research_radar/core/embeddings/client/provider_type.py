from enum import Enum


class EmbeddingsProvider(Enum):
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    WATSONX = "watsonx"
    GOOGLE = "google"
