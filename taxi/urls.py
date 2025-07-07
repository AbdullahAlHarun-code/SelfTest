from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/delete/<int:category_id>/', views.category_delete, name='category_delete'),
    
    # Question URLs
    path('questions/', views.question_list, name='question_list'),
    path('questions/create/', views.question_create, name='question_create'),
    path('questions/<int:question_id>/', views.question_detail, name='question_detail'),
    path('questions/<int:question_id>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:question_id>/delete/', views.question_delete, name='question_delete'),
    path('questions/<int:question_id>/test/', views.question_test, name='question_test'),
    path('questions/<int:question_id>/simple_test/', views.simple_question_test, name='simple_question_test'),
    
    # Debug URLs
    path('debug/questions/', views.debug_questions, name='debug_questions'),
    path('debug/question/<int:question_id>/', views.debug_question_test, name='debug_question_test'),
]
