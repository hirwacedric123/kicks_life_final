from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from .forms import SignUpForm
from .models import User, Post, Purchase, Bookmark, ProductImage, UserQRCode, OTPVerification, ProductReview
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum, Count, Q
import os
import decimal
from django.utils import timezone
from .qr_utils import update_user_qr_code, decode_qr_data, get_user_purchases_from_qr
from .otp_utils import create_otp, verify_otp
import json
from django.core.paginator import Paginator

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}! You can now log in.')
            return redirect('login')  # Redirect to login page after successful registration
    else:
        form = SignUpForm()
    
    return render(request, 'authentication/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')  # Redirect to dashboard or homepage
    else:
        form = AuthenticationForm()
    
    return render(request, 'authentication/login.html', {'form': form})

@login_required
def dashboard(request):
    # Get filter parameters from the request
    search_query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'newest')
    
    # Start with all products (no job posts anymore)
    posts = Post.objects.all()
    
    # Filter out sold-out products
    posts = posts.filter(inventory__gt=0)
    
    # Filter out the user's own products if they are a vendor
    if request.user.is_vendor_role:
        posts = posts.exclude(user=request.user)
    
    # Apply search filter if provided
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    # Apply category filter if provided
    if category:
        posts = posts.filter(category=category)
    
    # Apply price range filters
    if min_price:
        try:
            posts = posts.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            posts = posts.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == 'price_low':
        posts = posts.order_by('price')
    elif sort_by == 'price_high':
        posts = posts.order_by('-price')
    elif sort_by == 'popular':
        posts = posts.order_by('-total_purchases', '-created_at')
    elif sort_by == 'rating':
        # Order by average rating (we'll implement this later)
        posts = posts.order_by('-created_at')
    else:  # newest (default)
        posts = posts.order_by('-created_at')
    
    # Get all categories for the filter dropdown
    categories = Post.CATEGORY_CHOICES
    
    # Get user's bookmarked posts for easier template rendering
    bookmarked_posts = [bookmark.post.id for bookmark in Bookmark.objects.filter(user=request.user)]
    
    # Pagination
    paginator = Paginator(posts, 20)  # 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'search_query': search_query,
        'selected_category': category,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'categories': categories,
        'bookmarked_posts': bookmarked_posts,
        'total_products': posts.count(),
    }
    
    return render(request, 'authentication/dashboard.html', context)

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_bookmarked = Bookmark.objects.filter(user=request.user, post=post).exists()
    
    # Check if the user is the owner of the post
    is_owner = (post.user == request.user)
    
    # Get auxiliary images for the product
    auxiliary_images = ProductImage.objects.filter(product=post).order_by('display_order')
    
    # Check if the user has purchased this product
    has_purchased = Purchase.objects.filter(
        buyer=request.user, 
        product=post, 
        status__in=['completed', 'processing']
    ).exists()
    
    # Get product reviews
    reviews = ProductReview.objects.filter(product=post).order_by('-created_at')
    
    # Check if current user has already reviewed this product
    user_review = None
    if request.user.is_authenticated:
        user_review = ProductReview.objects.filter(product=post, reviewer=request.user).first()
    
    context = {
        'post': post,
        'is_bookmarked': is_bookmarked,
        'has_purchased': has_purchased,
        'is_owner': is_owner,
        'auxiliary_images': auxiliary_images,
        'reviews': reviews,
        'user_review': user_review,
    }
    
    return render(request, 'authentication/post_detail.html', context)

