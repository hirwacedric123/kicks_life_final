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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['applicant', 'job']

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'post']
