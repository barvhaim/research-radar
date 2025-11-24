import logging
import os
from enum import Enum
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# --- 1. CONFIGURATION LOGIC ---

class EmbeddingsProvider(Enum):
    HUGGINGFACE = "huggingface" # Local, CPU, Fast (Default)
    OLLAMA = "ollama"           # Local, requires Ollama running
    WATSONX = "watsonx"         # Remote, requires API Key

def get_embeddings_client():
    """
    Factory function to get the correct embedding model based on env vars.
    Currently supports: HUGGINGFACE.
    """
    # Default to HUGGINGFACE
    provider = os.getenv("EMBEDDINGS_PROVIDER", EmbeddingsProvider.HUGGINGFACE.value).lower()
    
    logger.info(f"Initializing Embeddings Provider: {provider.upper()}")

    if provider == EmbeddingsProvider.HUGGINGFACE.value:
        # This is the one we are using!
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    elif provider == EmbeddingsProvider.OLLAMA.value:
        # Placeholder for future use
        # from langchain_ollama import OllamaEmbeddings
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("EMBEDDINGS_MODEL_NAME", "mxbai-embed-large")
        raise NotImplementedError("Ollama provider is not yet installed. Run 'uv add langchain-ollama' to enable.")

    elif provider == EmbeddingsProvider.WATSONX.value:
        # Placeholder for future use
        # from langchain_ibm import WatsonxEmbeddings
        raise NotImplementedError("WatsonX provider is not yet installed. Run 'uv add langchain-ibm' to enable.")

    raise ValueError(f"Unsupported embeddings provider: {provider}")


# --- 2. THE MAIN PROCESSOR CLASS ---

class PaperRAGProcessor:
    """
    Manages the RAG pipeline: Chunking, Embedding, and Indexing.
    Runs In-Memory (no garbage files).
    """

    def __init__(self):
        """
        Initialize the processor components using the factory.
        """
        # 1. Load the Embedding Model
        try:
            self.embeddings = get_embeddings_client()
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise e
        
        # 2. Connect to Vector Database (In-Memory)
        logger.info("Initializing Ephemeral (In-Memory) Vector DB...")
        try:
            self.vector_store = Chroma(
                collection_name="research_papers",
                embedding_function=self.embeddings,
                persist_directory=None  # <--- Forces RAM-only mode
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise e
        
        # 3. Define the Text Splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def process_paper(self, paper_data: dict):
        """
        Takes a paper object, splits it, and indexes it.
        """
        paper_url = paper_data.get("paper_url", "unknown_url")
        text_content = paper_data.get("text_content")
        metadata = paper_data.get("metadata", {})

        if not text_content:
            logger.warning(f"No content for {paper_url}. Skipping.")
            return

        logger.info(f"Starting RAG processing for: {paper_url}")

        try:
            # 1. Chunking
            chunks = self.text_splitter.split_text(text_content)
            logger.info(f"Split text into {len(chunks)} chunks.")

            if not chunks:
                logger.warning("Text splitting resulted in 0 chunks.")
                return

            # 2. Formatting
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_meta = metadata.copy()
                chunk_meta.update({
                    "source": paper_url,
                    "chunk_index": i
                })
                doc = Document(page_content=chunk, metadata=chunk_meta)
                documents.append(doc)

            # 3. Indexing
            self.vector_store.add_documents(documents)
            logger.info(f"Successfully indexed {len(documents)} chunks to ChromaDB.")

        except Exception as e:
            logger.error(f"Failed to process paper {paper_url}: {e}")

    def search(self, query: str, k: int = 3):
        """
        Search the database.
        """
        logger.info(f"Searching Vector DB for: '{query}'")
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []