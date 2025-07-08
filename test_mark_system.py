#!/usr/bin/env python
"""
Test script to verify mark categories and functionality
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxi.models import Category, Question
from django.contrib.auth.models import User

def test_mark_categories():
    """Test if mark categories exist and are properly structured"""
    print("=== Testing Mark Categories ===")
    
    # Check if main mark category exists
    mark_category = Category.objects.filter(name='mark', parent__isnull=True).first()
    if not mark_category:
        print("❌ Main 'mark' category not found!")
        return False
    else:
        print(f"✅ Main category found: {mark_category.name}")
    
    # Check subcategories
    expected_subcategories = [
        'Below 70%',
        '70% but below 80%',
        '80% but below 90%',
        '90% and over'
    ]
    
    for sub_name in expected_subcategories:
        sub_cat = Category.objects.filter(name=sub_name, parent=mark_category).first()
        if not sub_cat:
            print(f"❌ Subcategory '{sub_name}' not found!")
            return False
        else:
            print(f"✅ Subcategory found: {sub_cat.name}")
    
    print("\n=== All Categories ===")
    all_categories = Category.objects.all()
    for cat in all_categories:
        parent_name = cat.parent.name if cat.parent else "None"
        print(f"- {cat.name} (parent: {parent_name})")
    
    return True

def test_question_assignment():
    """Test assigning mark category to a question"""
    print("\n=== Testing Question Assignment ===")
    
    # Get first question
    question = Question.objects.first()
    if not question:
        print("❌ No questions found in database!")
        return False
    
    print(f"Testing with question: {question.question_text[:50]}...")
    
    # Get first user
    user = User.objects.first()
    if not user:
        print("❌ No users found in database!")
        return False
    
    print(f"Testing with user: {user.username}")
    
    # Test the update_mark_category method directly
    result = question.update_mark_category(user)
    if result:
        print(f"✅ Mark category assignment successful: {result.name}")
        
        # Check question's categories
        question_categories = question.categories.all()
        print(f"Question now has categories: {[cat.name for cat in question_categories]}")
        
        return True
    else:
        print("❌ Mark category assignment failed!")
        return False

if __name__ == '__main__':
    categories_ok = test_mark_categories()
    if categories_ok:
        test_question_assignment()
    else:
        print("Cannot test question assignment - categories not set up properly")
