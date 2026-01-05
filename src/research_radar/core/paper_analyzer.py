import logging
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
        llm = get_chat_llm_client()
        parser = StrOutputParser()

        return prompt | llm | parser

    def generate_analysis(self, article_hash: str) -> Dict[str, str]:
        """
        Runs the analysis loop.
        """
        results = {}
        logger.info("Starting intial summary.")

        # Build chain once
        try:
            chain = self._build_llm_chain()
        except Exception as e:
            logger.error("Failed to build LLM chain: %s", e)
            return {}

        for question in self.questions:
            # 1. RAG Retrieval
            chunks = self.rag_processor.search(question, k=15, article_hash=article_hash)
            context_text = "\n\n".join([doc.page_content for doc in chunks])

            if not context_text:
                logger.warning("No RAG context found for: %s", question)
                results[question] = "Data not found in paper."
                continue

            # 2. LLM Generation
            try:
                logger.info("Generating answer for: %s", question)
                answer = chain.invoke({"context": context_text, "question": question})
                results[question] = answer
            except Exception as e:
                logger.error("LLM error on question '%s': %s", question, e)
                results[question] = "Error generating answer."

        return results

    @staticmethod
    def format_analysis(results: Dict[str, str]) -> str:
        """
        A helper function formatting the analysis to string a LLM can read.
        """
        logger.info("Starting formatting analysis")

        if not results:
            return "No analysis data available."

        formatted_analysis = ""
        for question, answer in results.items():
            formatted_analysis += f"Question: {question}\nAnswer: {answer}\n\n"

        logger.info("Analysis formatted sucssefully")
        return formatted_analysis

    def _get_summary_prompt_template_str(self) -> str:
        """Fetch the summary prompt template string from YAML."""
        template = get_prompt("paper_summary")
        template_str = template.get("paper_summary")

        if not template_str:
            raise NotImplementedError("Prompt template 'paper_summary' not found.")
        return template_str

    def generate_summary(self, results: Dict[str, str]):
        """
        Uses LLM in order to create a summary from the analysis.
        """
        context_string = self.format_analysis(results)
        logger.info("Generating summary from analysis.")

        try:
            template_str = self._get_summary_prompt_template_str()
        except Exception as exc:
            logger.error(f"Could not load summary prompt: {exc}")
            return "Could not load summary prompt"

        prompt = PromptTemplate(
            input_variables=["context_str"],
            template=template_str,
        )

        llm = get_chat_llm_client()
        parser = StrOutputParser()

        chain = prompt | llm | parser

        try:
            summary = chain.invoke({"context_str": context_string})
            return summary
        except Exception as exe:
            logger.error(f"Error generating summary: {exe}")
            return "Error generating summary"
