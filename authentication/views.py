import os
import csv
import io
import json
from datetime import datetime
from decimal import Decimal
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from .forms import SignUpForm, ProductReviewForm
from .models import User, Post, Purchase, Bookmark, ProductImage, ProductReview
# Removed QR and OTP utilities for simplified workflow
from django.views.decorators.csrf import csrf_exempt

# ============================================
# LANDING PAGE (PUBLIC)
# ============================================

def landing_page(request):
    """
    Main landing page for KoraQuest - Public facing homepage
    Shows featured products, categories, and promotional content
    """
    # Get featured/new products (latest 8 products)
    new_arrivals = Post.objects.filter(
        inventory__gt=0
    ).order_by('-created_at')[:8]
    
    # Get best sellers (most purchased products)
    best_sellers = Post.objects.filter(
        inventory__gt=0
    ).order_by('-total_purchases')[:8]
    
    # Get featured products (you can add is_featured field later)
    featured_products = Post.objects.filter(
        inventory__gt=0,
        price__isnull=False
    ).order_by('-created_at')[:4]
    
    # Get all categories with product counts
    categories_with_counts = []
    for category_code, category_name in Post.CATEGORY_CHOICES:
        count = Post.objects.filter(
            category=category_code,
            inventory__gt=0
        ).count()
        if count > 0:  # Only show categories with products
            categories_with_counts.append({
                'code': category_code,
                'name': category_name,
                'count': count
            })
    
    # Get recent reviews for testimonials
    recent_reviews = ProductReview.objects.filter(
        rating__gte=4  # Only show 4-5 star reviews
    ).select_related('reviewer', 'product').order_by('-created_at')[:6]
    
    # Statistics for "Why Choose Us" section
    stats = {
        'total_products': Post.objects.filter(inventory__gt=0).count(),
        'total_orders': Purchase.objects.filter(status='completed').count(),
        'happy_customers': User.objects.filter(role='customer').count(),
    }
    
    context = {
        'new_arrivals': new_arrivals,
        'best_sellers': best_sellers,
        'featured_products': featured_products,
        'categories': categories_with_counts,
        'recent_reviews': recent_reviews,
        'stats': stats,
        'is_landing_page': True,  # Flag for template
    }
    
    return render(request, 'authentication/landing_page.html', context)

def generate_csv_report(data, filename, headers):
    """Generate CSV report from data"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(data)
    
    return response

def generate_pdf_report(data, filename, title, headers, summary_data=None):
    """Generate PDF report from data"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    
    # Create the PDF object
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Add title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 20))
    
    # Add summary if provided
    if summary_data:
        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20
        )
        for key, value in summary_data.items():
            elements.append(Paragraph(f"<b>{key}:</b> {value}", summary_style))
        elements.append(Spacer(1, 20))
    
    # Create table
    if data:
        table = Table([headers] + data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
    
    # Build PDF
    doc.build(elements)
    return response

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

# Register API
@csrf_exempt
@require_http_methods(["POST"])
def register_api(request):
    """API endpoint for user registration"""
    try:
        # Check content type
        content_type = request.content_type
        
        # Handle both JSON and form data
        if content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data',
                    'errors': {'json': ['Request body contains invalid JSON']}
                }, status=400)
        else:
            # Handle form data (your current approach)
            data = request.POST
        
        # Create form with data
        form = SignUpForm(data)
        
        if form.is_valid():
            user = form.save()
            
            # Return success response with user data
            return JsonResponse({
                'success': True,
                'message': 'Account created successfully',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'is_vendor_role': user.is_vendor_role
                }
            }, status=201)  # 201 for successful creation
        else:
            # Return validation errors
            return JsonResponse({
                'success': False,
                'message': 'Validation failed',
                'errors': form.errors
            }, status=400)
            
    except Exception as e:
        # Handle unexpected errors
        return JsonResponse({
            'success': False,
            'message': 'Server error occurred',
            'errors': {'server': [str(e)]}
        }, status=500)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')  # Redirect to dashboard or homepage
        else:
            # Form is invalid, re-render with errors
            return render(request, 'authentication/login.html', {'form': form})
    else:
        form = AuthenticationForm()
        return render(request, 'authentication/login.html', {'form': form})

