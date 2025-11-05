import logging
import pandas as pd
from time import time
from docling.document_converter import DocumentConverter
from docling.datamodel.extraction import DoclingDocument

logger = logging.getLogger(__name__)

class PaperContentExtractor:
    """
    A class to extract *content* from research paper.
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
        
        print("Converting")
        start_time = time()
        result = converter.convert(self.paper_url)

        doc = result.document 
        end_time = time() - start_time
        print(f"Conversion done in {end_time:.2f} seconds")
        
        markdown_ver = doc.export_to_markdown()
        
        return markdown_ver
    

