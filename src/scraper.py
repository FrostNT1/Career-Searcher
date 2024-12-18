import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self, company_config: Dict):
        """
        Initialize the scraper with company-specific configuration.
        
        Args:
            company_config (Dict): Configuration for the company to scrape
        """
        self.config = company_config
        self.session = requests.Session()
        if 'headers' in company_config:
            self.session.headers.update(company_config['headers'])
    
    def _make_request(self, url: str, retries: int = 3, delay: int = 2) -> Optional[str]:
        """
        Make an HTTP request with retry logic and delay.
        
        Args:
            url (str): URL to request
            retries (int): Number of retries on failure
            delay (int): Delay between retries in seconds
        
        Returns:
            Optional[str]: HTML content if successful, None otherwise
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url)
                response.raise_for_status()
                time.sleep(delay)  # Be respectful to the server
                return response.text
            except requests.RequestException as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                continue
        return None

    def _parse_job_listing(self, listing_element) -> Optional[Dict]:
        """
        Parse a job listing element into structured data.
        
        Args:
            listing_element: BeautifulSoup element containing job information
        
        Returns:
            Optional[Dict]: Structured job data if successful, None otherwise
        """
        try:
            # Extract job title
            title_element = listing_element.select_one(self.config['title_selector'])
            title = title_element.text.strip() if title_element else None

            # Extract location
            location_element = listing_element.select_one(self.config['location_selector'])
            location = location_element.text.strip() if location_element else None

            # Extract job URL
            link_element = listing_element.select_one(self.config['link_selector'])
            job_url = link_element.get('href') if link_element else None
            
            # Handle relative URLs
            if job_url and job_url.startswith('/'):
                job_url = f"{self.config['base_url']}{job_url}"

            if not all([title, location, job_url]):
                logger.warning(f"Missing data - Title: {title}, Location: {location}, URL: {job_url}")
                return None

            # Print job details for debugging
            print(f"\nFound Job:")
            print(f"Title: {title}")
            print(f"Location: {location}")
            print(f"URL: {job_url}")
            print("-" * 50)

            return {
                'title': title,
                'location': location,
                'url': job_url,
                'company': self.config['name'],
                'scraped_date': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error parsing job listing: {str(e)}")
            return None

    def scrape_jobs(self) -> List[Dict]:
        """
        Scrape all job listings from the company's career page.
        
        Returns:
            List[Dict]: List of job listings
        """
        all_jobs = []
        page = 1
        max_pages = self.config['pagination'].get('max_pages', 20)

        print(f"\n=== Starting scraping for {self.config['name']} ===")
        print(f"Max pages to scrape: {max_pages}")
        
        while page <= max_pages:
            # Construct URL for current page
            if page == 1:
                url = self.config['career_url']
            else:
                url = f"{self.config['pagination']['base_url']}?{self.config['pagination']['param_name']}={page}"
            
            print(f"\nScraping page {page}")
            print(f"URL: {url}")
            
            html_content = self._make_request(url)
            
            if not html_content:
                print(f"❌ Failed to get content for page {page}")
                break

            soup = BeautifulSoup(html_content, 'html.parser')
            job_elements = soup.select(self.config['job_listing_selector'])
            
            print(f"Found {len(job_elements)} job listings on page {page}")

            if not job_elements:
                print(f"No job listings found on page {page}, stopping pagination")
                break

            # Parse each job listing
            for job_element in job_elements:
                job_data = self._parse_job_listing(job_element)
                if job_data:
                    all_jobs.append(job_data)

            # Check if we should continue to next page
            # Some sites might have a specific "next page" indicator or total pages count
            if self.config.get('pagination', {}).get('has_next_page_selector'):
                next_page = soup.select_one(self.config['pagination']['has_next_page_selector'])
                if not next_page:
                    print(f"No next page indicator found after page {page}")
                    break
            
            page += 1
            print(f"Moving to page {page}")
            print("-" * 50)

        print(f"\n=== Scraping Complete for {self.config['name']} ===")
        print(f"Total jobs found: {len(all_jobs)}")
        print("=" * 50)
        return all_jobs

def load_company_configs(config_path: str = 'config/companies.json') -> List[Dict]:
    """
    Load company configurations from JSON file.
    
    Args:
        config_path (str): Path to company configuration file
    
    Returns:
        List[Dict]: List of company configurations
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config['companies']
    except Exception as e:
        logger.error(f"Error loading company configs: {str(e)}")
        return []

def scrape_all_companies() -> List[Dict]:
    """
    Scrape jobs from all configured companies.
    
    Returns:
        List[Dict]: Combined list of all job listings
    """
    all_jobs = []
    companies = load_company_configs()
    
    for company_config in companies:
        try:
            scraper = JobScraper(company_config)
            jobs = scraper.scrape_jobs()
            all_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"Error scraping {company_config['name']}: {str(e)}")
            continue

    return all_jobs

if __name__ == "__main__":
    # Test scraping
    jobs = scrape_all_companies()
    print(f"Total jobs found: {len(jobs)}")
    for job in jobs[:5]:  # Print first 5 jobs as sample
        print(f"\nTitle: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"URL: {job['url']}") 