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
    # Fetch all products for ShopMetro from MongoDB
    shopmetro_products = collection.find({"supermarket": "ShopMetro"})
    products_by_category = {}

    # Group products by category
    for product in shopmetro_products:
        category = product['category']
        if category not in products_by_category:
            products_by_category[category] = []
        products_by_category[category].append(product)

    updated_count = 0
    new_count = 0
    failed_count = 0

    # Process each category
    for category, url in category_urls.items():
        if category not in products_by_category:
            print(f"No products in MongoDB for category: {category}")
            continue

        # Scrape products from category page
        try:
            scraped_products = scrape_category(category, url)
            existing_products = {p['url']: p for p in products_by_category[category]}

            for scraped_product in scraped_products:
                url = scraped_product['url']
                title = scraped_product['title']
                new_original_price = scraped_product['original_price']
                new_discounted_price = scraped_product['discounted_price']

                # Check if product exists in MongoDB
                if url in existing_products:
                    product = existing_products[url]
                    old_original_price = product.get('original_price', None)
                    old_discounted_price = product.get('discounted_price', None)
                    price_history = product.get('price_history', [])

                    # Update original price if it has changed
                    if old_original_price != new_original_price:
                        current_date = datetime.now().isoformat()
                        # Add old price to history if not already added
                        if not price_history:
                            price_history.append({
                                "price": old_original_price,
                                "date_scraped": current_date
                            })

                        # Update original price in MongoDB
                        collection.update_one(
                            {'_id': product['_id']},
                            {
                                '$set': {
                                    'original_price': new_original_price,
                                    'price_history': price_history,
                                }
                            }
                        )
                        print(f"Updated original price for '{title}' to {new_original_price}")
                        updated_count += 1

                    # Update discounted price if it has changed
                    if old_discounted_price != new_discounted_price:
                        collection.update_one(
                            {'_id': product['_id']},
                            {'$set': {'discounted_price': new_discounted_price}}
                        )
                        print(f"Updated discounted price for '{title}' to {new_discounted_price}")
                        updated_count += 1

                else:
                    # New product, insert into MongoDB
                    collection.insert_one({
                        'id': scraped_product.get('id'),
                        'title': title,
                        'url': url,
                        'image': scraped_product.get('image'),
                        'original_price': new_original_price,
                        'discounted_price': new_discounted_price,
                        'price_history': [  # Only add history for the original price
                            {
                                "price": new_original_price,
                                "date_scraped": datetime.now().isoformat()
                            }
                        ] if new_original_price else [],
                        'supermarket': 'ShopMetro',
                        'category': category,
                    })
                    print(f"Added new product '{title}' with original price {new_original_price} and discounted price {new_discounted_price}")
                    new_count += 1
        except Exception as e:
            print(f"Error processing category {category}: {e}")
            traceback.print_exc()
            failed_count += 1

    print(f"\nUpdate completed. Updated {updated_count} products, added {new_count} new products, failed {failed_count} categories.")


# Run the updater
update_shopmetro_products()