@csrf_exempt
@require_http_methods(['POST'])
def login_api(request):
    """API endpoint for user login"""
    try:
        # Parse request data based on content type
        content_type = request.content_type
        if content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data',
                    'errors': {'json': ['Request body contains invalid JSON']}
                }, status=400)
        else:
            # Handle form data
            data = request.POST.dict()
        
        # Validate required fields
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': 'Missing credentials',
                'errors': {
                    'credentials': ['Both username and password are required']
                }
            }, status=400)
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Optional: Create authentication token for future API requests
                # You can use Django's built-in Token authentication or create your own
                try:
                    from django.contrib.auth.models import update_last_login
                    from rest_framework.authtoken.models import Token
                    
                    # Update last login time
                    update_last_login(None, user)
                    
                    # Get or create authentication token
                    token, created = Token.objects.get_or_create(user=user)
                    
                    # Return successful login response with user data and token
                    return JsonResponse({
                        'success': True,
                        'message': 'Login successful',
                        'data': {
                            'user': {
                                'id': user.id,
                                'username': user.username,
                                'email': user.email,
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'role': user.role,
                                'is_vendor_role': user.is_vendor_role,
                                'phone_number': getattr(user, 'phone_number', ''),
                                'last_login': user.last_login.isoformat() if user.last_login else None
                            },
                            'auth': {
                                'token': token.key,
                                'token_type': 'Bearer',
                                'expires_in': '30 days'  # Or your token expiry logic
                            }
                        }
                    }, status=200)
                    
                except ImportError:
                    # Fallback if DRF is not installed - return without token
                    return JsonResponse({
                        'success': True,
                        'message': 'Login successful',
                        'data': {
                            'user': {
                                'id': user.id,
                                'username': user.username,
                                'email': user.email,
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'role': user.role,
                                'is_vendor_role': user.is_vendor_role,
                                'phone_number': getattr(user, 'phone_number', ''),
                                'last_login': user.last_login.isoformat() if user.last_login else None
                            }
                        }
                    }, status=200)
                    
            else:
                # User account is disabled
                return JsonResponse({
                    'success': False,
                    'message': 'Account disabled',
                    'errors': {
                        'account': ['This account has been disabled. Please contact support.']
                    }
                }, status=403)
        else:
            # Invalid credentials
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials',
                'errors': {
                    'credentials': ['Username or password is incorrect']
                }
            }, status=401)
            
    except Exception as e:
        # Handle unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Login API error: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'message': 'Internal server error',
            'errors': {
                'server': ['An unexpected error occurred during login']
            }
        }, status=500)

def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

@csrf_exempt
@require_http_methods(['POST'])
def logout_api(request):
    auth_logout(request)
    return JsonResponse({
        'message': 'you have been successfully logged out'
    }, status=201)