@login_required
def purchase_product(request, post_id):
    if request.method == 'POST':
        product = get_object_or_404(Post, id=post_id)
        
        # Check if user is trying to buy their own product
        if product.user == request.user:
            messages.error(request, "You cannot purchase your own product.")
            return redirect('post_detail', post_id=post_id)
        
        # Check if price is None or not set
        if product.price is None:
            messages.error(request, f'Unable to purchase {product.title}. The product does not have a valid price.')
            return redirect('post_detail', post_id=post_id)
        
        # Get quantity from form
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid quantity.")
            return redirect('post_detail', post_id=post_id)
        
        # Check if enough inventory
        if product.inventory < quantity:
            messages.error(request, f'Sorry, there are only {product.inventory} items available.')
            return redirect('post_detail', post_id=post_id)
        
        # Get delivery method and details
        delivery_method = request.POST.get('delivery_method', 'pickup')
        delivery_address = request.POST.get('delivery_address', '')
        delivery_latitude = request.POST.get('delivery_latitude')
        delivery_longitude = request.POST.get('delivery_longitude')
        payment_method = request.POST.get('payment_method', 'momo')  # New payment method field
        
        # Calculate total price
        from decimal import Decimal
        total_price = product.price * quantity
        delivery_fee = Decimal('5.00') if delivery_method == 'delivery' else Decimal('0.00')
        
        # Validate delivery details if delivery is selected
        if delivery_method == 'delivery':
            if not delivery_address:
                messages.error(request, "Please provide a delivery address for home delivery.")
                return redirect('post_detail', post_id=post_id)
        
        # Determine initial status based on delivery method
        initial_status = 'awaiting_delivery' if delivery_method == 'delivery' else 'awaiting_pickup'
        
        # Create a new purchase with KoraQuest workflow
        purchase = Purchase(
            buyer=request.user,
            product=product,
            quantity=quantity,
            purchase_price=total_price,
            delivery_method=delivery_method,
            payment_method=payment_method,
            delivery_fee=delivery_fee,
            delivery_address=delivery_address,
            status=initial_status
        )
        
        # Add location coordinates if provided
        if delivery_latitude and delivery_longitude:
            try:
                purchase.delivery_latitude = float(delivery_latitude)
                purchase.delivery_longitude = float(delivery_longitude)
            except (ValueError, TypeError):
                pass  # Ignore invalid coordinates
        
        purchase.save()
        
        # Update inventory
        product.inventory -= quantity
        
        # Update statistics
        product.total_purchases += 1
        product.save()
        
        # Update QR code to include this purchase
        from .qr_utils import update_user_qr_code
        update_user_qr_code(request.user)
        
        # Success message based on delivery method
        if delivery_method == 'delivery':
            messages.success(request, f'You have successfully purchased {quantity} {product.title}! Total: ${total_price + delivery_fee:.2f} (including ${delivery_fee:.2f} delivery fee). KoraQuest will deliver to your address.')
        else:
            messages.success(request, f'You have successfully purchased {quantity} {product.title}! Please go to KoraQuest to collect your items.')
        
        return redirect('purchase_history')
    
    return redirect('post_detail', post_id=post_id)

