from emailer import JobEmailer

def test_email_setup():
    """Test email configuration with a sample job listing."""
    test_jobs = [
        {
            "title": "Test Data Scientist Position",
            "company": "Test Company",
            "location": "Remote, US",
            "url": "http://example.com/job",
            "match_score": 0.95
        }
    ]
    
    emailer = JobEmailer()
    success = emailer.send_job_notifications(test_jobs)
    
    if success:
        print("✅ Email test successful! Check your inbox.")
    else:
        print("❌ Email test failed. Check the logs for details.")

if __name__ == "__main__":
    test_email_setup() 