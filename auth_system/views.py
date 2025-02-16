from __future__ import print_function
import time
import sib_api_v3_sdk 
from sib_api_v3_sdk import Configuration, EmailCampaignsApi, TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# from sendinblue import ApiException

from datetime import date
from .models import UserProfile
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .forms import ProfilePictureForm
from django.core.files import File 
from .models import MongoDBUser
from pymongo import MongoClient
from collections import defaultdict


from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect  
from django.http import JsonResponse
from django.utils.crypto import get_random_string

from django.conf import settings
import requests
from django.contrib.auth.tokens import default_token_generator

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.exceptions import ObjectDoesNotExist
from .forms import UserProfileForm, UpdateNameForm
from bson import ObjectId
import uuid






client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
like_dislike_collection = db['ProductLikesDislikes']
# like_dislike_collection = db['auth']
product_collection = db['Sept_FInal_Final']

comments_collection = db['Comments']
user_collection = db['Users']
# user_collection = db['New_Users']
favorites_collection = db['FavoritesFinal']
clicks_collection = db['UserClicks']
saved_favorites_collection = db['SavedFavorites']

# Create your views here.
def HomePage(request):
    return render(request, 'home/index.html', {})

@csrf_protect
def Register(request):
    if request.method == 'POST':
        # account
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        uname = request.POST.get('uname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # personal information
        gender = request.POST.get('gender')
        birthday = request.POST.get('birthday')
        region = request.POST.get('region')
        city = request.POST.get('city')
        purpose = request.POST.get('purpose')

        # Calculate age
        today = date.today()
        birth_date = date.fromisoformat(birthday)
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        # Password validation rules
        if password is None:
            messages.error(request, 'Password is required.')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        elif not any(char.isupper() for char in password):
            messages.error(request, 'Password must contain at least one uppercase letter.')
        elif not any(char.isdigit() for char in password):
            messages.error(request, 'Password must contain at least one number.')
        elif not any(char in "!@#$%^&*" for char in password):
            messages.error(request, 'Password must contain at least one special character.')
        elif ' ' in password:
            messages.error(request, 'Password should not contain spaces.')

        # Check if the password and confirm_password match
        if password != confirm_password:
            messages.error(request, 'Password and Confirm Password do not match.')


        # Check if the username already exists
        if User.objects.filter(username=uname).exists():
            messages.error(request, 'This username is already in use.')
        # Check if the email already exists
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'This email address is already in use.')

        else:

            # separate account info | saving into database
            # new_user = User.objects.create_user(uname, email, password)
            new_user = User(username=uname, email=email)
            new_user.set_password(password)  # Encrypt the password
            new_user.first_name = fname
            new_user.last_name = lname
            new_user.save()

            # Generate a unique verification token
            # verification_token = get_random_string(length=32)  # You can adjust the length as needed

            # Create a UserProfile model (assuming you have one) to store additional user information
            # Update the UserProfile model with the token
            user_profile = UserProfile(user=new_user, gender=gender, birthday=birthday, region=region, city=city, age=age, purpose=purpose)

            # Set the default profile picture for the user profile
            # First, you need to open the default profile picture file and assign it to the profile_picture field.
            with open('media/profile_pics/default_profile.png', 'rb') as f:
                default_profile_picture = File(f)
                user_profile.profile_picture.save('default_profile.png', default_profile_picture, save=True)

            user_profile.save()

            # # Create a MongoDBUser object and save user details to MongoDB
            # mongo_user = MongoDBUser(user_id=new_user.id, username=uname, email=email, password=password, confirm_password=confirm_password, fname=fname, lname=lname,
            #                         gender=gender, birthday=birthday, region=region, city=city, age=age, purpose=purpose)
            # mongo_user.save()  # Save user details to MongoDB
            # Hash password for MongoDB as well
            hashed_password = new_user.password  # Already hashed by Django's set_password
            mongo_user = MongoDBUser(user_id=new_user.id, username=uname, email=email, password=hashed_password, 
                         confirm_password=confirm_password, fname=fname, lname=lname,
                         gender=gender, birthday=birthday, region=region, city=city, 
                         age=age, purpose=purpose)
            mongo_user.save()

            # Send a verification email to the user
            # send_verification_email(new_user, verification_token)

            # return redirect('auth_system:verification-page') # proceed to verification-page when form submitted successfully
             # Instead of sending verification email, redirect to login page with success message
            messages.success(request, "You have successfully registered! Log in now.")
            return redirect('auth_system:login-page')  # Redirect to the login page after successful registration

    return render(request, 'auth_system/register.html',{}) # return to register page when form submission failed

