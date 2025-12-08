import logging
from typing import Dict, List
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from research_radar.llm.client import get_chat_llm_client
from research_radar.llm.prompts import get_prompt
from research_radar.workflow.state import WorkflowState

logger = logging.getLogger(__name__)


class PaperRelevanceChecker:
    """
    A class to check the relevance of a paper based on its AI keywords
    against a list of required keywords.
    """

    def __init__(
        self, metadata: Dict, required_keywords: List[str], min_match_threshold: int = 1
    ):
        """
        Initializes the relevance checker.

        Args:
            metadata (Dict): The extracted paper metadata (must contain 'ai_keywords').
            required_keywords (List[str]): The keywords provided by the user/system.
            min_match_threshold (int): The minimum number of keyword matches required for relevance.
        """
        self.metadata = metadata
        self.required_keywords = required_keywords
        self.min_match_threshold = min_match_threshold
        if metadata is not None:
            self.paper_id = metadata.get("id", "N/A")
        else:
            self.paper_id = "N/A"

    def check_relevance(self, state: WorkflowState) -> bool:
        """
        Performs the relevance check.

        Returns:
            bool: True if the paper is relevant, False otherwise.
        """
        if not self.metadata or not self.required_keywords:
            logger.warning(
                "Relevance Check Error for paper %s: Missing metadata or required keywords.",
                self.paper_id,
            )
            return False

        # --- STEP 1: Process and Normalize Keywords ---

        ai_keywords_list: List[str] = self.metadata.get("ai_keywords", [])

        if not ai_keywords_list:
            logger.info("No AI keywords found. Proceeding to LLM check.")
            return self.llm_check(state)

        ai_keywords_set = {
            k.strip().lower() for k in ai_keywords_list if k and k.strip()
        }
        required_keywords_set = {
            k.strip().lower() for k in self.required_keywords if k.strip()
        }
        # --- STEP 2: Find Intersection and Match Count ---
        intersection = ai_keywords_set.intersection(required_keywords_set)
        match_count = len(intersection)
        is_relevant = match_count >= self.min_match_threshold

        logger.info(
            "Paper %s Keyword Match: %s (Found: %s, Required: %s)",
            self.paper_id,
            is_relevant,
            match_count,
            self.min_match_threshold,
        )

        if is_relevant:
            return True

        # --- STEP 2: LLM FALLBACK CHECK ---
        logger.info("Keyword match failed. Proceeding to LLM fallback check.")
        return self.llm_check(state)

    @staticmethod
    def _get_prompt_template_str() -> str:
        """Fetch the prompt template string for paper relevance checking."""
        template = get_prompt("paper_relevance_check")
        template_str = template.get("paper_relevance_check")

        if not template_str:
            raise NotImplementedError(
                "Prompt template 'paper_relevance_check' not found."
            )

        return template_str

    def _build_llm_chain(self) -> RunnableSequence:
        """
        Build a LangChain RunnableSequence:
            PromptTemplate -> Chat LLM -> JsonOutputParser
        """
        template_str = self._get_prompt_template_str()

        prompt = PromptTemplate(
            input_variables=["required_keywords", "abstract_text"],
            template=template_str,
        )

        llm = get_chat_llm_client()
        parser = JsonOutputParser()

        # chaining: prompt | llm | parser
        return prompt | llm | parser

    def llm_check(self, state: WorkflowState) -> bool:
        """
        Performs the LLM relevance check (returns only True/False).
        """
        metadata = state.get("metadata")
        required_keywords = state.get("required_keywords", [])
        abstract_text = metadata.get("summary") if metadata else None
        paper_id = state.get("paper_id")

        if metadata is None or not abstract_text:
            logger.warning(
                "LLM Check Error: Metadata or abstract missing for paper %s. Cannot proceed.",
                paper_id,
            )
            return False

        logger.info("Executing LLM relevance check using the paper's Abstract.")

        try:
            chain = self._build_llm_chain()
        except NotImplementedError as exc:
            logger.error("LLM Check Error: %s", exc)
            return False

        try:
            result = chain.invoke(
                {
                    "required_keywords": ", ".join(required_keywords),
                    "abstract_text": abstract_text,
                }
            )

            is_relevant = bool(result.get("is_relevant"))
            reason = result.get("reason", "")

            logger.info("Reason: %s", reason)
            logger.info("Decision: %s", is_relevant)

            return is_relevant

        except Exception as exc:
            logger.error(
                "LLM JSON relevance check failed for paper %s. Error: %s",
                paper_id,
                exc,
            )
            return False

    # End of paper_relevance_checker.py