@login_required
def bookmark_toggle(request, post_id):
    if request.method == 'POST':
        try:
            post = get_object_or_404(Post, id=post_id)
            
            # Check if this post is already bookmarked by the user
            existing_bookmark = Bookmark.objects.filter(user=request.user, post=post).first()
            
            if existing_bookmark:
                # If bookmark already existed, delete it (toggle off)
                existing_bookmark.delete()
                is_bookmarked = False
                status = 'removed'
            else:
                # Create a new bookmark
                Bookmark.objects.create(user=request.user, post=post)
                is_bookmarked = True
                status = 'added'
            
            return JsonResponse({
                'success': True,
                'is_bookmarked': is_bookmarked,
                'status': status,
                'post_id': post_id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def purchase_history(request):
    purchases = Purchase.objects.filter(buyer=request.user).order_by('-created_at')
    
    context = {
        'purchases': purchases
    }
    
    return render(request, 'authentication/purchase_history.html', context)

@login_required
def bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'bookmarks': bookmarks
    }
    
    return render(request, 'authentication/bookmarks.html', context)

@login_required
def vendor_dashboard(request):
    # Ensure user is a vendor
    if not request.user.is_vendor_role:
        messages.error(request, 'You need to be registered as a vendor to access this dashboard.')
        return redirect('dashboard')
    
    # Get vendor's products
    products = Post.objects.filter(user=request.user)
    
    # Get purchases for vendor's products
    purchases = Purchase.objects.filter(product__user=request.user)
    
    # Calculate statistics
    total_sales = purchases.filter(status='completed').count()
    total_revenue = request.user.total_sales
    
    # Get recent purchases
    recent_purchases = purchases.order_by('-created_at')[:5]
    
    context = {
        'products': products,
        'purchases': purchases,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'recent_purchases': recent_purchases
    }
    
    return render(request, 'authentication/vendor_dashboard.html', context)

@login_required
def user_settings(request):
    # Handle form submissions for profile/account updates and role upgrades
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        upgrade_type = request.POST.get('upgrade_type')
        
        # Profile form submission
        if form_type == 'profile':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            
            # Update user profile
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.phone_number = phone_number
            
            # Handle profile picture upload
            profile_picture = request.FILES.get('profile_picture')
            if profile_picture:
                request.user.profile_picture = profile_picture
            
            request.user.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('user_settings')
        
        # Account form submission (password change)
        elif form_type == 'account':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password and confirm_password:
                if new_password == confirm_password:
                    request.user.set_password(new_password)
                    request.user.save()
                    messages.success(request, 'Password changed successfully. Please log in again.')
                    return redirect('login')
                else:
                    messages.error(request, 'Passwords do not match.')
            else:
                messages.error(request, 'Please fill in both password fields.')
        
        # Role upgrade form submissions
        elif upgrade_type == 'vendor':
            # Process vendor upgrade
            if request.user.is_vendor_role:
                messages.info(request, 'You are already registered as a vendor.')
            else:
                # Enable vendor role without changing other roles
                request.user.is_vendor_role = True
                request.user.save()
                messages.success(request, 'Congratulations! Your account has been upgraded to include Vendor capabilities. You can now create product posts.')
    
    return render(request, 'authentication/settings.html')

@login_required
def create_post(request):
    # Check if user has vendor permissions
    if not request.user.is_vendor_role:
        messages.error(request, 'You need to upgrade your account to Vendor status to create product listings.')
        return redirect('user_settings')
    
    # Direct to product creation since we only have products now
    return redirect('create_product')

@login_required
def create_product(request):
    # Check if user has vendor role
    if not request.user.is_vendor_role:
        messages.error(request, 'You need to upgrade your account to Vendor status to create product listings.')
        return redirect('user_settings')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        main_image = request.FILES.get('main_image')
        price = request.POST.get('price')
        category = request.POST.get('category')
        inventory = request.POST.get('inventory', 1)
        
        try:
            inventory = int(inventory)
            if inventory < 0:
                inventory = 1
        except (ValueError, TypeError):
            inventory = 1
        
        if title and description and main_image and price:
            # Create the main product (no post_type needed since all posts are products now)
            post = Post(
                title=title,
                description=description,
                image=main_image,
                user=request.user,
                price=price,
                category=category,
                inventory=inventory
            )
            post.save()
            
            # Process auxiliary images (limit to 5)
            auxiliary_images = request.FILES.getlist('auxiliary_images')
            print(f"DEBUG: Found {len(auxiliary_images)} auxiliary images in create_product")
            max_images = min(len(auxiliary_images), 5)  # Limit to 5 images
            
            for i in range(max_images):
                print(f"DEBUG: Creating auxiliary image {i+1} of {max_images}")
                ProductImage.objects.create(
                    product=post,
                    image=auxiliary_images[i],
                    display_order=i
                )
                
            messages.success(request, 'Product listing created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please fill all required fields')
    
    return render(request, 'authentication/create_product.html')

@login_required
def like_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
            
        return JsonResponse({
            'liked': liked,
            'total_likes': post.total_likes()
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Below functions are kept for backward compatibility but redirect to settings page
@login_required
def become_vendor(request):
    if request.method == 'POST':
        if request.user.is_vendor_role:
            messages.info(request, 'You are already registered as a vendor.')
        else:
            request.user.is_vendor_role = True
            request.user.save()
            messages.success(request, 'Congratulations! Your account has been upgraded to Vendor status. You can now create product posts.')
    
    return redirect('user_settings')

@login_required
def edit_product(request, product_id):
    # Check if user has vendor role
    if not request.user.is_vendor_role:
        messages.error(request, 'You need to have Vendor status to edit product listings.')
        return redirect('dashboard')
    
    # Get the product (ensure it belongs to the user)
    product = get_object_or_404(Post, id=product_id, user=request.user)
    
    # Business Rule: Check if product has been purchased or bookmarked
    has_purchases = Purchase.objects.filter(product=product).exists()
    has_bookmarks = Bookmark.objects.filter(post=product).exists()
    
    if has_purchases or has_bookmarks:
        messages.error(request, 'This product cannot be edited as it has been purchased or bookmarked by customers.')
        return redirect('vendor_dashboard')
    
    # Get existing auxiliary images
    auxiliary_images = ProductImage.objects.filter(product=product).order_by('display_order')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category = request.POST.get('category')
        inventory = request.POST.get('inventory')
        
        if title and description and price:
            # Update product details
            product.title = title
            product.description = description
            product.price = price
            product.category = category
            
            # Update inventory if provided
            if inventory:
                try:
                    inventory_value = int(inventory)
                    if inventory_value >= 0:
                        product.inventory = inventory_value
                except (ValueError, TypeError):
                    pass  # Keep existing inventory if invalid value
            
            # Handle main image update if provided
            main_image = request.FILES.get('main_image')
            if main_image:
                product.image = main_image
            
            product.save()
            
            # Handle auxiliary images
            # Check if any auxiliary images should be deleted
            images_to_keep = request.POST.getlist('keep_auxiliary_image')
            
            # Delete images not in the keep list
            for aux_image in auxiliary_images:
                if str(aux_image.id) not in images_to_keep:
                    aux_image.delete()
            
            # Count remaining images after deletion
            remaining_images_count = ProductImage.objects.filter(product=product).count()
            
            # Calculate how many new images we can add
            max_new_images = 5 - remaining_images_count
            
            if max_new_images > 0:
                # Add new auxiliary images up to the allowed limit
                new_auxiliary_images = request.FILES.getlist('auxiliary_images')
                print(f"DEBUG: Found {len(new_auxiliary_images)} new auxiliary images")
                max_to_add = min(len(new_auxiliary_images), max_new_images)
                
                for i in range(max_to_add):
                    print(f"DEBUG: Creating auxiliary image {i+1} of {max_to_add}")
                    ProductImage.objects.create(
                        product=product,
                        image=new_auxiliary_images[i],
                        display_order=remaining_images_count + i
                    )
            
            messages.success(request, 'Product updated successfully!')
            return redirect('vendor_dashboard')
        else:
            messages.error(request, 'Please fill all required fields')
    
    context = {
        'product': product,
        'auxiliary_images': auxiliary_images
    }
    
    return render(request, 'authentication/edit_product.html', context)

# KoraQuest Views
@login_required
def user_qr_code(request):
    """Display user's QR code with their purchase information"""
    # Update/create QR code for the user
    user_qr = update_user_qr_code(request.user)
    
    # Get user's pending purchases (both pickup and delivery)
    pending_purchases = Purchase.objects.filter(
        buyer=request.user,
        status__in=['awaiting_pickup', 'awaiting_delivery']
    ).select_related('product')
    
    context = {
        'user_qr': user_qr,
        'pending_purchases': pending_purchases,
        'qr_expires_at': user_qr.expires_at,
    }
    
    return render(request, 'authentication/user_qr_code.html', context)

@login_required
def koraquest_dashboard(request):
    """Dashboard for KoraQuest users to manage purchases and inventory"""
    if not request.user.is_koraquest():
        messages.error(request, 'Access denied. KoraQuest role required.')
        return redirect('dashboard')
    
    # Get all purchases awaiting pickup
    awaiting_purchases = Purchase.objects.filter(
        status='awaiting_pickup'
    ).select_related('buyer', 'product', 'product__user').order_by('-created_at')
    
    # Get all purchases awaiting delivery
    awaiting_deliveries = Purchase.objects.filter(
        status='awaiting_delivery'
    ).select_related('buyer', 'product', 'product__user').order_by('-created_at')
    
    # Get orders out for delivery
    out_for_delivery = Purchase.objects.filter(
        status='out_for_delivery'
    ).select_related('buyer', 'product', 'product__user').order_by('-created_at')
    
    # Get completed purchases for revenue tracking
    completed_purchases = Purchase.objects.filter(
        status='completed',
        koraquest_user=request.user
    ).select_related('buyer', 'product')
    
    # Calculate revenue statistics
    total_commission = completed_purchases.aggregate(
        total=Sum('koraquest_commission_amount')
    )['total'] or 0
    
    monthly_commission = completed_purchases.filter(
        pickup_confirmed_at__month=timezone.now().month,
        pickup_confirmed_at__year=timezone.now().year
    ).aggregate(total=Sum('koraquest_commission_amount'))['total'] or 0
    
    context = {
        'awaiting_purchases': awaiting_purchases,
        'awaiting_deliveries': awaiting_deliveries,
        'out_for_delivery': out_for_delivery,
        'completed_purchases': completed_purchases[:10],  # Latest 10
        'total_commission': total_commission,
        'monthly_commission': monthly_commission,
        'total_completed': completed_purchases.count(),
    }
    
    return render(request, 'authentication/koraquest_dashboard.html', context)

@login_required
def scan_qr_code(request):
    """QR code scanner interface for KoraQuest users"""
    print('Scan Called')
    if not request.user.is_koraquest():
        messages.error(request, 'Access denied. KoraQuest role required.')
        return redirect('dashboard')
    
    print('User is Koraquest')
    # Create context for rendering
    context = {
        'page_title': 'QR Code Scanner',
        'error_message': None,
        'success_message': None,
    }
    
    if request.method == 'POST':
        print('Request Made')
        qr_data = request.POST.get('qr_data')
        print(qr_data)
        purchase_id = request.POST.get('purchase_id')
        
        if qr_data:
            try:
                # Decode QR data
                decoded_data = decode_qr_data(qr_data.strip())
                print("============================= Decoded QR Data:")
                print(decoded_data)
                
                if isinstance(decoded_data, dict) and 'error' in decoded_data:
                    context['error_message'] = decoded_data['error']
                    messages.error(request, decoded_data['error'])
                    return render(request, 'authentication/scan_qr_code.html', context)
                
                # Get purchase information
                purchase_info = get_user_purchases_from_qr(decoded_data)
                
                # If no purchases found or empty QR data
                if not purchase_info.get('purchases'):
                    context['error_message'] = 'No pending purchases found in this QR code.'
                    messages.warning(request, context['error_message'])
                    return render(request, 'authentication/scan_qr_code.html', context)
                
                # If purchase_id is provided, complete that specific purchase
                if purchase_id:
                    try:
                        # Find the specific purchase from the database
                        purchase = Purchase.objects.get(id=purchase_id)
                        
                        # Verify the purchase belongs to the user in the QR code
                        if purchase.buyer.id != purchase_info['user_id']:
                            context['error_message'] = 'Purchase verification failed: User mismatch.'
                            messages.error(request, context['error_message'])
                            return render(request, 'authentication/scan_qr_code.html', context)
                        
                        # Complete the purchase directly (fallback from JS flow)
                        purchase.status = 'completed'
                        purchase.koraquest_user = request.user
                        purchase.pickup_confirmed_at = timezone.now()
                        purchase.save()
                        
                        # Update vendor and buyer stats
                        vendor = purchase.product.user
                        vendor.total_sales += purchase.vendor_payment_amount
                        vendor.save()
                        
                        buyer = purchase.buyer
                        buyer.total_purchases += (purchase.purchase_price * purchase.quantity)
                        buyer.save()
                        
                        # Success message
                        context['success_message'] = f'Purchase {purchase.order_id} confirmed successfully! Vendor payment: ${purchase.vendor_payment_amount}, KoraQuest commission: ${purchase.koraquest_commission_amount}'
                        messages.success(request, context['success_message'])
                        
                        # Redirect to dashboard after successful completion
                        return redirect('koraquest_dashboard')
                    except Purchase.DoesNotExist:
                        context['error_message'] = f'Purchase not found with ID: {purchase_id}'
                        messages.error(request, context['error_message'])
                        return render(request, 'authentication/scan_qr_code.html', context)
                
                # If no specific purchase_id, show all purchases
                user = get_object_or_404(User, id=purchase_info['user_id'])
                
                # Add data to context
                context.update({
                    'qr_data': purchase_info,
                    'user_info': user,
                    'success_message': f'Successfully retrieved purchase information for {user.username}.'
                })
                
                messages.success(request, context['success_message'])
                return render(request, 'authentication/scan_qr_code.html', context)
                
            except Exception as e:
                context['error_message'] = f"Error processing QR code: {str(e)}"
                messages.error(request, context['error_message'])
                return render(request, 'authentication/scan_qr_code.html', context)
        else:
            context['error_message'] = 'No QR data provided'
            messages.error(request, context['error_message'])
            return render(request, 'authentication/scan_qr_code.html', context)
    
    # For GET requests, just render the scan page
    print("nothing kweri")
    return render(request, 'authentication/scan_qr_code.html', context)

@login_required
def confirm_purchase_pickup(request, purchase_id):
    """Confirm purchase pickup and initiate OTP verification"""
    if not request.user.is_koraquest():
        messages.error(request, 'Access denied. KoraQuest role required.')
        return redirect('dashboard')
    
    purchase = get_object_or_404(Purchase, id=purchase_id, status='awaiting_pickup')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'request_otp':
            # Create OTP for buyer
            otp_result = create_otp(purchase.buyer, 'purchase_confirmation')
            
            return JsonResponse({
                'success': True,
                'message': f'OTP sent to {purchase.buyer.email}',
                'otp_id': otp_result['otp_id']
            })
        
        elif action == 'verify_otp':
            password = request.POST.get('password')
            otp_code = request.POST.get('otp_code')
            
            # Verify buyer's password
            if not purchase.buyer.check_password(password):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid password'
                })
            
            # Verify OTP
            otp_result = verify_otp(purchase.buyer, otp_code, 'purchase_confirmation')
            
            if not otp_result['valid']:
                return JsonResponse({
                    'success': False,
                    'error': otp_result['error']
                })
            
            # Complete the purchase
            purchase.status = 'completed'
            purchase.koraquest_user = request.user
            purchase.pickup_confirmed_at = timezone.now()
            purchase.save()
            
            # Update vendor and buyer stats
            vendor = purchase.product.user
            vendor.total_sales += purchase.vendor_payment_amount
            vendor.save()
            
            buyer = purchase.buyer
            buyer.total_purchases += (purchase.purchase_price * purchase.quantity)
            buyer.save()
            
            # Update product inventory and sales
            product = purchase.product
            product.inventory -= purchase.quantity
            product.total_purchases += purchase.quantity
            product.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Purchase confirmed successfully!',
                'vendor_payment': str(purchase.vendor_payment_amount),
                'koraquest_commission': str(purchase.koraquest_commission_amount)
            })
    
    context = {
        'purchase': purchase,
        'payment_split': purchase.calculate_payment_split()
    }
    
    return render(request, 'authentication/confirm_purchase_pickup.html', context)

