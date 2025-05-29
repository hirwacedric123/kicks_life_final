from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Post, Purchase, Bookmark, ProductImage, UserQRCode, OTPVerification, ProductReview

class UserAdmin(BaseUserAdmin):
    # Add the custom fields to the admin interface
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'role', 'is_vendor_role', 'profile_picture', 'total_sales', 'total_purchases')
        }),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_vendor_role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_vendor_role', 'is_staff', 'is_active')

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'price', 'category', 'inventory', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'description')

class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'product', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'delivery_method', 'created_at')
    search_fields = ('buyer__username', 'product__title')

class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('reviewer__username', 'product__title')

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(Bookmark)
admin.site.register(ProductImage)
admin.site.register(UserQRCode)
admin.site.register(OTPVerification)
