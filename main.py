from flask import Flask
import requests
from bs4 import BeautifulSoup
import time
import random
import os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
import pandas as pd
import io
import pytz

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, this is your web scraper running with Gunicorn!"

# Import settings from config.py
import config

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
]

def get_html(url, retries=3):
    for i in range(retries):
        headers = {"User-Agent": random.choice(user_agents)}
        response = requests.get(url, headers=headers)
        time.sleep(10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            if soup.find("span", class_="a-size-base-plus a-color-base a-text-normal"):
                return soup
            else:
                print(f"Retry {i + 1} - Essential elements not loaded. Retrying...")
                time.sleep(10)
    print("Failed to load essential elements after retries.")
    return None

def parse_product_data(soup):
    products = []
    for product in soup.find_all("div", {"data-asin": True}):
        if not product["data-asin"]:
            continue
        product_id = product["data-asin"]
        title_tag = product.find("span", class_="a-size-base-plus a-color-base a-text-normal")
        title = title_tag.text.strip() if title_tag else "N/A"
        rating_tag = product.find("span", class_="a-icon-alt")
        rating = rating_tag.text.strip() if rating_tag else "N/A"
        rating_count_tag = product.find("span", class_="a-size-base s-underline-text")
        rating_count = rating_count_tag.text.strip() if rating_count_tag else "N/A"
        sell_count_tag = product.find("span", class_="a-size-base a-color-secondary")
        sell_count = sell_count_tag.text.strip() if sell_count_tag else "N/A"
        price_tag = product.find("span", class_="a-price-whole")
        price = f"₹{price_tag.text.strip()}" if price_tag else "N/A"
        mrp_tag = product.find("span", class_="a-price a-text-price")
        mrp = mrp_tag.find("span", class_="a-offscreen").text.strip() if mrp_tag else "N/A"
        discount_tag = product.find("span", text=lambda text: text and "%" in text)
        discount = discount_tag.text.strip() if discount_tag else "N/A"

        products.append({
            "Product ID": product_id,
            "Title": title,
            "Rating": rating,
            "Rating Count": rating_count,
            "Monthly Sales": sell_count,
            "Selling Price": price,
            "MRP": mrp,
            "Discount": discount
        })
    return products

def send_to_telegram(products):
    # Create a DataFrame from the products
    df = pd.DataFrame(products)

    # Create a CSV file in memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    # Get the CSV content from the buffer
    csv_buffer.seek(0)  # Move to the beginning of the StringIO object
    csv_content = csv_buffer.getvalue()

    # Send the CSV as a file to Telegram
    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": "Here is the scraped data.",
        },
        files={"document": ("scraped_data.csv", csv_content)}
    )

    if response.status_code == 200:
        print("Data sent to Telegram successfully!")
    else:
        print(f"Failed to send data to Telegram. Status code: {response.status_code}")

def main():
    all_products = []
    for page in range(1, config.MAX_PAGES + 1):
        url = config.BASE_URL.format(page)
        soup = get_html(url)
        if not soup:
            print(f"Skipping page {page} due to incomplete load.")
            continue

        products = parse_product_data(soup)
        all_products.extend(products)

        time.sleep(random.uniform(8, 12))

        if not products:
            print("No more products found, ending scraping.")
            break

    send_to_telegram(all_products)
    print("Scraping complete.")

if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=pytz.timezone("Asia/Kolkata"))
    for scrape_time in config.SCRAPE_TIMES:
        scheduler.add_job(main, "cron", hour=scrape_time.hour, minute=scrape_time.minute)
    print("Scheduler started. Scraper will run at configured times.")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped manually.")
