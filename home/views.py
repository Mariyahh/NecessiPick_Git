from typing import Any
from django.shortcuts import render, redirect
from pymongo import MongoClient
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from fuzzywuzzy import fuzz  
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from uuid import uuid4
from bson import ObjectId
from pymongo import DESCENDING

from datetime import datetime  
from django.db.models import Q
from django.http import JsonResponse
from bson.json_util import dumps
from django.db.models import Sum
from .forms import ContactForm

import re
import json
import logging
import nltk
import random

from django.views.decorators.csrf import csrf_exempt
import uuid
from django.contrib.auth.decorators import login_required
from auth_system.views import like_dislike_collection as likes_dislikes_collection
import requests
from django.shortcuts import render, HttpResponseRedirect
from django.conf import settings
from django.contrib import messages
from auth_system.models import UserProfile

# Initialize NLTK stopwords
nltk.download("stopwords")
from nltk.corpus import stopwords
stop_words = set(stopwords.words("english"))

logger = logging.getLogger(__name__)


# Connect to MongoDB
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']

comments_collection = db['Comments']
user_collection = db['Users']
favorites_collection = db['FavoritesFinal']
clicks_collection = db['UserClicks']


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


# Preprocess text: remove stopwords, punctuation, and extra spaces
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = " ".join([word for word in text.split() if word not in stop_words])  # Remove stopwords
    return text

def extract_weight(title):
    # Define regular expression patterns to match various weight/quantity units
    weight_patterns = [
        r'\b\d+\s*(?:g|grams|kg|kilograms|oz|ounces|lb|pounds)\b',
        r'\b\d+\s*(?:ml|milliliters)\b',
    ]

    for pattern in weight_patterns:
        # Search for the pattern in the title
        weight_match = re.search(pattern, title, re.IGNORECASE)

        if weight_match:
            return weight_match.group()

    # If no matching pattern is found, return None
    return None


