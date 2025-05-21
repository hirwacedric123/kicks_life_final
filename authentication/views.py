from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import UserRegistrationForm
from .models import Post, User, Purchase, JobApplication, Bookmark
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum, Count
import os
import decimal

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}! You can now log in.')
            return redirect('login')  # Redirect to login page after successful registration
    else:
        form = UserRegistrationForm()
    
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
    # Get the category parameter from the request to filter posts
    category = request.GET.get('category')
    search_query = request.GET.get('q')
    
    # Filter posts based on category
    if category == 'jobs':
        posts = Post.objects.filter(post_type='job')
        view_type = 'jobs'
    else:
        # Default to products/market if no category specified or any other value
        posts = Post.objects.filter(post_type='product')
        view_type = 'market'
    
    # Apply search filter if provided
    if search_query:
        posts = posts.filter(title__icontains=search_query)
    
    context = {
        'posts': posts,
        'view_type': view_type,
        'search_query': search_query
    }
    
    return render(request, 'authentication/dashboard.html', context)

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_bookmarked = Bookmark.objects.filter(user=request.user, post=post).exists()
    
    # Check if the user has purchased this product (if it's a product)
    has_purchased = False
    if post.post_type == 'product':
        has_purchased = Purchase.objects.filter(
            buyer=request.user, 
            product=post, 
            status__in=['completed', 'processing']
        ).exists()
    
    # Check if the user has applied for this job (if it's a job)
    has_applied = False
    application = None
    if post.post_type == 'job':
        application = JobApplication.objects.filter(
            applicant=request.user,
            job=post
        ).first()
        has_applied = application is not None
    
    context = {
        'post': post,
        'is_bookmarked': is_bookmarked,
        'has_purchased': has_purchased,
        'has_applied': has_applied,
        'application': application
    }
    
    return render(request, 'authentication/post_detail.html', context)

@login_required
def purchase_product(request, post_id):
    if request.method == 'POST':
        product = get_object_or_404(Post, id=post_id, post_type='product')
        
        # Create a new purchase
        purchase = Purchase(
            buyer=request.user,
            product=product,
            quantity=1,  # Default to 1 for now
            purchase_price=product.price,
            status='completed'  # Auto-complete for demo purposes
        )
        purchase.save()
        
        # Update statistics
        product.total_purchases += 1
        product.save()
        
        request.user.total_purchases += decimal.Decimal(product.price)
        request.user.save()
        
        product.user.total_sales += decimal.Decimal(product.price)
        product.user.save()
        
        messages.success(request, f'You have successfully purchased {product.title}!')
        return redirect('purchase_history')
    
    return redirect('post_detail', post_id=post_id)

@login_required
def apply_for_job(request, post_id):
    job = get_object_or_404(Post, id=post_id, post_type='job')
    
    # Check if user is a freelancer
    if not request.user.is_freelancer_role:
        messages.error(request, 'You need to be registered as a freelancer to apply for jobs.')
        return redirect('user_settings')
    
    # Check if already applied
    if JobApplication.objects.filter(applicant=request.user, job=job).exists():
        messages.info(request, 'You have already applied for this job.')
        return redirect('post_detail', post_id=post_id)
    
    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter')
        
        # Create the application
        application = JobApplication(
            applicant=request.user,
            job=job,
            cover_letter=cover_letter,
            status='pending'
        )
        
        # Use the freelancer's CV if available
        if request.user.freelancer_cv:
            application.cv = request.user.freelancer_cv
        else:
            cv_file = request.FILES.get('cv')
            if cv_file:
                application.cv = cv_file
            else:
                messages.error(request, 'Please upload your CV or complete your freelancer profile first.')
                return redirect('post_detail', post_id=post_id)
        
        application.save()
        
        # Update job application count
        job.total_applications += 1
        job.save()
        
        messages.success(request, f'Your application for {job.title} has been submitted successfully!')
        return redirect('freelancer_dashboard')
    
    context = {
        'job': job,
        'has_cv': bool(request.user.freelancer_cv)
    }
    
    return render(request, 'authentication/apply_job.html', context)

