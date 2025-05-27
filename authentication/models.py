from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import uuid

class User(AbstractUser):
    USER_ROLES = (
        ('user', 'user'),
        ('staff', 'Staff'),
        ('hiring_company', 'Hiring Company'),
        ('vendor', 'Vendor'),
        ('freelancer', 'Freelancer'),
    )
    
    # Base role for all users
    role = models.CharField(max_length=20, choices=USER_ROLES, default='user')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Additional role flags to support multiple roles
    is_vendor_role = models.BooleanField(default=False)
    is_hiring_company_role = models.BooleanField(default=False)
    is_freelancer_role = models.BooleanField(default=False)
    
    # Freelancer specific fields
    freelancer_skills = models.TextField(blank=True, null=True)
    freelancer_cv = models.FileField(upload_to='cvs/', blank=True, null=True)
    
    # Profile picture
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Stats
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_purchases = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def is_user(self):
        return self.role == 'user' and not (self.is_vendor_role or self.is_hiring_company_role or self.is_freelancer_role)
    
    def is_staff_member(self):
        return self.role == 'staff'
    
    def is_hiring_company(self):
        return self.is_hiring_company_role
    
    def is_vendor(self):
        return self.is_vendor_role
    
    def is_freelancer(self):
        return self.is_freelancer_role

class Post(models.Model):
    POST_TYPES = (
        ('product', 'Product'),
        ('job', 'Job Posting'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='posts/')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    
    # Post type (product or job)
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='product')
    
    # Product specific fields
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    inventory = models.IntegerField(default=1, help_text="Number of items in stock")
    
    # Job specific fields
    job_location = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=50, blank=True, null=True)  # Full-time, Part-time, Contract, etc.
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    
    # Stats
    total_purchases = models.IntegerField(default=0)
    total_applications = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title
        
    def total_likes(self):
        return self.likes.count()
    
    class Meta:
        ordering = ['-created_at']

class Purchase(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    order_id = models.CharField(max_length=50, unique=True, blank=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='purchases')
    quantity = models.IntegerField(default=1)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            # Generate a unique order ID
            self.order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.buyer.username} - {self.product.title} - {self.order_id}"
    
    class Meta:
        ordering = ['-created_at']

class JobApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('pre_interview', 'Pre-Interview Assessment'),
        ('interview', 'Interview'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    job = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='applications/cvs/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True, null=True)
    interview_details = models.TextField(blank=True, null=True, help_text="Details about interview time, place, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['applicant', 'job']

class ApplicationComment(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='application_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment on {self.application} by {self.author.username}"
    
    class Meta:
        ordering = ['created_at']

class Quiz(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    
    job = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField()
    time_limit_minutes = models.IntegerField(default=30)
    passing_score = models.IntegerField(default=70)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = 'Quizzes'

class QuizQuestion(models.Model):
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('text', 'Text Answer'),
        ('code', 'Code Snippet'),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    code_snippet = models.TextField(blank=True, null=True, help_text="Optional code snippet for the question")
    points = models.IntegerField(default=10)
    
    def __str__(self):
        return f"{self.question_text[:30]}..."

class QuizOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.option_text

class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.application.applicant.username}'s attempt at {self.quiz.title}"

class QuizAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuizOption, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(blank=True, null=True)
    code_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Answer to {self.question} by {self.attempt.application.applicant.username}"

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'post']

class ProductImage(models.Model):
    product = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='auxiliary_images')
    image = models.ImageField(upload_to='product_gallery/')
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.product.title} - {self.display_order}"
    
    class Meta:
        ordering = ['display_order']

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('application_status_change', 'Application Status Change'),
        ('new_application', 'New Application'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('general', 'General'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='general')
    title = models.CharField(max_length=255)
    message = models.TextField()
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
    
    class Meta:
        ordering = ['-created_at']
