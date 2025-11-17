import logging
from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)

class PaperContentExtractor:
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

        logger.info(f"Extracting content for paper ID: {self.paper_url}")

        """ Downloads detection model and recognition model from library """
        converter = DocumentConverter()
        
        result = converter.convert(self.paper_url)
        result_as_docling_document = result.document 
        markdown_content = result_as_docling_document.export_to_markdown()

        logger.info(f"Extraction finished for {self.paper_url}. Content length: {len(markdown_content)} chars.")
        return markdown_content
    

