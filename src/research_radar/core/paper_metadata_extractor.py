"""Module for extracting metadata from research papers via HuggingFace API."""

import logging
from typing import Dict, Optional, Any
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class PaperMetadataExtractor:  # pylint: disable=too-few-public-methods
    """
    A class to extract metadata from research paper.
    """

    # --- GLOBAL CONFIGURATION ---
    HUGGINGFACE_PAPERS_WEB_BASE_URL = "https://huggingface.co/papers/"
    HUGGINGFACE_SINGLE_PAPER_API_BASE_URL = "https://huggingface.co/api/papers/"
    ARXIV_PDF_BASE_URL = "https://arxiv.org/pdf/"

    def __init__(self, paper_id: str):
        self.paper_id = paper_id
        self.api_url = f"{self.HUGGINGFACE_SINGLE_PAPER_API_BASE_URL}{paper_id}"

    def extract_metadata(self) -> Optional[Dict]:  # pylint: disable=too-many-locals
        """
        Extract metadata from the research paper.
        :return:
        """
        logger.info("Extracting metadata for paper ID: %s", self.paper_id)

        # --- STEP 1: FETCHING DATA FROM THE API ---
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()

            raw_data = response.json()

            paper = raw_data.get("paper", raw_data)

            if not paper.get("id"):
                logger.warning(
                    "Processing Error: API returned incomplete data for %s. Returning None.",
                    self.paper_id,
                )
                return None

            logger.info("Raw metadata fetched successfully.")

        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning(f"Hugging Face failed ({e}). Attempting ArXiv Fallback...")
            # If HF fails, we call the new fallback function
            return self._fetch_from_arxiv_fallback()
        
        # --- STEP 2: PROCESSING AND FLATTENING METADATA ---

        hf_paper_url = f"{self.HUGGINGFACE_PAPERS_WEB_BASE_URL}{self.paper_id}"
        arxiv_pdf_url = f"{self.ARXIV_PDF_BASE_URL}{self.paper_id}"
        github_repo = paper.get("githubRepo")

        authors_list = [
            author.get("name")
            for author in paper.get("authors", [])
            if author.get("name")
        ]
        authors_string = ", ".join(authors_list)

        ai_keywords_list = paper.get("ai_keywords", [])

        paper_upvotes = paper.get("upvotes")

        submitted_by_raw = raw_data.get("submittedBy", {})
        submitter_detail = paper.get("submittedOnDailyBy", {})
        submitter_source_final = submitter_detail or submitted_by_raw

        submitter_follower_count = (
            submitted_by_raw.get("followerCount")
            or submitter_detail.get("followerCount")
            or 0
        )
        summary_text = paper.get("summary")

        paper_info: Dict[str, Any] = {
            "id": self.paper_id,
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
            "ai_keywords": ai_keywords_list,
            "summary": summary_text,
            "submitter_fullname": submitter_source_final.get("fullname"),
            "submitter_username": submitter_source_final.get("name")
            or submitter_source_final.get("user"),
            "submitter_isPro": submitter_source_final.get("isPro"),
            "submitter_followerCount": submitter_follower_count,
        }

        return paper_info
    
    def _fetch_from_arxiv_fallback(self) -> Optional[Dict]:
        """
        Fallback: Query official ArXiv API if Hugging Face fails.
        """
        arxiv_api_url = "http://export.arxiv.org/api/query"
        
        try:
            # Query ArXiv
            response = requests.get(arxiv_api_url, params={"id_list": self.paper_id}, timeout=10)
            if response.status_code != 200:
                return None

            # Parse XML
            root = ET.fromstring(response.content)
            # The namespace often breaks finding items, so we search generically
            entry = root.find("{http://www.w3.org/2005/Atom}entry")
            
            if entry is None:
                return None

            # Extract Data manually from XML
            title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip().replace("\n", " ")
            summary = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip().replace("\n", " ")
            published = entry.find("{http://www.w3.org/2005/Atom}published").text
            
            # Get all authors
            authors = [
                author.find("{http://www.w3.org/2005/Atom}name").text 
                for author in entry.findall("{http://www.w3.org/2005/Atom}author")
            ]

            logger.info("Successfully fetched metadata from ArXiv Fallback.")

            # Return standardized dictionary
            return {
                "id": self.paper_id,
                "title": title,
                "publishedAt": published,
                "hf_paper_url": None, # Not available
                "arxiv_pdf_url": f"https://arxiv.org/pdf/{self.paper_id}.pdf",
                "github_repo": None,
                "upvotes": 0,
                "authors_names": ", ".join(authors),
                "ai_summary": None,
                "ai_keywords": [],
                "summary": summary,
                "source": "arxiv_official"
            }

        except Exception as e:
            logger.error(f"ArXiv Fallback also failed: {e}")
            return None
