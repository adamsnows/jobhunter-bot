"""
LinkedIn Jobs scraper using web scraping only.
Scrapes job listings from LinkedIn Jobs public pages.
"""

from typing import List, Dict, Any, Optional
import json
import re
import time
import random
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

from .base_scraper import BaseScraper
from ..models.job import Job, JobSource, JobStatus
from ..utils.logger import get_logger


class LinkedInScraper(BaseScraper):
    """
    LinkedIn Jobs scraper using web scraping only.
    Uses undetected Chrome driver to avoid bot detection.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LinkedIn scraper.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.logger = get_logger(__name__)

        # Base URLs
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = "https://www.linkedin.com/jobs/search"

        # Driver configuration
        self.driver = None
        self.wait = None

        # Rate limiting
        self.min_delay = 2
        self.max_delay = 5

        # Job selectors
        self.selectors = {
            'job_cards': '[data-view-name="job-search-card"]',
            'job_title': 'h3.base-search-card__title a',
            'company_name': 'h4.base-search-card__subtitle a, h4.base-search-card__subtitle span',
            'location': '.job-search-card__location',
            'posted_time': '.job-search-card__listdate',
            'job_link': 'h3.base-search-card__title a',
            'description': '.show-more-less-html__markup',
            'apply_button': '.jobs-apply-button'
        }
            'job_card': '.base-card',
            'title': '.base-search-card__title',
            'company': '.base-search-card__subtitle',
            'location': '.job-search-card__location',
            'link': '.base-card__full-link',
            'date': 'time',
            'description_preview': '.job-search-card__snippet'
        }

        # Detail page selectors
        self.detail_selectors = {
            'description': '.show-more-less-html__markup',
            'criteria': '.description__job-criteria-item',
            'salary': '.salary',
            'benefits': '.benefits'
        }

        # Search parameters mapping
        self.search_params_map = {
            'keywords': 'keywords',
            'location': 'location',
            'distance': 'distance',
            'posted_time': 'f_TPR',
            'experience_level': 'f_E',
            'job_type': 'f_JT',
            'company_size': 'f_C',
            'industry': 'f_I',
            'salary': 'f_SB'
        }

        self.logger.info("LinkedIn scraper initialized")

    def get_base_url(self) -> str:
        """Return LinkedIn base URL."""
        return "https://www.linkedin.com"

    def get_search_url(self) -> str:
        """Return LinkedIn jobs search URL."""
        return f"{self.base_url}/jobs/search"

    def build_search_params(self, keywords: List[str], location: str = None) -> Dict[str, Any]:
        """
        Build search parameters for LinkedIn Jobs search.

        Args:
            keywords: List of keywords to search for
            location: Location filter

        Returns:
            Dictionary of search parameters
        """
        params = {}

        # Keywords
        if keywords:
            # Join keywords with OR operator for broader search
            keywords_str = ' OR '.join(f'"{kw}"' for kw in keywords)
            params['keywords'] = keywords_str

        # Location
        if location or self.location:
            params['location'] = location or self.location

        # Distance (25 miles default)
        params['distance'] = self.config.get('distance', 25)

        # Posted time filter (last 24 hours = r86400, last week = r604800)
        posted_time = self.config.get('posted_time', 'r604800')  # Last week
        params['f_TPR'] = posted_time

        # Remote work
        if self.remote_ok:
            params['f_WT'] = '2'  # Remote jobs

        # Job type (full-time, part-time, contract, etc.)
        job_types = self.config.get('job_types', ['F'])  # F = Full-time
        if job_types:
            params['f_JT'] = ','.join(job_types)

        # Experience level
        experience_levels = self.config.get('experience_levels', [])
        if experience_levels:
            params['f_E'] = ','.join(experience_levels)

        # Sort by date
        params['sortBy'] = 'DD'  # Date Descending

        # Number of results per page
        params['count'] = self.config.get('results_per_page', 25)

        return params

    def search_jobs(self, keywords: List[str], location: str = None, **kwargs) -> List[Job]:
        """
        Search for jobs on LinkedIn.

        Args:
            keywords: List of keywords to search for
            location: Location filter
            **kwargs: Additional search parameters

        Returns:
            List of Job objects
        """
        if self.use_api and self.api_key:
            return self._search_jobs_api(keywords, location, **kwargs)
        else:
            return super().search_jobs(keywords, location, **kwargs)

    def _search_jobs_api(self, keywords: List[str], location: str = None, **kwargs) -> List[Job]:
        """
        Search jobs using LinkedIn API (if available).

        Note: LinkedIn's official API has limited job search capabilities.
        This is a placeholder for future API integration.
        """
        self.logger.warning("LinkedIn API search not implemented yet. Falling back to web scraping.")
        return super().search_jobs(keywords, location, **kwargs)

    def _find_job_elements(self, soup: BeautifulSoup) -> List:
        """
        Find job listing elements in LinkedIn search results.

        Args:
            soup: BeautifulSoup object of the search results page

        Returns:
            List of job listing elements
        """
        # Try different selectors as LinkedIn frequently changes their structure
        selectors = [
            'ul.jobs-search__results-list li',
            '.jobs-search-results__list-item',
            '[data-entity-urn*="jobPosting"]',
            '.job-search-card'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                self.logger.debug(f"Found {len(elements)} job elements using selector: {selector}")
                return elements

        self.logger.warning("No job elements found with any known selector")
        return []

    def parse_job_listing(self, job_element) -> Optional[Job]:
        """
        Parse a LinkedIn job listing element into a Job object.

        Args:
            job_element: BeautifulSoup element containing job information

        Returns:
            Job object if parsing successful, None otherwise
        """
        try:
            # Extract basic information
            title = self.extract_text(job_element, self.job_selectors['title'])
            company = self.extract_text(job_element, self.job_selectors['company'])
            location = self.extract_text(job_element, self.job_selectors['location'])

            if not title or not company:
                self.logger.debug("Missing required fields (title or company)")
                return None

            # Extract job URL
            job_url = self.extract_link(job_element, self.job_selectors['link'])

            # Extract job ID from URL or data attributes
            external_id = self._extract_job_id(job_element, job_url)

            if not external_id:
                self.logger.debug("Could not extract job ID")
                return None

            # Extract posted date
            posted_date = self._extract_posted_date(job_element)

            # Extract description preview
            description_preview = self.extract_text(job_element, self.job_selectors['description_preview'])

            # Determine if remote
            is_remote = self._is_remote_job(location, description_preview)

            # Create Job object
            job = Job(
                title=self.clean_text(title),
                company=self.clean_text(company),
                location=self.clean_text(location),
                description=self.clean_text(description_preview),
                url=job_url,
                source=JobSource.LINKEDIN,
                external_id=external_id,
                posted_date=posted_date,
                is_remote=is_remote,
                status=JobStatus.FOUND
            )

            return job

        except Exception as e:
            self.logger.warning(f"Error parsing LinkedIn job listing: {str(e)}")
            return None

    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific LinkedIn job.

        Args:
            job_url: URL to the job posting

        Returns:
            Dictionary containing detailed job information
        """
        details = {}

        try:
            self._apply_rate_limit()
            response = self._make_request(job_url)

            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch job details: {response.status_code}")
                return details

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract full job description
            description = self.extract_text(soup, self.detail_selectors['description'])
            if description:
                details['description'] = self.clean_text(description)

            # Extract job criteria (experience level, job type, etc.)
            criteria_elements = soup.select(self.detail_selectors['criteria'])
            criteria = {}

            for element in criteria_elements:
                key_elem = element.select_one('.description__job-criteria-subheader')
                value_elem = element.select_one('.description__job-criteria-text')

                if key_elem and value_elem:
                    key = self.clean_text(key_elem.get_text())
                    value = self.clean_text(value_elem.get_text())
                    criteria[key.lower().replace(' ', '_')] = value

            if criteria:
                details['criteria'] = criteria

            # Extract salary information
            salary_element = soup.select_one(self.detail_selectors['salary'])
            if salary_element:
                salary_text = self.extract_text(salary_element)
                salary_min, salary_max = self.extract_salary(salary_text)
                if salary_min or salary_max:
                    details['salary_min'] = salary_min
                    details['salary_max'] = salary_max
                    details['salary_text'] = salary_text

            # Extract benefits
            benefits_element = soup.select_one(self.detail_selectors['benefits'])
            if benefits_element:
                benefits = self.extract_text(benefits_element)
                details['benefits'] = benefits

            # Extract company information
            company_info = self._extract_company_info(soup)
            if company_info:
                details['company_info'] = company_info

            # Extract application information
            apply_info = self._extract_apply_info(soup)
            if apply_info:
                details['apply_info'] = apply_info

        except Exception as e:
            self.logger.error(f"Error fetching LinkedIn job details: {str(e)}")

        return details

    def _extract_job_id(self, job_element, job_url: str) -> Optional[str]:
        """
        Extract LinkedIn job ID from element or URL.

        Args:
            job_element: BeautifulSoup job element
            job_url: Job URL

        Returns:
            Job ID string or None
        """
        # Try to extract from data attributes
        for attr in ['data-entity-urn', 'data-job-id', 'data-tracking-id']:
            if job_element.has_attr(attr):
                value = job_element[attr]
                if 'jobPosting' in value:
                    # Extract ID from URN format
                    match = re.search(r'jobPosting:(\d+)', value)
                    if match:
                        return f"linkedin_{match.group(1)}"
                elif value.isdigit():
                    return f"linkedin_{value}"

        # Try to extract from URL
        if job_url:
            match = re.search(r'/view/(\d+)', job_url)
            if match:
                return f"linkedin_{match.group(1)}"

        # Try to extract from any data attribute containing numbers
        for attr, value in job_element.attrs.items():
            if isinstance(value, str) and value.isdigit() and len(value) > 5:
                return f"linkedin_{value}"

        return None

    def _extract_posted_date(self, job_element) -> Optional[datetime]:
        """
        Extract posted date from job element.

        Args:
            job_element: BeautifulSoup job element

        Returns:
            Datetime object or None
        """
        time_element = job_element.select_one(self.job_selectors['date'])

        if time_element:
            # Try datetime attribute first
            if time_element.has_attr('datetime'):
                try:
                    return datetime.fromisoformat(time_element['datetime'].replace('Z', '+00:00'))
                except ValueError:
                    pass

            # Parse text content
            time_text = self.extract_text(time_element)
            return self._parse_relative_date(time_text)

        return None

    def _parse_relative_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse relative date text (e.g., "2 days ago") into datetime.

        Args:
            date_text: Relative date text

        Returns:
            Datetime object or None
        """
        if not date_text:
            return None

        date_text = date_text.lower().strip()
        now = datetime.now()

        # Pattern matching for relative dates
        patterns = [
            (r'(\d+)\s*hour?s?\s*ago', 'hours'),
            (r'(\d+)\s*day?s?\s*ago', 'days'),
            (r'(\d+)\s*week?s?\s*ago', 'weeks'),
            (r'(\d+)\s*month?s?\s*ago', 'months'),
            (r'yesterday', 'days'),
            (r'today', 'hours')
        ]

        for pattern, unit in patterns:
            match = re.search(pattern, date_text)
            if match:
                if unit == 'hours':
                    if pattern == r'today':
                        delta = timedelta(hours=0)
                    else:
                        delta = timedelta(hours=int(match.group(1)))
                elif unit == 'days':
                    if pattern == r'yesterday':
                        delta = timedelta(days=1)
                    else:
                        delta = timedelta(days=int(match.group(1)))
                elif unit == 'weeks':
                    delta = timedelta(weeks=int(match.group(1)))
                elif unit == 'months':
                    delta = timedelta(days=int(match.group(1)) * 30)  # Approximate
                else:
                    continue

                return now - delta

        return None

    def _is_remote_job(self, location: str, description: str) -> bool:
        """
        Determine if job is remote based on location and description.

        Args:
            location: Job location text
            description: Job description text

        Returns:
            True if job appears to be remote
        """
        remote_indicators = [
            'remote', 'remoto', 'home office', 'work from home',
            'anywhere', 'distributed', 'virtual', 'telecommute'
        ]

        text_to_check = f"{location} {description}".lower()

        return any(indicator in text_to_check for indicator in remote_indicators)

    def _extract_company_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract company information from job detail page.

        Args:
            soup: BeautifulSoup object of job detail page

        Returns:
            Dictionary containing company information
        """
        company_info = {}

        # Company name (alternative selector)
        company_link = soup.select_one('.topcard__org-name-link')
        if company_link:
            company_info['name'] = self.clean_text(company_link.get_text())
            company_info['url'] = self.extract_link(company_link, attr='href')

        # Company size
        company_size = soup.select_one('.company-size')
        if company_size:
            company_info['size'] = self.clean_text(company_size.get_text())

        # Industry
        industry = soup.select_one('.company-industry')
        if industry:
            company_info['industry'] = self.clean_text(industry.get_text())

        return company_info

    def _extract_apply_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract application information from job detail page.

        Args:
            soup: BeautifulSoup object of job detail page

        Returns:
            Dictionary containing application information
        """
        apply_info = {}

        # Apply button/link
        apply_button = soup.select_one('.jobs-apply-button, .apply-button')
        if apply_button:
            apply_info['apply_url'] = self.extract_link(apply_button, attr='href')

        # Number of applicants
        applicants_text = soup.select_one('.num-applicants__caption')
        if applicants_text:
            applicants = self.extract_text(applicants_text)
            # Extract number from text like "47 applicants"
            match = re.search(r'(\d+)', applicants)
            if match:
                apply_info['num_applicants'] = int(match.group(1))
                apply_info['applicants_text'] = applicants

        # Application deadline
        deadline = soup.select_one('.application-deadline')
        if deadline:
            apply_info['deadline'] = self.clean_text(deadline.get_text())

        return apply_info

    def authenticate(self) -> bool:
        """
        Authenticate with LinkedIn (if credentials provided).

        Returns:
            True if authentication successful, False otherwise
        """
        if not self.email or not self.password:
            self.logger.info("No LinkedIn credentials provided, using public access")
            return True

        try:
            # Navigate to login page
            login_url = f"{self.base_url}/login"
            response = self._make_request(login_url)

            if response.status_code != 200:
                self.logger.error("Failed to access LinkedIn login page")
                return False

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find CSRF token
            csrf_token = None
            csrf_input = soup.select_one('input[name="loginCsrfParam"]')
            if csrf_input:
                csrf_token = csrf_input.get('value')

            # Prepare login data
            login_data = {
                'session_key': self.email,
                'session_password': self.password,
                'loginCsrfParam': csrf_token
            }

            # Submit login form
            login_submit_url = f"{self.base_url}/checkpoint/lg/login-submit"
            response = self.session.post(login_submit_url, data=login_data)

            # Check if login was successful
            if 'feed' in response.url or 'challenge' in response.url:
                self.logger.info("LinkedIn authentication successful")
                self.authenticated = True
                return True
            else:
                self.logger.error("LinkedIn authentication failed")
                return False

        except Exception as e:
            self.logger.error(f"Error during LinkedIn authentication: {str(e)}")
            return False

    def _passes_filters(self, job: Job) -> bool:
        """
        LinkedIn-specific job filtering.

        Args:
            job: Job object to check

        Returns:
            True if job passes all filters
        """
        # Call parent filter first
        if not super()._passes_filters(job):
            return False

        # LinkedIn-specific filters

        # Filter out jobs that are too old
        max_age_days = self.config.get('max_job_age_days', 30)
        if job.posted_date:
            age_days = (datetime.now() - job.posted_date).days
            if age_days > max_age_days:
                return False

        # Filter by company blacklist
        company_blacklist = self.config.get('company_blacklist', [])
        if job.company.lower() in [company.lower() for company in company_blacklist]:
            return False

        # Filter by required skills in title/description
        required_skills = self.config.get('required_skills', [])
        if required_skills:
            job_text = f"{job.title} {job.description}".lower()
            if not any(skill.lower() in job_text for skill in required_skills):
                return False

        return True

    def _setup_driver(self) -> None:
        """Setup Chrome driver with anti-detection measures"""
        try:
            options = uc.ChromeOptions()

            # Anti-detection options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # User agent
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Window size
            options.add_argument('--window-size=1920,1080')

            # Headless mode (opcional)
            if self.config.get('headless', True):
                options.add_argument('--headless')

            # Create driver
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)

            # Execute script to hide webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self.logger.info("Chrome driver setup successful")

        except Exception as e:
            self.logger.error(f"Failed to setup Chrome driver: {str(e)}")
            raise

    def _random_delay(self) -> None:
        """Add random delay between requests"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def search_jobs(self, keywords: str, location: str = "", limit: int = 25) -> List[Job]:
        """
        Search for jobs on LinkedIn.

        Args:
            keywords: Job search keywords
            location: Location to search in
            limit: Maximum number of jobs to return

        Returns:
            List of Job objects
        """
        jobs = []

        try:
            if not self.driver:
                self._setup_driver()

            # Build search URL
            search_params = {
                'keywords': keywords,
                'location': location,
                'f_TPR': 'r604800',  # Past week
                'f_WT': '2',  # Remote jobs
                'start': 0
            }

            search_url = f"{self.jobs_url}?{urlencode(search_params)}"

            self.logger.info(f"Searching LinkedIn jobs: {search_url}")

            # Navigate to search page
            self.driver.get(search_url)
            self._random_delay()

            # Wait for job cards to load
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['job_cards'])))
            except TimeoutException:
                self.logger.warning("Job cards not found, page might have changed")
                return jobs

            # Scroll to load more jobs
            self._scroll_to_load_jobs(limit)

            # Get job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['job_cards'])

            self.logger.info(f"Found {len(job_cards)} job cards")

            # Process each job card
            for i, card in enumerate(job_cards[:limit]):
                try:
                    job = self._extract_job_from_card(card)
                    if job:
                        jobs.append(job)
                        self.logger.info(f"Extracted job {i+1}: {job.title} at {job.company}")

                    # Random delay between processing
                    if i % 5 == 0:
                        self._random_delay()

                except Exception as e:
                    self.logger.error(f"Error extracting job from card {i}: {str(e)}")
                    continue

            self.logger.info(f"Successfully extracted {len(jobs)} jobs from LinkedIn")

        except Exception as e:
            self.logger.error(f"Error searching LinkedIn jobs: {str(e)}")

        return jobs

    def _scroll_to_load_jobs(self, target_jobs: int) -> None:
        """Scroll down to load more job listings"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scrolls = 0
            max_scrolls = 10

            while scrolls < max_scrolls:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait for new content to load
                time.sleep(2)

                # Check if we have enough jobs
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['job_cards'])
                if len(job_cards) >= target_jobs:
                    break

                # Check if new content loaded
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break

                last_height = new_height
                scrolls += 1

        except Exception as e:
            self.logger.error(f"Error scrolling to load jobs: {str(e)}")

    def _extract_job_from_card(self, card) -> Optional[Job]:
        """Extract job information from a job card element"""
        try:
            # Extract basic information
            title_element = card.find_element(By.CSS_SELECTOR, self.selectors['job_title'])
            title = title_element.text.strip()
            job_url = title_element.get_attribute('href')

            # Company name
            company_element = card.find_element(By.CSS_SELECTOR, self.selectors['company_name'])
            company = company_element.text.strip()

            # Location
            try:
                location_element = card.find_element(By.CSS_SELECTOR, self.selectors['location'])
                location = location_element.text.strip()
            except NoSuchElementException:
                location = "Remote"

            # Posted time
            try:
                posted_element = card.find_element(By.CSS_SELECTOR, self.selectors['posted_time'])
                posted_date = self._parse_posted_date(posted_element.text.strip())
            except NoSuchElementException:
                posted_date = datetime.now()

            # Extract job ID from URL
            job_id = self._extract_job_id_from_url(job_url)

            # Get detailed job information
            job_details = self._get_job_details(job_url)

            # Create Job object
            job = Job(
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                description=job_details.get('description', ''),
                salary=job_details.get('salary', ''),
                url=job_url,
                source=JobSource.LINKEDIN,
                posted_date=posted_date,
                status=JobStatus.FOUND,
                skills_required=job_details.get('skills', []),
                employment_type=job_details.get('employment_type', ''),
                experience_level=job_details.get('experience_level', '')
            )

            return job

        except Exception as e:
            self.logger.error(f"Error extracting job from card: {str(e)}")
            return None

    def _get_job_details(self, job_url: str) -> Dict[str, Any]:
        """Get detailed job information by visiting the job page"""
        details = {
            'description': '',
            'salary': '',
            'skills': [],
            'employment_type': '',
            'experience_level': ''
        }

        try:
            # Navigate to job detail page
            self.driver.get(job_url)
            self._random_delay()

            # Wait for description to load
            try:
                description_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['description']))
                )
                details['description'] = description_element.text.strip()
            except TimeoutException:
                self.logger.warning(f"Could not load job description for {job_url}")

            # Extract skills from description
            details['skills'] = self._extract_skills_from_description(details['description'])

            # Extract employment type and experience level
            details['employment_type'], details['experience_level'] = self._extract_job_metadata()

        except Exception as e:
            self.logger.error(f"Error getting job details from {job_url}: {str(e)}")

        return details

    def _extract_skills_from_description(self, description: str) -> List[str]:
        """Extract skills from job description"""
        skills = []

        # Common tech skills to look for
        tech_skills = [
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust',
            'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'FastAPI',
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Git', 'Linux'
        ]

        description_lower = description.lower()

        for skill in tech_skills:
            if skill.lower() in description_lower:
                skills.append(skill)

        return skills

    def _extract_job_metadata(self) -> tuple:
        """Extract employment type and experience level from job page"""
        employment_type = ""
        experience_level = ""

        try:
            # Look for job criteria section
            criteria_elements = self.driver.find_elements(By.CSS_SELECTOR, '.jobs-unified-top-card__job-insight span')

            for element in criteria_elements:
                text = element.text.strip().lower()

                if any(term in text for term in ['full-time', 'part-time', 'contract', 'temporary']):
                    employment_type = text.title()

                if any(term in text for term in ['entry', 'junior', 'senior', 'mid', 'lead']):
                    experience_level = text.title()

        except Exception as e:
            self.logger.error(f"Error extracting job metadata: {str(e)}")

        return employment_type, experience_level

    def _extract_job_id_from_url(self, url: str) -> str:
        """Extract job ID from LinkedIn job URL"""
        try:
            # LinkedIn job URLs contain the job ID
            # Format: https://www.linkedin.com/jobs/view/123456789
            match = re.search(r'/jobs/view/(\d+)', url)
            if match:
                return f"linkedin_{match.group(1)}"
        except Exception:
            pass

        # Fallback: use timestamp
        return f"linkedin_{int(time.time())}"

    def _parse_posted_date(self, posted_text: str) -> datetime:
        """Parse posted date from LinkedIn format"""
        try:
            posted_text = posted_text.lower().strip()
            now = datetime.now()

            if 'hour' in posted_text:
                hours = int(re.search(r'(\d+)', posted_text).group(1))
                return now - timedelta(hours=hours)
            elif 'day' in posted_text:
                days = int(re.search(r'(\d+)', posted_text).group(1))
                return now - timedelta(days=days)
            elif 'week' in posted_text:
                weeks = int(re.search(r'(\d+)', posted_text).group(1))
                return now - timedelta(weeks=weeks)
            elif 'month' in posted_text:
                months = int(re.search(r'(\d+)', posted_text).group(1))
                return now - timedelta(days=months * 30)
            else:
                return now

        except Exception:
            return datetime.now()

    def get_job_details(self, job_id: str) -> Optional[Job]:
        """Get detailed information for a specific job"""
        # For LinkedIn scraping, we get details during the search process
        # This method is mainly for API compatibility
        return None

    def close(self) -> None:
        """Close the web driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Chrome driver closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing Chrome driver: {str(e)}")

    def __del__(self):
        """Cleanup on object destruction"""
        self.close()
