import logging
import os
from typing import Dict
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from research_radar.llm.client import get_chat_llm_client
from research_radar.llm.prompts import get_prompt
from research_radar.core.paper_rag_processor import PaperRAGProcessor

logger = logging.getLogger(__name__)


class PaperAnalyzer:
    """
    A class to analyze papers using RAG and LLM.
    """

    def __init__(self, rag_processor: PaperRAGProcessor):
        self.rag_processor = rag_processor
        self.questions = [
            "What problem does the paper address?",
            "Why is this problem important?",
            "What is the main claim or conclusion?",
            "What is the key insight of the paper?",
        ]

    @staticmethod
    def _get_prompt_template_str() -> str:
        """Fetch the prompt template string from YAML."""
        template = get_prompt("paper_analysis")
        template_str = template.get("paper_analysis")

        if not template_str:
            raise NotImplementedError("Prompt template 'paper_analysis' not found.")
        return template_str

    def _build_llm_chain(self) -> RunnableSequence:
        """
        Builds the LangChain sequence: Prompt -> LLM -> StringParser
        """
        template_str = self._get_prompt_template_str()

        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=template_str,
        )

        # Use the centralized factory
        llm = get_chat_llm_client(
            model_name=os.getenv("LLM_MODEL"),
            model_parameters={
                "temperature": 0,
                "max_tokens": 1024,
            },
        )
        parser = StrOutputParser()

        return prompt | llm | parser

    def generate_analysis(self, article_hash: str) -> Dict[str, str]:
        """
        Runs the analysis loop.
        """
        results = {}
        logger.info("Starting initial summary.")

        # Build chain once
        try:
            chain = self._build_llm_chain()
        except Exception as e:
            logger.error("Failed to build LLM chain: %s", e)
            return {}

        for q in self.questions:
            # 1. RAG Retrieval
            chunks = self.rag_processor.search(q, k=4, article_hash=article_hash)
            context_text = "\n\n".join([doc.page_content for doc in chunks])

            if not context_text:
                logger.warning("No RAG context found for: %s", q)
                results[q] = "Data not found in paper."
                continue

            # 2. LLM Generation
            try:
                logger.info("Generating answer for: %s", q)
                answer = chain.invoke({"context": context_text, "question": q})
                results[q] = answer
            except Exception as e:
                logger.error("LLM error on question '%s': %s", q, e)
                results[q] = "Error generating answer."

        return results