# Calculate similarity using TF-IDF and Cosine Similarity
def calculate_similarity(input_title, product_titles):
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform([input_title] + product_titles)
    cosine_similarities = linear_kernel(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    return cosine_similarities

# Find similar products based on similarity scores within a threshold range
def find_similar_products(title):
    product_titles = [p.get('title', '') for p in collection.find()]

    # Split the input title into product name and weight/grams
    input_title_parts = re.split(r'\s+\|\s+', title)
    input_name = input_title_parts[0]
    input_weight = input_title_parts[-1]

    # Preprocess input title parts
    input_name = preprocess_text(input_name)
    input_weight = preprocess_text(input_weight)

    title_parts_list = [re.split(r'\s+\|\s+', product_title) for product_title in product_titles]
    product_names = [preprocess_text(parts[0]) for parts in title_parts_list]
    product_weights = [preprocess_text(parts[-1]) for parts in title_parts_list]

    # Fetch the category names
    product_categories = [p.get('category', '') for p in collection.find()]

    similarity_scores = calculate_similarity(input_name, product_names)

    similar_products = []
    for i, score in enumerate(similarity_scores):
        if 0.50 <= score <= 0.9:  # Adjust the threshold range as needed
            # Check if the weight/grams are similar
            if fuzz.ratio(input_weight, product_weights[i]) >= 80:  # Adjust the similarity threshold as needed
                product_doc = collection.find()[i]  # Get the MongoDB document
                similar_products.append({
                    'title': product_titles[i],
                    'supermarket': product_doc.get('supermarket', ''),  # Fetch the 'supermarket' field
                    'original_price': product_doc.get('original_price', ''),  # Fetch the 'original_price' field
                    'url': product_doc.get('url', ''),  # Fetch the 'url' field
                    'similarity_score': score,
                    'category': product_categories[i],  # Add the category name
                })

    similar_products.sort(key=lambda x: x['similarity_score'], reverse=True)

    return similar_products




# Function to get the number of likes for a product
def get_likes_count(product, dislike_like_data):
    likes_count = sum(1 for item in dislike_like_data if item['product_id'] == product['id'] and item['action'] == 'like')
    return likes_count

# Function to get the number of dislikes for a product
def get_dislikes_count(product, dislike_like_data):
    dislikes_count = sum(1 for item in dislike_like_data if item['product_id'] == product['id'] and item['action'] == 'dislike')
    return dislikes_count

def search(request):
    search_query = request.GET.get('search_query', '')
    # Assuming product ID is stored under 'id' field in MongoDB
    search_results_list = list(collection.find({"title": {"$regex": search_query, "$options": "i"}}))
    
    # Create a list of products that includes id for each product with a '/' slash at the end
    products = [{'id': f"{item['id']}/", 'title': item['title']} for item in search_results_list] if search_results_list else []
    
    return JsonResponse({'search_results': products})



def get_product_title(product_id):
    sept_final_final_collection = db['Sept_FInal_Final']
    product = sept_final_final_collection.find_one({'id': product_id})
    if product:
        return product['title']
    return "Product Not Found"  # Handle the case where the product is not found


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def about_us(request):
    return render(request, 'aboutus.html')
# def get_random_comments(num_comments):
#     comments_collection = db['Comments']
#     comments_data = list(comments_collection.find({}))
#     random_comments = random.sample(comments_data, num_comments)
#     return random_comments
def discounts(request):
    # Fetch products with discounted prices
    discounted_products = list(collection.find({'discounted_price': {'$exists': True}}))

    # Get the selected supermarket from query parameters
    selected_supermarket = request.GET.get('supermarket')

    # Filter products if a supermarket is selected
    if selected_supermarket:
        discounted_products = [product for product in discounted_products if product['supermarket'] == selected_supermarket]

    # Implement pagination
    paginator = Paginator(discounted_products, 15)
    page = request.GET.get('page')

    try:
        product_page = paginator.page(page)
    except PageNotAnInteger:
        product_page = paginator.page(1)
    except EmptyPage:
        product_page = paginator.page(paginator.num_pages)

    # Pass the selected supermarket to the context
    context = {
        'discounted_products': product_page,
        'selected_supermarket': selected_supermarket,
    }

    return render(request, 'discounts.html', context)


def get_latest_comments(num_comments):
    comments_collection = db['Comments']
    
    # Sort comments by timestamp in descending order and limit to the specified number
    latest_comments = comments_collection.find({}).sort("timestamp", DESCENDING).limit(num_comments)
    
    return list(latest_comments)
def home(request): 
   
    product_details_list = {}
     # Fetch data from MongoDB
    categories = collection.distinct('category')
    for category in categories:
        products = collection.find({'category': category})
        product_details_list[category] = list(products)

    # Create a list to store the randomly selected products
    random_shopmetro = []
    random_waltermart = []
    random_puregold = []

# for dropdown
    for category, products in product_details_list.items():
        if products:
            random_products = random.sample(products, 5)  # Select 4 random products
            for product in random_products:
                if product['supermarket'] == 'ShopMetro':
                    random_shopmetro.append(product)
                elif product['supermarket'] == 'WalterMart':
                    random_waltermart.append(product)
                elif product['supermarket'] == 'Puregold':
                    random_puregold.append(product)
    # Shuffle the lists to randomize their order
    random.shuffle(random_shopmetro)
    random.shuffle(random_waltermart)
    random.shuffle(random_puregold)
# for likes and dislike

    dislike_like_collection = db['ProductLikesDislikes']
    dislike_like_data = list(dislike_like_collection.find({}))
    for category, products in product_details_list.items():
        for product in products:
            product['like_count'] = get_likes_count(product, dislike_like_data)
            product['dislike_count'] = get_dislikes_count(product, dislike_like_data)

    def get_reaction_count(product_id, action_type):
        return sum(1 for entry in dislike_like_data if entry['product_id'] == product_id and entry['action'] == action_type)

# for comments
    num_comments_to_fetch = 5  # Fetch the latest 5 comments
    latest_comments = get_latest_comments(num_comments_to_fetch)
    users_collection = db['Users']
    user_info = []

    for comment in latest_comments:
        user_id = comment['user_id']
        user = users_collection.find_one({'user_id': user_id})

        user_profile = UserProfile.objects.filter(user__id=user_id).first()
        profile_picture_url = user_profile.profile_picture.url if user_profile and user_profile.profile_picture else 'default_profile.png'

        # Fetch the product title for the comment
        product_id = comment['product_id']
        product_title = get_product_title(product_id)
        # Get actual like and dislike counts for each product
        like_count = get_reaction_count(product_id, 'like')
        dislike_count = get_reaction_count(product_id, 'dislike')

        user_info.append({
            'fname': user['fname'],
            'lname': user['lname'],
            'username': user['username'],
            'product_title': product_title,
            'comment_text': comment['text'],
            'profile_picture_url': profile_picture_url,
            'dislike_count': dislike_count, # Add dislike count
            'comment_date': comment.get('timestamp').strftime("%d/%m/%Y") if comment.get('timestamp') else "N/A"

        })

# for discounts
    random_discount = []
    random.shuffle(random_discount)
    random_discount = random_discount[:7]
    for category, products in product_details_list.items():
        discounted_products = [product for product in products if product.get('discounted_price')]
        if discounted_products:
            random_product = random.choice(discounted_products)
            random_discount.append(random_product)

     # Sorting based on the 'sort' query parameter
    sort_option = request.GET.get('sort')
    for category, products in product_details_list.items():
        product_details_list[category] = sort_products(products, sort_option)

   

    context = {
        'product_details_list': product_details_list,
        'random_shopmetro': random_shopmetro,
        'random_waltermart': random_waltermart,
        'random_puregold': random_puregold,        
        'random_discount': random_discount, 
        'products': products, #added
        'random_comments': user_info,
        # 'random_comments': user_info,  # Pass the user information to the template

    }
    return render(request, 'index.html', context)


def category(request, category_name):
    dislike_like_collection = db['ProductLikesDislikes']
    dislike_like_data = list(dislike_like_collection.find({}))
    # Retrieve products for the specified category from MongoDB
    products = list(collection.find({'category': category_name}))  # Convert cursor to list

    # Get the selected sorting option from the URL query parameters
    sort_option = request.GET.get('sort')
     # Update the products list to include like and dislike counts
    for product in products:
        product['like_count'] = get_likes_count(product, dislike_like_data)
        product['dislike_count'] = get_dislikes_count(product, dislike_like_data)

    # Get the selected price range from the URL query parameters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Get the selected supermarket from the URL query parameters
    selected_supermarket = request.GET.get('supermarket')

   # Connect to the ProductLikesDislikes collection


    if sort_option == 'likes':
        # Sort by highest likes
        products.sort(key=lambda product: get_likes_count(product, dislike_like_data), reverse=True)
    elif sort_option == 'dislikes':
        # Sort by highest dislikes
        products.sort(key=lambda product: get_dislikes_count(product, dislike_like_data), reverse=True)
    else:
        # Default sorting (e.g., by price)
        sorting_key = None  # Your existing sorting logic here


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

    # Create a Paginator object with 20 products per page
    paginator = Paginator(products, 20)

    # Get the requested page number from the URL query parameters~
    page = request.GET.get('page')

    try:
        # Try to get the products for the requested page
        product_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, default to page 1~
        product_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., page 9999), deliver the last page of results
        product_page = paginator.page(paginator.num_pages)

    # Implement sorting and price filtering as needed (similar to your current code)

    context = {
        'product_page': product_page,  # Pass the paginated products to the template
        'total_products': total_products,  # Pass the total number of products for the selected category
        'sort_option': sort_option,  # Pass the selected sorting option to the template
        'category_name': category_name,
        'min_price': min_price,  # Pass the selected min price to the template
        'max_price': max_price,
        'selected_supermarket': selected_supermarket,  # Pass the selected supermarket to the template
    }

    return render(request, 'category.html', context)