def get_token_user(request):
    """Helper function to get user from token authentication"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.replace('Bearer ', '')
    try:
        from rest_framework.authtoken.models import Token
        token_obj = Token.objects.get(key=token)
        return token_obj.user
    except:
        return None

@csrf_exempt
@require_http_methods(['GET'])
def dashboard_api(request):
    """API endpoint for dashboard data with filtering, sorting, and pagination"""
    try:
        # Authentication - support both session and token auth
        if request.user.is_authenticated:
            user = request.user
        else:
            user = get_token_user(request)
            if not user:
                return JsonResponse({
                    'success': False,
                    'message': 'Authentication required',
                    'errors': {'auth': ['Please provide valid authentication credentials']}
                }, status=401)
        
        # Get filter parameters from the request
        search_query = request.GET.get('q', '').strip()
        category = request.GET.get('category', '')
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        sort_by = request.GET.get('sort', 'newest')
        page_number = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 20))  # Allow custom page size
        
        # Validate page_size (limit to reasonable values)
        if page_size > 100:
            page_size = 100
        elif page_size < 1:
            page_size = 20
        
        # Start with all products (no job posts anymore)
        posts = Post.objects.all()
        
        # Filter out sold-out products (inventory must be greater than 0)
        posts = posts.filter(inventory__gt=0)
        
        # Filter out the user's own products if they are a vendor
        if user.is_vendor_role:
            posts = posts.exclude(user=user)
        
        # Apply search filter if provided
        if search_query:
            posts = posts.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )
        
        # Apply category filter if provided
        if category:
            # Convert to lowercase to match the model's CATEGORY_CHOICES keys
            category = category.lower()
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
            # Order by average rating (implement this later)
            posts = posts.order_by('-created_at')
        else:  # newest (default)
            posts = posts.order_by('-created_at')
        
        # Get total count before pagination
        total_products = posts.count()
        
        # Get user's bookmarked posts
        bookmarked_posts = [bookmark.post.id for bookmark in Bookmark.objects.filter(user=user)]
        
        # Get user's liked posts
        liked_posts = [post.id for post in Post.objects.filter(likes=user)]
        
        # Pagination
        paginator = Paginator(posts, page_size)
        try:
            page_obj = paginator.get_page(page_number)
        except Exception:
            page_obj = paginator.get_page(1)
        
        # Convert posts to JSON-serializable format
        posts_data = []
        for post in page_obj:
            # Get auxiliary images
            auxiliary_images = ProductImage.objects.filter(product=post).order_by('display_order')
            aux_images_data = []
            for img in auxiliary_images:
                aux_images_data.append({
                    'id': img.id,
                    'image_url': img.image.url if img.image else None,
                    'display_order': img.display_order
                })
            
            # Calculate average rating if reviews exist
            reviews = ProductReview.objects.filter(product=post)
            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
            avg_rating = round(avg_rating, 1) if avg_rating else None
            
            post_data = {
                'id': post.id,
                'title': post.title,
                'description': post.description,
                'price': float(post.price) if post.price else None,
                'category': post.category,
                'category_display': post.get_category_display(),
                'inventory': post.inventory,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
                'total_purchases': post.total_purchases,
                'image_url': post.image.url if post.image else None,
                'auxiliary_images': aux_images_data,
                'average_rating': avg_rating,
                'review_count': reviews.count(),
                'total_likes': post.total_likes(),
                'is_bookmarked': post.id in bookmarked_posts,
                'is_liked': post.id in liked_posts,
                'user': {
                    'id': post.user.id,
                    'username': post.user.username,
                    'first_name': post.user.first_name,
                    'last_name': post.user.last_name,
                    'is_vendor_role': post.user.is_vendor_role,
                    'profile_picture_url': post.user.profile_picture.url if post.user.profile_picture else None
                }
            }
            posts_data.append(post_data)
        
        # Get all categories for the filter dropdown
        categories_data = []
        for choice in Post.CATEGORY_CHOICES:
            categories_data.append({
                'value': choice[0],
                'label': choice[1]
            })
        
        # Build response
        response_data = {
            'success': True,
            'message': 'Dashboard data retrieved successfully',
            'data': {
                'posts': posts_data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'page_size': page_size,
                    'total_items': total_products,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                    'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
                    'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
                },
                'filters': {
                    'search_query': search_query,
                    'selected_category': category,
                    'min_price': min_price,
                    'max_price': max_price,
                    'sort_by': sort_by,
                    'available_categories': categories_data,
                    'available_sorts': [
                        {'value': 'newest', 'label': 'Newest First'},
                        {'value': 'price_low', 'label': 'Price: Low to High'},
                        {'value': 'price_high', 'label': 'Price: High to Low'},
                        {'value': 'popular', 'label': 'Most Popular'},
                        {'value': 'rating', 'label': 'Highest Rated'}
                    ]
                },
                'user_info': {
                    'id': user.id,
                    'username': user.username,
                    'is_vendor_role': user.is_vendor_role,
                    'total_bookmarks': len(bookmarked_posts),
                    'total_liked_posts': len(liked_posts)
                },
                'summary': {
                    'total_products': total_products,
                    'products_on_page': len(posts_data),
                    'search_applied': bool(search_query),
                    'filters_applied': bool(category or min_price or max_price),
                    'sort_applied': sort_by != 'newest'
                }
            }
        }
        
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Dashboard API error: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'message': 'Internal server error',
            'errors': {'server': ['An unexpected error occurred']}
        }, status=500)

@csrf_exempt 
@require_http_methods(['POST'])
def bookmark_toggle_api(request, post_id):
    """API endpoint to toggle bookmark status"""
    try:
        # Get user from token
        user = get_token_user(request)
        if not user:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required',
                'errors': {'auth': ['Please provide valid authentication credentials']}
            }, status=401)
        
        post = get_object_or_404(Post, id=post_id)
        
        # Check if this post is already bookmarked by the user
        existing_bookmark = Bookmark.objects.filter(user=user, post=post).first()
        
        if existing_bookmark:
            # If bookmark already existed, delete it (toggle off)
            existing_bookmark.delete()
            is_bookmarked = False
            status_text = 'removed'
        else:
            # Create a new bookmark
            Bookmark.objects.create(user=user, post=post)
            is_bookmarked = True
            status_text = 'added'
        
        return JsonResponse({
            'success': True,
            'message': f'Bookmark {status_text} successfully',
            'data': {
                'is_bookmarked': is_bookmarked,
                'status': status_text,
                'post_id': post_id
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error toggling bookmark',
            'errors': {'server': [str(e)]}
        }, status=500)

@csrf_exempt
@require_http_methods(['POST'])
def like_post_api(request, post_id):
    """API endpoint to toggle like status"""
    try:
        # Get user from token
        user = get_token_user(request)
        if not user:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required',
                'errors': {'auth': ['Please provide valid authentication credentials']}
            }, status=401)
        
        post = get_object_or_404(Post, id=post_id)
        
        if user in post.likes.all():
            post.likes.remove(user)
            liked = False
            status_text = 'removed'
        else:
            post.likes.add(user)
            liked = True
            status_text = 'added'
        
        return JsonResponse({
            'success': True,
            'message': f'Like {status_text} successfully',
            'data': {
                'liked': liked,
                'total_likes': post.total_likes(),
                'status': status_text,
                'post_id': post_id
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error toggling like',
            'errors': {'server': [str(e)]}
        }, status=500)

@csrf_exempt
@require_http_methods(['GET'])
def categories_api(request):
    """API endpoint to get all available categories"""
    try:
        categories_data = []
        for choice in Post.CATEGORY_CHOICES:
            # Get count of products in each category
            count = Post.objects.filter(category=choice[0], inventory__gt=0).count()
            categories_data.append({
                'value': choice[0],
                'label': choice[1],
                'product_count': count
            })
        
        return JsonResponse({
            'success': True,
            'message': 'Categories retrieved successfully',
            'data': {
                'categories': categories_data,
                'total_categories': len(categories_data)
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error retrieving categories',
            'errors': {'server': [str(e)]}
        }, status=500)

@login_required
def dashboard(request):
    # Redirect admin users to admin dashboard
    if request.user.is_admin:
        return redirect('admin_dashboard')
    
    # Get filter parameters from the request
    search_query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'newest')
    
    # Start with all products (no job posts anymore)
    posts = Post.objects.all()
    
    # Filter out sold-out products (inventory must be greater than 0)
    posts = posts.filter(inventory__gt=0)
    
    # Apply search filter if provided
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply category filter if provided
    if category:
        # Convert to lowercase to match the model's CATEGORY_CHOICES keys
        category = category.lower()
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
    
    # Get user's liked posts for easier template rendering
    liked_posts = [post.id for post in Post.objects.filter(likes=request.user)]
    
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
        'liked_posts': liked_posts,
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
    
    # Allow repeat purchases - remove the restriction
    # has_purchased = Purchase.objects.filter(
    #     buyer=request.user, 
    #     product=post, 
    #     status__in=['completed', 'processing']
    # ).exists()
    has_purchased = False  # Always allow purchases
    
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
        
        # Check if price is None or not set
        if product.price is None:
            messages.error(request, f'Unable to purchase {product.title}. The product does not have a valid price.')
            return redirect('post_detail', post_id=post_id)

        # Check if product is out of stock
        if product.inventory <= 0:
            messages.error(request, f'Sorry, {product.title} is currently out of stock.')
            return redirect('post_detail', post_id=post_id)
        
        # Get quantity from form
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid quantity.")
            return redirect('post_detail', post_id=post_id)
        
        # Check if enough inventory (with fresh data to prevent race conditions)
        product.refresh_from_db()  # Get latest inventory data
        if product.inventory < quantity:
            if product.inventory == 0:
                messages.error(request, f'Sorry, {product.title} is now out of stock.')
            else:
                messages.error(request, f'Sorry, there are only {product.inventory} items available.')
            return redirect('post_detail', post_id=post_id)
        
        # Get delivery method and details
        delivery_method = request.POST.get('delivery_method', 'pickup')
        delivery_address = request.POST.get('delivery_address', '')
        delivery_latitude = request.POST.get('delivery_latitude')
        delivery_longitude = request.POST.get('delivery_longitude')
        payment_method = request.POST.get('payment_method', 'momo')
        notes = request.POST.get('notes', '')
        
        # Calculate total price
        total_price = product.price * quantity
        delivery_fee = Decimal('5.00') if delivery_method == 'delivery' else Decimal('0.00')
        
        # Validate delivery details if delivery is selected
        if delivery_method == 'delivery':
            if not delivery_address:
                messages.error(request, "Please provide a delivery address for home delivery.")
                return redirect('post_detail', post_id=post_id)
        
        # Determine initial status based on delivery method
        initial_status = 'pending'  # Simplified: all orders start as pending
        
        # Create a new purchase with simplified workflow
        purchase = Purchase(
            buyer=request.user,
            product=product,
            quantity=quantity,
            purchase_price=total_price,
            delivery_method=delivery_method,
            payment_method=payment_method,
            delivery_fee=delivery_fee,
            delivery_address=delivery_address,
            status=initial_status,
            notes=notes
        )
        
        # Add location coordinates if provided
        if delivery_latitude and delivery_longitude:
            try:
                purchase.delivery_latitude = float(delivery_latitude)
                purchase.delivery_longitude = float(delivery_longitude)
            except (ValueError, TypeError):
                pass  # Ignore invalid coordinates
        
        purchase.save()
        
        # Update inventory immediately after successful purchase
        product.inventory -= quantity
        
        # Update statistics
        product.total_purchases += 1
        product.save()
        
        # Update user's total purchases
        request.user.total_purchases += total_price + delivery_fee
        request.user.save()
        
        # Success message based on delivery method
        if delivery_method == 'delivery':
            messages.success(request, f'Order placed successfully! {quantity} x {product.title} for RWF {total_price + delivery_fee:,.2f} (including RWF {delivery_fee:,.2f} delivery fee). We will contact you soon for delivery arrangements.')
        else:
            messages.success(request, f'Order placed successfully! {quantity} x {product.title} for RWF {total_price:,.2f}. Please visit our store to collect your items.')
        
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
    
    # Check if export is requested
    export_format = request.GET.get('export')
    if export_format in ['csv', 'pdf']:
        # Prepare data for export
        headers = ['Order ID', 'Product', 'Seller', 'Date', 'Price', 'Status', 'Quantity', 'Delivery Method']
        data = []
        
        for purchase in purchases:
            data.append([
                purchase.order_id,
                purchase.product.title,
                f"{purchase.product.user.first_name} {purchase.product.user.last_name}",
                purchase.created_at.strftime('%Y-%m-%d %H:%M'),
                f"RWF {purchase.purchase_price:,.1f}",
                purchase.status.title(),
                purchase.quantity,
                purchase.delivery_method.title()
            ])
        
        # Summary data for PDF
        summary_data = {
            'Total Purchases': purchases.count(),
            'Total Spent': f"RWF {(purchases.aggregate(total=Sum('purchase_price'))['total'] or 0):,.1f}",
            'Completed Orders': purchases.filter(status='completed').count(),
            'Pending Orders': purchases.filter(status__in=['pending', 'processing']).count(),
            'Report Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        filename = f"purchase_history_{request.user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        title = f"Purchase History Report - {request.user.get_full_name() or request.user.username}"
        
        if export_format == 'csv':
            return generate_csv_report(data, filename, headers)
        elif export_format == 'pdf':
            return generate_pdf_report(data, filename, title, headers, summary_data)
    
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
def admin_dashboard(request):
    """Simplified admin dashboard for store owner"""
    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admin role required.')
        return redirect('dashboard')
    
    # Get all products (since there's only one store owner)
    products = Post.objects.all()
    
    # Get all purchases
    purchases = Purchase.objects.all()
    
    # Calculate statistics
    total_orders = purchases.count()
    pending_orders = purchases.filter(status='pending').count()
    completed_orders = purchases.filter(status='completed').count()
    
    # Calculate total revenue
    total_revenue = purchases.filter(status='completed').aggregate(
        total=Sum('purchase_price')
    )['total'] or 0
    
    # Get recent orders
    recent_orders = purchases.order_by('-created_at')[:10]
    
    # Get low stock products
    low_stock_products = products.filter(inventory__lte=5)
    
    context = {
        'products': products,
        'purchases': purchases,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products
    }
    
    return render(request, 'authentication/admin_dashboard.html', context)

@login_required
def update_order_status(request, purchase_id):
    """Update order status for admin"""
    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admin role required.')
        return redirect('dashboard')
    
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        tracking_number = request.POST.get('tracking_number', '')
        
        if new_status in ['processing', 'shipped', 'delivered', 'completed', 'cancelled']:
            purchase.status = new_status
            if tracking_number:
                purchase.tracking_number = tracking_number
            purchase.save()
            
            messages.success(request, f'Order {purchase.order_id} status updated to {new_status.title()}')
        else:
            messages.error(request, 'Invalid status selected')
    
    return redirect('admin_dashboard')

@login_required
def user_settings(request):
    # Handle form submissions for profile/account updates and role upgrades
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        upgrade_type = request.POST.get('upgrade_type')
        
        # Profile picture upload (AJAX request)
        if form_type == 'profile_picture':
            if 'profile_picture' in request.FILES:
                try:
                    user = request.user
                    user.profile_picture = request.FILES['profile_picture']
                    user.save()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Profile picture updated successfully!'})
                    else:
                        messages.success(request, 'Profile picture updated successfully!')
                        return redirect('user_settings')
                except Exception as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': f'Failed to update profile picture: {str(e)}'})
                    else:
                        messages.error(request, f'Failed to update profile picture: {str(e)}')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'No image file provided'})
                else:
                    messages.error(request, 'No image file provided')
        
        # Profile form submission
        elif form_type == 'profile':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            
            # Update user profile
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.phone_number = phone_number
            
            # Handle profile picture upload if included in the form
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
        try:
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
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
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

# Removed all QR Code, OTP, and Kicks_life 250 views for simplified single-vendor workflow
