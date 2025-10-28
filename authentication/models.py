from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class User(AbstractUser):
    USER_ROLES = (
        ('customer', 'Customer'),
        ('admin', 'Admin/Store Owner'),
    )
    
    # Base role for all users
    role = models.CharField(max_length=20, choices=USER_ROLES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Profile picture
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Stats
    total_purchases = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def is_customer(self):
        return self.role == 'customer'
    
    @property
    def is_admin(self):
        return self.role == 'admin'

class Post(models.Model):
    CATEGORY_CHOICES = (
        ('sneakers', 'Sneakers'),
        ('boots', 'Boots'),
        ('formal', 'Formal Shoes'),
        ('sandals', 'Sandals & Slippers'),
        ('athletic', 'Athletic & Sports'),
        ('casual', 'Casual Shoes'),
        ('kids', 'Kids Shoes'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='posts/')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', null=True, blank=True, help_text="Store admin who created this product")
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    
    # Product fields
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    inventory = models.IntegerField(default=1, help_text="Number of items in stock")
    
    # Stats
    total_purchases = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title
        
    def total_likes(self):
        return self.likes.count()
    
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0
    
    def review_count(self):
        return self.reviews.count()
    
    def is_sold_out(self):
        return self.inventory <= 0
    
    class Meta:
        ordering = ['-created_at']

class ProductReview(models.Model):
    product = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'reviewer']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reviewer.username} - {self.product.title} - {self.rating} stars"

class Purchase(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    DELIVERY_CHOICES = (
        ('pickup', 'Store Pickup'),
        ('delivery', 'Home Delivery'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('momo', 'Mobile Money'),
        ('credit', 'Credit Card'),
        ('cash', 'Cash on Delivery'),
    )
    
    order_id = models.CharField(max_length=50, unique=True, blank=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='purchases')
    quantity = models.IntegerField(default=1)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='pickup')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='momo')
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    delivery_address = models.TextField(blank=True, null=True, help_text="Delivery address for home delivery")
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Simplified fields for direct store operations
    notes = models.TextField(blank=True, null=True, help_text="Order notes or special instructions")
    tracking_number = models.CharField(max_length=100, blank=True, null=True, help_text="Tracking number for shipped orders")
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            # Generate a unique order ID
            self.order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Set delivery fee if delivery method is delivery
        if self.delivery_method == 'delivery' and self.delivery_fee == 0:
            from decimal import Decimal
            self.delivery_fee = Decimal('5.00')  # RWF5 delivery fee
        
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calculate total amount including delivery fees"""
        from decimal import Decimal
        return self.purchase_price + self.delivery_fee
    
    def __str__(self):
        return f"{self.buyer.username} - {self.product.title} - {self.order_id}"
    
    class Meta:
        ordering = ['-created_at']

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
        return f"{self.product.title} - Image {self.display_order + 1}"
    
    class Meta:
        ordering = ['display_order']

# Removed QR Code and OTP models for simplified workflow
