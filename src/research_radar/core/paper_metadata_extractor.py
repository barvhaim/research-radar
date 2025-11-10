import logging
from typing import Dict, Optional, Any
import requests


logger = logging.getLogger(__name__)

# --- GLOBAL CONFIGURATION ---
HUGGINGFACE_PAPER_BASE_URL = "https://huggingface.co/papers/"
ARXIV_PDF_BASE_URL = "https://arxiv.org/pdf/"
SINGLE_PAPER_API_BASE_URL = "https://huggingface.co/api/papers/"


class PaperMetadataExtractor:
    """
    A class to extract metadata from research paper.
    """

    def __init__(self, paper_id: str):
        self.paper_id = paper_id
        self.API_URL = f"{SINGLE_PAPER_API_BASE_URL}{paper_id}"

    def extract_metadata(self) -> Optional[Dict]:
        """
        Extract metadata from the research paper.
        :return:
        """
        logger.info(f"Extracting metadata for paper ID: {self.paper_id}")

        # --- STEP 1: FETCHING DATA FROM THE API ---
        try:
            response = requests.get(self.API_URL)
            response.raise_for_status()

            raw_data = response.json()

            paper = raw_data.get("paper", raw_data)

            if not (paper.get("id") or paper.get("arxivId")):
                logger.warning(
                    f"Processing Error: API returned incomplete data for {self.arxiv_id}. Returning None."
                )
                return None

            logger.info("Raw metadata fetched successfully.")

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Fetch Error: Could not retrieve data for {self.paper_id}. Error: {e}"
            )
            return None
        # --- STEP 2: PROCESSING AND FLATTENING METADATA ---

        arxiv_id = self.paper_id
        hf_paper_url = f"{HUGGINGFACE_PAPER_BASE_URL}{arxiv_id}"
        arxiv_pdf_url = f"{ARXIV_PDF_BASE_URL}{arxiv_id}"
        github_repo = paper.get("githubRepo")

        authors_list = [
            author.get("name")
            for author in paper.get("authors", [])
            if author.get("name")
        ]
        authors_string = ", ".join(authors_list)

        ai_keywords_list = paper.get("ai_keywords", [])
        ai_keywords_string = " | ".join(ai_keywords_list)

        paper_upvotes = paper.get("upvotes")

        submitted_by_raw = raw_data.get("submittedBy", {})
        submitter_detail = paper.get("submittedOnDailyBy", {})
        submitter_source_final = submitter_detail or submitted_by_raw

        submitter_follower_count = submitted_by_raw.get(
            "followerCount"
        ) or submitter_detail.get("followerCount")

        paper_info: Dict[str, Any] = {
            "arxiv_id": arxiv_id,
            "title": paper.get("title"),
            "publishedAt": paper.get("publishedAt"),
            "submittedOnDailyAt": paper.get("submittedOnDailyAt")
            or raw_data.get("submittedOnDailyAt"),
            "hf_paper_url": hf_paper_url,
            "arxiv_pdf_url": arxiv_pdf_url,
            "github_repo": github_repo,
            "upvotes": paper_upvotes,
            "authors_names": authors_string,
            "ai_summary": paper.get("ai_summary"),
            "ai_keywords": ai_keywords_string,
            "submitter_fullname": submitter_source_final.get("fullname"),
            "submitter_username": submitter_source_final.get("name")
            or submitter_source_final.get("user"),
            "submitter_isPro": submitter_source_final.get("isPro"),
            "submitter_followerCount": submitter_follower_count,
        }

        return paper_info
