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
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('edit-job/<int:job_id>/', views.edit_job, name='edit_job'),
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
    path('application/<int:application_id>/details/', views.application_details, name='application_details'),
    path('application/<int:application_id>/view/', views.view_application, name='view_application'),
    path('application/<int:application_id>/comment/', views.add_application_comment, name='add_application_comment'),
    
    # Quiz management
    path('job/<int:job_id>/create-quiz/', views.create_quiz, name='create_quiz'),
    path('quiz/<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('quiz/<int:quiz_id>/add-question/', views.add_quiz_question, name='add_quiz_question'),
    path('quiz/<int:quiz_id>/application/<int:application_id>/take/', views.take_quiz, name='take_quiz'),
    
    # Notification management
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Legacy paths (kept for compatibility)
    path('become-vendor/', views.become_vendor, name='become_vendor'),
    path('become-hiring-company/', views.become_hiring_company, name='become_hiring_company'),
    path('become-freelancer/', views.become_freelancer, name='become_freelancer'),
]