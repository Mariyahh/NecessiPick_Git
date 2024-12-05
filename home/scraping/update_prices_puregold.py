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

# Category URLs for Puregold
category_urls = [
         {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FISH%20&%20SEAFOOD/class/OTHER%20CANNED%20SEAFOOD/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FISH%20&%20SEAFOOD/class/SALMON/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FISH%20&%20SEAFOOD/class/SARDINES/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FISH%20&%20SEAFOOD/class/SPECIALTY%20SARDINES/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FISH%20&%20SEAFOOD/class/SQUID/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FISH%20&%20SEAFOOD/class/TUNA/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FISH%20&%20SEAFOOD/class/BOTTLED%20SARDINES/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FISH%20&%20SEAFOOD/class/MACKEREL/page/1',
         'category': 'Canned Goods'},
        
        # Canned Fruits
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FRUITS/class/FRUIT%20COCKTAIL/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FRUITS/class/LYCHEE/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FRUITS/class/OTHER%20CANNED%20FRUITS/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FRUITS/class/PEACHES/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20FRUITS/class/PINEAPPLE/page/1',
         'category': 'Canned Goods'},

        # CANNED MEAT
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20MEAT/class/BEEF%20LOAF/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20MEAT/class/CANNED%20HAM/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20MEAT/class/CARNE%20NORTE/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20MEAT/class/CHICKEN%20CHUNKS/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20MEAT/class/CORNED%20BEEF/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20MEAT/class/LUNCHEON%20MEAT/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20MEAT/class/MEAT%20DINNERS/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20MEAT/class/MEAT%20LOAF/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20MEAT/class/SAUSAGES/page/1',
         'category': 'Canned Goods'},

        # CANNED VEGETABLES
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/BLACK%20BEANS/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/CAPERS/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/CORN/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/GARBANZOS%20BEANS/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/GREEN%20PEAS/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/MUSHROOM/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/OLIVES/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/OTHER%20CANNED%20VEGETABLES/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/PICKLES/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/PORK%20&%20BEANS/page/1',
         'category': 'Canned Goods'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CANNED%20GOODS/subcat/CANNED%20VEGETABLES/class/TOMATOES/page/1',
         'category': 'Canned Goods'},
        
        # MILK PRODUCTS
        # ADULT MILK
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/ADULT%20MILK/class/ADULT%20LIQUID%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/ADULT%20MILK/class/ADULT%20POWDER%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/ADULT%20MILK/class/PRE-NATAL%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/ADULT%20MILK/class/SPECIALIZED%20ADULT%20POWDERED%20MILK/page/1',
         'category': 'Milk'},
        
        # LIQUID MILK
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/LIQUID%20MILK/class/CONDENSED%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/LIQUID%20MILK/class/EVAPORATED%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/LIQUID%20MILK/class/KIDS%20READY-TO-DRINK%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/LIQUID%20MILK/class/MILK-BASED%20DRINKS/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/LIQUID%20MILK/class/STERILIZED%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/LIQUID%20MILK/class/UHT%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/LIQUID%20MILK/class/YOGHURT%20MILK%20/page/1',
         'category': 'Milk'},

        # POWDERED MILK
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/MILK%20&%20MILK%20PRODUCTS/subcat/POWDERED%20MILK/class/FORTIFIED%20MILK/page/1',
         'category': 'Milk'},

        # CHILDRENS MILK
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/FORMULA%20MILK%20&%20BABY%20FOODS/subcat/CHILDRENS%20MILK/class/0-6MONTHS%20INFANT%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/FORMULA%20MILK%20&%20BABY%20FOODS/subcat/CHILDRENS%20MILK/class/STAGE%202%20INFANT%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/FORMULA%20MILK%20&%20BABY%20FOODS/subcat/CHILDRENS%20MILK/class/STAGE%203%20GROWING-UP%20MILK/page/1',
         'category': 'Milk'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/FORMULA%20MILK%20&%20BABY%20FOODS/subcat/CHILDRENS%20MILK/class/STAGE%204%20GROWING-UP%20MILK/page/1',
         'category': 'Milk'},

        # COFFEE PRODUCTS
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BEVERAGES/subcat/COFFEE/class/DECAF*BREWED%20COFFEE/page/1',
         'category': 'Coffee'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BEVERAGES/subcat/COFFEE/class/INSTANT%20COFFEE/page/1',
         'category': 'Coffee'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BEVERAGES/subcat/COFFEE/class/PRE-MIXED%20COFFEE/page/1',
         'category': 'Coffee'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BEVERAGES/subcat/COFFEE/class/READY-TO-DRINK%20COFFEE/page/1',
         'category': 'Coffee'},


        # NOODLES
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/GROCERY%20STAPLES/subcat/INSTANT%20NOODLES/class/CUP-%20DRY/page/1',
         'category': 'Noodles'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/GROCERY%20STAPLES/subcat/INSTANT%20NOODLES/class/CUP-%20WET/page/1',
         'category': 'Noodles'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/GROCERY%20STAPLES/subcat/INSTANT%20NOODLES/class/POUCH-%20DRY/page/1',
         'category': 'Noodles'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/GROCERY%20STAPLES/subcat/INSTANT%20NOODLES/class/POUCH-%20WET/page/1',
         'category': 'Noodles'},
        

        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/GROCERY%20STAPLES/subcat/PASTA%20&%20PANCIT/class/PANCIT-OTHER/page/1',
         'category': 'Noodles'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/GROCERY%20STAPLES/subcat/PASTA%20&%20PANCIT/class/PANCIT-VERMICILLI/page/1',
         'category': 'Noodles'},


        # LAUNDRY AIDS
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/HOUSEHOLD%20MAINTENANCE/subcat/LAUNDRY%20BLEACH/class/LAUNDRY%20BLEACH/page/1',
         'category': 'Laundry Aids'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/HOUSEHOLD%20MAINTENANCE/subcat/LAUNDRY%20DETERGENT/class/LAUNDRY%20DETERGENT/page/1',
         'category': 'Laundry Aids'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/HOUSEHOLD%20MAINTENANCE/subcat/LAUNDRY%20FABCON/class/LAUNDRY%20FABRIC%20CONDITIONER/page/1',
         'category': 'Laundry Aids'},

        # BREAD
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BAKERY/subcat/BREAD/class/BUNS%20AND%20ROLLS/page/1',
         'category': 'Bread'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BAKERY/subcat/BREAD/class/CAKES%20AND%20PASTRIES/page/1',
         'category': 'Bread'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BAKERY/subcat/BREAD/class/LOAVES/page/1',
         'category': 'Bread'},

        # WATER
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BEVERAGES/subcat/WATER/class/DISTILLED%20WATER/page/1',
         'category': 'Water'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BEVERAGES/subcat/WATER/class/FLAVORED%20WATER/page/1',
         'category': 'Water'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BEVERAGES/subcat/WATER/class/MINERAL%20WATER/page/1',
         'category': 'Water'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BEVERAGES/subcat/WATER/class/PURIFIED%20WATER/page/1',
         'category': 'Water'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/BEVERAGES/subcat/WATER/class/SPARKLING%20WATER/page/1',
         'category': 'Water'},

        # CANDLE
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/HOUSEHOLD%20MAINTENANCE/subcat/PAPER%20AND%20PLASTIC%20DISPOSA/class/PARTY%20FAVORS/page/1',
         'category': 'Candle'},

        # FISH SAUCE
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CONDIMENTS%20SAUCES%20&%20DRESS/subcat/CONDIMENTS%20&%20DRESSINGS/class/FISH%20PASTE/page/1',
         'category': 'Fish Sauce'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CONDIMENTS%20SAUCES%20&%20DRESS/subcat/CONDIMENTS%20&%20DRESSINGS/class/FISH%20SAUCE/page/1',
         'category': 'Fish Sauce'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CONDIMENTS%20SAUCES%20&%20DRESS/subcat/CONDIMENTS%20&%20DRESSINGS/class/SHRIMP%20PASTE/page/1',
         'category': 'Fish Sauce'},

        # SOY SAUCE
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CONDIMENTS%20SAUCES%20&%20DRESS/subcat/CONDIMENTS%20&%20DRESSINGS/class/SOY%20SAUCE/page/1',
         'category': 'Soy Sauce'},
         
        # VINEGAR
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CONDIMENTS%20SAUCES%20&%20DRESS/subcat/CONDIMENTS%20&%20DRESSINGS/class/CANE%20VINEGAR/page/1',
         'category': 'Vinegar'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CONDIMENTS%20SAUCES%20&%20DRESS/subcat/CONDIMENTS%20&%20DRESSINGS/class/CIDER%20VINEGAR/page/1',
         'category': 'Vinegar'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CONDIMENTS%20SAUCES%20&%20DRESS/subcat/CONDIMENTS%20&%20DRESSINGS/class/REGULAR%20FERMENTED%20VINEGAR/page/1',
         'category': 'Vinegar'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CONDIMENTS%20SAUCES%20&%20DRESS/subcat/CONDIMENTS%20&%20DRESSINGS/class/SPECIALTY%20VINEGAR/page/1',
         'category': 'Vinegar'},
        {'url': 'https://puregold.com.ph/pgcatalog/category/catalogclass/category/CONDIMENTS%20SAUCES%20&%20DRESS/subcat/CONDIMENTS%20&%20DRESSINGS/class/SPICED%20VINEGAR/page/1',
         'category': 'Vinegar'},
  
]

