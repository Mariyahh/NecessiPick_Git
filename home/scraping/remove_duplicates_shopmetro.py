from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']

def remove_duplicates_shopmetro():
    # Fetch all products with 'supermarket': 'ShopMetro'
    shopmetro_products = collection.find({"supermarket": "ShopMetro"})
    duplicates_removed = 0

    # Dictionary to track unique products by (title, url)
    unique_products = {}

    for product in shopmetro_products:
        # Unique key based on title and url
        key = (product['title'], product['url'])

        if key in unique_products:
            # Duplicate found, remove this product
            collection.delete_one({"_id": product["_id"]})
            print(f"Removed duplicate: {product['title']} | {product['url']}")
            duplicates_removed += 1
        else:
            # Add to unique products if not already present
            unique_products[key] = product["_id"]

    print(f"Total duplicates removed: {duplicates_removed}")

# Run the script
remove_duplicates_shopmetro()
