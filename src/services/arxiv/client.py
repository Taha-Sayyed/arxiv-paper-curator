#by taha
import time
import asyncio
import httpx
import logging
import xml.etree.ElementTree as ET




from urllib.parse import quote, urlencode
from functools import cached_property
from pathlib import Path
from typing import Dict, List, Optional
from src.config import ArxivSettings
from src.schemas.arxiv.paper import ArxivPaper
from src.exceptions import ArxivAPIException, ArxivAPITimeoutError, ArxivParseError, PDFDownloadException, PDFDownloadTimeoutError


logger = logging.getLogger(__name__)


class ArxivClient:
    """Client for fetching papers from arXiv API"""
    def __init__(self,settings:ArxivSettings):
        self._settings=settings
        #To track the time when client made last request for Rate limitting
        self._last_request_time:Optional[float]=None

    @cached_property
    def pdf_cache_dir(self)->Path:
        cache_dir=Path(self._settings.pdf_cache_dir)
        cache_dir.mkdir(parents=True,exist_ok=True)
        return cache_dir
    
    @property
    def base_url(self)->str:
        return self._settings.base_url
    
    @property
    def namespaces(self)->dict:
        return self._settings.namespaces
    
    @property
    def rate_limit_delay(self)->float:
        return self._settings.rate_limit_delay
    
    @property
    def timeout_seconds(self)->int:
        return self._settings.timeout_seconds
    
    @property
    def max_results(self)->int:
        return self._settings.max_results
    
    @property
    def search_category(self)->str:
        return self._settings.search_category
    
    async def fetch_papers(
            self,
            max_results:Optional[int]=None, #(uses settings default if None)
            start:int=0,
            sort_by: str = "submittedDate",
            sort_order: str = "descending",
            from_date: Optional[str] = None, #Filter papers submitted after this date (format: YYYYMMDD)
            to_date: Optional[str] = None, #Filter papers submitted before this date (format: YYYYMMDD)

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

        try:
            logger.info(f"Fetching {max_results} {self.search_category} papers from arXiv")

            # Add rate limiting delay between all requests (arXiv recommends 3 seconds)
            if self._last_request_time is not None:
                time_since_last = time.time() - self._last_request_time
                if time_since_last < self.rate_limit_delay:
                    sleep_time = self.rate_limit_delay - time_since_last
                    await asyncio.sleep(sleep_time)

            self._last_request_time = time.time()

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url)
                response.raise_for_status()
                xml_data = response.text

            papers = self._parse_response(xml_data)
            logger.info(f"Fetched {len(papers)} papers")

            return papers

        except httpx.TimeoutException as e:
            logger.error(f"arXiv API timeout: {e}")
            raise ArxivAPITimeoutError(f"arXiv API request timed out: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"arXiv API HTTP error: {e}")
            raise ArxivAPIException(f"arXiv API returned error {e.response.status_code}: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch papers from arXiv: {e}")
            raise ArxivAPIException(f"Unexpected error fetching papers from arXiv: {e}")

    async def fetch_papers_with_query(
        self,
        search_query: str,
        max_results: Optional[int] = None,
        start: int = 0,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> List[ArxivPaper]: #Fetch papers from arXiv using a custom search query
        if max_results is None:
            max_results = self.max_results
        
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": min(max_results, 2000),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        safe = ":+[]*"  # Don't encode :, +, [, ], *, characters needed for arXiv queries
        url = f"{self.base_url}?{urlencode(params, quote_via=quote, safe=safe)}"

        #Add rate limitting (arXiv recommends 3 seconds)

        try:
            # Add rate limiting delay between all requests (arXiv recommends 3 seconds)
            if self._last_request_time is not None:
                time_since_last = time.time() - self._last_request_time
                if time_since_last < self.rate_limit_delay:
                    sleep_time = self.rate_limit_delay - time_since_last
                    await asyncio.sleep(sleep_time)

            self._last_request_time = time.time()

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url)
                response.raise_for_status()
                xml_data = response.text

            papers = self._parse_response(xml_data)
            logger.info(f"Query returned {len(papers)} papers")

            return papers

        except httpx.TimeoutException as e:
            logger.error(f"arXiv API timeout: {e}")
            raise ArxivAPITimeoutError(f"arXiv API request timed out: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"arXiv API HTTP error: {e}")
            raise ArxivAPIException(f"arXiv API returned error {e.response.status_code}: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch papers from arXiv: {e}")
            raise ArxivAPIException(f"Unexpected error fetching papers from arXiv: {e}")
        
        #arXiv paper ID (e.g., "2507.17748v1" or "2507.17748")

    async def fetch_paper_by_id(self, arxiv_id: str) -> Optional[ArxivPaper]:
        # Clean the arXiv ID (remove version if needed for search)
        clean_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
        params = {"id_list": clean_id, 
                  "max_results": 1}
        
        safe = ":+[]*"  # Don't encode :, +, [, ], *, characters needed for arXiv queries

        url = f"{self.base_url}?{urlencode(params, quote_via=quote, safe=safe)}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                xml_data = response.text

            papers = self._parse_response(xml_data)

            if papers:
                return papers[0]
            else:
                logger.warning(f"Paper {arxiv_id} not found")
                return None

        except httpx.TimeoutException as e:
            logger.error(f"arXiv API timeout for paper {arxiv_id}: {e}")
            raise ArxivAPITimeoutError(f"arXiv API request timed out for paper {arxiv_id}: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"arXiv API HTTP error for paper {arxiv_id}: {e}")
            raise ArxivAPIException(f"arXiv API returned error {e.response.status_code} for paper {arxiv_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch paper {arxiv_id} from arXiv: {e}")
            raise ArxivAPIException(f"Unexpected error fetching paper {arxiv_id} from arXiv: {e}")
        

        







