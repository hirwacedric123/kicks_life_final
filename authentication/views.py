from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import UserRegistrationForm
from .models import Post, User, Purchase, JobApplication, Bookmark, ProductImage, ApplicationComment, Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer, Notification
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum, Count
import os
import decimal
from django.utils import timezone

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
    
    # Business Rule: Prevent hiring companies from viewing the Job Board
    if category == 'jobs' and request.user.is_hiring_company_role:
        messages.error(request, 'Hiring companies cannot access the Job Board. Use your dashboard to manage your job postings.')
        return redirect('hiring_company_dashboard')
    
    # Filter posts based on category
    if category == 'jobs':
        posts = Post.objects.filter(post_type='job')
        view_type = 'jobs'
        
        # Filter out the user's own job postings if they are a hiring company
        if request.user.is_hiring_company_role:
            posts = posts.exclude(user=request.user)
    else:
        # Default to products/market if no category specified or any other value
        posts = Post.objects.filter(post_type='product')
        view_type = 'market'
        
        # Filter out the user's own products if they are a vendor
        if request.user.is_vendor_role:
            posts = posts.exclude(user=request.user)
    
    # Apply search filter if provided
    if search_query:
        posts = posts.filter(title__icontains=search_query)
    
    # Get user's bookmarked posts for easier template rendering
    bookmarked_posts = [bookmark.post.id for bookmark in Bookmark.objects.filter(user=request.user)]
    
    context = {
        'posts': posts,
        'view_type': view_type,
        'search_query': search_query,
        'bookmarked_posts': bookmarked_posts
    }
    
    return render(request, 'authentication/dashboard.html', context)

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_bookmarked = Bookmark.objects.filter(user=request.user, post=post).exists()
    
    # Check if the user is the owner of the post
    is_owner = (post.user == request.user)
    
    # Get auxiliary images if this is a product
    auxiliary_images = []
    if post.post_type == 'product':
        auxiliary_images = ProductImage.objects.filter(product=post).order_by('display_order')
    
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
    job_stats = None
    if post.post_type == 'job':
        application = JobApplication.objects.filter(
            applicant=request.user,
            job=post
        ).first()
        has_applied = application is not None
        
        # Get job statistics if the user is the owner (hiring company)
        if is_owner:
            applications = JobApplication.objects.filter(job=post)
            job_stats = {
                'total_applications': applications.count(),
                'pending_applications': applications.filter(status='pending').count(),
                'under_review_applications': applications.filter(status='under_review').count(),
                'interview_applications': applications.filter(status='interview').count(),
                'accepted_applications': applications.filter(status='accepted').count(),
                'rejected_applications': applications.filter(status='rejected').count(),
            }
    
    context = {
        'post': post,
        'is_bookmarked': is_bookmarked,
        'has_purchased': has_purchased,
        'has_applied': has_applied,
        'application': application,
        'is_owner': is_owner,
        'auxiliary_images': auxiliary_images,
        'job_stats': job_stats
    }
    
    return render(request, 'authentication/post_detail.html', context)

@login_required
def purchase_product(request, post_id):
    if request.method == 'POST':
        product = get_object_or_404(Post, id=post_id, post_type='product')
        
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
        
        # Calculate total price
        total_price = product.price * quantity
        
        # Create a new purchase
        purchase = Purchase(
            buyer=request.user,
            product=product,
            quantity=quantity,
            purchase_price=total_price,
            status='completed'  # Auto-complete for demo purposes
        )
        purchase.save()
        
        # Update inventory
        product.inventory -= quantity
        
        # Update statistics
        product.total_purchases += 1
        product.save()
        
        request.user.total_purchases += decimal.Decimal(total_price)
        request.user.save()
        
        product.user.total_sales += decimal.Decimal(total_price)
        product.user.save()
        
        messages.success(request, f'You have successfully purchased {quantity} {product.title}!')
        return redirect('purchase_history')
    
    return redirect('post_detail', post_id=post_id)

