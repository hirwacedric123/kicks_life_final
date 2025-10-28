from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views_rest, api_views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'users', api_views_rest.UserViewSet, basename='user')
router.register(r'posts', api_views_rest.PostViewSet, basename='post')
router.register(r'purchases', api_views_rest.PurchaseViewSet, basename='purchase')
router.register(r'bookmarks', api_views_rest.BookmarkViewSet, basename='bookmark')
router.register(r'reviews', api_views_rest.ProductReviewViewSet, basename='review')

# API URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/register/', api_views_rest.UserRegistrationView.as_view(), name='api-register'),
    path('auth/login/', api_views_rest.UserLoginView.as_view(), name='api-login'),
    path('auth/logout/', api_views_rest.user_logout_view, name='api-logout'),
    
    # Dashboard and statistics
    path('dashboard/stats/', api_views_rest.dashboard_stats, name='api-dashboard-stats'),
    
    # Admin API endpoints
    path('admin/statistics/', api_views.get_admin_statistics, name='api-admin-statistics'),
    path('admin/orders/<str:order_id>/', api_views.get_order_details, name='api-order-details'),
    path('admin/orders/update/', api_views.update_order_status_api, name='api-update-order-status'),
    
    # Include router URLs
    path('', include(router.urls)),
]
