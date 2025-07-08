from django.urls import path
from . import views
from . import views_exam  # Import the new exam views module

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
    
    # Exam URLs
    path('exam/mock-test/', views_exam.mock_test_categories, name='mock_test_categories'),
    path('exam/mock-test/start/<int:category_id>/', views_exam.start_mock_test, name='start_mock_test'),
    path('exam/mock-test/<int:exam_id>/q/<int:question_number>/', views_exam.take_mock_test, name='take_mock_test'),
    path('exam/mock-test/<int:exam_id>/complete/', views_exam.complete_mock_test, name='complete_mock_test'),
    path('exam/results/<int:exam_id>/', views_exam.view_mock_test_result, name='view_mock_test_result'),
    path('exam/results/', views_exam.user_results, name='user_results'),
    path('exam/report/', views_exam.user_report, name='user_report'),
    
    # Debug URLs
    path('debug/questions/', views.debug_questions, name='debug_questions'),
    path('debug/question/<int:question_id>/', views.debug_question_test, name='debug_question_test'),
]