# For real time error message } email and username validation
@csrf_protect
def check_email(request):
    email = request.POST.get('email')
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

csrf_protect
def check_uname(request):
    uname = request.POST.get('uname')
    exists = User.objects.filter(username=uname).exists()
    return JsonResponse({'exists': exists})

# Verifies user once link is clicked from the email
def EmailVerification(request, token):
    user_profile = UserProfile.objects.filter(email_verification_token=token).first()
    if user_profile:
        user_profile.email_verified = True
        user_profile.save()
        messages.success(request, 'Email verification successful. You can now log in.')
        return redirect('auth_system:login-page')
        # return render('auth_system:login-page')

    else:
        messages.error(request, 'Invalid verification token.')
        return redirect('auth_system:verification-page')
        # return render('auth_system:verification-page')

# Pending verification page
def VerificationPage(request):
    return render(request, 'auth_system/verification-page.html', {})

# def send_verification_email(user, token):
    subject = 'Email Verification'
    message = f'Please click the following link to verify your email: http://http://127.0.0.1:8000/verification/{token}/'
    # message = f'Please click the following link to verify your email: http://127.0.0.1:8000/verification/{token}/'

    from_email = settings.EMAIL_HOST_USER
    to_email = [user.email]

     # Prepare context to render the template
    context = {
        'user': user,
        'token': token,
    }
    # Load the email template as a string
    html_content = render_to_string('auth_system/verify_email.html', context)
    text_content = strip_tags(html_content)

    data = {
        'from': from_email,
        'to': to_email,
        'subject': subject,
        'text': text_content,
        'html': html_content,
    }
    response = requests.post(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
        auth=("api", settings.MAILGUN_API_KEY),
        data=data
    )

    if response.status_code == 200:
        print("Email sent successfully")
    else:
        print("Failed to send email. Status code:", response.status_code)


def send_verification_email(user, token):
    # Load the email template as a string
    context = {'user': user, 'token': token}
    html_content = render_to_string('auth_system/verify_email.html', context)
    text_content = strip_tags(html_content)

    # Configure the Sendinblue API client
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY  # Replace with your Brevo API key
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    subject = 'Email Verification'
    sender = {"name": "Necessipick", "email": 'necessipick@gmail.com'}  # Replace with your sender details
    to = [{"email": user.email, "name": user.username}]

    # Create the Sendinblue email object
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        subject=subject,
        html_content=html_content,
        sender=sender,
    )

    try:
        # Send the transactional email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
        print("Email sent successfully")
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)

# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
 
@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    form = ProfilePictureForm(instance=user_profile)  # Define the form here

     # Retrieve the user's liked and disliked product IDs from MongoDB
    user_id = request.user.id
    liked_products = like_dislike_collection.distinct('product_id', {'user_id': user_id, 'action': 'like'})
    disliked_products = like_dislike_collection.distinct('product_id', {'user_id': user_id, 'action': 'dislike'})

    print("Liked products:", liked_products)
    print("Disliked products:", disliked_products)

    # Fetch the product details for liked and disliked products from MongoDB
    liked_product_details = list(product_collection.find({'id': {'$in': liked_products}}))
    disliked_product_details = list(product_collection.find({'id': {'$in': disliked_products}}))

    print("Liked product details:", liked_product_details)
    print("Disliked product details:", disliked_product_details)

    context = {
        'user_profile': user_profile,
        'form': form,
        'liked_products': liked_product_details,
        'disliked_products': disliked_product_details,
    }

    return render(request, 'auth_system/profile.html', context)


