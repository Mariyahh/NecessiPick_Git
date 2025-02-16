from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']

def add_id_to_puregold_products():
    """Ensure all Puregold products have an 'id' field matching their '_id'."""
    puregold_products = collection.find({"supermarket": "Puregold"})
    updated_count = 0

    for product in puregold_products:
        if 'id' not in product:
            # Add 'id' field with the string value of '_id'
            collection.update_one(
                {"_id": product["_id"]},
                {"$set": {"id": str(product["_id"])}}
            )
            updated_count += 1
            print(f"[INFO] Added 'id' to product with title: {product['title']}")

    print(f"\n[INFO] Completed updating products. Total products updated: {updated_count}")

# Run the script
add_id_to_puregold_products()
