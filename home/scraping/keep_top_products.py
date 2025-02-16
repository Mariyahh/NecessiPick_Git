from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']

SUPERMARKETS = ["Puregold", "ShopMetro", "WalterMart"]
LIMIT_PER_SUPERMARKET = 700

def keep_top_products():
    """Keep only the first 700 products per supermarket, prioritizing products with 'price_history'."""
    for supermarket in SUPERMARKETS:
        print(f"[INFO] Processing {supermarket}...")

        # Fetch products with 'price_history' first
        prioritized_products = list(collection.find(
            {"supermarket": supermarket, "price_history": {"$exists": True, "$ne": []}}
        ).sort("_id", 1).limit(LIMIT_PER_SUPERMARKET))

        # If there are not enough prioritized products, fetch the remaining needed
        remaining_slots = LIMIT_PER_SUPERMARKET - len(prioritized_products)
        if remaining_slots > 0:
            additional_products = list(collection.find(
                {"supermarket": supermarket, "price_history": {"$exists": False}}
            ).sort("_id", 1).limit(remaining_slots))
            prioritized_products.extend(additional_products)

        # Get the IDs to keep
        ids_to_keep = [product["_id"] for product in prioritized_products]
        print(f"[INFO] Keeping {len(ids_to_keep)} products for {supermarket}.")

        # Delete products not in the first 700
        delete_result = collection.delete_many({
            "supermarket": supermarket,
            "_id": {"$nin": ids_to_keep}
        })
        print(f"[INFO] Deleted {delete_result.deleted_count} excess products for {supermarket}.")

# Run the cleanup
keep_top_products()