@login_required
def edit_profile(request):
    user = request.user  # Get the currently logged-in user
    user_profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        name_form = UpdateNameForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)

        if name_form.is_valid() and profile_form.is_valid():
            name_form.save()
            profile_form.save()
            return redirect('auth_system:profile')  # Redirect to the profile page after saving
    else:
        name_form = UpdateNameForm(instance=user)
        profile_form = UserProfileForm(instance=user_profile)


    return render(request, 'auth_system/edit_profile.html',  {'name_form': name_form, 'profile_form': profile_form})


@login_required
def update_profile_picture(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            return redirect('auth_system:profile')
    else:
        form = ProfilePictureForm(instance=request.user.userprofile)
    
    return render(request, 'auth_system/update_profile_picture.html', {'form': form})


def Login(request):
    if request.method == 'POST':
        # account
        username = request.POST.get('username')
        password = request.POST.get('passwordli')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome Back, {user.first_name} {user.last_name}')
            return redirect('auth_system:auth_home')
        else:
            messages.error(request, 'Incorrect username or password')

    return render(request, 'auth_system/login.html', {})

def get_product_count(request):
    supermarket = request.GET.get('supermarket', '')
    user_id = request.user.id

    # Your logic to get the count of products with prices for the specified supermarket
    count = favorites_collection.count_documents({'supermarket': supermarket, 'user_id': user_id, 'original_price': {'$exists': True}})

    return JsonResponse({'count': count})

@login_required
def display_favorites(request):
    user = request.user
    favorite_products_cursor = favorites_collection.find({'user_id': user.id})
    favorite_products = list(favorite_products_cursor)  # Convert the cursor to a list
    
    # Retrieve saved favorites for the current user
    user_id = str(request.user.id)
    print("user:    ", user_id)
    saved_favorites = saved_favorites_collection.find({'user_id': user_id})
    print(saved_favorites)

    saved_favorites_list = list(saved_favorites)
    print(saved_favorites_list)

    # Convert ObjectId to string for rendering in the template
    for favorite in saved_favorites:
        favorite['_id'] = str(favorite['_id'])

    # Group products by batch_identifier and supermarket
    grouped_products = defaultdict(list)
    for product in favorite_products:
        batch_identifier = product['batch_identifier']
        supermarket = product['supermarket']
        grouped_products[(batch_identifier, supermarket)].append(product)

    # Create a new dictionary for displaying prices per batch
    display_data = {}
    for (batch_identifier, supermarket), products in grouped_products.items():
        if batch_identifier not in display_data:
            display_data[batch_identifier] = {
                'image': products[0]['image'],
                'title': products[0]['title'],
                'puregold_price': None,
                'shopmetro_price': None,
                'waltermart_price': None,
                'min_price': float('inf'),  # Initialize min_price as positive infinity
            }
        if supermarket == 'Puregold':
            # Extract and convert the numeric part of the price string
            price_str = products[0]['original_price']
            price = float(price_str.replace('₱', '').replace(',', ''))
            display_data[batch_identifier]['puregold_price'] = price
        elif supermarket == 'ShopMetro':
            price_str = products[0]['original_price']
            price = float(price_str.replace('₱', '').replace(',', ''))
            display_data[batch_identifier]['shopmetro_price'] = price
        elif supermarket == 'WalterMart':
            price_str = products[0]['original_price']
            price = float(price_str.replace('₱', '').replace(',', ''))
            display_data[batch_identifier]['waltermart_price'] = price

        # Update the minimum price if a lower price is found
        if price < display_data[batch_identifier]['min_price']:
            display_data[batch_identifier]['min_price'] = price

    context = {
        'favorite_products': display_data,  # Pass the data for displaying prices to the template
        'batch_identifiers': display_data.keys(),
        'is_empty': len(display_data) == 0,  # Check if favorites are empty
        'saved_favorites': saved_favorites_list,
    }

    return render(request, 'auth_system/add_to_list.html', context)

def remove_favorite(request):
    if request.method == "POST":
        batch_identifier = request.POST.get("batch_identifier")
        user = request.user

        try:
            # Use user ID and batch_identifier to remove records from MongoDB favorites collection.
            favorites_collection.delete_many({"user_id": user.id, "batch_identifier": batch_identifier})

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False})

