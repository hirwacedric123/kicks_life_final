from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login', http_method_names=['post', 'get']), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.user_settings, name='user_settings'),
    
    # Post creation and interaction
    path('create-post/', views.create_post, name='create_post'),
    path('create-product/', views.create_product, name='create_product'),
    path('create-job/', views.create_job, name='create_job'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    
    # Post detail and actions
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/purchase/', views.purchase_product, name='purchase_product'),
    path('post/<int:post_id>/apply/', views.apply_for_job, name='apply_for_job'),
    path('bookmark/<int:post_id>/', views.bookmark_toggle, name='bookmark_toggle'),
    
    # User dashboards
    path('vendor-dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('hiring-dashboard/', views.hiring_company_dashboard, name='hiring_company_dashboard'),
    path('freelancer-dashboard/', views.freelancer_dashboard, name='freelancer_dashboard'),
    
    # User history and saved items
    path('purchases/', views.purchase_history, name='purchase_history'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    
    # Job application management
    path('application/<int:application_id>/update/', views.update_application_status, name='update_application_status'),
    
    # Legacy paths (kept for compatibility)
    path('become-vendor/', views.become_vendor, name='become_vendor'),
    path('become-hiring-company/', views.become_hiring_company, name='become_hiring_company'),
    path('become-freelancer/', views.become_freelancer, name='become_freelancer'),
]