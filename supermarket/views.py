from django.shortcuts import render
from pymongo import MongoClient
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import re
from collections import defaultdict  # Import defaultdict for category counts
from collections import Counter
from django.http import JsonResponse
from bson.json_util import dumps, ObjectId  # Import dumps and ObjectId
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from django.conf import settings

from fuzzywuzzy import fuzz

import uuid
from django.contrib.auth.decorators import login_required
from auth_system.views import like_dislike_collection as likes_dislikes_collection



client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']
dislike_like_collection = db['ProductLikesDislikes']

def find_similar_products(title, weight, brand, supermarket, collection):
    similar_products = []

    # Get the current supermarket's products
    current_supermarket_products = list(collection.find({'supermarket': supermarket}))

    # Create dictionaries to store the highest combined similarity score and corresponding product for each supermarket
    highest_combined_similarity_scores = {}
    highest_combined_similarity_products = {}

    # Iterate through the documents in the MongoDB collection
    for other_supermarket_product in collection.find({'supermarket': {'$ne': supermarket}}):
        # Calculate the similarity score between the input title and the product title
        title_similarity_score = fuzz.ratio(title.lower(), other_supermarket_product.get('title', '').lower())

        # Calculate the similarity score between the input weight and the product weight
        weight_similarity_score = fuzz.ratio(weight.lower(), other_supermarket_product.get('weight', '').lower())

        # Calculate the similarity score between the input brand and the product brand
        brand_similarity_score = fuzz.ratio(brand.lower(), other_supermarket_product.get('brand', '').lower())

        # You can adjust the threshold as needed to consider titles, weights, and brands similar
        if (
            title_similarity_score >= 65
            and weight_similarity_score >= 80
            and brand_similarity_score >= 80
        ):  # Adjust the thresholds as needed
            current_supermarket = other_supermarket_product['supermarket']
            # Calculate the combined similarity score
            combined_similarity_score = (
                title_similarity_score + weight_similarity_score + brand_similarity_score
            )

            # Check if we have a product for this supermarket and if the combined similarity score is higher
            if (
                current_supermarket not in highest_combined_similarity_scores
                or combined_similarity_score > highest_combined_similarity_scores[current_supermarket]
            ):
                highest_combined_similarity_scores[current_supermarket] = combined_similarity_score
                highest_combined_similarity_products[current_supermarket] = {
                    'title': other_supermarket_product.get('title', ''),
                    'supermarket': current_supermarket,
                    'original_price': other_supermarket_product.get('original_price', ''),
                    'url': other_supermarket_product.get('url', ''),
                    'image': other_supermarket_product.get('image', ''),
                    'title_similarity_score': title_similarity_score,
                    'weight_similarity_score': weight_similarity_score,
                    'brand_similarity_score': brand_similarity_score,
                    'combined_similarity_score': combined_similarity_score,  # Include the combined similarity score
                }

    # Convert the highest combined similarity products dictionary into a list
    similar_products = list(highest_combined_similarity_products.values())

    # Sort the similar products by combined similarity score (highest first)
    similar_products.sort(key=lambda x: x['combined_similarity_score'], reverse=True)
    print(f"Similar Products from other supermarkets: {similar_products}")  # Add this print statement

    return similar_products

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Quick View/template
def quickview_modal(request, product_id):

    product = collection.find_one({'id': product_id})

    # Get the product title
    product_title = product.get('title', '')
    product_price = product.get('original_price', '')
    product_supermarket = product.get('supermarket', '')
    product_image = product.get('image', '')

      # Calculate the like and dislike counts for the product
    like_count = dislike_like_collection.count_documents({'product_id': product_id, 'action': 'like'})
    dislike_count = dislike_like_collection.count_documents({'product_id': product_id, 'action': 'dislike'})
    

    
    context = {
        'product':product,
        'product_title': product_title,
        'product_price': product_price,
        'product_supermarket': product_supermarket,
        'product_image': product_image,
        'like_count': like_count,
        'dislike_count': dislike_count,
    }
   
    return render(request, 'supermarket/quickview_modal.html', context)

# Function to get the number of likes for a product
def get_likes_count(product, dislike_like_data):
    likes_count = sum(1 for item in dislike_like_data if item['product_id'] == product['id'] and item['action'] == 'like')
    return likes_count

# Function to get the number of dislikes for a product
def get_dislikes_count(product, dislike_like_data):
    dislikes_count = sum(1 for item in dislike_like_data if item['product_id'] == product['id'] and item['action'] == 'dislike')
    return dislikes_count