def clear_favorites(request):
    if request.method == "POST":
        user = request.user
        try:
            # Use user ID to remove all records associated with the user from the favorites collection
            favorites_collection.delete_many({"user_id": user.id})

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False})


def Logout(request):
    logout(request)
    return redirect('auth_system:login-page')

# enter email where the reset pass instruction is to be sent
def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            # Check if the email exists in your database
            user_profile = User.objects.get(email=email)
            # Generate a unique token for this user
            token = default_token_generator.make_token(user_profile)
            # Store the token in the user model
            user_profile.userprofile.password_reset_token = token
            user_profile.userprofile.save()
            # Send the password reset email with the token
            send_password_reset_email(user_profile, token)
            messages.success(request, 'Instructions have been sent. Please check your email.')
        except ObjectDoesNotExist:
            messages.error(request, 'The provided email does not exist in our database.')
    return render(request, 'auth_system/request_password_reset.html')


def send_password_reset_email(user, token):
    # Load the email template as a string
    context = {'user': user, 'token': token}
     # Load the email template as a string
    html_content = render_to_string('auth_system/password_reset_email.html', context)
    text_content = strip_tags(html_content)

    # Configure the Sendinblue API client
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY  # Replace with your Brevo API key
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


    subject = 'Password Reset'
    sender = {"name": "Necessipick", "email": 'necessipick@gmail.com'}  # Replace with your sender details
    to = [{"email": user.email, "name": user.username}]

   # Create the Sendinblue email object
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        subject=subject,
        html_content=html_content,
        sender=sender,
    )

    try:
        # Send the transactional email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
        print("Email sent successfully")
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


def send_password_reset_email(user, token):
    # Load the email template as a string
    context = {'user': user, 'token': token}
     # Load the email template as a string
    html_content = render_to_string('auth_system/password_reset_email.html', context)
    text_content = strip_tags(html_content)

    # Configure the Sendinblue API client
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY  # Replace with your Brevo API key
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


    subject = 'Password Reset'
    sender = {"name": "Necessipick", "email": 'necessipick@gmail.com'}  # Replace with your sender details
    to = [{"email": user.email, "name": user.username}]

   # Create the Sendinblue email object
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        subject=subject,
        html_content=html_content,
        sender=sender,
    )

    try:
        # Send the transactional email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
        print("Email sent successfully")
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


    

