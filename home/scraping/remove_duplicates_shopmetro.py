from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']

def remove_duplicates_shopmetro():
    """Remove duplicate ShopMetro products from MongoDB."""
    print("[INFO] Starting duplicate removal for 'ShopMetro' products.")

    # Fetch all products with 'supermarket': 'ShopMetro'
    shopmetro_products = list(collection.find({"supermarket": "ShopMetro"}))
    duplicates_removed = 0

    # Dictionary to track unique products by normalized (title, url)
    unique_products = {}

    for product in shopmetro_products:
        # Normalize title and url to avoid duplicates due to minor differences
        normalized_title = product['title'].strip().lower() if 'title' in product else ''
        normalized_url = product['url'].strip().lower().replace(" ", "") if 'url' in product else ''
        key = (normalized_title, normalized_url)

        if key in unique_products:
            # Duplicate found, decide which one to keep
            existing_product = unique_products[key]

            # Prioritize the product with the description field
            if 'description' in product and 'description' not in existing_product:
                # Keep the current product and remove the previous one
                collection.delete_one({"_id": existing_product['_id']})
                print(f"[INFO] Removed older duplicate without description: {existing_product['title']} | {existing_product['url']}")
                unique_products[key] = product
            elif 'description' not in product and 'description' in existing_product:
                # Keep the existing product (do nothing)
                collection.delete_one({"_id": product["_id"]})
                print(f"[INFO] Removed duplicate without description: {product['title']} | {product['url']}")
            else:
                # Both have or both lack a description: keep the newer product
                if product['_id'] > existing_product['_id']:
                    # Keep the current product and remove the previous one
                    collection.delete_one({"_id": existing_product['_id']})
                    print(f"[INFO] Removed older duplicate: {existing_product['title']} | {existing_product['url']}")
                    unique_products[key] = product
                else:
                    # Remove the current product as it's older
                    collection.delete_one({"_id": product["_id"]})
                    print(f"[INFO] Removed duplicate: {product['title']} | {product['url']}")
            duplicates_removed += 1
        else:
            # Add to unique products if not already present
            unique_products[key] = product

    print(f"[INFO] Total duplicates removed: {duplicates_removed}")

# Run the script
remove_duplicates_shopmetro()