def scrape_category(category, url):
    """Scrape all products from a specific category page."""
    print(f"\n[INFO] Starting to scrape category: {category} from {url}")
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        print("[INFO] Page loaded successfully.")

        # Scroll to load all products
        SCROLL_PAUSE_TIME = 2
        last_height = driver.execute_script("return document.body.scrollHeight")
        print("[INFO] Starting infinite scrolling to load products...")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("[INFO] Scrolling complete.")
                break
            last_height = new_height

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        print("[INFO] Page source parsed successfully.")

        # Extract products
        products = []
        product_containers = soup.find_all('div', class_='Item')
        print(f"[INFO] Found {len(product_containers)} product containers on the page.")

        for container in product_containers:
            image_element = container.find('img', class_='Image')
            image = image_element['data-src'] if image_element else None

            title_element = container.find('div', class_='description-style')
            title = title_element.a.text.strip() if title_element and title_element.a else None

            url_element = container.find('a', href=True)
            product_url = url_element['href'] if url_element else None

            price_wrapper = container.find('div', class_='product-price-style')
            original_price = price_wrapper.text.strip() if price_wrapper else None

            discounted_price_element = price_wrapper.find('del') if price_wrapper else None
            discounted_price = discounted_price_element.text.strip() if discounted_price_element else None

            if title and product_url:
                print(f"[INFO] Scraped product: {title} | URL: {product_url}")
                products.append({
                    'title': title,
                    'url': product_url,
                    'image': image,
                    'original_price': original_price,
                    'discounted_price': discounted_price,
                })

        return products

    except Exception as e:
        print(f"[ERROR] Error while scraping category {category}: {e}")
        traceback.print_exc()
        return []
    finally:
        driver.quit()
        print("[INFO] WebDriver closed.")

