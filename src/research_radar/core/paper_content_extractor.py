"""Module for extracting content from research papers."""

import logging
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

logger = logging.getLogger(__name__)


class PaperContentExtractor:  # pylint: disable=too-few-public-methods
    """
    A class to extract content from research paper.
    """

    def __init__(self, source: str):
        self.paper_url = source

    def extract_content(self) -> str:
        """
        Extract content from the research paper.
        :return: Markdown
        """

        logger.info("Extracting content for paper ID: %s", self.paper_url)

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False  # Disable OCR
        pipeline_options.do_table_structure = False  # Disable table visualisation
        pipeline_options.generate_page_images = (
            False  # Disable pages rendering as images
        )
        pipeline_options.generate_picture_images = False  # Disable figures extraction

        # Downloads detection model and recognition model from library
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options, backend=PyPdfiumDocumentBackend
                )
            }
        )

        result = converter.convert(self.paper_url)
        result_as_docling_document = result.document
        markdown_content = result_as_docling_document.export_to_markdown()

        logger.info(
            "Extraction finished for %s. Content length: %d chars.",
            self.paper_url,
            len(markdown_content),
        )
        return markdown_content
