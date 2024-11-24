from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import time
import traceback
from urllib.parse import urlparse, urljoin

# MongoDB Connection
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']

# Chrome WebDriver Setup
webdriver_path = r'C:\Users\jenne\OneDrive\Desktop\freelance\chromedriver_win32\chromedriver.exe'
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
service = webdriver.chrome.service.Service(webdriver_path)

def extract_product_identifier(url):
    """Extract the unique product identifier from the URL."""
    parsed_url = urlparse(url)
    # Split the path and extract the last meaningful segment
    segments = parsed_url.path.split('/')
    for segment in reversed(segments):
        if segment:  # Ignore empty segments
            return segment.lower().strip()  # Use the last non-empty segment as the identifier
    return ""

def scrape_website_waltermart(url, category):
    print(f"Scraping category: {category} from {url}")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    
    # Handle modals in WalterMart
    try:
        time.sleep(20)  # Wait for modals to load
        place_order_button = driver.find_element(By.XPATH, "//button[contains(@data-action, 'change-delivery')]")
        place_order_button.click()
        time.sleep(10)

        search_box = driver.find_element(By.ID, "fp-search-box-mobile")
        search_box.send_keys("North Edsa")
        search_box.send_keys(Keys.RETURN)
        time.sleep(10)

        continue_button = driver.find_element(By.XPATH, "//a[@data-store-id='1950']")
        continue_button.click()
        time.sleep(18)
    except Exception as e:
        print(f"[WARNING] Modal handling failed: {e}")

    # Fetch existing products and normalize keys
    existing_products_map = {
        (p['title'].strip().lower(), extract_product_identifier(p['url'])): p
        for p in collection.find({"supermarket": "WalterMart", "category": category})
    }

    while True:
        # Parse the page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_containers = soup.find_all('div', class_='fp-item-container')
        for container in product_containers:
            # Extract product details
            image_element = container.find('div', class_='fp-item-image').find('img')
            image = image_element['data-src'] if image_element else ''

            title_element = container.find('div', class_='fp-item-name').find('a')
            title = title_element.text.strip() if title_element else ''

            url_element = container.find('div', class_='fp-item-name').find('a')
            raw_url = url_element['href'] if url_element else ''
            product_url = urljoin(url, raw_url)

            original_price_element = container.find('div', class_='fp-item-price').find('span', class_='fp-item-base-price')
            original_price = original_price_element.text.strip() if original_price_element else ''

            discounted_price_element = container.find('div', class_='fp-item-callout')
            discounted_price = discounted_price_element.text.strip() if discounted_price_element else ''

            # Normalize data for duplicate detection
            normalized_title = title.lower()
            product_identifier = extract_product_identifier(product_url)
            key = (normalized_title, product_identifier)

            # Check for duplicates
            if key in existing_products_map:
                existing_product = existing_products_map[key]
                updates = {}

                # Update original price if it has changed
                if existing_product.get('original_price') != original_price:
                    if 'price_history' not in existing_product:
                        existing_product['price_history'] = []

                    # Append the old price to price_history with default date_scraped
                    if existing_product.get('original_price'):
                        existing_product['price_history'].append({
                            "price": existing_product.get('original_price'),
                            "date_scraped": existing_product.get('date_scraped', '2023-09-01T00:00:00')  # Default to September 2023
                        })

                    # Append the new price to price_history with the current date
                    existing_product['price_history'].append({
                        "price": original_price,
                        "date_scraped": datetime.now().isoformat()
                    })

                    updates['original_price'] = original_price
                    updates['price_history'] = existing_product['price_history']
                    print(f"[INFO] Updated original price for '{title}' from {existing_product.get('original_price')} to {original_price}")

                # Update discounted price if it has changed
                if existing_product.get('discounted_price') != discounted_price:
                    updates['discounted_price'] = discounted_price
                    print(f"[INFO] Updated discounted price for '{title}' from {existing_product.get('discounted_price')} to {discounted_price}")

                # Apply updates if any
                if updates:
                    collection.update_one({'_id': existing_product['_id']}, {'$set': updates})
                    print(f"[INFO] Updated product: {title}")

            else:
                # Add new product
                new_product = {
                    'id': str(datetime.now().timestamp()).replace('.', ''),  # Generate unique ID
                    'title': title,
                    'url': product_url,
                    'image': image,
                    'original_price': original_price,
                    'discounted_price': discounted_price,
                    'price_history': [
                        {
                            "price": original_price,
                            "date_scraped": datetime.now().isoformat()
                        }
                    ] if original_price else [],
                    'category': category,
                    'supermarket': 'WalterMart',
                }
                result = collection.insert_one(new_product)
                # Update existing_products_map to include the newly added product
                existing_products_map[key] = new_product
                print(f"[INFO] Added new product: {title}")

        # Pagination
        try:
            next_page_button = driver.find_element(By.CSS_SELECTOR, '.fp-pager-item-next a')
            if 'fp-disabled' in next_page_button.get_attribute('class'):
                break
            next_page_button.click()
            time.sleep(15)
        except Exception as e:
            print(f"[INFO] No more pages or pagination failed: {e}")
            break

    driver.quit()



# WalterMart Categories
categories = [
    {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?department_id=1496148',
         'category': 'Canned Goods'},
        {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?department_id=22459165',
        'category': 'Milk'},
        {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?department_id=22459167',
        'category': 'Coffee'},
        {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?department_id=22459177',
        'category': 'Noodles'},
        {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?department_id=22459226',
        'category': 'Laundry Aids'},
        {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?department_id=22459112',
        'category': 'Bread'},
        {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?department_id=1496167',
        'category': 'Water'},
        {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?department_id=22459141&q=candle',
        'category': 'Candle'},
        {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?q=fish%20sauce&department_id=22459193',
        'category': 'Fish Sauce'},
        {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?q=soy%20sauce&department_id=22459193',
        'category': 'Soy Sauce'},
        {'url': 'https://www.waltermartdelivery.com.ph/shop#!/?q=vinegar&department_id=22459193',
        'category': 'Vinegar'},
]

# Run Scraper
for category in categories:
    scrape_website_waltermart(category['url'], category['category'])
