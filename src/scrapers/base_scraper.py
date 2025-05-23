"""
Base scraper class for all job platforms.
Provides common functionality and interface that all scrapers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
import logging
from urllib.parse import urljoin, urlencode
import re

from ..models.job import Job
from ..utils.logger import get_logger


class BaseScraper(ABC):
    """
    Abstract base class for all job platform scrapers.
    Defines the interface and common functionality for scraping job sites.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the scraper with configuration.
        
        Args:
            config: Dictionary containing scraper configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Rate limiting settings
        self.min_delay = config.get('min_delay', 1)
        self.max_delay = config.get('max_delay', 3)
        self.last_request_time = 0
        
        # Search settings
        self.max_pages = config.get('max_pages', 5)
        self.max_jobs_per_search = config.get('max_jobs_per_search', 50)
        
        # Filters
        self.location = config.get('location', '')
        self.keywords = config.get('keywords', [])
        self.remote_ok = config.get('remote_ok', True)
        self.min_salary = config.get('min_salary')
        self.max_salary = config.get('max_salary')
        
        # Platform-specific settings
        self.base_url = self.get_base_url()
        self.search_url = self.get_search_url()
        
        # Track processed job IDs to avoid duplicates
        self.processed_job_ids: Set[str] = set()
        
    @abstractmethod
    def get_base_url(self) -> str:
        """Return the base URL for the platform."""
        pass
    
    @abstractmethod
    def get_search_url(self) -> str:
        """Return the search URL for the platform."""
        pass
    
    @abstractmethod
    def build_search_params(self, keywords: List[str], location: str = None) -> Dict[str, Any]:
        """
        Build search parameters for the platform's search API/URL.
        
        Args:
            keywords: List of keywords to search for
            location: Location filter (optional)
            
        Returns:
            Dictionary of search parameters
        """
        pass
    
    @abstractmethod
    def parse_job_listing(self, job_element) -> Optional[Job]:
        """
        Parse a single job listing element into a Job object.
        
        Args:
            job_element: BeautifulSoup element or raw data containing job information
            
        Returns:
            Job object if parsing successful, None otherwise
        """
        pass
    
    @abstractmethod
    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific job.
        
        Args:
            job_url: URL to the job posting
            
        Returns:
            Dictionary containing detailed job information
        """
        pass
    
    def search_jobs(self, keywords: List[str], location: str = None, **kwargs) -> List[Job]:
        """
        Search for jobs on the platform.
        
        Args:
            keywords: List of keywords to search for
            location: Location filter (optional)
            **kwargs: Additional search parameters
            
        Returns:
            List of Job objects
        """
        self.logger.info(f"Starting job search on {self.__class__.__name__}")
        self.logger.info(f"Keywords: {keywords}, Location: {location}")
        
        jobs = []
        page = 1
        
        try:
            while page <= self.max_pages and len(jobs) < self.max_jobs_per_search:
                self.logger.info(f"Searching page {page}")
                
                # Apply rate limiting
                self._apply_rate_limit()
                
                # Get search results for current page
                page_jobs = self._search_page(keywords, location, page, **kwargs)
                
                if not page_jobs:
                    self.logger.info(f"No more jobs found on page {page}")
                    break
                
                # Filter and add jobs
                filtered_jobs = self._filter_jobs(page_jobs)
                jobs.extend(filtered_jobs)
                
                self.logger.info(f"Found {len(page_jobs)} jobs on page {page}, {len(filtered_jobs)} passed filters")
                
                page += 1
                
        except Exception as e:
            self.logger.error(f"Error during job search: {str(e)}")
            raise
        
        self.logger.info(f"Job search completed. Found {len(jobs)} total jobs")
        return jobs
    
    def _search_page(self, keywords: List[str], location: str, page: int, **kwargs) -> List[Job]:
        """
        Search for jobs on a specific page.
        
        Args:
            keywords: List of keywords to search for
            location: Location filter
            page: Page number to search
            **kwargs: Additional search parameters
            
        Returns:
            List of Job objects from the page
        """
        try:
            # Build search parameters
            search_params = self.build_search_params(keywords, location)
            search_params.update(kwargs)
            
            # Add page parameter
            search_params['page'] = page
            
            # Make request
            response = self._make_request(self.search_url, params=search_params)
            
            if response.status_code != 200:
                self.logger.warning(f"Search request failed with status {response.status_code}")
                return []
            
            # Parse job listings
            return self._parse_search_results(response.text)
            
        except Exception as e:
            self.logger.error(f"Error searching page {page}: {str(e)}")
            return []
    
    def _parse_search_results(self, html_content: str) -> List[Job]:
        """
        Parse search results HTML and extract job listings.
        
        Args:
            html_content: HTML content of search results page
            
        Returns:
            List of Job objects
        """
        jobs = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            job_elements = self._find_job_elements(soup)
            
            for element in job_elements:
                try:
                    job = self.parse_job_listing(element)
                    if job and job.external_id not in self.processed_job_ids:
                        jobs.append(job)
                        self.processed_job_ids.add(job.external_id)
                        
                except Exception as e:
                    self.logger.warning(f"Error parsing job listing: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error parsing search results: {str(e)}")
        
        return jobs
    
    @abstractmethod
    def _find_job_elements(self, soup: BeautifulSoup) -> List:
        """
        Find job listing elements in the search results page.
        
        Args:
            soup: BeautifulSoup object of the search results page
            
        Returns:
            List of job listing elements
        """
        pass
    
    def _filter_jobs(self, jobs: List[Job]) -> List[Job]:
        """
        Apply filters to job listings.
        
        Args:
            jobs: List of Job objects to filter
            
        Returns:
            List of filtered Job objects
        """
        filtered = []
        
        for job in jobs:
            if self._passes_filters(job):
                filtered.append(job)
        
        return filtered
    
    def _passes_filters(self, job: Job) -> bool:
        """
        Check if a job passes all configured filters.
        
        Args:
            job: Job object to check
            
        Returns:
            True if job passes all filters, False otherwise
        """
        # Remote work filter
        if self.remote_ok and not job.is_remote and not job.location.lower().find('remote') != -1:
            if self.location and job.location.lower().find(self.location.lower()) == -1:
                return False
        
        # Salary filters
        if self.min_salary and job.salary_min and job.salary_min < self.min_salary:
            return False
            
        if self.max_salary and job.salary_max and job.salary_max > self.max_salary:
            return False
        
        # Additional platform-specific filters can be implemented in subclasses
        return True
    
    def _make_request(self, url: str, params: Dict = None, **kwargs) -> requests.Response:
        """
        Make HTTP request with error handling and retry logic.
        
        Args:
            url: URL to request
            params: Query parameters
            **kwargs: Additional requests parameters
            
        Returns:
            Response object
        """
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30, **kwargs)
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                
                self.logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                time.sleep(retry_delay * (attempt + 1))
        
        raise Exception(f"Failed to make request after {max_retries} attempts")
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            delay = random.uniform(self.min_delay, self.max_delay)
            time.sleep(delay)
        
        self.last_request_time = time.time()
    
    def extract_text(self, element, selector: str = None, default: str = "") -> str:
        """
        Extract text from a BeautifulSoup element.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector (optional)
            default: Default value if text not found
            
        Returns:
            Extracted text or default value
        """
        try:
            if selector:
                target = element.select_one(selector)
                if target:
                    return target.get_text(strip=True)
            else:
                return element.get_text(strip=True)
        except Exception:
            pass
        
        return default
    
    def extract_link(self, element, selector: str = None, attr: str = 'href') -> str:
        """
        Extract link from a BeautifulSoup element.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector (optional)
            attr: Attribute to extract (default: 'href')
            
        Returns:
            Extracted link or empty string
        """
        try:
            if selector:
                target = element.select_one(selector)
                if target and target.has_attr(attr):
                    link = target[attr]
                    return urljoin(self.base_url, link)
            elif element.has_attr(attr):
                link = element[attr]
                return urljoin(self.base_url, link)
        except Exception:
            pass
        
        return ""
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        return text.strip()
    
    def extract_salary(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """
        Extract salary range from text.
        
        Args:
            text: Text containing salary information
            
        Returns:
            Tuple of (min_salary, max_salary)
        """
        if not text:
            return None, None
        
        # Common salary patterns
        patterns = [
            r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*-\s*R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            r'(\d{1,3}(?:\.\d{3})*)\s*-\s*(\d{1,3}(?:\.\d{3})*)',
            r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            r'(\d{1,3}(?:\.\d{3})*)\s*(?:mil|k)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:
                        min_sal = self._parse_salary_value(match.group(1))
                        max_sal = self._parse_salary_value(match.group(2))
                        return min_sal, max_sal
                    else:
                        salary = self._parse_salary_value(match.group(1))
                        return salary, salary
                except ValueError:
                    continue
        
        return None, None
    
    def _parse_salary_value(self, value: str) -> Optional[int]:
        """
        Parse a salary value string into an integer.
        
        Args:
            value: Salary value string
            
        Returns:
            Parsed salary value or None
        """
        if not value:
            return None
        
        # Remove common formatting
        value = value.replace('.', '').replace(',', '').replace('R$', '').strip()
        
        # Handle 'k' notation
        if value.lower().endswith('k'):
            value = value[:-1]
            multiplier = 1000
        elif value.lower().endswith('mil'):
            value = value[:-3]
            multiplier = 1000
        else:
            multiplier = 1
        
        try:
            return int(float(value) * multiplier)
        except ValueError:
            return None
    
    def get_platform_name(self) -> str:
        """Get the name of the platform."""
        return self.__class__.__name__.replace('Scraper', '')
    
    def close(self):
        """Clean up resources."""
        if self.session:
            self.session.close()
