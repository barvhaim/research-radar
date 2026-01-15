"""YouTube video transcript extraction using yt-dlp."""

import glob
import logging
import os
import re
import time
from typing import List
import yt_dlp

logger = logging.getLogger(__name__)


class YouTubeContentExtractor:
    """A class to extract content (transcript) from a YouTube video."""

    MAX_RETRIES = 3
    RETRY_DELAY = 2.0

    def __init__(self, source: str):
        """:param source: The YouTube Video ID"""
        self.video_id = source
        self.video_url = f"https://www.youtube.com/watch?v={source}"

    def extract_content(self) -> str:
        """
        Extract content (transcript) from the YouTube video.
        :return: Transcript text
        """
        logger.info("Extracting content for video ID: %s", self.video_id)

        transcript = self._get_video_transcript()

        if not transcript:
            raise ValueError(f"Failed to extract transcript for video: {self.video_id}")

        logger.info(
            "Extraction finished for %s. Content length: %d chars.",
            self.video_id,
            len(transcript),
        )
        return transcript

    def _get_video_transcript(self) -> str:
        """Internal logic to download and parse subtitles."""
        retries = 0
        subtitle_files = []

        while retries <= self.MAX_RETRIES:
            try:
                # Configure yt-dlp options (Silent & Efficient)
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "skip_download": True,
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                    "subtitleslangs": ["en", "en-US"],
                    "subtitlesformat": "vtt",
                    "outtmpl": "%(id)s.%(ext)s",
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(self.video_url, download=True)

                    # Check for requested subtitles
                    if "requested_subtitles" in info_dict:
                        subtitle_info = info_dict["requested_subtitles"]
                        # Prioritize explicit English, then auto-generated
                        lang = next(
                            (l for l in ["en", "en-US"] if l in subtitle_info), None
                        )

                        if lang:
                            subtitle_file = f"{self.video_id}.{lang}.vtt"
                            subtitle_files.append(subtitle_file)

                            # Parse the VTT file
                            return self._parse_vtt_file(subtitle_file, subtitle_files)

                self._cleanup_files(subtitle_files)
                return ""

            except Exception as e:
                retries += 1
                logger.warning("Retry %d/%d failed: %s", retries, self.MAX_RETRIES, e)
                time.sleep(self.RETRY_DELAY)

        self._cleanup_files(subtitle_files)
        return ""

    def _parse_vtt_file(self, file_path: str, files_to_clean: List[str]) -> str:
        """Reads and cleans VTT subtitle format."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            lines = content.split("\n")
            transcript = []
            capture = False

            for line in lines:
                # VTT parsing logic
                if "-->" in line:
                    capture = True
                    continue
                if (
                    line.strip()
                    in ["WEBVTT", "Kind: captions", "Language: en", "Language: en-US"]
                    or not line.strip()
                ):
                    continue

                if capture and line.strip():
                    clean_line = self._extract_sentence(line.strip())
                    transcript.append(clean_line)

            self._cleanup_files(files_to_clean)
            return " ".join(transcript)

        except Exception as e:
            logger.error("Error parsing VTT: %s", e)
            self._cleanup_files(files_to_clean)
            return ""

    def _extract_sentence(self, line: str) -> str:
        """Removes VTT timestamps/tags like <c>."""
        first_word = line.split("<")[0].strip()
        words = re.findall(r"<c>\s?([^<]+)</c>", line)
        full_sentence = " ".join([first_word] + [w.strip() for w in words])
        return full_sentence

    def _cleanup_files(self, files: List[str]):
        """Deletes temporary subtitle files."""
        # Clean up explicitly tracked files
        for file in files:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    logger.debug("Removed file: %s", file)
            except Exception as e:
                logger.warning("Failed to remove file %s: %s", file, e)

        # Also clean up any VTT files matching the video ID pattern
        # yt-dlp may create files like: video_id.en.vtt, video_id.en-US.vtt, etc.
        vtt_patterns = [
            f"{self.video_id}*.vtt",
            f"{self.video_id}*.vtt.part",
        ]
        for pattern in vtt_patterns:
            for vtt_file in glob.glob(pattern):
                try:
                    os.remove(vtt_file)
                    logger.debug("Cleaned up VTT file: %s", vtt_file)
                except Exception as e:
                    logger.warning("Failed to remove VTT file %s: %s", vtt_file, e)