# Function to get the number of likes for a product





# Modify the product_detail view to find similar products
def product_detail(request, product_id):
    product = collection.find_one({'id': product_id})
    comments = comments_collection.find({'product_id': product_id})

    # Get the current user
    user = request.user

    # Check if the user has already liked or disliked this product
    user_interaction = likes_dislikes_collection.find_one({'user_id': user.id, 'product_id': product_id})

    # Check if the user has already commented on this product
    user_has_commented = comments_collection.find_one({'user_id': user.id, 'product_id': product_id})

    # Count the number of comments for the product
    comment_count = comments_collection.count_documents({'product_id': product_id})
    print("Comment Count:", comment_count)

     # Calculate the like and dislike counts for the product
    like_count = likes_dislikes_collection.count_documents({'product_id': product_id, 'action': 'like'})
    dislike_count = likes_dislikes_collection.count_documents({'product_id': product_id, 'action': 'dislike'})
    

    # Get the product title
    product_title = product.get('title', '')
    supermarket = product.get('supermarket', '') #added

    # Use the find_similar_products function to find similar products
    similar_products = find_similar_products(product_title)

    # Create a separate list for products from the same supermarket
    products_same_supermarket = [p for p in similar_products if p.get('supermarket') == supermarket]

    # Get 4 random products from the same supermarket #########        ADDED
    random_products = list(collection.aggregate([
        {'$match': {'supermarket': supermarket, 'category': product.get('category', '')}},
        {'$sample': {'size': 4}}
    ]))

    # Exclude the current product from the list
    random_products = [p for p in random_products if p.get('id') != product_id]
    #########        ADDED

    print("Random:", random_products)

    # Get the historical price data for the product
    price_history = product.get('price_history', [])

    # Format the date in the price history data
    formatted_price_history = []
    for entry in price_history:
        date_scraped = entry.get('date_scraped')
        if date_scraped:
            # Parse the date from ISO format
            date_object = datetime.fromisoformat(date_scraped)

            # Format the date as "Month Year"
            formatted_date = date_object.strftime('%B %Y')

            # Create a new entry with the formatted date
            formatted_entry = {
                'price': entry.get('price', ''),
                'date_scraped': formatted_date,
            }

            formatted_price_history.append(formatted_entry)

    # Serialize the formatted price history data to JSON
    formatted_price_history_json = json.dumps(formatted_price_history)

    # Log the price data to the console for debugging
    logging.debug(f'Product ID: {product_id}, Price History: {formatted_price_history}')

    context = {
        'product': product,
        'similar_products': similar_products,  # Pass the list of similar products to the template
        'random_products': random_products,
        'formatted_price_history_json': formatted_price_history_json,
        'has_price_history': bool(formatted_price_history),  # Check if price history exists

        'user_interaction': user_interaction,
        'like_count': like_count,
        'dislike_count': dislike_count,
        'comment_count': comment_count,
        'comments': comments,
        'user_has_commented': user_has_commented is not None,
    }
    return render(request, 'product_detail.html', context)



