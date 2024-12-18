# Career Searcher

An automated job search tool that scrapes job postings from top financial institutions and sends email notifications for matching positions.

## Features

- Scrapes job listings from multiple companies:
  - BlackRock
  - Vanguard
  - Wellington Management
  - Goldman Sachs
  - Morgan Stanley
  - JPMorgan
  - Citadel
  - Two Sigma
  - Point72
  
- Smart job matching:
  - Configurable primary and related keywords
  - Location filtering (US-based positions)
  - Seniority level filtering
  - Customizable matching threshold

- Email notifications:
  - HTML formatted job listings
  - Configurable recipient list
  - Job details including title, company, location, and direct link
  - Duplicate job detection

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/career-searcher.git
cd career-searcher
```

2. Create and activate conda environment:
```bash
conda env create -n career-searcher python=3.11 -y
conda activate career-searcher
pip install -r requirements.txt
```

3. Configure email settings:
Create a `.env` file in the root directory:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_specific_password
SENDER_EMAIL=your_email@gmail.com
```

4. Configure search criteria:
Edit `config/search_criteria.json` to set your job search preferences:
- Primary keywords (exact matches)
- Related terms (related roles/skills)
- Locations
- Excluded terms (e.g., senior positions)

5. Configure email recipients:
Edit `config/email_list.json` to set up notification recipients.

## Usage

Test email setup:
```bash
python src/test_email.py
```

Run the job search:
```bash
python src/main.py
```

## Configuration

### Adding New Companies

Add new companies to `config/companies.json` with the following structure:
```json
{
    "name": "Company Name",
    "career_url": "https://careers.company.com",
    "base_url": "https://company.com",
    "job_listing_selector": "CSS Selector",
    "title_selector": "CSS Selector",
    "location_selector": "CSS Selector",
    "link_selector": "CSS Selector",
    "pagination": {
        "type": "url_param",
        "param_name": "page",
        "base_url": "https://careers.company.com/jobs",
        "max_pages": 10
    }
}
```

### Search Criteria

Modify `config/search_criteria.json` to adjust:
- Job titles and keywords
- Location preferences
- Exclusion criteria
- Matching threshold

## Project Structure

```
career-searcher/
├── config/
│   ├── companies.json     # Company configurations
│   ├── search_criteria.json   # Search preferences
│   └── email_list.json    # Email recipients
├── data/
│   └── job_history.json   # Tracked jobs
├── src/
│   ├── scraper.py        # Web scraping logic
│   ├── matcher.py        # Job matching logic
│   ├── emailer.py        # Email notification system
│   ├── main.py          # Main script
│   └── test_email.py    # Email testing
├── .env                 # Email configuration
├── .gitignore
├── environment.yml      # Conda environment
├── LICENSE             # MIT License
└── README.md
```

## Future Enhancements

1. Support for more companies
2. Advanced matching using NLP
3. Web interface for configuration
4. Job application tracking
5. Scheduled runs (cron jobs)
6. Analytics dashboard

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2024 Shivam Tyagi

Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided that the above copyright notice and this permission notice appear in all copies. 