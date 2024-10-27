from datetime import time

BASE_URL = "https://www.amazon.in/s?k=two+brothers+organic+farms&page={}"
MAX_PAGES = 2  # Change as needed
SCRAPE_TIMES = [
    time(hour=23, minute=30),
    time(hour=23, minute=34),  # Add more entries for testing
    time(hour=0, minute=2),
    # Remove these after testing
]