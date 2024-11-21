from typing import Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime  # Import datetime module

# Your webdriver path and Chrome options
webdriver_path = r'C:\Users\jenne\Desktop\chromedriver_win32\chromedriver.exe'
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument(f"webdriver.chrome.driver={webdriver_path}")

# Connect to MongoDB
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['qwerty']

def scrape_product_price(url, product_id):
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    # Implement your scraping logic here to get the new price
    # For example, find the original and discounted price elements and extract the price values
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    original_price_element = soup.find('span', class_='woocommerce-Price-amount amount').find('bdi')
    original_price = original_price_element.text.strip() if original_price_element else ''

    # You can similarly scrape the discounted price if it's available on the page
 
    driver.quit()

    # Update the product in MongoDB with the new price and date scraped
    current_date = datetime.utcnow().isoformat()  # Get the current date in ISO format
    

    # Prepare the update data
    update_data = {
        "$set": {
            "original_price": original_price,
        },
        "$push": {
            "price_history": {
                "price": original_price,
                "date_scraped": current_date
            }
        }
    }

    # Update the product in MongoDB based on the product_id
    collection.update_one({"id": product_id}, update_data)

# URLs and corresponding product IDs
url_to_product_id = {
    'https://shopmetro.ph/marketmarket-supermarket/product/bear-brand-adult-plus-300g/': '64e089c6536ea90428262ad7',
    'https://shopmetro.ph/marketmarket-supermarket/product/gardenia-regular-slice-600g/': '64e08ca4536ea90428262cbc',
    'https://shopmetro.ph/marketmarket-supermarket/product/alaska-evaporated-filled-milk-370ml/': '64e089a2536ea90428262abd',
    'https://shopmetro.ph/marketmarket-supermarket/product/san-marino-corned-tuna-180g/': '64e0895a536ea90428262a9d',
    'https://shopmetro.ph/marketmarket-supermarket/product/silver-swan-soy-sauce-200ml/': '64e08d26536ea90428262cfd',
    'https://shopmetro.ph/marketmarket-supermarket/product/argentina-meat-loaf-150g/': '64e088b1536ea90428262a2e',
    'https://shopmetro.ph/marketmarket-supermarket/product/cdo-karne-norte-100g/': '64e088cd536ea90428262a3f',
    'https://shopmetro.ph/marketmarket-supermarket/product/lorins-gin-plastic-super-patis-350ml/': '64e08cea536ea90428262cdb',
    'https://shopmetro.ph/marketmarket-supermarket/product/zonrox-bleach-original-1l/': '64e08c8d536ea90428262cb2',
    'https://shopmetro.ph/marketmarket-supermarket/product/wilkins-distilled-water-1l/': '64e08cc7536ea90428262ccf',


}

# Loop through the URLs and scrape/update the prices
for url, product_id in url_to_product_id.items():
    scrape_product_price(url, product_id)


    -----------------
    from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from django.shortcuts import render
import time
from pymongo import MongoClient
from django.utils.text import slugify

from .chatbot_module import generate_description
webdriver_path = r'C:\Users\jenne\OneDrive\Desktop\freelance\chromedriver_win32\chromedriver.exe'
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument(f"webdriver.chrome.driver={webdriver_path}")

# Connect to MongoDB
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['2024_Supermarket']


def scrape_website_1(url, category):
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    SCROLL_PAUSE_TIME = 2 
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    html_content = driver.page_source

    driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')

    product_containers = soup.find_all('div', class_='product-small')

    product_details = []

    for container in product_containers:
        image_element = container.find('img', class_='attachment-woocommerce_thumbnail')
        image = image_element['src'] if image_element else ''

        title_element = container.find('p', class_='name')
        title = title_element.a.text.strip() if title_element and title_element.a else ''

        price_element = container.find('span', class_='woocommerce-Price-amount')
        price = price_element.bdi.text.strip() if price_element else ''

        url_element = container.find('a', class_='woocommerce-LoopProduct-link')
        url = url_element['href'] if url_element else ''

        if any(product['title'] == title for product in product_details):
            continue

        description = generate_description(title, price)  # Generate description using ChatGPT

        product_details.append({
            'image': image,
            'title': title,
            'price': price,
            'url': url,
            'category': category,
            'supermarket': 'ShopMetro',
            'description': description,
        })

        # Save the product details into MongoDB
        collection.insert_one({
            'image': image,
            'title': title,
            'price': price,
            'url': url,
            'category': category,
            'supermarket': 'ShopMetro',
            'description': description,
        })

    return product_details




def compare(request):
    product_details_list = {}

    website_data = [
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/canned-goods/',
         'category': 'Canned Goods'},
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/milk/',
         'category': 'Milk'},
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/product-category/breakfast-world/coffee/',
         'category': 'Coffee'},
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/noodles/',
         'category': 'Noodles'},
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/product-category/home-care/laundry-aids/',
         'category': 'Laundry Aids'},
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/product-category/breakfast-world/bread/',
         'category': 'Bread'},
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/product-category/beverage-wines-liquor-and-spirits/water/',
         'category': 'Water'},
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/?s=candle&post_type=product&type_aws=true&aws_id=1&aws_filter=1&awscat=Form%3A1+Filter%3AAll',
         'category': 'Candle'},
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/condiments/fish-sauce/',
         'category': 'Fish Sauce'},
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/condiments/soy-sauce/',
         'category': 'Soy Sauce'},
        {'url': 'https://shopmetro.ph/marketmarket-supermarket/product-category/pantry-essentials/condiments/vinegar/',
         'category': 'Vinegar'}
    ]
    
    for website in website_data:
        category = website['category']
        products = collection.find({'category': category})
        product_details_list[category] = list(products)

    context = {
        'product_details_list': product_details_list,
    }
    return render(request, 'compare.html', context)