@login_required
def confirm_delivery(request, purchase_id):
    """Confirm delivery completion and initiate OTP verification"""
    if not request.user.is_koraquest():
        messages.error(request, 'Access denied. KoraQuest role required.')
        return redirect('dashboard')
    
    purchase = get_object_or_404(Purchase, id=purchase_id, status__in=['awaiting_delivery', 'out_for_delivery'])
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'mark_out_for_delivery':
            # Mark as out for delivery
            purchase.status = 'out_for_delivery'
            purchase.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Order marked as out for delivery!'
            })
        
        elif action == 'request_otp':
            # Create OTP for buyer
            otp_result = create_otp(purchase.buyer, 'delivery_confirmation')
            
            return JsonResponse({
                'success': True,
                'message': f'OTP sent to {purchase.buyer.email}',
                'otp_id': otp_result['otp_id']
            })
        
        elif action == 'verify_delivery':
            password = request.POST.get('password')
            otp_code = request.POST.get('otp_code')
            
            # Verify buyer's password
            if not purchase.buyer.check_password(password):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid password'
                })
            
            # Verify OTP
            otp_result = verify_otp(purchase.buyer, otp_code, 'delivery_confirmation')
            
            if not otp_result['valid']:
                return JsonResponse({
                    'success': False,
                    'error': otp_result['error']
                })
            
            # Complete the delivery
            purchase.status = 'completed'
            purchase.koraquest_user = request.user
            purchase.pickup_confirmed_at = timezone.now()  # Using same field for delivery confirmation time
            purchase.save()
            
            # Update vendor and buyer stats
            vendor = purchase.product.user
            vendor.total_sales += purchase.vendor_payment_amount
            vendor.save()
            
            buyer = purchase.buyer
            buyer.total_purchases += purchase.purchase_price
            buyer.save()
            
            # Update product sales (inventory already reduced during purchase)
            product = purchase.product
            product.total_purchases += purchase.quantity
            product.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Delivery confirmed successfully!',
                'vendor_payment': str(purchase.vendor_payment_amount),
                'koraquest_commission': str(purchase.koraquest_commission_amount)
            })
    
    context = {
        'purchase': purchase,
        'payment_split': purchase.calculate_payment_split(),
        'is_delivery': True
    }
    
    return render(request, 'authentication/confirm_purchase_pickup.html', context)

@login_required
def update_qr_code_ajax(request):
    """AJAX endpoint to update user's QR code"""
    if request.method == 'POST':
        user_qr = update_user_qr_code(request.user)
        
        return JsonResponse({
            'success': True,
            'qr_image_url': user_qr.qr_image.url if user_qr.qr_image else None,
            'expires_at': user_qr.expires_at.isoformat()
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def koraquest_purchase_history(request):
    """View purchase history for KoraQuest users"""
    if not request.user.is_koraquest():
        messages.error(request, 'Access denied. KoraQuest role required.')
        return redirect('dashboard')
    
    purchases = Purchase.objects.filter(
        koraquest_user=request.user,
        status='completed'
    ).select_related('buyer', 'product', 'product__user').order_by('-pickup_confirmed_at')
    
    # Pagination could be added here
    context = {
        'purchases': purchases,
        'total_commission': purchases.aggregate(
            total=Sum('koraquest_commission_amount')
        )['total'] or 0
    }
    
    return render(request, 'authentication/koraquest_purchase_history.html', context)