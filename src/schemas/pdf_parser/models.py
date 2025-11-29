#by taha

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


#PDF parser types
class ParserType(str, Enum):
    
    DOCLING = "docling"
    GROBID = "grobid"  # For future use


#Represents a section of a paper
class PaperSection(BaseModel):

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    level: int = Field(default=1, description="Section hierarchy level")

#Represents a figure in a paper
class PaperFigure(BaseModel):

    caption: str = Field(..., description="Figure caption")
    id: str = Field(..., description="Figure identifier")

Represents a table in a paper
class PaperTable(BaseModel):

    caption: str = Field(..., description="Table caption")
    id: str = Field(..., description="Table identifier")

#PDF-specific content extracted by parsers like Docling
class PdfContent(BaseModel):

    sections: List[PaperSection] = Field(default_factory=list, description="Paper sections")
    figures: List[PaperFigure] = Field(default_factory=list, description="Figures")
    tables: List[PaperTable] = Field(default_factory=list, description="Tables")
    raw_text: str = Field(..., description="Full extracted text")
    references: List[str] = Field(default_factory=list, description="References")
    parser_used: ParserType = Field(..., description="Parser used for extraction")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Parser metadata")

#Paper metadata from arXiv API
class ArxivMetadata(BaseModel):

    title: str = Field(..., description="Paper title from arXiv")
    authors: List[str] = Field(..., description="Authors from arXiv")
    abstract: str = Field(..., description="Abstract from arXiv")
    arxiv_id: str = Field(..., description="arXiv identifier")
    categories: List[str] = Field(default_factory=list, description="arXiv categories")
    published_date: str = Field(..., description="Publication date")
    pdf_url: str = Field(..., description="PDF download URL")

#Complete paper data combining arXiv metadata and PDF content
class ParsedPaper(BaseModel):

    arxiv_metadata: ArxivMetadata = Field(..., description="Metadata from arXiv API")
    pdf_content: Optional[PdfContent] = Field(None, description="Content extracted from PDF")