def update_puregold_products():
    """Update Puregold products in the MongoDB."""
    print("[INFO] Fetching existing products for supermarket 'Puregold' from MongoDB.")
    
    # Fetch all existing products for "Puregold"
    puregold_products = list(collection.find({"supermarket": "Puregold"}))
    
    # Create a set of normalized (title, url) pairs for efficient lookup
    existing_products_map = {
        (p['title'].strip().lower(), p['url'].strip().lower().replace(" ", "")): p for p in puregold_products
    }

    updated_count = 0
    new_count = 0
    failed_count = 0

    print("[INFO] Starting update process for Puregold categories.")
    for entry in category_urls:
        category = entry['category']
        url = entry['url']

        print(f"\n[INFO] Processing category: {category}")
        try:
            # Scrape products for the current category
            scraped_products = scrape_category(category, url)
            
            for scraped_product in scraped_products:
                title = scraped_product['title'].strip()
                product_url = scraped_product['url'].strip()
                new_original_price = scraped_product['original_price']
                new_discounted_price = scraped_product['discounted_price']
                normalized_key = (title.lower(), product_url.lower().replace(" ", ""))

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
                        # Append the old price to the price_history
                        if old_original_price:
                            price_history.append({
                                "price": old_original_price,
                                "date_scraped": existing_product.get('date_scraped', '2023-09-01T00:00:00')  # Default to September 2023
                            })

                        # Append the new price to the price_history with the current timestamp
                        if new_original_price:
                            price_history.append({
                                "price": new_original_price,
                                "date_scraped": datetime.now().isoformat()
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
                    # New product: insert into MongoDB with both _id and id fields
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
                        'supermarket': 'Puregold',
                        'category': category,
                    }
                    
                    # Insert the product and get the generated _id
                    result = collection.insert_one(new_product)
                    # Add the id field as the string of the _id
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
update_puregold_products()