@login_required
def apply_for_job(request, post_id):
    job = get_object_or_404(Post, id=post_id, post_type='job')
    
    # Check if user is a freelancer
    if not request.user.is_freelancer_role:
        messages.error(request, 'You need to be registered as a freelancer to apply for jobs.')
        return redirect('user_settings')
    
    # Business Rule: A freelancer who becomes a hiring company can no longer apply for jobs
    if request.user.is_freelancer_role and request.user.is_hiring_company_role:
        messages.error(request, 'You cannot apply for jobs as you are now registered as a hiring company. Hiring companies cannot apply for jobs.')
        return redirect('post_detail', post_id=post_id)
    
    # Check if user is trying to apply to their own job posting
    if job.user == request.user:
        messages.error(request, 'You cannot apply to your own job posting.')
        return redirect('post_detail', post_id=post_id)
    
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
    pre_interview_applications = applications.filter(status='pre_interview').count()
    interview_applications = applications.filter(status='interview').count()
    accepted_applications = applications.filter(status='accepted').count()
    rejected_applications = applications.filter(status='rejected').count()
    
    # Get unread notifications for the user
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    
    # Get recent notifications (read and unread)
    recent_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    
    # Get applications that are in pre_interview status with available quizzes
    pre_interview_apps_with_quizzes = []
    for app in applications.filter(status='pre_interview'):
        # Get quizzes for this job
        all_quizzes = Quiz.objects.filter(job=app.job)
        
        # Get already attempted quizzes
        attempted_quiz_ids = QuizAttempt.objects.filter(application=app).values_list('quiz_id', flat=True)
        
        # Get available quizzes (not attempted yet)
        available_quizzes = all_quizzes.exclude(id__in=attempted_quiz_ids)
        
        if available_quizzes.exists():
            pre_interview_apps_with_quizzes.append({
                'application': app,
                'available_quizzes': available_quizzes
            })
    
    context = {
        'applications': applications,
        'pending_applications': pending_applications,
        'under_review_applications': under_review_applications,
        'pre_interview_applications': pre_interview_applications,
        'interview_applications': interview_applications,
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications,
        'unread_notifications': unread_notifications,
        'recent_notifications': recent_notifications,
        'pre_interview_apps_with_quizzes': pre_interview_apps_with_quizzes,
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
        interview_details = request.POST.get('interview_details')
        
        if new_status in dict(JobApplication.STATUS_CHOICES).keys():
            # Store old status for comparison
            old_status = application.status
            
            application.status = new_status
            if feedback:
                application.feedback = feedback
            if interview_details:
                application.interview_details = interview_details
            application.save()
            
            # Create notification for the applicant when status changes
            if old_status != new_status:
                # Get human-readable status names
                status_display = dict(JobApplication.STATUS_CHOICES).get(new_status, new_status)
                
                # Create notification title and message based on status
                if new_status == 'pre_interview':
                    title = "Assessment Required - Take Your Pre-Interview Test"
                    message = f"Your application for '{application.job.title}' has moved to the assessment stage. Please complete the required tests to proceed to the interview stage."
                elif new_status == 'interview':
                    title = "Congratulations! You've Been Selected for Interview"
                    message = f"Your application for '{application.job.title}' has been selected for an interview. Check your application details for interview information."
                elif new_status == 'accepted':
                    title = "🎉 Congratulations! Your Application Has Been Accepted"
                    message = f"Great news! Your application for '{application.job.title}' has been accepted. The employer will contact you soon with next steps."
                elif new_status == 'rejected':
                    title = "Application Update"
                    message = f"Your application for '{application.job.title}' status has been updated. Please check your dashboard for details."
                else:
                    title = f"Application Status Updated to {status_display}"
                    message = f"Your application for '{application.job.title}' status has been updated to {status_display}."
                
                # Create the notification
                Notification.objects.create(
                    recipient=application.applicant,
                    notification_type='application_status_change',
                    title=title,
                    message=message,
                    application=application
                )
            
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
        
        # Freelancer profile update (from dedicated freelancer tab)
        elif form_type == 'freelancer_profile':
            # Ensure user is a freelancer
            if not request.user.is_freelancer_role:
                messages.error(request, 'You need to be registered as a freelancer to update this profile.')
                return redirect('user_settings')
            
            # Update freelancer skills
            freelancer_skills = request.POST.get('freelancer_skills')
            if freelancer_skills:
                request.user.freelancer_skills = freelancer_skills
            
            # Update CV if a new one was uploaded
            freelancer_cv = request.FILES.get('freelancer_cv')
            if freelancer_cv:
                request.user.freelancer_cv = freelancer_cv
                
            request.user.save()
            messages.success(request, 'Freelancer profile updated successfully.')
            return redirect('user_settings#freelancer')
        
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
                # Business Rule: A hiring company can become a vendor but never a freelancer
                if request.user.is_hiring_company_role:
                    messages.error(request, 'Hiring companies cannot register as freelancers.')
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
            # Create the main product
            post = Post(
                title=title,
                description=description,
                image=main_image,
                user=request.user,
                post_type='product',
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
        
        # Quiz/test creation fields
        quiz_title = request.POST.get('quiz_title')
        quiz_description = request.POST.get('quiz_description')
        time_limit = request.POST.get('time_limit', 30)
        passing_score = request.POST.get('passing_score', 70)
        difficulty = request.POST.get('difficulty', 'medium')
        
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
            
            # Create quiz if provided
            if quiz_title and quiz_description:
                quiz = Quiz(
                    job=post,
                    title=quiz_title,
                    description=quiz_description,
                    time_limit_minutes=int(time_limit),
                    passing_score=int(passing_score),
                    difficulty=difficulty
                )
                quiz.save()
                messages.success(request, 'Job posting created successfully with pre-selection test!')
            else:
                messages.success(request, 'Job posting created successfully!')
            
            return redirect('hiring_company_dashboard')
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

@login_required
def edit_product(request, product_id):
    # Check if user has vendor role
    if not request.user.is_vendor_role:
        messages.error(request, 'You need to have Vendor status to edit product listings.')
        return redirect('dashboard')
    
    # Get the product
    product = get_object_or_404(Post, id=product_id, post_type='product')
    
    # Check if the product belongs to the current user
    if product.user != request.user:
        messages.error(request, 'You do not have permission to edit this product.')
        return redirect('vendor_dashboard')
    
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

@login_required
def add_application_comment(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    
    # Check if user is authorized (either the applicant or the job poster)
    if request.user != application.applicant and request.user != application.job.user:
        messages.error(request, 'You are not authorized to comment on this application.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = ApplicationComment(
                application=application,
                author=request.user,
                content=content
            )
            comment.save()
            messages.success(request, 'Comment added successfully.')
            
            # Redirect to appropriate dashboard based on user role
            if request.user == application.job.user:
                return redirect('application_details', application_id=application_id)
            else:
                return redirect('view_application', application_id=application_id)
        else:
            messages.error(request, 'Comment cannot be empty.')
    
    # If not POST or empty content, redirect back
    if request.user == application.job.user:
        return redirect('application_details', application_id=application_id)
    else:
        return redirect('view_application', application_id=application_id)

@login_required
def application_details(request, application_id):
    # For hiring companies to view application details
    if not request.user.is_hiring_company_role:
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('dashboard')
    
    application = get_object_or_404(JobApplication, id=application_id)
    
    # Ensure the job belongs to the hiring company
    if application.job.user != request.user:
        messages.error(request, 'You are not authorized to view this application.')
        return redirect('hiring_company_dashboard')
    
    # Get comments on this application
    comments = ApplicationComment.objects.filter(application=application).order_by('created_at')
    
    # Get quizzes for this job
    quizzes = Quiz.objects.filter(job=application.job)
    
    context = {
        'application': application,
        'comments': comments,
        'quizzes': quizzes
    }
    
    return render(request, 'authentication/application_details.html', context)

@login_required
def view_application(request, application_id):
    # For freelancers to view their application details
    application = get_object_or_404(JobApplication, id=application_id)
    
    # Ensure the application belongs to the freelancer
    if application.applicant != request.user:
        messages.error(request, 'You are not authorized to view this application.')
        return redirect('freelancer_dashboard')
    
    # Get comments on this application
    comments = ApplicationComment.objects.filter(application=application).order_by('created_at')
    
    # Get quiz attempts by this freelancer
    quiz_attempts = QuizAttempt.objects.filter(application=application)
    
    # Get quizzes available for this job that haven't been attempted yet
    available_quizzes = []
    if application.status == 'pre_interview':
        all_quizzes = Quiz.objects.filter(job=application.job)
        attempted_quiz_ids = quiz_attempts.values_list('quiz_id', flat=True)
        available_quizzes = all_quizzes.exclude(id__in=attempted_quiz_ids)
    
    context = {
        'application': application,
        'comments': comments,
        'quiz_attempts': quiz_attempts,
        'available_quizzes': available_quizzes
    }
    
    return render(request, 'authentication/view_application.html', context)

@login_required
def create_quiz(request, job_id):
    # Only hiring companies can create quizzes for their jobs
    if not request.user.is_hiring_company_role:
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('dashboard')
    
    job = get_object_or_404(Post, id=job_id, post_type='job')
    
    # Ensure the job belongs to the hiring company
    if job.user != request.user:
        messages.error(request, 'You are not authorized to create quizzes for this job.')
        return redirect('hiring_company_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        time_limit = request.POST.get('time_limit', 30)
        passing_score = request.POST.get('passing_score', 70)
        difficulty = request.POST.get('difficulty', 'medium')
        
        if title and description:
            quiz = Quiz(
                job=job,
                title=title,
                description=description,
                time_limit_minutes=time_limit,
                passing_score=passing_score,
                difficulty=difficulty
            )
            quiz.save()
            messages.success(request, 'Quiz created successfully.')
            return redirect('edit_quiz', quiz_id=quiz.id)
        else:
            messages.error(request, 'Please fill all required fields.')
    
    context = {
        'job': job
    }
    
    return render(request, 'authentication/create_quiz.html', context)

@login_required
def edit_quiz(request, quiz_id):
    # Only hiring companies can edit quizzes
    if not request.user.is_hiring_company_role:
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('dashboard')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Ensure the quiz belongs to a job owned by the hiring company
    if quiz.job.user != request.user:
        messages.error(request, 'You are not authorized to edit this quiz.')
        return redirect('hiring_company_dashboard')
    
    # Get existing questions
    questions = QuizQuestion.objects.filter(quiz=quiz)
    
    context = {
        'quiz': quiz,
        'questions': questions
    }
    
    return render(request, 'authentication/edit_quiz.html', context)

@login_required
def add_quiz_question(request, quiz_id):
    # Only hiring companies can add questions
    if not request.user.is_hiring_company_role:
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('dashboard')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Ensure the quiz belongs to a job owned by the hiring company
    if quiz.job.user != request.user:
        messages.error(request, 'You are not authorized to edit this quiz.')
        return redirect('hiring_company_dashboard')
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        question_type = request.POST.get('question_type')
        code_snippet = request.POST.get('code_snippet')
        points = request.POST.get('points', 10)
        
        if question_text and question_type:
            question = QuizQuestion(
                quiz=quiz,
                question_text=question_text,
                question_type=question_type,
                code_snippet=code_snippet,
                points=points
            )
            question.save()
            
            # For multiple choice questions, handle options
            if question_type == 'multiple_choice':
                options_count = int(request.POST.get('options_count', 0))
                for i in range(1, options_count + 1):
                    option_text = request.POST.get(f'option_{i}')
                    is_correct = request.POST.get(f'correct_{i}') == 'on'
                    
                    if option_text:
                        QuizOption.objects.create(
                            question=question,
                            option_text=option_text,
                            is_correct=is_correct
                        )
            
            messages.success(request, 'Question added successfully.')
            return redirect('edit_quiz', quiz_id=quiz.id)
        else:
            messages.error(request, 'Please fill all required fields.')
    
    context = {
        'quiz': quiz
    }
    
    return render(request, 'authentication/add_quiz_question.html', context)

@login_required
def take_quiz(request, quiz_id, application_id):
    # Only freelancers can take quizzes
    if not request.user.is_freelancer_role:
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('dashboard')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    application = get_object_or_404(JobApplication, id=application_id)
    
    # Ensure the application belongs to the freelancer
    if application.applicant != request.user:
        messages.error(request, 'You are not authorized to take this quiz.')
        return redirect('freelancer_dashboard')
    
    # Ensure the quiz belongs to the job applied for
    if quiz.job != application.job:
        messages.error(request, 'This quiz is not associated with your job application.')
        return redirect('view_application', application_id=application.id)
    
    # Check if application is in the right status
    if application.status != 'pre_interview':
        messages.error(request, 'You can only take quizzes during the pre-interview assessment phase.')
        return redirect('view_application', application_id=application.id)
    
    # Check if quiz has already been attempted
    if QuizAttempt.objects.filter(quiz=quiz, application=application).exists():
        messages.error(request, 'You have already attempted this quiz.')
        return redirect('view_application', application_id=application.id)
    
    # Get quiz questions
    questions = QuizQuestion.objects.filter(quiz=quiz)
    
    if request.method == 'POST':
        # Create a new attempt
        attempt = QuizAttempt(
            quiz=quiz,
            application=application,
            completed_at=timezone.now()
        )
        attempt.save()
        
        # Process answers
        total_points = 0
        earned_points = 0
        
        for question in questions:
            if question.question_type == 'multiple_choice':
                selected_option_id = request.POST.get(f'question_{question.id}')
                if selected_option_id:
                    selected_option = QuizOption.objects.get(id=selected_option_id)
                    is_correct = selected_option.is_correct
                    points_earned = question.points if is_correct else 0
                    
                    answer = QuizAnswer(
                        attempt=attempt,
                        question=question,
                        selected_option=selected_option,
                        is_correct=is_correct,
                        points_earned=points_earned
                    )
                    answer.save()
                    
                    earned_points += points_earned
                    total_points += question.points
            
            elif question.question_type == 'text':
                text_answer = request.POST.get(f'question_{question.id}')
                # For text answers, manual grading is required
                answer = QuizAnswer(
                    attempt=attempt,
                    question=question,
                    text_answer=text_answer,
                    is_correct=False,  # Will be graded later
                    points_earned=0
                )
                answer.save()
                total_points += question.points
            
            elif question.question_type == 'code':
                code_answer = request.POST.get(f'question_{question.id}')
                # For code answers, manual grading is required
                answer = QuizAnswer(
                    attempt=attempt,
                    question=question,
                    code_answer=code_answer,
                    is_correct=False,  # Will be graded later
                    points_earned=0
                )
                answer.save()
                total_points += question.points
        
        # Calculate score (based on multiple choice questions only for now)
        if total_points > 0:
            score = (earned_points / total_points) * 100
            attempt.score = score
            
            # Check if passed
            if score >= quiz.passing_score:
                attempt.passed = True
                
                # If all quizzes for this job have been passed, move to interview
                all_quizzes = Quiz.objects.filter(job=application.job)
                all_passed = True
                
                for job_quiz in all_quizzes:
                    # Skip this quiz if it's the one we just took
                    if job_quiz.id == quiz.id:
                        continue
                    
                    # Check if this quiz has been attempted and passed
                    quiz_attempt = QuizAttempt.objects.filter(quiz=job_quiz, application=application).first()
                    if not quiz_attempt or not quiz_attempt.passed:
                        all_passed = False
                        break
                
                if all_passed:
                    application.status = 'interview'
                    application.save()
                    messages.success(request, 'Congratulations! You have passed all assessments and moved to the interview stage.')
            
            attempt.save()
        
        messages.success(request, 'Quiz completed successfully.')
        return redirect('view_application', application_id=application.id)
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'application': application
    }
    
    return render(request, 'authentication/take_quiz.html', context)

@login_required
def edit_job(request, job_id):
    # Check if user has hiring company role
    if not request.user.is_hiring_company_role:
        messages.error(request, 'You need to have Hiring Company status to edit job listings.')
        return redirect('dashboard')
    
    # Get the job
    job = get_object_or_404(Post, id=job_id, post_type='job')
    
    # Check if the job belongs to the current user
    if job.user != request.user:
        messages.error(request, 'You do not have permission to edit this job.')
        return redirect('hiring_company_dashboard')
    
    # Business Rule: Prevent editing job posts if someone has already applied to them
    if JobApplication.objects.filter(job=job).exists():
        messages.error(request, 'This job cannot be edited because applications have already been received.')
        return redirect('hiring_company_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        job_location = request.POST.get('job_location')
        job_type = request.POST.get('job_type')
        salary_range = request.POST.get('salary_range')
        
        if title and description and job_location and job_type:
            # Update job details
            job.title = title
            job.description = description
            job.job_location = job_location
            job.job_type = job_type
            job.salary_range = salary_range
            
            # Handle image update if provided
            image = request.FILES.get('image')
            if image:
                job.image = image
            
            job.save()
            messages.success(request, 'Job posting updated successfully!')
            return redirect('hiring_company_dashboard')
        else:
            messages.error(request, 'Please fill all required fields')
    
    context = {
        'job': job
    }
    
    return render(request, 'authentication/edit_job.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    # Return JSON response for AJAX calls
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    # Redirect back to the previous page
    return redirect(request.META.get('HTTP_REFERER', 'freelancer_dashboard'))

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
    
    return redirect('freelancer_dashboard')