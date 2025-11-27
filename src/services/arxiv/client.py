#by taha
import time
from functools import cached_property
from pathlib import Path
from typing import Dict, List, Optional
from src.config import ArxivSettings
from src.schemas.arxiv.paper import ArxivPaper

class ArxivClient:
    """Client for fetching papers from arXiv API"""
    def __init__(self,settings:ArxivSettings):
        self.__settings=settings
        #To track the time when client made last request for Rate limitting
        self._last_request_time:Optional[float]=None

    @cached_property
    def pdf_cache_dir(self)->Path:
        cache_dir=Path(self.__settings.pdf_cache_dir)
        cache_dir.mkdir(parents=True,exist_ok=True)
        return cache_dir
    
    @property
    def base_url(self)->str:
        return self.__settings.base_url
    
    @property
    def namespaces(self)->dict:
        return self.__settings.namespaces
    
    @property
    def rate_limit_delay(self)->float:
        return self.__settings.rate_limit_delay
    
    @property
    def timeout_seconds(self)->int:
        return self.__settings.timeout_seconds
    
    @property
    def max_results(self)->int:
        return self.__settings.max_results
    
    @property
    def search_category(self)->str:
        return self.__settings.search_category
    
    async def fetch_papers(
            self,
            max_results:Optional[int]=None, #(uses settings default if None)
            start:int=0,
            sort_by: str = "submittedDate",
            sort_order: str = "descending",
            from_date: Optional[str] = None,
            to_date: Optional[str] = None,

    )->List[ArxivPaper]: #List of ArxivPaper objects for the configured category
        if max_results is None:
            max_results = self.max_results

        #Build Search Category
        search_query = f"cat:{self.search_category}"

        #Add date filtering if provided
        if from_date or to_date:
            # Convert dates to arXiv format (YYYYMMDDHHMM) - use 0000 for start of day, 2359 for end
            date_from = f"{from_date}0000" if from_date else "*"
            date_to = f"{to_date}2359" if to_date else "*"
            # Use correct arXiv API syntax with + symbols
            search_query += f" AND submittedDate:[{date_from}+TO+{date_to}]"

        params = {
            "search_query": search_query,
            "start": start,
            "max_results": min(max_results, 2000),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        safe = ":+[]"  # Don't encode :, +, [, ] characters needed for arXiv queries
        url = f"{self.base_url}?{urlencode(params, quote_via=quote, safe=safe)}"


