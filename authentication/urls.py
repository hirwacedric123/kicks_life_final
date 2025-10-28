from django.urls import path, include
from . import views
from . import api_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.user_settings, name='user_settings'),
    
    # Post creation and interaction
    path('create-post/', views.create_post, name='create_post'),
    path('create-product/', views.create_product, name='create_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    
    # Post detail and actions
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/purchase/', views.purchase_product, name='purchase_product'),
    path('bookmark/<int:post_id>/', views.bookmark_toggle, name='bookmark_toggle'),
    
    # Admin dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('update-order-status/<int:purchase_id>/', views.update_order_status, name='update_order_status'),
    
    # User history and saved items
    path('purchases/', views.purchase_history, name='purchase_history'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    
    # Removed complex QR code and OTP URLs for simplified workflow
    
    # REST API endpoints
    path('api/rest/', include('authentication.api_urls')),
]

# API endpoints
api_endpoints = [
    path('v1/register/', views.register_api, name='register_api'),
    path('v1/login/', views.login_api, name='login_api'),
    path('v1/logout/', views.logout_api, name='logout_api'),
    path('v1/dashboard/', views.dashboard_api, name='dashboard_api'),
    path('v1/bookmark/<int:post_id>/', views.bookmark_toggle_api, name='bookmark_toggle_api'),
    path('v1/like/<int:post_id>/', views.like_post_api, name='like_post_api'),
    path('v1/categories/', views.categories_api, name='categories_api'),
]

# Add api_endpoints to main urlpatterns
urlpatterns += api_endpoints