def discounts(request):
    # Fetch all products with a discounted price from MongoDB
    discounted_products = list(collection.find({'discounted_price': {'$exists': True}}))

    # Get the selected supermarket from the URL query parameters
    selected_supermarket = request.GET.get('supermarket')

    # Filter products based on the selected supermarket (if provided)
    if selected_supermarket and selected_supermarket != 'None':
        discounted_products = [product for product in discounted_products if product['supermarket'] == selected_supermarket]


    # Create a Paginator object with 15 products per page
    paginator = Paginator(discounted_products, 15)

    # Get the requested page number from the URL query parameters
    page = request.GET.get('page')

    try:
        # Try to get the products for the requested page
        product_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, default to page 1
        product_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver the last page of results
        product_page = paginator.page(paginator.num_pages)

    context = {
        'discounted_products': product_page,
        'selected_supermarket': selected_supermarket,
    }

    return render(request, 'discounts.html', context)


@login_required
def chart(request):
    # You can add any context data if needed
    context = {
        'example_data': 'Hello from the new template!',
    }

    return render(request, 'chart.html', context)


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# ADDITIONALS


# def contact_us(request):
#     if request.method == 'POST':
#         message = request.POST['message']
#         subject = request.POST['subject']
#         name = request.POST['name']
#         from_email = request.POST['email']

