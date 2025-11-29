#by taha

# Week 2+: ArXiv API exceptions
class ArxivAPIException(Exception):
    """Base exception for arXiv API-related errors."""


class ArxivAPITimeoutError(ArxivAPIException):
    """Exception raised when arXiv API request times out."""


class ArxivAPIRateLimitError(ArxivAPIException):
    """Exception raised when arXiv API rate limit is exceeded."""


class ArxivParseError(ArxivAPIException):
    """Exception raised when arXiv API response parsing fails."""

# Week 2: PDF parsing exceptions 

class PDFDownloadException(Exception):
    """Base exception for PDF download-related errors."""

class PDFDownloadTimeoutError(PDFDownloadException):
    """Exception raised when PDF download times out."""


# Week 2+: Metadata fetching exceptions

class LLMException(Exception):
    """Base exception for LLM-related errors."""

class OllamaException(LLMException):
    """Exception raised for Ollama service errors."""


class OllamaConnectionError(OllamaException):
    """Exception raised when cannot connect to Ollama service."""


class OllamaTimeoutError(OllamaException):
    """Exception raised when Ollama service times out."""
