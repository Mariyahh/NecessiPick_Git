from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import time
import traceback

# MongoDB connection
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']

# Chrome WebDriver setup
webdriver_path = r'C:\Users\jenne\OneDrive\Desktop\freelance\chromedriver_win32\chromedriver.exe'
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument(f"webdriver.chrome.driver={webdriver_path}")

# Category URLs for ShopMetro
category_urls = {
    'Bread': 'https://shopmetro.ph/marketmarket-supermarket/product-category/breakfast-world/bread/',
    'Milk': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/milk/',
    'Coffee': 'https://shopmetro.ph/marketmarket-supermarket/product-category/breakfast-world/coffee/',
    'Noodles': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/noodles/',
    'Laundry Aids': 'https://shopmetro.ph/marketmarket-supermarket/product-category/home-care/laundry-aids/',
    'Water': 'https://shopmetro.ph/marketmarket-supermarket/product-category/beverage-wines-liquor-and-spirits/water/',
    'Candle': 'https://shopmetro.ph/marketmarket-supermarket/?s=candle&post_type=product&type_aws=true&aws_id=1&aws_filter=1&awscat=Form%3A1+Filter%3AAll',
    'Fish Sauce': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/condiments/fish-sauce/',
    'Soy Sauce': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/condiments/soy-sauce/',
    'Vinegar': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/condiments/vinegar/',
}
def scrape_category(category, url):
    """Scrape all products from a specific category page."""
    print(f"Scraping category: {category} from {url}")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    # Scroll to load all products
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Extract products
    products = []
    product_containers = soup.find_all('div', class_='product-small')
    for container in product_containers:
        title_element = container.find('p', class_='name')
        price_wrapper = container.find('div', class_='price-wrapper')  # Price wrapper element
        url_element = container.find('a', class_='woocommerce-LoopProduct-link')
        image_element = container.find('img', class_='attachment-woocommerce_thumbnail')

        title = title_element.a.text.strip() if title_element and title_element.a else None
        url = url_element['href'] if url_element else None
        image = image_element['src'] if image_element else None

        # Extract prices
        original_price = None
        discounted_price = None

        if price_wrapper:
            # Check for discounted price
            discounted_element = price_wrapper.find('ins')
            original_element = price_wrapper.find('del')

            if discounted_element:
                discounted_price = discounted_element.text.strip()
            if original_element:
                original_price = original_element.text.strip()
            else:
                # If no discount, fetch the standard price
                single_price_element = price_wrapper.find('span', class_='woocommerce-Price-amount')
                if single_price_element:
                    original_price = single_price_element.text.strip()

        # Only append if title and at least one price is available
        if title and (original_price or discounted_price):
            products.append({
                'title': title,
                'url': url,
                'image': image,
                'original_price': original_price,
                'discounted_price': discounted_price,
            })

    return products


def update_shopmetro_products():
    """Update ShopMetro products in the MongoDB."""
    print("[INFO] Fetching existing products for supermarket 'ShopMetro' from MongoDB.")
    
    # Fetch all existing products for "ShopMetro"
    shopmetro_products = list(collection.find({"supermarket": "ShopMetro"}))
    
    # Create a set of normalized (title, url) pairs for efficient lookup
    existing_products_map = {
        (p['title'].strip().lower(), p['url'].strip().lower()): p for p in shopmetro_products
    }

    updated_count = 0
    new_count = 0
    failed_count = 0

    print("[INFO] Starting update process for ShopMetro categories.")
    for category, url in category_urls.items():
        print(f"\n[INFO] Processing category: {category}")
        try:
            # Scrape products for the current category
            scraped_products = scrape_category(category, url)
            
            for scraped_product in scraped_products:
                title = scraped_product['title'].strip()
                product_url = scraped_product['url'].strip()
                new_original_price = scraped_product['original_price']
                new_discounted_price = scraped_product['discounted_price']
                normalized_key = (title.lower(), product_url.lower())

                # Check if product exists using normalized title and url as unique identifiers
                if normalized_key in existing_products_map:
                    # Existing product: update prices if they have changed
                    existing_product = existing_products_map[normalized_key]
                    old_original_price = existing_product.get('original_price', None)
                    old_discounted_price = existing_product.get('discounted_price', None)
                    price_history = existing_product.get('price_history', [])

                    updates = {}

                    # Update original price if it has changed
                    if old_original_price != new_original_price:
                        current_date = datetime.now().isoformat()
                        
                        # Append the old price to the price history
                        if old_original_price:
                            price_history.append({
                                "price": old_original_price,
                                "date_scraped": existing_product.get('date_scraped', '2023-09-01T00:00:00')  # Default to September 2023
                            })
                        
                        # Append the new price to the price history
                        price_history.append({
                            "price": new_original_price,
                            "date_scraped": current_date
                        })
                        
                        updates['original_price'] = new_original_price
                        updates['price_history'] = price_history
                        print(f"[INFO] Updated original price for '{title}' from {old_original_price} to {new_original_price}")

                    # Update discounted price if it has changed
                    if old_discounted_price != new_discounted_price:
                        updates['discounted_price'] = new_discounted_price
                        print(f"[INFO] Updated discounted price for '{title}' from {old_discounted_price} to {new_discounted_price}")

                    # Apply updates if there are any
                    if updates:
                        collection.update_one({'_id': existing_product['_id']}, {'$set': updates})
                        updated_count += 1
                else:
                    # If the product is not in the existing_products_map, add it
                    if normalized_key not in existing_products_map:
                        new_product = {
                            'title': title,
                            'url': product_url,
                            'image': scraped_product['image'],
                            'original_price': new_original_price,
                            'discounted_price': new_discounted_price,
                            'price_history': [
                                {
                                    "price": new_original_price,
                                    "date_scraped": datetime.now().isoformat()
                                }
                            ] if new_original_price else [],
                            'supermarket': 'ShopMetro',
                            'category': category,
                        }
                        result = collection.insert_one(new_product)
                        # Update the map with the new product
                        existing_products_map[normalized_key] = new_product
                        collection.update_one({'_id': result.inserted_id}, {'$set': {'id': str(result.inserted_id)}})
                        print(f"[INFO] Added new product: '{title}' with original price {new_original_price}")
                        new_count += 1

        except Exception as e:
            print(f"[ERROR] Failed to process category {category}: {e}")
            traceback.print_exc()
            failed_count += 1

    print(f"\n[INFO] Update process complete. Summary:")
    print(f"[INFO] Products updated: {updated_count}")
    print(f"[INFO] New products added: {new_count}")
    print(f"[INFO] Categories failed: {failed_count}")


# Run the updater
update_shopmetro_products()
