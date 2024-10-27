from datetime import time

BASE_URL = "https://www.amazon.in/s?k=two+brothers+organic+farms&page={}"
MAX_PAGES = 2  # Change as needed
SCRAPE_TIMES = [
    time(hour=00, minute=28),
    time(hour=6, minute=5),  # Add more entries for testing
    time(hour=6, minute=8),
    # Remove these after testing
]