@login_required
def bookmark_toggle(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        bookmark, created = Bookmark.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            # If bookmark already existed, delete it (toggle off)
            bookmark.delete()
            is_bookmarked = False
        else:
            is_bookmarked = True
        
        return JsonResponse({
            'success': True,
            'is_bookmarked': is_bookmarked
        })
    
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
    products = Post.objects.filter(user=request.user, post_type='product')
    
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
def hiring_company_dashboard(request):
    # Ensure user is a hiring company
    if not request.user.is_hiring_company_role:
        messages.error(request, 'You need to be registered as a hiring company to access this dashboard.')
        return redirect('dashboard')
    
    # Get company's job postings
    jobs = Post.objects.filter(user=request.user, post_type='job')
    
    # Get applications for company's jobs
    applications = JobApplication.objects.filter(job__user=request.user)
    
    # Count applications by status
    pending_applications = applications.filter(status='pending').count()
    under_review_applications = applications.filter(status='under_review').count()
    interview_applications = applications.filter(status='interview').count()
    accepted_applications = applications.filter(status='accepted').count()
    rejected_applications = applications.filter(status='rejected').count()
    
    # Get recent applications
    recent_applications = applications.order_by('-created_at')[:5]
    
    context = {
        'jobs': jobs,
        'applications': applications,
        'pending_applications': pending_applications,
        'under_review_applications': under_review_applications,
        'interview_applications': interview_applications,
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications,
        'recent_applications': recent_applications
    }
    
    return render(request, 'authentication/hiring_company_dashboard.html', context)

@login_required
def freelancer_dashboard(request):
    # Ensure user is a freelancer
    if not request.user.is_freelancer_role:
        messages.error(request, 'You need to be registered as a freelancer to access this dashboard.')
        return redirect('dashboard')
    
    # Get freelancer's job applications
    applications = JobApplication.objects.filter(applicant=request.user)
    
    # Count applications by status
    pending_applications = applications.filter(status='pending').count()
    under_review_applications = applications.filter(status='under_review').count()
    interview_applications = applications.filter(status='interview').count()
    accepted_applications = applications.filter(status='accepted').count()
    rejected_applications = applications.filter(status='rejected').count()
    
    context = {
        'applications': applications,
        'pending_applications': pending_applications,
        'under_review_applications': under_review_applications,
        'interview_applications': interview_applications,
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications
    }
    
    return render(request, 'authentication/freelancer_dashboard.html', context)

@login_required
def update_application_status(request, application_id):
    # Only hiring companies can update application status
    if not request.user.is_hiring_company_role:
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('dashboard')
    
    application = get_object_or_404(JobApplication, id=application_id)
    
    # Ensure the job belongs to the hiring company
    if application.job.user != request.user:
        messages.error(request, 'You are not authorized to update this application.')
        return redirect('hiring_company_dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        feedback = request.POST.get('feedback')
        
        if new_status in dict(JobApplication.STATUS_CHOICES).keys():
            application.status = new_status
            if feedback:
                application.feedback = feedback
            application.save()
            
            messages.success(request, f'Application status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status provided.')
    
    return redirect('hiring_company_dashboard')

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
            
            # Check if a CV was uploaded - if so, enable freelancer role
            profile_cv = request.FILES.get('profile_cv')
            if profile_cv:
                # Get skills information
                profile_skills = request.POST.get('profile_skills')
                
                if not profile_skills:
                    messages.error(request, 'Please provide your professional skills to enable freelancer features.')
                    return redirect('user_settings')
                
                # Save CV file and skills to the user model
                request.user.freelancer_cv = profile_cv
                request.user.freelancer_skills = profile_skills
                
                # Enable freelancer role without changing primary role
                if not request.user.is_freelancer_role:
                    request.user.is_freelancer_role = True
                    messages.success(request, 'Your account has been upgraded with Freelancer capabilities!')
            
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
        
        elif upgrade_type == 'hiring_company':
            # Process hiring company upgrade
            if request.user.is_hiring_company_role:
                messages.info(request, 'You are already registered as a hiring company.')
            else:
                company_name = request.POST.get('company_name')
                company_description = request.POST.get('company_description')
                
                if not company_name or not company_description:
                    messages.error(request, 'Please fill all required fields for company registration.')
                else:
                    # Enable hiring company role without changing other roles
                    request.user.is_hiring_company_role = True
                    request.user.save()
                    messages.success(request, 'Congratulations! Your account has been upgraded to include Hiring Company capabilities. You can now post job listings.')
        
        elif upgrade_type == 'freelancer':
            # Process freelancer upgrade
            if request.user.is_freelancer_role:
                messages.info(request, 'You are already registered as a freelancer.')
            else:
                cv_file = request.FILES.get('cv')
                skills = request.POST.get('skills')
                
                if not cv_file or not skills:
                    messages.error(request, 'Please upload your CV and list your skills to register as a freelancer.')
                else:
                    # Save CV and skills to the user model
                    request.user.freelancer_cv = cv_file
                    request.user.freelancer_skills = skills
                    
                    # Enable freelancer role without changing other roles
                    request.user.is_freelancer_role = True
                    request.user.save()
                    messages.success(request, 'Congratulations! Your application has been submitted. Your account has been upgraded to include Freelancer capabilities.')
    
    return render(request, 'authentication/settings.html')

@login_required
def create_post(request):
    # Check if user has proper permissions
    if not (request.user.is_vendor_role or request.user.is_hiring_company_role):
        messages.error(request, 'You need to upgrade your account to create posts. Become a vendor or hiring company first.')
        return redirect('dashboard')
    
    # Direct to the appropriate post creation form based on user role
    if request.user.is_vendor_role and not request.user.is_hiring_company_role:
        return redirect('create_product')
    elif request.user.is_hiring_company_role and not request.user.is_vendor_role:
        return redirect('create_job')
    else:
        # If user has both roles, ask which type of post they want to create
        return render(request, 'authentication/post_type_selection.html')

@login_required
def create_product(request):
    # Check if user has vendor role
    if not request.user.is_vendor_role:
        messages.error(request, 'You need to upgrade your account to Vendor status to create product listings.')
        return redirect('user_settings')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        price = request.POST.get('price')
        category = request.POST.get('category')
        
        if title and description and image and price:
            post = Post(
                title=title,
                description=description,
                image=image,
                user=request.user,
                post_type='product',
                price=price,
                category=category
            )
            post.save()
            messages.success(request, 'Product listing created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please fill all required fields')
    
    return render(request, 'authentication/create_product.html')

@login_required
def create_job(request):
    # Check if user has hiring company role
    if not request.user.is_hiring_company_role:
        messages.error(request, 'You need to upgrade your account to Hiring Company status to create job listings.')
        return redirect('user_settings')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        job_location = request.POST.get('job_location')
        job_type = request.POST.get('job_type')
        salary_range = request.POST.get('salary_range')
        
        if title and description and job_location and job_type:
            post = Post(
                title=title,
                description=description,
                image=image if image else None,
                user=request.user,
                post_type='job',
                job_location=job_location,
                job_type=job_type,
                salary_range=salary_range
            )
            post.save()
            messages.success(request, 'Job posting created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please fill all required fields')
    
    return render(request, 'authentication/create_job.html')

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
def become_hiring_company(request):
    if request.method == 'POST':
        if request.user.is_hiring_company_role:
            messages.info(request, 'You are already registered as a hiring company.')
            return redirect('user_settings')
        
        company_name = request.POST.get('company_name')
        company_description = request.POST.get('company_description')
        
        if not company_name or not company_description:
            messages.error(request, 'Please fill all required fields')
            return redirect('user_settings')
        
        # Update user role to hiring company
        request.user.is_hiring_company_role = True
        request.user.save()
        messages.success(request, 'Congratulations! Your account has been upgraded to Hiring Company status. You can now post job listings.')
        return redirect('user_settings')
    
    return redirect('user_settings')

@login_required
def become_freelancer(request):
    if request.method == 'POST':
        if request.user.is_freelancer_role:
            messages.info(request, 'You are already registered as a freelancer.')
            return redirect('user_settings')
        
        cv_file = request.FILES.get('cv')
        skills = request.POST.get('skills')
        
        if not cv_file or not skills:
            messages.error(request, 'Please upload your CV and list your skills')
            return redirect('user_settings')
        
        # Save CV and skills to the user model
        request.user.freelancer_cv = cv_file
        request.user.freelancer_skills = skills
        
        # Enable freelancer role
        request.user.is_freelancer_role = True
        request.user.save()
        messages.success(request, 'Congratulations! Your application has been submitted. Your account has been upgraded to Freelancer status.')
        return redirect('user_settings')
    
    return redirect('user_settings')