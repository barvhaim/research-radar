import logging
from typing import Dict, List

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
            self.paper_id = metadata.get("arxiv_id", "N/A")
        else:
            self.paper_id = "N/A"

    def check_relevance(self) -> bool:
        """
        Performs the relevance check.

        Returns:
            bool: True if the paper is relevant, False otherwise.
        """
        if not self.metadata or not self.required_keywords:
            logger.warning(
                f"Relevance Check Error for paper {self.paper_id}: Missing metadata or required keywords."
            )
            return False

        # --- STEP 1: Process and Normalize Keywords ---

        ai_keywords_list: List[str] = self.metadata.get("ai_keywords", [])

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

        # --- STEP 3: Logging and Result ---
        logger.info(f"Paper {self.paper_id} Relevance Check Results:")
        logger.info(f"\tRequired Keywords: {self.required_keywords}")
        logger.info(f"\tPaper AI Keywords: {ai_keywords_set}")
        logger.info(f"\tMatches Found: {match_count} ({', '.join(intersection)})")
        logger.info(f"\tMinimum Required Matches: {self.min_match_threshold}")
        logger.info(f"\tIs Relevant: {is_relevant}")

        return is_relevant


# End of paper_relevance_checker.py