#         # Forming the message
#         email_text = f'''
#         You have received a new message from NecessiPick contact form:

#         Subject: {subject}
#         Name: {name}
#         Email: {from_email}
#         Message:
#         {message}
#         '''

#         try:
#             response = requests.post(
#                 f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
#                 auth=('api', settings.MAILGUN_API_KEY),
#                 data={
#                     'from': from_email,
#                     'to': settings.EMAIL_HOST_USER,
#                     'subject': 'NecessiPick contact form',
#                     'text': email_text
#                 }
#             )

#             if response.status_code == 200:
#                 # Add a success message if the email is sent successfully
#                 messages.success(request, 'Your message has been sent successfully!')
#             else:
#                 # Add an error message if there is an issue with the Mailgun API request
#                 messages.error(request, 'There was an error sending your message. Please try again later.')

#         except Exception as e:
#             print(f"Mailgun API error: {e}")
#             # Add an error message if there is an exception
#             messages.error(request, 'There was an error sending your message. Please try again later.')

#         return HttpResponseRedirect(request.path_info)  # Redirect to the same page

#     return render(request, 'contactus.html')


import requests
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def contact_us(request):
    if request.method == 'POST':
        message = request.POST['message']
        subject = request.POST['subject']
        name = request.POST['name']
        from_email = request.POST['email']

        # Forming the message
        email_text = f'''
        You have received a new message from NecessiPick contact form:

        Subject: {subject}
        Name: {name}
        Email: {from_email}
        Message:
        {message}
        '''

        # Configure the Brevo API client
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY  # Replace with your Brevo API key
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        # Create the Brevo email object
        sender = {"email": settings.EMAIL_HOST_USER, "name": "Recipient Name"}  # Replace with your sender details
        to = [{"email": 'necessipick@gmail.com', "name": "Necessipick"}]  # Replace with your recipient details

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            subject='NecessiPick contact form',
            html_content=email_text,
            sender=sender,
        )

        try:
            # Send the transactional email
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(api_response)
            messages.success(request, 'Your message has been sent successfully!')
        except ApiException as e:
            print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
            messages.error(request, 'There was an error sending your message. Please try again later.')

        return HttpResponseRedirect(request.path_info)  # Redirect to the same page

    return render(request, 'contactus.html')





