#!/usr/bin/env python
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxi.models import Question, Choice

# Check if question 736 exists
try:
    question = Question.objects.prefetch_related('choices').get(id=736)
    print(f"Question 736 found: {question.question_text[:50]}...")
    print(f"Question type: {question.question_type}")
    print(f"Number of choices: {question.choices.count()}")
    
    # Check choices
    for choice in question.choices.all():
        print(f"  {choice.option_label}. {choice.choice_text} - {'Correct' if choice.is_correct else 'Incorrect'}")
    
    # Test get_test_stats method
    from django.contrib.auth.models import User
    try:
        # Get first user
        user = User.objects.first()
        if user:
            stats = question.get_test_stats(user)
            print(f"Test stats for user {user.username}: {stats}")
        else:
            print("No users found")
    except Exception as e:
        print(f"Error getting test stats: {e}")
        
except Question.DoesNotExist:
    print("Question 736 does not exist")
    # Get all questions to see what exists
    questions = Question.objects.all()[:5]
    print("Available questions:")
    for q in questions:
        print(f"  ID: {q.id}, Text: {q.question_text[:50]}...")
except Exception as e:
    print(f"Error: {e}")
