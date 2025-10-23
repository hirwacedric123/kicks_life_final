from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views_rest

# Create router for ViewSets
router = DefaultRouter()
router.register(r'users', api_views_rest.UserViewSet, basename='user')
router.register(r'posts', api_views_rest.PostViewSet, basename='post')
router.register(r'purchases', api_views_rest.PurchaseViewSet, basename='purchase')
router.register(r'bookmarks', api_views_rest.BookmarkViewSet, basename='bookmark')
router.register(r'reviews', api_views_rest.ProductReviewViewSet, basename='review')
router.register(r'qr-codes', api_views_rest.UserQRCodeViewSet, basename='qr-code')
router.register(r'otp', api_views_rest.OTPVerificationViewSet, basename='otp')

# API URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/register/', api_views_rest.UserRegistrationView.as_view(), name='api-register'),
    path('auth/login/', api_views_rest.UserLoginView.as_view(), name='api-login'),
    path('auth/logout/', api_views_rest.user_logout_view, name='api-logout'),
    
    # Dashboard and statistics
    path('dashboard/stats/', api_views_rest.dashboard_stats, name='api-dashboard-stats'),
    path('vendors/<int:vendor_id>/statistics/', api_views_rest.vendor_statistics, name='api-vendor-statistics'),
    
    # QR Code purchase flow (KoraQuest specific)
    path('qr/purchases/', api_views_rest.get_purchases_by_qr, name='api-qr-purchases'),
    path('purchases/complete-pickup/', api_views_rest.complete_purchase_pickup, name='api-complete-pickup'),
    
    # Include router URLs
    path('', include(router.urls)),
]