# This funciton is responsible for fetching the similar products to be added to the shopping list
# This function is similar to the "find_similar_products" in supermarket>views.py
def find_compare_products(user_id, title, weight, brand, supermarket, collection, favorites_collection):
    similar_products = []

    # Create dictionaries to store the highest similar product for each supermarket
    highest_similarity_per_supermarket = {}

    # ADDED -----------------------------
    # Get the user's favorite products
    user_favorites = favorites_collection.find({'user_id': user_id}, {'id': 1})

    # Extract product IDs from user favorites
    user_favorite_ids = [favorite['id'] for favorite in user_favorites]
    # END ADDED -----------------------------

    # Iterate through the documents in the MongoDB collection
    for other_supermarket_product in collection.find({'supermarket': {'$ne': supermarket}}):
        ############# ADDED ----------------------------
        # Skip products that are already in the user's favorites
        if other_supermarket_product['id'] in user_favorite_ids:
            continue
        ############# END ADDED ----------------------------


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

            # Check if we have a product for this supermarket and if it has the highest similarity score
            if (
                current_supermarket not in highest_similarity_per_supermarket
                or combined_similarity_score > highest_similarity_per_supermarket[current_supermarket]['combined_similarity_score']
            ):
                highest_similarity_per_supermarket[current_supermarket] = {
                    'id': other_supermarket_product.get('id', ''),
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

    # Convert the highest similar products for each supermarket into a list
    similar_products = list(highest_similarity_per_supermarket.values())

    # Sort the similar products by combined similarity score (highest first)
    similar_products.sort(key=lambda x: x['combined_similarity_score'], reverse=True)
    print(f"Similar Products from other supermarkets: {similar_products}\n")  # Add this print statement

    return similar_products


 

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# ADDITIONS NI MARI


@login_required
def toggle_like_dislike(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')  # 'like' or 'dislike'

        # Get the current user
        user = request.user

        # Check if the user has already liked or disliked this product
        user_interaction = likes_dislikes_collection.find_one({'user_id': user.id, 'product_id': product_id})

        # Prepare an update query to update the MongoDB collection
        update_query = {
            'user_id': user.id,
            'product_id': product_id,
        }

        if user_interaction:
            if user_interaction['action'] == action:
                # User clicked the same button again, remove the interaction
                likes_dislikes_collection.delete_one(update_query)
                result = 'removed'
            else:
                # User changed their action, update the interaction
                likes_dislikes_collection.update_one(update_query, {'$set': {'action': action}})
                result = 'updated'
        else:
            # User is interacting with this product for the first time, create a new interaction
            update_query['action'] = action
            likes_dislikes_collection.insert_one(update_query)
            result = 'added'

        # Add information about the user's interaction in the response
        response_data = {
            'result': result,
            'user_interaction': user_interaction,
            'action': action
        }

        return JsonResponse({'result': result})

@login_required
def add_comment(request, product_id):
    if request.method == 'POST':
        user = request.user
        comment_text = request.POST.get('comment_text')

        user_id = user.id
        user_data = user_collection.find_one({'user_id': user_id})

        if user_data:
            user_name = user_data['username']
        else:
            user_name = 'Anonymous'

        # Generate a unique comment_id using UUID
        comment_id = str(uuid4())

        # Check if the user has already commented on this product
        existing_comment = comments_collection.find_one({'user_id': user_id, 'product_id': product_id})

        if existing_comment:
            # You can choose to handle this case differently, e.g., show an error message
            return HttpResponseForbidden("You have already commented on this product.")

        comment_data = {
            'comment_id': comment_id,
            'user_id': user_id,
            'user_name': user_name,
            'product_id': product_id,
            'text': comment_text,
            'timestamp': datetime.now(),
        }

        comments_collection.insert_one(comment_data)

        return redirect('home:product_detail', product_id=product_id)
    else:
        # Render the comment form or a template where users can add comments
        return render(request, 'product_detail.html')


########################### BAGO TO FOR DELETING COMMENTS
@login_required
def delete_comment(request, comment_id):
    # Directly query MongoDB to find the comment
    comment = comments_collection.find_one({'comment_id': comment_id, 'user_id': request.user.id})

    if comment:
        # If comment is found, delete it
        comments_collection.delete_one({'comment_id': comment_id})
        return JsonResponse({'result': 'success'})
    else:
        # If comment is not found, return an error
        return JsonResponse({'result': 'error'}, status=404)




@login_required 
def add_to_favorites(request, product_id):
    # Retrieve the product from the original collection
    product = collection.find_one({'id': product_id})

    if not product:
        return HttpResponse("Product not found.", status=404)

    # Get the current user
    user = request.user

    # Check if the product is already in the favorites collection
    existing_favorite = favorites_collection.find_one({'user_id': user.id, 'id': product_id})

    if existing_favorite:
        return HttpResponse("Product is already in your favorites.", status=400)

    # If the product is not in favorites, add it to the favorites collection with a unique batch identifier
    batch_identifier = str(uuid.uuid4())  # Generate a unique batch identifier
    product['batch_identifier'] = batch_identifier  # Add the batch identifier to the product
    product['user_id'] = user.id

    # Generate a unique _id based on user_id and product_id
    product['_id'] = f"{user.id}_{product_id}"

    favorites_collection.insert_one(product)

    # Use the find_compare_products function to find similar products
    similar_products = find_compare_products(user.id, product.get('title', ''), product.get('weight', ''), product.get('brand', ''), product.get('supermarket', ''), collection, favorites_collection)
    
    # Collect all similar products that are not already in favorites
    new_similar_products = [similar_product for similar_product in similar_products if not favorites_collection.find_one({'_id': f"{user.id}_{similar_product['id']}"})]

    # Iterate through the new similar products and add them to the favorites collection with the same batch identifier
    for similar_product in new_similar_products:
        # Generate a unique _id for similar products
        similar_product['_id'] = f"{user.id}_{similar_product['id']}"
        similar_product['batch_identifier'] = batch_identifier  # Add the same batch identifier
        similar_product['user_id'] = user.id
        favorites_collection.insert_one(similar_product)

    return HttpResponse("Product added to shopping list successfully.", status=200)

# Binago ni Mari
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# @login_required 
# def add_to_favorites(request, product_id):
#     # Retrieve the product from the original collection
#     product = collection.find_one({'id': product_id})

#     if not product:
#         return HttpResponse("Product not found.", status=404)

#     # Get the current user
#     user = request.user

#     # Check if the product is already in the favorites collection
#     existing_favorite = favorites_collection.find_one({'user_id': user.id, 'id': product_id})

#     if existing_favorite:
#         return HttpResponse("Product is already in your favorites.", status=400)

#     # If the product is not in favorites, add it to the favorites collection with a unique batch identifier
#     batch_identifier = str(uuid.uuid4())  # Generate a unique batch identifier
#     product['batch_identifier'] = batch_identifier  # Add the batch identifier to the product
#     product['user_id'] = user.id
    
#     # Generate a unique _id based on user_id and product_id
#     product['_id'] = f"{user.id}_{product_id}"

#     favorites_collection.insert_one(product)

#     # Use the find_compare_products function to find similar products
#     similar_products = find_compare_products(user.id, product.get('title', ''), product.get('weight', ''), product.get('brand', ''), product.get('supermarket', ''), collection, favorites_collection)
    
#     # Collect all similar products that are not already in favorites
#     new_similar_products = [similar_product for similar_product in similar_products if not favorites_collection.find_one({'_id': f"{user.id}_{similar_product['id']}"})]

#     # Iterate through the new similar products and add them to the favorites collection with the same batch identifier
#     for similar_product in new_similar_products:
#         # Generate a unique _id for similar products
#         similar_product['_id'] = f"{user.id}_{similar_product['id']}"
#         similar_product['batch_identifier'] = batch_identifier  # Add the same batch identifier
#         similar_product['user_id'] = user.id
#         favorites_collection.insert_one(similar_product)

#     return HttpResponse("Product added to favorites successfully.", status=200)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


# @csrf_exempt
# def track_product_click(request):
#     if request.method == 'POST':
#         product_id = request.POST.get('id')
#         user_id = request.user.id
#         print('1     Product clicked with ID:', product_id)
#         # Include any other data you want to capture (e.g., timestamp, interaction type)

#         # Retrieve the user's purpose from the Users collection
#         user_data = user_collection.find_one({'user_id': user_id})
#         user_purpose = user_data.get('purpose') if user_data else None

#         print('2     Product clicked with ID:', product_id)

#         # Store the user-product interaction data in MongoDB, including the purpose
#         user_interaction_data = {
#             'user_id': user_id,
#             'product_id': product_id,
#             'purpose': user_purpose,
#             'time_stamp': datetime.now()
#             # Include other interaction data here
#         }
#         clicks_collection.insert_one(user_interaction_data)

#         print('1     Product STORED IN MONGO ID:', product_id)

#         return HttpResponse('Click tracked successfully')
#     else:
#         return HttpResponse('Invalid request method')