# All categories 
def supermarket_page(request, supermarket_name):
    # Retrieve products from the selected supermarket
    # products = collection.find({'supermarket': supermarket_name})
    dislike_like_data = list(dislike_like_collection.find({}))

    all_products =list(collection.find({'supermarket': supermarket_name}))

    # Define banner image URLs for each supermarket (adjust these URLs as needed)
    supermarket_banners = {
        'WalterMart': '/static/imgs/banner/waltermart.png',
        'Puregold': '/static/imgs/banner/puregold.png',
        'ShopMetro': '/static/imgs/banner/shopmetro2.png',
    }
    # Get the banner image URL for the selected supermarket
    banner_image_url = supermarket_banners.get(supermarket_name)

    # Calculate category counts for the selected supermarket
    category_counts = Counter(product['category'].replace(' ', '_') for product in all_products)
    # Calculate the total number of products for the selected supermarket
    total_products = len(all_products)
    # Calculate the number of likes and dislikes in every product then display
    for product in all_products:
        product['like_count'] = get_likes_count(product, dislike_like_data)
        product['dislike_count'] = get_dislikes_count(product, dislike_like_data)

 
    # %%%%%%%%%%%%%%%%%%%%%%%%%
    # Create a custom paginator
    # Create a Paginator object with 20 products per page
    paginator = Paginator(all_products, 20)
    # Get the requested page number from the URL query parameters
    page = request.GET.get('page')

    try:
        # Try to get the products for the requested page
        product_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, default to page 1
        product_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., page 9999), deliver the last page of results
        product_page = paginator.page(paginator.num_pages)
    
   
    context = {
        'supermarket_name': supermarket_name,
        'all_products': all_products,
        'product_page': product_page,  # Pass the paginated products to the template
        'total_products': total_products,  # Pass the total number of products for the selected category
        'category_counts': category_counts,
        'banner_image_url': banner_image_url,
       
    }
    return render(request, 'supermarket/supermarket_page.html', context)



# product per category
def supermarket_category(request, supermarket_name, category_name):
    categories = collection.distinct('category', {'supermarket': supermarket_name})
    dislike_like_data = list(dislike_like_collection.find({}))

    # Create a dictionary to store product by category
    product_by_category = {}

    # # Retrieve products for each category
    # for category in categories:
    #     products = collection.find({'supermarket': supermarket_name, 'category': category_name})
    #     product_by_category[category] = list(products)


    products = list(collection.find({'supermarket': supermarket_name, 'category': category_name}))
    all_products =list(collection.find({'supermarket': supermarket_name}))

    # Update the products list to include like and dislike counts
    for product in products:
        product['like_count'] = get_likes_count(product, dislike_like_data)
        product['dislike_count'] = get_dislikes_count(product, dislike_like_data)
    
    # Get the selected sorting option from the URL query parameters
    sort_option = request.GET.get('sort')

    if sort_option == 'likes':
        # Sort by highest likes
        products.sort(key=lambda product: get_likes_count(product, dislike_like_data), reverse=True)
    elif sort_option == 'dislikes':
        # Sort by highest dislikes
        products.sort(key=lambda product: get_dislikes_count(product, dislike_like_data), reverse=True)
    else:
        # Default sorting (e.g., by price)
        sorting_key = None  # Your existing sorting logic here


    
    # Get the selected sorting option from the URL query parameters
    sort_option = request.GET.get('sort')

    # Get the selected price range from the URL query parameters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Get the selected supermarket from the URL query parameters
    selected_supermarket = request.GET.get('supermarket')

    # Filter products based on the selected price range
    if min_price is not None and max_price is not None:
        min_price = float(min_price)
        max_price = float(max_price)
        products = [product for product in products if min_price <= get_price(product) <= max_price]

    # Filter products based on the selected supermarket (if provided)
    if selected_supermarket and selected_supermarket != 'None':
        products = [product for product in products if product['supermarket'] == selected_supermarket]

     # Determine the sorting key based on the selected option
    if sort_option == 'price_low_to_high':
        sorting_key = 'discounted_price'  # Sort by discounted price ascending
    elif sort_option == 'price_high_to_low':
        sorting_key = '-discounted_price'  # Sort by discounted price descending
    else:
        sorting_key = None  # Default: No sorting

    if sorting_key:
        # Sort the entire list of products based on the sorting key
        products = sort_products(products, sort_option)


    # Calculate the total number of products for the selected category
    total_products = len(products)

    # # Calculate category counts for the selected supermarket
    category_counts = Counter(product['category'].replace(' ', '_') for product in all_products)

    # Create a Paginator object with 20 products per page
    paginator = Paginator(products, 20)
   
    # Get the requested page number from the URL query parameters
    page = request.GET.get('page')

    try:
        # Try to get the products for the requested page
        product_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, default to page 1
        product_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., page 9999), deliver the last page of results
        product_page = paginator.page(paginator.num_pages)
    

    context = {
        'supermarket': supermarket_name,
        # 'category': category_name,
        'categories': categories,
        'category_name': category_name,
        'products': products,
        'product_by_category' : product_by_category,

        'product_page': product_page,  # Pass the paginated products to the template
        'total_products': total_products,
        'category_counts': category_counts,
        'sort_option': sort_option,


    }

    return render(request, 'supermarket/supermarket_category.html', context)


