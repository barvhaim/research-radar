import logging
import hashlib

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_chroma import Chroma
from langsmith import traceable

from research_radar.core.embeddings.client.factory import get_embeddings_client

logger = logging.getLogger(__name__)


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
            persist_directory=None,
        )

    def _split_markdown(self, markdown_text: str):
        """
        Chunking logics
        """
        headers_to_split_on = [("#", "Header 1"), ("##", "Header 2")]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        header_splits = markdown_splitter.split_text(markdown_text)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500, chunk_overlap=300
        )
        return text_splitter.split_documents(header_splits)

    @traceable(run_type="chain", name="index_paper")
    def process_paper(self, paper_data: dict):
        """
        Process paper; receive an extracted paper, cut and embedd it.
        """
        paper_url = paper_data.get("paper_url", "unknown_url")
        text_content = paper_data.get("text_content")

        if not text_content:
            logger.warning("No content for %s", paper_url)
            return

        article_hash = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
        logger.info("Processing paper: %s (Hash: %s...)", paper_url, article_hash[:8])

        try:
            chunks = self._split_markdown(text_content)
            logger.info("Split into %d chunks.", len(chunks))

            for chunk in chunks:
                chunk.metadata["source"] = paper_url
                chunk.metadata["article_hash"] = article_hash

            batch_size = 20
            total_chunks = len(chunks)

            for i in range(0, total_chunks, batch_size):
                batch = chunks[i : i + batch_size]
                self.vector_store.add_documents(batch)
                logger.info(
                    f"Indexed batch {i//batch_size + 1}: chunks {i} to {min(i+batch_size, total_chunks)}"
                )

            logger.info("Successfully indexed %d chunks.", len(chunks))

            return article_hash

        except Exception as e:
            logger.error("Failed to process paper: %s", e)
            return None

    @traceable(run_type="retriever", name="retrieve_chunks")
    def search(self, query: str, k: int = 4, article_hash: str = None):
        """
        Runs vector search
        """

        logger.info("Searching for: '%s'", query)

        filter_dict = None
        if article_hash:
            filter_dict = {"article_hash": article_hash}

        try:
            return self.vector_store.similarity_search(query, k=k, filter=filter_dict)
        except Exception as e:
            logger.error("Search failed: %s", e)
            return []
