import logging
from typing import Dict, List
from research_radar.llm.prompts import get_prompt
from langchain_core.output_parsers import JsonOutputParser

from langchain_core.messages import HumanMessage
from research_radar.llm.client import get_chat_llm_client
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
                f"Relevance Check Error for paper %s: Missing metadata or required keywords.",
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
            f"Paper %s Keyword Match: %s (Found: %s, Required: %s)",
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

    def llm_check(self, state: WorkflowState) -> bool:
        """
        Performs the LLM relevance check (returns only True/False).
        """
        metadata = state.get("metadata")
        required_keywords = state.get("required_keywords", [])
        abstract_text = metadata.get("summary")
        paper_id = state.get("paper_id")

        if metadata is None or not abstract_text:
            logger.warning(
                f"LLM Check Error: Metadata or abstract missing for paper %s. Cannot proceed.",
                paper_id,
            )
            return False

        logger.info("Executing LLM relevance check using the paper's Abstract.")

        template = get_prompt("paper_relevance_check")
        template = template.get("paper_relevance_check")

        if not template:
            logger.error(
                "LLM Check Error: Prompt template 'paper_relevance_check' not found."
            )
            return False

        rendered_prompt = template.format(
        required_keywords=", ".join(required_keywords),
        abstract_text=abstract_text,
    )

        try:
            llm_client = get_chat_llm_client()
            response = llm_client.invoke([HumanMessage(content=rendered_prompt)])
            raw_text = response.content.strip()

            # Parse JSON
            parser = JsonOutputParser()
            parsed = parser.parse(raw_text)
            is_relevant = bool(parsed.get("is_relevant"))
            reason = parsed.get("reason", "")

            logger.info(f"Reason: {reason}")
            logger.info(f"Decision: {is_relevant}")


            return is_relevant

        except Exception as e:
            logger.error(
                "LLM JSON relevance check failed for paper %s. Error: %s",
                paper_id,
                e,
            )
            return False


    # End of paper_relevance_checker.py
