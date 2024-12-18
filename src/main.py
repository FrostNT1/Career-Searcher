import json
import logging
from datetime import datetime
from scraper import scrape_all_companies
from matcher import JobMatcher
from emailer import JobEmailer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_job_history(history_path: str = 'data/job_history.json'):
    """Load previously tracked jobs."""
    try:
        with open(history_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "tracked_jobs": [],
            "last_update": None,
            "statistics": {
                "total_jobs_found": 0,
                "total_notifications_sent": 0,
                "last_notification_date": None
            }
        }

def save_job_history(history: dict, history_path: str = 'data/job_history.json'):
    """Save updated job history."""
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=4)

def update_job_history(history: dict, new_jobs: list):
    """Update job history with new jobs."""
    # Add new job URLs to tracked jobs
    current_urls = set(history['tracked_jobs'])
    new_urls = {job['url'] for job in new_jobs}
    history['tracked_jobs'] = list(current_urls | new_urls)
    
    # Update statistics
    history['statistics']['total_jobs_found'] += len(new_jobs)
    if new_jobs:
        history['statistics']['total_notifications_sent'] += 1
        history['statistics']['last_notification_date'] = datetime.now().isoformat()
    
    history['last_update'] = datetime.now().isoformat()
    return history

def filter_new_jobs(jobs: list, history: dict) -> list:
    """Filter out previously seen jobs."""
    tracked_urls = set(history['tracked_jobs'])
    return [job for job in jobs if job['url'] not in tracked_urls]

def main():
    """Main function to orchestrate the job search process."""
    try:
        logger.info("Starting job search process")
        
        # Load job history
        history = load_job_history()
        
        # Scrape jobs from all configured companies
        all_jobs = scrape_all_companies()
        logger.info(f"Scraped {len(all_jobs)} total jobs")
        
        # Filter for new jobs only
        new_jobs = filter_new_jobs(all_jobs, history)
        logger.info(f"Found {len(new_jobs)} new jobs")
        
        if new_jobs:
            # Match jobs against criteria
            matcher = JobMatcher()
            matching_jobs = matcher.filter_jobs(new_jobs)
            logger.info(f"Found {len(matching_jobs)} matching jobs")
            
            if matching_jobs:
                # Send email notifications
                emailer = JobEmailer()
                if emailer.send_job_notifications(matching_jobs):
                    # Update and save job history
                    history = update_job_history(history, new_jobs)
                    save_job_history(history)
                    logger.info("Job search process completed successfully")
                else:
                    logger.error("Failed to send email notifications")
            else:
                logger.info("No matching jobs found")
        else:
            logger.info("No new jobs found")
            
    except Exception as e:
        logger.error(f"Error in job search process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 