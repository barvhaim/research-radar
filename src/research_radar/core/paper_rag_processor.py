import logging
import hashlib
import os
from enum import Enum
from typing import Dict, Any

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# PART 1: Provider configuration

class EmbeddingsProvider(Enum):
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    WATSONX = "watsonx"

def _get_base_llm_settings(model_name: str, provider: EmbeddingsProvider) -> Dict:
    """
    Organizes connection details
    """
    if provider == EmbeddingsProvider.OLLAMA:
        return {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "model": model_name,
        }
    elif provider == EmbeddingsProvider.WATSONX:
        return {
            "model_id": model_name,
            "url": os.getenv("WATSONX_API_ENDPOINT", "https://us-south.ml.cloud.ibm.com"),
            "project_id": os.getenv("WATSONX_PROJECT_ID"),
            "apikey": os.getenv("WATSONX_API_KEY"),
            "params": {
                "truncate_input_tokens": int(os.getenv("WATSONX_TRUNCATE_INPUT_TOKENS", "3")),
                "return_options": {"input_text": True},
            },
        }
    return {}

def get_embeddings_client() -> Any:
    """
    Picks tool
    Default to HUGGINGFACE (local)
    """ 
    provider_str = os.getenv("EMBEDDINGS_PROVIDER", "huggingface").lower()
    
    try:
        provider = EmbeddingsProvider(provider_str)
    except ValueError:
        provider = EmbeddingsProvider.HUGGINGFACE

    if provider == EmbeddingsProvider.HUGGINGFACE:
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    elif provider == EmbeddingsProvider.OLLAMA:
        model_name = os.getenv("EMBEDDINGS_MODEL_NAME", "mxbai-embed-large")
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(**_get_base_llm_settings(model_name, provider))

    elif provider == EmbeddingsProvider.WATSONX:
        model_name = os.getenv("EMBEDDINGS_MODEL_NAME", "ibm/granite-embedding-107m-multilingual")
        from langchain_ibm import WatsonxEmbeddings
        settings = _get_base_llm_settings(model_name, provider)
        return WatsonxEmbeddings(
            model_id=settings["model_id"],
            url=settings["url"],
            apikey=settings["apikey"],
            project_id=settings["project_id"],
            params=settings["params"]
        )

    raise ValueError(f"Unsupported embeddings provider: {provider}")

# PART 2: Processor

class PaperRAGProcessor:
    """
    Manage RAG pipeline
    """
    def __init__(self):
        """
        Call the provider, initiate DB
        """
        self.embeddings = get_embeddings_client()
        
        logger.info("Initializing Ephemeral (In-Memory) ChromaDB...")
        self.vector_store = Chroma(
            collection_name="research_papers",
            embedding_function=self.embeddings,
            persist_directory=None 
        )

    def _split_markdown(self, markdown_text: str):
        """
        Chunking logics
        """
        headers_to_split_on = [("#", "Header 1"), ("##", "Header 2")]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        header_splits = markdown_splitter.split_text(markdown_text)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=100
        )
        return text_splitter.split_documents(header_splits)

    def process_paper(self, paper_data: dict):
        """
        Process paper; receive an extracted paper, cut and embedd it.
        """
        paper_url = paper_data.get("paper_url", "unknown_url")
        text_content = paper_data.get("text_content")
        
        if not text_content:
            logger.warning(f"No content for {paper_url}")
            return

        article_hash = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
        logger.info(f"Processing paper: {paper_url} (Hash: {article_hash[:8]}...)")

        try:
            chunks = self._split_markdown(text_content)
            logger.info(f"Split into {len(chunks)} chunks.")

            for chunk in chunks:
                chunk.metadata["source"] = paper_url
                chunk.metadata["article_hash"] = article_hash 

            self.vector_store.add_documents(chunks)
            logger.info(f"Successfully indexed {len(chunks)} chunks.")
            
            return article_hash 

        except Exception as e:
            logger.error(f"Failed to process paper: {e}")
            return None

    def search(self, query: str, k: int = 3, article_hash: str = None):
        """
        Runs vector search
        """

        logger.info(f"Searching for: '{query}'")
        
        filter_dict = None
        if article_hash:
            filter_dict = {"article_hash": article_hash}

        try:
            return self.vector_store.similarity_search(query, k=k, filter=filter_dict)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []