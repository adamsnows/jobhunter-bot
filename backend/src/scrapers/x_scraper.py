"""
X (Twitter) Jobs scraper.
Searches for job postings on X using hashtags and keywords.
"""

import tweepy
from typing import List, Dict, Any, Optional
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import logging

from .base_scraper import BaseScraper
from ..models.job import Job, JobSource, JobStatus

# Initialize logger
logger = logging.getLogger(__name__)


class XScraper(BaseScraper):
    """
    X (Twitter) Jobs scraper.

    Searches for job postings using X API v2 and web scraping.
    Looks for tweets with job-related hashtags and keywords.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize X scraper.

        Args:
            config: Configuration dictionary containing:
                - api_key: X API key (optional)
                - api_secret: X API secret (optional)
                - access_token: X access token (optional)
                - access_token_secret: X access token secret (optional)
                - bearer_token: X Bearer token (for API v2)
                - use_api: Whether to use API or web scraping (default: True if credentials provided)
        """
        super().__init__(config)

        # X API credentials
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.access_token = config.get('access_token')
        self.access_token_secret = config.get('access_token_secret')
        self.bearer_token = config.get('bearer_token')

        # Determine if we should use API
        self.use_api = config.get('use_api', bool(self.bearer_token or (self.api_key and self.api_secret)))

        # Initialize X API client
        self.api_client = None
        if self.use_api:
            self._init_api_client()

        # Job-related hashtags and keywords
        self.job_hashtags = config.get('job_hashtags', [
            '#job', '#jobs', '#hiring', '#jobsearch', '#career', '#careers',
            '#employment', '#work', '#vacancy', '#opening', '#jobopening',
            '#developer', '#python', '#javascript', '#java', '#react', '#nodejs',
            '#fullstack', '#backend', '#frontend', '#devops', '#datascience',
            '#machinelearning', '#ai', '#remote', '#remotework', '#wfh'
        ])

        # Company/recruiter accounts to monitor
        self.company_accounts = config.get('company_accounts', [])

        # Keywords that indicate job postings
        self.job_keywords = config.get('job_keywords', [
            'hiring', 'looking for', 'join our team', 'we are seeking',
            'opportunity', 'position available', 'now hiring', 'job opening',
            'developer needed', 'engineer wanted', 'remote position',
            'full-time', 'part-time', 'contract', 'freelance'
        ])

        # Keywords that indicate NOT job postings
        self.exclude_keywords = config.get('exclude_keywords', [
            'looking for job', 'seeking employment', 'need work',
            'unemployed', 'job hunting', 'resume', 'cv'
        ])

        # Location keywords for Brazilian market
        self.location_keywords = config.get('location_keywords', [
            'brasil', 'brazil', 'são paulo', 'sp', 'rio de janeiro', 'rj',
            'belo horizonte', 'mg', 'curitiba', 'pr', 'porto alegre', 'rs',
            'salvador', 'ba', 'recife', 'pe', 'brasília', 'df', 'fortaleza', 'ce',
            'remoto', 'remote', 'home office'
        ])

        self.logger.info(f"X scraper initialized (API: {self.use_api})")

    def _init_api_client(self):
        """Initialize X API client."""
        try:
            if self.bearer_token:
                # Use API v2 with Bearer token
                self.api_client = tweepy.Client(bearer_token=self.bearer_token)
                self.logger.info("X API v2 client initialized with Bearer token")

            elif self.api_key and self.api_secret:
                # Use API v1.1 with OAuth
                auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
                if self.access_token and self.access_token_secret:
                    auth.set_access_token(self.access_token, self.access_token_secret)

                self.api_client = tweepy.API(auth, wait_on_rate_limit=True)
                self.logger.info("X API v1.1 client initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize X API client: {str(e)}")
            self.use_api = False
            self.api_client = None

    def get_base_url(self) -> str:
        """Return X base URL."""
        return "https://twitter.com"

    def get_search_url(self) -> str:
        """Return X search URL."""
        return f"{self.base_url}/search"

    def build_search_params(self, keywords: List[str], location: str = None) -> Dict[str, Any]:
        """
        Build search parameters for X search.

        Args:
            keywords: List of keywords to search for
            location: Location filter (optional)

        Returns:
            Dictionary of search parameters
        """
        params = {}

        # Build search query
        query_parts = []

        # Add keywords
        if keywords:
            # Create keyword combinations with job hashtags
            keyword_queries = []
            for keyword in keywords:
                keyword_queries.append(f'"{keyword}"')
            query_parts.extend(keyword_queries)

        # Add job hashtags
        hashtag_query = ' OR '.join(self.job_hashtags[:10])  # Limit to avoid query length issues
        query_parts.append(f"({hashtag_query})")

        # Add job keywords
        job_keywords_query = ' OR '.join(f'"{kw}"' for kw in self.job_keywords[:5])
        query_parts.append(f"({job_keywords_query})")

        # Add location if specified
        if location or self.location:
            loc = location or self.location
            query_parts.append(f'"{loc}"')

        # Exclude non-job tweets
        for exclude in self.exclude_keywords:
            query_parts.append(f'-"{exclude}"')

        # Combine all parts
        query = ' '.join(query_parts)

        # Limit query length (X has query length limits)
        if len(query) > 500:
            query = query[:500]

        params['q'] = query
        params['src'] = 'typed_query'
        params['f'] = 'live'  # Recent tweets

        return params

    def search_jobs(self, keywords: List[str], location: str = None, **kwargs) -> List[Job]:
        """
        Search for jobs on X.

        Args:
            keywords: List of keywords to search for
            location: Location filter
            **kwargs: Additional search parameters

        Returns:
            List of Job objects
        """
        if self.use_api and self.api_client:
            return self._search_jobs_api(keywords, location, **kwargs)
        else:
            return self._search_jobs_web(keywords, location, **kwargs)

    def _search_jobs_api(self, keywords: List[str], location: str = None, **kwargs) -> List[Job]:
        """
        Search jobs using X API.

        Args:
            keywords: List of keywords to search for
            location: Location filter
            **kwargs: Additional search parameters

        Returns:
            List of Job objects
        """
        jobs = []

        try:
            # Build search query
            query_parts = []

            # Add keywords with job indicators
            for keyword in keywords:
                query_parts.append(f'"{keyword}"')

            # Add job hashtags
            hashtags = ' OR '.join(self.job_hashtags[:5])
            query_parts.append(f"({hashtags})")

            # Add hiring indicators
            hiring_terms = ' OR '.join(['"hiring"', '"job opening"', '"we are looking"'])
            query_parts.append(f"({hiring_terms})")

            # Exclude job seekers
            for exclude in self.exclude_keywords:
                query_parts.append(f'-"{exclude}"')

            # Location filter
            if location or self.location:
                loc = location or self.location
                if any(brazil_term in loc.lower() for brazil_term in ['brasil', 'brazil', 'sp', 'rj']):
                    brazil_terms = ' OR '.join(self.location_keywords)
                    query_parts.append(f"({brazil_terms})")

            query = ' '.join(query_parts)

            # Limit query length
            if len(query) > 450:
                query = query[:450]

            self.logger.info(f"X API search query: {query}")

            # Search tweets
            tweets = tweepy.Paginator(
                self.api_client.search_recent_tweets,
                query=query,
                max_results=100,  # Max per request
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations'],
                expansions=['author_id'],
                user_fields=['username', 'name', 'verified']
            ).flatten(limit=self.max_jobs_per_search)

            # Process tweets
            for tweet in tweets:
                job = self._parse_tweet_to_job(tweet)
                if job:
                    jobs.append(job)

            self.logger.info(f"Found {len(jobs)} job tweets via API")

        except Exception as e:
            self.logger.error(f"Error searching jobs via X API: {str(e)}")
            # Fallback to web scraping
            return self._search_jobs_web(keywords, location, **kwargs)

        return jobs

    def _search_jobs_web(self, keywords: List[str], location: str = None, **kwargs) -> List[Job]:
        """
        Search jobs using web scraping (fallback method).

        Args:
            keywords: List of keywords to search for
            location: Location filter
            **kwargs: Additional search parameters

        Returns:
            List of Job objects
        """
        self.logger.info("Using web scraping for X job search")
        return super().search_jobs(keywords, location, **kwargs)

    def _find_job_elements(self, soup: BeautifulSoup) -> List:
        """
        Find job tweet elements in X search results.

        Args:
            soup: BeautifulSoup object of the search results page

        Returns:
            List of tweet elements
        """
        # X frequently changes their DOM structure
        selectors = [
            '[data-testid="tweet"]',
            '.tweet',
            '[role="article"]',
            '.tweet-text'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                self.logger.debug(f"Found {len(elements)} tweet elements using selector: {selector}")
                return elements

        self.logger.warning("No tweet elements found with any known selector")
        return []

    def parse_job_listing(self, tweet_element) -> Optional[Job]:
        """
        Parse a tweet element into a Job object.

        Args:
            tweet_element: BeautifulSoup element or tweet object containing job information

        Returns:
            Job object if parsing successful, None otherwise
        """
        try:
            # Handle API tweet object vs HTML element
            if hasattr(tweet_element, 'text'):
                return self._parse_tweet_to_job(tweet_element)
            else:
                return self._parse_tweet_html_to_job(tweet_element)

        except Exception as e:
            self.logger.warning(f"Error parsing X job tweet: {str(e)}")
            return None

    def _parse_tweet_to_job(self, tweet) -> Optional[Job]:
        """
        Parse API tweet object to Job.

        Args:
            tweet: Tweet object from X API

        Returns:
            Job object or None
        """
        try:
            text = tweet.text

            # Check if this looks like a job posting
            if not self._is_job_tweet(text):
                return None

            # Extract job information
            title = self._extract_job_title(text)
            company = self._extract_company_name(text, getattr(tweet, 'author_id', None))
            location = self._extract_location(text)

            # Create job URL
            tweet_id = tweet.id
            author_username = getattr(tweet, 'username', 'unknown')
            job_url = f"https://twitter.com/{author_username}/status/{tweet_id}"

            # Generate external ID
            external_id = f"x_{tweet_id}"

            # Check if remote
            is_remote = self._is_remote_job(location, text)

            job = Job(
                title=title or "Developer Position",
                company=company or "Unknown Company",
                location=location or "Not specified",
                description=self.clean_text(text[:500]),  # Limit description length
                url=job_url,
                source=JobSource.X_TWITTER,
                external_id=external_id,
                posted_date=getattr(tweet, 'created_at', datetime.now()),
                is_remote=is_remote,
                status=JobStatus.FOUND
            )

            return job

        except Exception as e:
            self.logger.warning(f"Error parsing API tweet to job: {str(e)}")
            return None

    def _parse_tweet_html_to_job(self, tweet_element) -> Optional[Job]:
        """
        Parse HTML tweet element to Job.

        Args:
            tweet_element: BeautifulSoup tweet element

        Returns:
            Job object or None
        """
        try:
            # Extract tweet text
            text_selectors = [
                '[data-testid="tweetText"]',
                '.tweet-text',
                '.js-tweet-text',
                '.tweet-text-container'
            ]

            text = ""
            for selector in text_selectors:
                text_elem = tweet_element.select_one(selector)
                if text_elem:
                    text = self.extract_text(text_elem)
                    break

            if not text or not self._is_job_tweet(text):
                return None

            # Extract metadata
            username = self._extract_username(tweet_element)
            tweet_id = self._extract_tweet_id(tweet_element)
            timestamp = self._extract_timestamp(tweet_element)

            # Extract job information
            title = self._extract_job_title(text)
            company = self._extract_company_name(text, username)
            location = self._extract_location(text)

            # Create job URL
            job_url = f"https://twitter.com/{username}/status/{tweet_id}" if username and tweet_id else ""

            # Generate external ID
            external_id = f"x_{tweet_id}" if tweet_id else f"x_{hash(text)}"

            # Check if remote
            is_remote = self._is_remote_job(location, text)

            job = Job(
                title=title or "Developer Position",
                company=company or username or "Unknown Company",
                location=location or "Not specified",
                description=self.clean_text(text[:500]),
                url=job_url,
                source=JobSource.X_TWITTER,
                external_id=external_id,
                posted_date=timestamp or datetime.now(),
                is_remote=is_remote,
                status=JobStatus.FOUND
            )

            return job

        except Exception as e:
            self.logger.warning(f"Error parsing HTML tweet to job: {str(e)}")
            return None

    def _is_job_tweet(self, text: str) -> bool:
        """
        Determine if a tweet is a job posting.

        Args:
            text: Tweet text

        Returns:
            True if tweet appears to be a job posting
        """
        text_lower = text.lower()

        # Check for exclusion keywords (job seekers)
        if any(exclude in text_lower for exclude in self.exclude_keywords):
            return False

        # Check for job indicators
        job_indicators = self.job_keywords + [
            'apply', 'send cv', 'send resume', 'email us',
            'apply now', 'dm me', 'pm me', 'contact',
            'salary', 'benefits', 'requirements'
        ]

        has_job_indicator = any(indicator in text_lower for indicator in job_indicators)

        # Check for job hashtags
        has_job_hashtag = any(hashtag.lower() in text_lower for hashtag in self.job_hashtags)

        # Check for tech keywords
        tech_keywords = [
            'python', 'javascript', 'java', 'react', 'nodejs', 'php',
            'developer', 'engineer', 'programmer', 'coding', 'software'
        ]
        has_tech_keyword = any(tech in text_lower for tech in tech_keywords)

        # Must have at least job indicator or hashtag, and preferably tech keyword
        return (has_job_indicator or has_job_hashtag) and (has_tech_keyword or has_job_indicator)

    def _extract_job_title(self, text: str) -> Optional[str]:
        """
        Extract job title from tweet text.

        Args:
            text: Tweet text

        Returns:
            Job title or None
        """
        # Common job title patterns
        patterns = [
            r'(?:hiring|looking for|seeking|need)\s+(?:a\s+)?([^\.!?\n]{5,50}?)(?:\s+(?:developer|engineer|programmer))',
            r'(?:position|role|opportunity):\s*([^\.!?\n]{5,50})',
            r'we need\s+(?:a\s+)?([^\.!?\n]{5,50}?)(?:\s+(?:developer|engineer))',
            r'join us as\s+(?:a\s+)?([^\.!?\n]{5,50})',
            r'([^\.!?\n]*(?:developer|engineer|programmer|analyst|designer)[^\.!?\n]*)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = self.clean_text(match.group(1))
                if 5 <= len(title) <= 100:  # Reasonable length
                    return title

        # Fallback: look for common job titles
        job_titles = [
            'python developer', 'javascript developer', 'java developer',
            'frontend developer', 'backend developer', 'fullstack developer',
            'software engineer', 'web developer', 'mobile developer',
            'devops engineer', 'data scientist', 'data analyst'
        ]

        text_lower = text.lower()
        for title in job_titles:
            if title in text_lower:
                return title.title()

        return None

    def _extract_company_name(self, text: str, username: str = None) -> Optional[str]:
        """
        Extract company name from tweet text or username.

        Args:
            text: Tweet text
            username: Tweet author username

        Returns:
            Company name or None
        """
        # Try to extract from text first
        patterns = [
            r'@(\w+)\s+is\s+hiring',
            r'join\s+(?:us\s+at\s+)?([A-Z][a-zA-Z\s&]+?)(?:\s+as|\s+for|\s+in|\s*!)',
            r'([A-Z][a-zA-Z\s&]+?)\s+is\s+(?:looking|hiring|seeking)',
            r'work\s+(?:at|for)\s+([A-Z][a-zA-Z\s&]+?)(?:\s|!|\.|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                company = self.clean_text(match.group(1))
                if 2 <= len(company) <= 50:
                    return company

        # Use username as fallback (remove common suffixes)
        if username:
            company = username.replace('_', ' ').replace('-', ' ')
            # Remove common job/tech suffixes
            suffixes = ['jobs', 'careers', 'hiring', 'tech', 'dev', 'official']
            for suffix in suffixes:
                if company.lower().endswith(suffix):
                    company = company[:-len(suffix)].strip()

            if len(company) >= 2:
                return company.title()

        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """
        Extract location from tweet text.

        Args:
            text: Tweet text

        Returns:
            Location string or None
        """
        # Location patterns
        patterns = [
            r'(?:location|based|in)\s*:?\s*([^\.!?\n,]{3,30})',
            r'(?:remote|remoto|home office)',
            r'(São Paulo|Rio de Janeiro|Belo Horizonte|Curitiba|Porto Alegre|Brasília|Salvador|Recife|Fortaleza)',
            r'(SP|RJ|MG|PR|RS|DF|BA|PE|CE)',
            r'(?:brasil|brazil)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'remote' in pattern or 'home office' in pattern:
                    return "Remote"
                location = self.clean_text(match.group(1) if match.groups() else match.group(0))
                if len(location) >= 2:
                    return location

        return None

    def _extract_username(self, tweet_element) -> Optional[str]:
        """Extract username from tweet HTML element."""
        selectors = [
            '[data-testid="User-Names"] a',
            '.username',
            '.js-user-profile-link',
            'a[href*="/"]'
        ]

        for selector in selectors:
            elem = tweet_element.select_one(selector)
            if elem:
                href = elem.get('href', '')
                if href.startswith('/'):
                    return href[1:].split('/')[0]
                text = self.extract_text(elem)
                if text.startswith('@'):
                    return text[1:]

        return None

    def _extract_tweet_id(self, tweet_element) -> Optional[str]:
        """Extract tweet ID from HTML element."""
        # Look for tweet ID in various attributes
        for attr in ['data-tweet-id', 'data-id', 'id']:
            if tweet_element.has_attr(attr):
                value = tweet_element[attr]
                if value.isdigit():
                    return value

        # Look for tweet ID in links
        links = tweet_element.select('a[href*="/status/"]')
        for link in links:
            href = link.get('href', '')
            match = re.search(r'/status/(\d+)', href)
            if match:
                return match.group(1)

        return None

    def _extract_timestamp(self, tweet_element) -> Optional[datetime]:
        """Extract timestamp from tweet HTML element."""
        time_selectors = [
            'time',
            '[datetime]',
            '.time'
        ]

        for selector in time_selectors:
            time_elem = tweet_element.select_one(selector)
            if time_elem:
                datetime_attr = time_elem.get('datetime')
                if datetime_attr:
                    try:
                        return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    except ValueError:
                        pass

                # Try to parse relative time
                time_text = self.extract_text(time_elem)
                parsed_time = self._parse_relative_date(time_text)
                if parsed_time:
                    return parsed_time

        return None

    def _parse_relative_date(self, date_text: str) -> Optional[datetime]:
        """Parse relative date from X (e.g., '2h', '3d', '1w')."""
        if not date_text:
            return None

        date_text = date_text.lower().strip()
        now = datetime.now()

        # X relative time patterns
        patterns = [
            (r'(\d+)s', 'seconds'),
            (r'(\d+)m', 'minutes'),
            (r'(\d+)h', 'hours'),
            (r'(\d+)d', 'days'),
            (r'(\d+)w', 'weeks')
        ]

        for pattern, unit in patterns:
            match = re.search(pattern, date_text)
            if match:
                value = int(match.group(1))
                if unit == 'seconds':
                    delta = timedelta(seconds=value)
                elif unit == 'minutes':
                    delta = timedelta(minutes=value)
                elif unit == 'hours':
                    delta = timedelta(hours=value)
                elif unit == 'days':
                    delta = timedelta(days=value)
                elif unit == 'weeks':
                    delta = timedelta(weeks=value)
                else:
                    continue

                return now - delta

        return None

    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific job tweet.

        Args:
            job_url: URL to the tweet

        Returns:
            Dictionary containing detailed job information
        """
        details = {}

        try:
            self._apply_rate_limit()
            response = self._make_request(job_url)

            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch tweet details: {response.status_code}")
                return details

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract full tweet text
            text_elem = soup.select_one('[data-testid="tweetText"]')
            if text_elem:
                full_text = self.extract_text(text_elem)
                details['full_description'] = self.clean_text(full_text)

            # Extract thread (replies from same user)
            thread_tweets = soup.select('[role="article"]')
            if len(thread_tweets) > 1:
                thread_texts = []
                for tweet in thread_tweets[1:6]:  # Limit to 5 additional tweets
                    thread_text = self.extract_text(tweet.select_one('[data-testid="tweetText"]'))
                    if thread_text:
                        thread_texts.append(thread_text)

                if thread_texts:
                    details['thread'] = thread_texts
                    details['full_description'] = full_text + '\n\n' + '\n\n'.join(thread_texts)

            # Extract engagement metrics
            metrics = self._extract_engagement_metrics(soup)
            if metrics:
                details['metrics'] = metrics

            # Extract links mentioned in tweet
            links = self._extract_links(soup)
            if links:
                details['links'] = links

        except Exception as e:
            self.logger.error(f"Error fetching X job details: {str(e)}")

        return details

    def _extract_engagement_metrics(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Extract engagement metrics from tweet page."""
        metrics = {}

        metric_selectors = {
            'likes': '[data-testid="like"]',
            'retweets': '[data-testid="retweet"]',
            'replies': '[data-testid="reply"]'
        }

        for metric, selector in metric_selectors.items():
            elem = soup.select_one(selector)
            if elem:
                text = self.extract_text(elem)
                # Extract number from text
                match = re.search(r'(\d+)', text.replace(',', ''))
                if match:
                    metrics[metric] = int(match.group(1))

        return metrics

    def _extract_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract external links from tweet."""
        links = []

        link_elements = soup.select('a[href^="http"]')
        for link in link_elements:
            href = link.get('href')
            # Skip X internal links
            if href and not any(domain in href for domain in ['twitter.com', 'x.com', 't.co']):
                links.append(href)

        return list(set(links))  # Remove duplicates

    def _passes_filters(self, job: Job) -> bool:
        """
        X-specific job filtering.

        Args:
            job: Job object to check

        Returns:
            True if job passes all filters
        """
        # Call parent filter first
        if not super()._passes_filters(job):
            return False

        # X-specific filters

        # Filter out very short descriptions (likely not real job posts)
        if len(job.description) < 50:
            return False

        # Filter by engagement (if available)
        # This would require additional API calls for metrics

        # Filter by account verification (if available)
        # This would require additional API calls

        return True
