from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_results, name='search_results'),
    path('item-detail/<int:pk>/', views.item_detail, name='item_detail'),
    path('add-item/', views.add_item, name='add_item'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('insights/', views.insights, name='insights'),
    path('quick-view/<int:pk>/', views.quick_view, name='quick_view'),
    path('request/approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('request/reject/<int:request_id>/', views.reject_request, name='reject_request'),
    path('transaction/confirm-return/<int:transaction_id>/', views.confirm_return, name='confirm_return'),
    path('transaction/rate/<int:transaction_id>/', views.submit_rating, name='submit_rating'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/notifications/count/', views.notification_count_api, name='notification_count_api'),
    path('register/', views.register, name='register'),
    path('admin-stats/', views.admin_stats, name='admin_stats'),
    path('login/', auth_views.LoginView.as_view(template_name='marketplace/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]