# form where new password is to be set
def reset_password_form(request, token): 
 
    # User = get_user_model()

    # Verify the token
    # Find the user with the associated token
    user_profile = UserProfile.objects.filter(password_reset_token=token).first()
    
    if user_profile and default_token_generator.check_token(user_profile.user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password == confirm_password:
                # Update the user's password
                user = user_profile.user  # Get the User object from UserProfile
                user.set_password(new_password)  # Use set_password on the User object
                user.save()                
                
                user_profile.password_reset_token = ""  # Clear the password reset token
                user_profile.save()

                messages.success(request, 'Password successfully reset. You can now log in with your new password.')
                return render(request, 'auth_system/login.html')
            else:
                messages.error(request, 'Passwords do not match. Please try again.')
                # return render(request, 'auth_system/reset_password_form.html')
            
        # Add an else block to handle GET requests (or other methods) when not resetting the password
        return render(request, 'auth_system/reset_password_form.html')
    else:
        return render(request, 'auth_system/403.html')



@login_required
def save_to_favorites(request):
    if request.method == "POST":
        user_id = str(request.user.id)
        batch_identifier = request.POST.get("batch_identifier")
        supermarket = request.POST.get("supermarket")
        price_str = request.POST.get("price")

        if price_str is None:
            return JsonResponse({"success": False, "message": "Price is required."})

        try:
            price = float(price_str)
        except ValueError:
            return JsonResponse({"success": False, "message": "There is no existing product of the selected supermarket price"})

        # Check if the product is already in SavedFavorites for the current user
        existing_record = saved_favorites_collection.find_one({
            'user_id': user_id,
            'batch_identifier': batch_identifier,
            'price': price,  # Convert to the appropriate type for comparison
            'supermarket': supermarket,
        })

        print("Existing Record:", existing_record)  # Add this line for debugging

        if existing_record:
            return JsonResponse({"success": False, "message": "The product is already in your favorites list."})

        try:
            # Get additional data from the associated record in Sept_FInal_Final
            associated_record = favorites_collection.find_one({'batch_identifier': batch_identifier})
            title = associated_record.get('title', '')
            original_price = associated_record.get('original_price', '')
            image = associated_record.get('image', '')

            # Create a custom _id using user_id and a new ObjectId
            custom_id = f'{user_id}_{ObjectId()}'

            # Generate a favorite_id using UUID
            favorite_id = str(uuid.uuid4())

            # Save the data to the SavedFavorites MongoDB collection
            saved_favorites_collection.insert_one({
                '_id': custom_id,
                'favorite_id': favorite_id,
                'user_id': user_id,
                'batch_identifier': batch_identifier,
                'supermarket': supermarket,
                'price': float(price),  # Convert to the appropriate type for storage
                'title': title,
                'original_price': original_price,
                'image': image,
            })

            return JsonResponse({"success": True, "message": "Successfully saved to favorites."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False})

@login_required
def remove_saved_favorite(request):
    if request.method == "POST":
        user_id = str(request.user.id)
        favorite_id = request.POST.get("favorite_id")
        print("fav id:         ", favorite_id)

        try:
            # Remove the favorite item based on user_id and favorite_id
            saved_favorites_collection.delete_one({'user_id': user_id, 'favorite_id': favorite_id})
            return JsonResponse({"success": True, "message": "Successfully removed from favorites."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False})

@login_required
def save_to_favorites(request):
    if request.method == "POST":
        user_id = str(request.user.id)
        batch_identifier = request.POST.get("batch_identifier")
        supermarket = request.POST.get("supermarket")
        price_str = request.POST.get("price")

        if price_str is None:
            return JsonResponse({"success": False, "message": "Price is required."})

        try:
            price = float(price_str)
        except ValueError:
            return JsonResponse({"success": False, "message": "There is no existing product of the selected supermarket price"})

        # Check if the product is already in SavedFavorites for the current user
        existing_record = saved_favorites_collection.find_one({
            'user_id': user_id,
            'batch_identifier': batch_identifier,
            'price': price,  # Convert to the appropriate type for comparison
            'supermarket': supermarket,
        })

        print("Existing Record:", existing_record)  # Add this line for debugging

        if existing_record:
            return JsonResponse({"success": False, "message": "The product is already in your favorites list."})

        try:
            # Get additional data from the associated record in Sept_FInal_Final
            associated_record = favorites_collection.find_one({'batch_identifier': batch_identifier})
            title = associated_record.get('title', '')
            original_price = associated_record.get('original_price', '')
            image = associated_record.get('image', '')

            # Create a custom _id using user_id and a new ObjectId
            custom_id = f'{user_id}_{ObjectId()}'

            # Generate a favorite_id using UUID
            favorite_id = str(uuid.uuid4())

            # Save the data to the SavedFavorites MongoDB collection
            saved_favorites_collection.insert_one({
                '_id': custom_id,
                'favorite_id': favorite_id,
                'user_id': user_id,
                'batch_identifier': batch_identifier,
                'supermarket': supermarket,
                'price': float(price),  # Convert to the appropriate type for storage
                'title': title,
                'original_price': original_price,
                'image': image,
            })

            return JsonResponse({"success": True, "message": "Successfully saved to favorites."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False})

@login_required
def remove_saved_favorite(request):
    if request.method == "POST":
        user_id = str(request.user.id)
        favorite_id = request.POST.get("favorite_id")
        print("fav id:         ", favorite_id)

        try:
            # Remove the favorite item based on user_id and favorite_id
            saved_favorites_collection.delete_one({'user_id': user_id, 'favorite_id': favorite_id})
            return JsonResponse({"success": True, "message": "Successfully removed from favorites."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False})

