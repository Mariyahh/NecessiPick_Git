from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']

def remove_duplicates_waltermart():
    """Remove duplicate WalterMart products based on title, prioritizing those with a description."""
    print("[INFO] Starting duplicate removal for 'WalterMart' products based on title.")

    # Fetch all products with 'supermarket': 'WalterMart'
    waltermart_products = list(collection.find({"supermarket": "WalterMart"}))
    duplicates_removed = 0

    # Dictionary to track unique products by normalized title
    unique_titles = {}

    for product in waltermart_products:
        # Normalize title to avoid duplicates due to minor differences
        normalized_title = product['title'].strip().lower() if 'title' in product else ''
        
        if normalized_title in unique_titles:
            # Duplicate found, decide which one to keep
            existing_product = unique_titles[normalized_title]

            # Prioritize the product with the description field
            if 'description' in product and 'description' not in existing_product:
                # Keep the current product and remove the previous one
                collection.delete_one({"_id": existing_product['_id']})
                print(f"[INFO] Removed older duplicate without description: {existing_product['title']}")
                unique_titles[normalized_title] = product
            elif 'description' not in product and 'description' in existing_product:
                # Keep the existing product (do nothing)
                collection.delete_one({"_id": product["_id"]})
                print(f"[INFO] Removed duplicate without description: {product['title']}")
            else:
                # Both have or both lack a description: keep the newer product
                if product['_id'] > existing_product['_id']:
                    # Keep the current product and remove the previous one
                    collection.delete_one({"_id": existing_product['_id']})
                    print(f"[INFO] Removed older duplicate: {existing_product['title']}")
                    unique_titles[normalized_title] = product
                else:
                    # Remove the current product as it's older
                    collection.delete_one({"_id": product["_id"]})
                    print(f"[INFO] Removed duplicate: {product['title']}")
            duplicates_removed += 1
        else:
            # Add to unique products if not already present
            unique_titles[normalized_title] = product

    print(f"[INFO] Total duplicates removed: {duplicates_removed}")

# Run the script
remove_duplicates_waltermart()
