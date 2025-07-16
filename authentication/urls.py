from django.urls import path
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
    
    # User dashboards
    path('vendor-dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    
    # User history and saved items
    path('purchases/', views.purchase_history, name='purchase_history'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    
    # Legacy paths (kept for compatibility)
    path('become-vendor/', views.become_vendor, name='become_vendor'),
    
    # KoraQuest specific URLs
    path('qr-code/', views.user_qr_code, name='user_qr_code'),
    path('koraquest-dashboard/', views.koraquest_dashboard, name='koraquest_dashboard'),
    path('scan-qr/', views.scan_qr_code, name='scan_qr_code'),
    path('confirm-pickup/<int:purchase_id>/', views.confirm_purchase_pickup, name='confirm_purchase_pickup'),
    path('confirm-delivery/<int:purchase_id>/', views.confirm_delivery, name='confirm_delivery'),
    path('update-qr-ajax/', views.update_qr_code_ajax, name='update_qr_code_ajax'),
    path('koraquest-history/', views.koraquest_purchase_history, name='koraquest_purchase_history'),
    
    # API endpoints for QR code scanning and verification flow
    path('api/purchases/by-qr/', api_views.get_purchases_by_qr, name='api_get_purchases_by_qr'),
    path('api/verify-credentials/', api_views.verify_buyer_credentials, name='api_verify_credentials'),
    path('api/send-otp/', api_views.send_otp, name='api_send_otp'),
    path('api/verify-otp/', api_views.verify_otp_view, name='api_verify_otp'),
    path('api/complete-purchase/', api_views.complete_purchase_pickup, name='api_complete_purchase'),
]