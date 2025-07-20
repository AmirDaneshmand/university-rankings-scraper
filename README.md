# University Rankings Scraper

This project scrapes university rankings for Ferdowsi University of Mashhad from five ranking systems: Leiden, SCImago, ISC, Times Higher Education, and Shanghai (ARWU). The results are stored in a JSON file (`data/university_rankings.json`).

## Project Structure

university-rankings-scraper/├── .gitignore├── .env├── main.py├── modules/│ ├── leiden.py│ ├── scimago.py│ ├── isc.py│ ├── times.py│ ├── shanghai.py├── data/│ └── university_rankings.json├── logs/│ └── log.txt├── requirements.txt└── README.md

## Requirements

- Python 3.8 or higher
- Chrome browser (for WebDriver)
- Internet connection

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AmirDaneshmand/university-rankings-scraper.git
   cd university-rankings-scraper
   ```

Create and activate a virtual environment (recommended):
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Create a .env file in the project root and set the DEBUG variable:
DEBUG=False

Set DEBUG=True to enable detailed logging for debugging.
Set DEBUG=False to minimize logs and only include errors.

Usage
Run the main script:
python main.py

The script will:

Scrape rankings for Ferdowsi University of Mashhad from Leiden, SCImago, ISC, Times Higher Education, and Shanghai systems.
Store results in data/university_rankings.json.
Log execution details and errors in logs/log.txt (not uploaded to GitHub due to .gitignore).

Output
The only output is data/university_rankings.json with the following structure:
{
"university": "Ferdowsi University of Mashhad",
"rankings": {
"leiden": {
"2013": null,
"2014": null,
...
"2024": null
},
"scimago": {
"2011": null,
"2012": null,
...
"2024": null
},
"isc": {
"1391-1392": null,
"1392-1393": null,
...
"1400-1401": "1-15",
"1401-1402": "3"
},
"times": {
"2013": null,
"2014": null,
...
"2024": null
},
"shanghai": {
"2013": null,
"2014": null,
...
"2024": null
}
}
}

Rankings are stored as integers (e.g., 3), strings for ranges (e.g., "1-15"), or null if not found.
The isc system uses Persian year ranges (e.g., "1401-1402"), while others use Gregorian years (e.g., "2024").

Notes

The script uses 2 parallel processes for stability and to reduce system load.
Random delays (10-15 seconds) are applied to avoid overwhelming servers.
Logs are stored in logs/log.txt. Set DEBUG=True in .env to enable detailed logging for debugging.
The logs/ directory is included in the Git repository, but log.txt is ignored by .gitignore.
If you encounter a PermissionError with webdriver-manager, clear the cache:rmdir /s /q ~/.wdm

Alternatively, set a custom path:import os
os.environ["WDM_LOCAL"] = "1"
os.environ["WDM_DIR"] = "C:/custom/path/to/drivers"

For issues with specific ranking systems, check logs/log.txt for detailed error messages.
The ISC rankings are scraped for "دانشگاه‌های جامع" (comprehensive universities) using the search term "فردوسی".

Troubleshooting

No rankings found: Verify the website structure hasn't changed. Check logs/log.txt for warnings like "جدول یافت نشد".
WebDriver errors: Ensure Chrome is installed and up-to-date. Clear the webdriver-manager cache if needed.
Missing logs directory: The script automatically creates the logs/ directory if it doesn't exist.
Slow execution: The script processes multiple years with delays to avoid server issues. Execution may take 5-10 minutes.
