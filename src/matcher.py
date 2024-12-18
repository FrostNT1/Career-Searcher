import json
from typing import Dict, List, Set
import logging
from difflib import SequenceMatcher
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobMatcher:
    def __init__(self, criteria_path: str = 'config/search_criteria.json'):
        """
        Initialize the job matcher with search criteria.
        
        Args:
            criteria_path (str): Path to search criteria JSON file
        """
        self.criteria = self._load_criteria(criteria_path)
        self._prepare_criteria()

    def _load_criteria(self, criteria_path: str) -> Dict:
        """
        Load search criteria from JSON file.
        
        Args:
            criteria_path (str): Path to criteria file
        
        Returns:
            Dict: Search criteria configuration
        """
        try:
            with open(criteria_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading search criteria: {str(e)}")
            return {}

    def _prepare_criteria(self):
        """Prepare criteria for matching by converting to sets and lowercase."""
        self.primary_keywords = {k.lower() for k in self.criteria['primary_keywords']}
        self.related_terms = {t.lower() for t in self.criteria['related_terms']}
        self.locations = {l.lower() for l in self.criteria['locations']}
        self.exclude_terms = {t.lower() for t in self.criteria['exclude_terms']}
        self.threshold = self.criteria.get('match_threshold', 0.7)

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity using SequenceMatcher.
        
        Args:
            str1 (str): First string
            str2 (str): Second string
        
        Returns:
            float: Similarity score between 0 and 1
        """
        # Split the longer title into parts and find best matching part
        words1 = str1.lower().split()
        words2 = str2.lower().split()
        
        # Try different combinations of consecutive words
        max_score = 0
        for i in range(len(words2)):
            for j in range(i + 1, len(words2) + 1):
                part = " ".join(words2[i:j])
                score = SequenceMatcher(None, str1.lower(), part).ratio()
                max_score = max(max_score, score)
                
                # Early exit if we find a very good match
                if max_score > 0.9:
                    return max_score
        
        return max_score

    def _is_location_match(self, job_location: str) -> bool:
        """
        Check if job location matches criteria.
        
        Args:
            job_location (str): Job location to check
        
        Returns:
            bool: True if location matches, False otherwise
        """
        job_location = job_location.lower()
        
        # Check for remote positions
        if "remote" in self.locations and "remote" in job_location:
            return True
            
        # Check for US locations
        us_indicators = {"united states", "us", "usa", "u.s.", "u.s.a"}
        if any(loc in job_location for loc in us_indicators):
            return True
            
        # Check state abbreviations (e.g., NY, CA, etc.)
        state_pattern = r'\b[A-Z]{2}\b'
        if re.search(state_pattern, job_location.upper()):
            return True
            
        return False

    def _has_excluded_terms(self, title: str) -> bool:
        """
        Check if job title contains any excluded terms.
        
        Args:
            title (str): Job title to check
        
        Returns:
            bool: True if contains excluded terms, False otherwise
        """
        title = title.lower()
        return any(term in title for term in self.exclude_terms)

    def calculate_match_score(self, job: Dict) -> float:
        """
        Calculate how well a job matches the search criteria.
        
        Args:
            job (Dict): Job listing to evaluate
        
        Returns:
            float: Match score between 0 and 1
        """
        title = job['title'].lower()
        print(f"\nAnalyzing Job: {job['title']}")
        print(f"Location: {job['location']}")
        
        # Check for excluded terms first
        if self._has_excluded_terms(title):
            print("❌ Excluded: Contains excluded terms (senior/lead/etc.)")
            return 0.0
            
        # Check location
        if not self._is_location_match(job['location']):
            print("❌ Excluded: Location not in US/Remote")
            return 0.0

        # Check for exact matches in title (highest priority)
        title_parts = title.split()
        for i in range(len(title_parts)):
            for j in range(i + 1, len(title_parts) + 1):
                part = " ".join(title_parts[i:j])
                if part in self.primary_keywords:
                    print(f"✨ Exact Match Found: {part}")
                    return 1.0

        # Calculate primary keyword matches (higher weight)
        primary_scores = [(keyword, self._calculate_similarity(keyword, title)) 
                         for keyword in self.primary_keywords]
        best_primary = max(primary_scores, key=lambda x: x[1])
        primary_score = best_primary[1] * 0.7

        print(f"Primary Keyword Match: {best_primary[0]} (Score: {best_primary[1]:.2f})")
        
        # Print all good primary matches for debugging
        good_primary_matches = [
            (kw, score) for kw, score in primary_scores 
            if score > 0.5  # Show any decent matches
        ]
        if good_primary_matches:
            print("Other good primary matches:")
            for kw, score in good_primary_matches:
                if kw != best_primary[0]:  # Don't repeat the best match
                    print(f"  - {kw}: {score:.2f}")

        # Calculate related term matches (lower weight)
        related_scores = [(term, self._calculate_similarity(term, title)) 
                         for term in self.related_terms]
        best_related = max(related_scores, key=lambda x: x[1])
        related_score = best_related[1] * 0.3

        print(f"Related Term Match: {best_related[0]} (Score: {best_related[1]:.2f})")

        # Special case: If title contains "quant" or "quantitative", boost the score
        if "quant" in title or "quantitative" in title:
            boost = 0.3  # 30% boost
            print(f"📈 Quantitative Role Boost: +{boost}")
            total_score = min(1.0, primary_score + related_score + boost)
        else:
            total_score = primary_score + related_score

        print(f"Total Match Score: {total_score:.2f}")
        print("-" * 50)

        return total_score

    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Filter jobs based on search criteria.
        
        Args:
            jobs (List[Dict]): List of job listings to filter
        
        Returns:
            List[Dict]: Filtered list of matching jobs with scores
        """
        print("\n=== Starting Job Matching Process ===")
        print(f"Threshold Score: {self.threshold}")
        print(f"Processing {len(jobs)} jobs...")
        print("=" * 50)
        
        matching_jobs = []
        
        for job in jobs:
            score = self.calculate_match_score(job)
            if score >= self.threshold:
                print(f"✅ MATCH: {job['title']} (Score: {score:.2f})")
                job_with_score = job.copy()
                job_with_score['match_score'] = round(score, 2)
                matching_jobs.append(job_with_score)
            else:
                print(f"❌ NO MATCH: {job['title']} (Score: {score:.2f})")

        # Sort by match score in descending order
        matching_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        print("\n=== Matching Process Complete ===")
        print(f"Found {len(matching_jobs)} matching jobs out of {len(jobs)} total jobs")
        print("=" * 50)
        
        return matching_jobs

if __name__ == "__main__":
    # Test matching
    matcher = JobMatcher()
    test_jobs = [
        {
            "title": "Data Scientist",
            "location": "New York, NY",
            "company": "Test Corp",
            "url": "http://example.com"
        },
        {
            "title": "Senior Data Scientist",
            "location": "Remote, US",
            "company": "Test Corp",
            "url": "http://example.com"
        }
    ]
    
    matched_jobs = matcher.filter_jobs(test_jobs)
    for job in matched_jobs:
        print(f"\nTitle: {job['title']}")
        print(f"Location: {job['location']}")
        print(f"Match Score: {job['match_score']}") 