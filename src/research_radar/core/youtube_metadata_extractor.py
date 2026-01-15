"""YouTube video metadata extraction using yt-dlp."""

import logging
from typing import Any, Dict, Optional

import yt_dlp

logger = logging.getLogger(__name__)


class YouTubeMetadataExtractor:  # pylint: disable=too-few-public-methods
    """A class to extract metadata from YouTube videos."""

    YOUTUBE_BASE_WATCH_URL = "https://www.youtube.com/watch?v="

    def __init__(self, video_id: str):
        self.video_id = video_id
        self.video_url = f"{self.YOUTUBE_BASE_WATCH_URL}{video_id}"

    def extract_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from the YouTube video.
        :return: Dictionary
        """
        logger.info("Extracting metadata for video ID: %s", self.video_id)

        try:
            # Configure yt-dlp to be fast and silent
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,  # Only metadata here
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.video_url, download=False)

            if not info:
                logger.warning(
                    "Processing Error: yt-dlp returned no data for %s. Returning None.",
                    self.video_id,
                )
                return None

            logger.info("Raw metadata fetched successfully.")

        except Exception as e:
            logger.error(
                "Fetch Error: Could not retrieve data for %s. Error: %s",
                self.video_id,
                e,
            )
            return None

        # Map Channel -> Author
        channel_name = info.get("uploader") or info.get("channel") or "Unknown Channel"

        # Map Tags -> AI Keywords
        tags = info.get("tags", [])

        # Map Description -> Summary
        description = info.get("description", "")

        # Map Likes -> Upvotes
        like_count = info.get("like_count", 0)
        view_count = info.get("view_count", 0)

        # Map Upload Date -> PublishedAt
        upload_date = info.get("upload_date")

        # Flattened Dictionary matching PaperMetadataExtractor schema
        video_info: Dict[str, Any] = {
            "id": self.video_id,
            "title": info.get("title"),
            "publishedAt": upload_date,
            "submittedOnDailyAt": upload_date,
            "hf_paper_url": self.video_url,
            "arxiv_pdf_url": self.video_url,
            "github_repo": None,
            "upvotes": like_count,
            "authors_names": channel_name,
            "ai_summary": None,
            "ai_keywords": tags,
            "summary": description,
            "submitter_fullname": channel_name,
            "submitter_username": info.get("uploader_id"),
            "submitter_isPro": False,
            "submitter_followerCount": info.get("channel_follower_count", 0),
            # Expending keys
            "view_count": view_count,
            "duration": info.get("duration"),
            "source_type": "youtube",
        }

        return video_info
