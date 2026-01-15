"""YouTube video information and transcript extraction utilities."""

import logging
import json
import os
import re
import time
import yt_dlp


logger = logging.getLogger(__name__)
MAX_RETRIES = 10
RETRY_DELAY = 5.0


def get_youtube_video_info(url: str) -> str:
    """
    Gets information about a YouTube video.

    :param url: The YouTube video URL.
    :returns: A JSON string containing video information (id, title, channel, etc.)
    """

    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

            video_info = {
                "title": info.get("title", ""),
                "channel": info.get("channel", ""),
                "upload_date": info.get("upload_date", ""),
                "duration": info.get("duration", 0),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "id": info.get("id", ""),
                "url": url,
            }

            return json.dumps(video_info)

    except Exception as e:
        return "Failed to retrieve video information: " + str(e)


def _extract_sentence(line):
    # Get the initial word before any timestamp
    first_word = line.split("<")[0].strip()

    # Find all words inside <c>...</c>
    words = re.findall(r"<c>\s?([^<]+)</c>", line)

    # Combine first word with the rest
    full_sentence = " ".join([first_word] + [w.strip() for w in words])
    return full_sentence


def get_video_transcript(  # pylint: disable=too-many-locals,too-many-statements
    video_id: str,
) -> str:
    """
    Transcribes the audio from a YouTube video using its ID.

    :param video_id: The YouTube video ID.
    :returns: The transcription of the YouTube video.
    """
    logger.info("Transcribing video with ID: %s", video_id)
    retries = 0
    subtitle_files = []  # Track files to clean up later

    while retries <= MAX_RETRIES:
        try:
            # Configure yt-dlp to be completely quiet and redirect all output
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "no_color": True,
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en", "en-US"],
                "subtitlesformat": "vtt",
                "outtmpl": "%(id)s.%(ext)s",
                # Redirect all output to devnull to prevent stdout pollution
                "noprogress": True,
                "logger": logging.getLogger("yt_dlp_silent"),
            }

            # Configure a silent logger for yt-dlp
            yt_dlp_logger = logging.getLogger("yt_dlp_silent")
            yt_dlp_logger.setLevel(
                logging.CRITICAL + 1
            )  # Above CRITICAL to suppress all messages
            yt_dlp_logger.addHandler(logging.NullHandler())

            # Rest of the function remains the same
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                info_dict = ydl.extract_info(video_url, download=True)

                logger.debug("Extracted info for video %s: %s", video_id, info_dict)
                if not info_dict:
                    return f"Failed to extract info for video {video_id}"

                if (
                    "requested_subtitles" in info_dict
                    and info_dict["requested_subtitles"]
                ):
                    subtitle_info = info_dict["requested_subtitles"]
                    lang = next(
                        (lang for lang in ["en", "en-US"] if lang in subtitle_info),
                        None,
                    )

                    if lang:
                        # The subtitle file is downloaded locally
                        subtitle_file = f"{video_id}.{lang}.vtt"
                        subtitle_files.append(subtitle_file)  # Add to clean up list

                        try:
                            with open(subtitle_file, "r", encoding="utf-8") as file:
                                content = file.read()

                                # Basic parsing of VTT format
                                # Skip header
                                lines = content.split("\n")
                                transcript = []
                                capture = False

                                skip_patterns = {
                                    "WEBVTT",
                                    "Kind: captions",
                                    "Language: en-US",
                                    "Language: en",
                                }
                                for line in lines:
                                    stripped = line.strip()
                                    # Skip timing lines and empty lines
                                    if (
                                        "-->" in line
                                        or not stripped
                                        or stripped in skip_patterns
                                    ):
                                        capture = True
                                        continue

                                    # If we've started capturing and line has content
                                    if capture and stripped:
                                        # Extract the sentence from the line
                                        parsed_line = _extract_sentence(stripped)
                                        transcript.append(parsed_line.strip())

                                # Log before cleanup
                                logger.info(
                                    "Transcript assembly complete. Found %d lines",
                                    len(transcript),
                                )
                                logger.info("Starting file cleanup...")

                                # Clean up before returning
                                _cleanup_files(subtitle_files)

                                logger.info(
                                    "File cleanup complete, preparing to return transcript"
                                )
                                final_transcript = " ".join(transcript)
                                logger.info(
                                    "Final transcript length: %d chars",
                                    len(final_transcript),
                                )

                                return final_transcript

                        except Exception as e:
                            logger.error("Error processing subtitle file: %s", e)
                            _cleanup_files(subtitle_files)
                            return f"Error reading subtitle file: {str(e)}"

                _cleanup_files(subtitle_files)
                return f"No English subtitles found for video {video_id}"

        except Exception as e:
            retries += 1
            if retries <= MAX_RETRIES:
                # Wait before retrying
                logger.warning(
                    "Attempt %d failed: %s. Retrying in %s seconds...",
                    retries,
                    e,
                    RETRY_DELAY,
                )
                time.sleep(RETRY_DELAY)
                continue
            _cleanup_files(subtitle_files)
            return f"Failed to transcribe the video after {MAX_RETRIES} attempts: {e}"

    _cleanup_files(subtitle_files)
    return "Failed to transcribe the video after maximum retries."


def _cleanup_files(files):
    """
    Removes the specified files from disk.

    :param files: List of file paths to remove.
    """
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
                logger.debug("Removed file: %s", file)
        except Exception as e:
            logger.warning("Failed to remove file %s: %s", file, e)