def sort_products(products, sort_option):
    # Filter out products with None prices before sorting
    products = [product for product in products if get_price(product) is not None]

    if sort_option == 'price_low_to_high':
        sorted_products = sorted(products, key=lambda x: get_price(x))
    elif sort_option == 'price_high_to_low':
        sorted_products = sorted(products, key=lambda x: get_price(x), reverse=True)
    else:
        sorted_products = products  # Default: no sorting

    return sorted_products


def get_price(product):
    # Try to get the discounted price, then the original price, and default to None if both are missing
    price_str = product.get('discounted_price') or product.get('original_price')

    if price_str:
        # Remove non-numeric characters and spaces from the price string
        cleaned_price_str = re.sub(r'[^\d.]', '', price_str)

        if cleaned_price_str:
            # Try to convert the cleaned price string to a float
            return float(cleaned_price_str)

    # Return None if price information is missing or cannot be converted
    return None

#


def get_nearest_supermarkets(lat, lng, supermarket_name):
    """Fetch nearest supermarkets using Google Places API."""
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 5000,
        "keyword": supermarket_name,
        "type": "supermarket",
        "key": settings.GEOLOCATION_API_KEY,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def get_supermarket_details(place_id):
    """Fetch supermarket details using Google Places API."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,rating,opening_hours,formatted_address,reviews",
        "key": settings.GEOLOCATION_API_KEY,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json().get("result", {})
        # Add isOpen status and limit reviews to the latest 3
        result["isOpen"] = result.get("opening_hours", {}).get("open_now", False)
        result["reviews"] = sorted(result.get("reviews", []), key=lambda x: x.get("time", 0), reverse=True)[:3]
        return result
    return {}

@csrf_exempt
def compare_modal(request, product_id=None):
    if request.method == "GET" and product_id:
        try:
            # Fetch product details
            product = collection.find_one({'id': product_id})

            product_title = product.get('title', '')
            product_weight = product.get('weight', '')
            product_brand = product.get('brand', '')
            product_price = product.get('original_price', '')
            product_supermarket = product.get('supermarket', '')
            product_image = product.get('image', '')

            # Find similar products
            similar_products = find_similar_products(
                product_title, product_weight, product_brand, product_supermarket, collection
            )

            # Collect supermarkets from similar products and ensure the current product's supermarket is included
            supermarket_names = [sp['supermarket'] for sp in similar_products[:2]]
            if product_supermarket not in supermarket_names:
                supermarket_names.append(product_supermarket)

            # Fetch the two nearest supermarkets for each similar product's supermarket
            user_lat, user_lng = 14.6407, 121.0024  # Replace with actual user location
            places_results = {}

            for supermarket in supermarket_names:
                nearest_supermarkets = get_nearest_supermarkets(user_lat, user_lng, supermarket)
                # Get detailed information for the two nearest supermarkets
                details = [
                    get_supermarket_details(s.get("place_id"))
                    for s in nearest_supermarkets[:2]  # Take only the first two
                    if s.get("place_id")
                ]
                places_results[supermarket] = details

            # Prepare context for rendering
            context = {
    'similar_products': similar_products,
    'product_title': product_title,
    'product_price': product_price,
    'product_supermarket': product_supermarket,
    'product_image': product_image,
    'places_results': {
        'selected': places_results.get(product_supermarket, []),  # Selected supermarket details
        'similar': {key: value for key, value in places_results.items() if key != product_supermarket},  # Similar supermarkets
    },
}

            return render(request, 'supermarket/compare_modal.html', context)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)
