#by taha
import time
from functools import cached_property
from pathlib import Path
from typing import Dict, List, Optional
from src.config import ArxivSettings

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
