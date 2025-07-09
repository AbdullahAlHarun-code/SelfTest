#!/usr/bin/env python
"""
Debug script to test category loading
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
from django.db.models import Count

def test_categories():
    """Test category loading functionality"""
    print("=== Testing Category Structure ===")
    
    # Check if there are any categories
    all_categories = Category.objects.all()
    print(f"Total categories in database: {all_categories.count()}")
    
    if all_categories.count() == 0:
        print("❌ No categories found in database!")
        return
    
    # Check root categories (no parent)
    root_categories = Category.objects.filter(parent__isnull=True, is_active=True)
    print(f"Root categories: {root_categories.count()}")
    
    for category in root_categories:
        print(f"- {category.name} (ID: {category.id})")
        
        # Check if it has questions
        questions_count = Question.objects.filter(categories=category).distinct().count()
        print(f"  Direct questions: {questions_count}")
        
        # Check if it has children
        children = category.children.all()
        print(f"  Children: {children.count()}")
        
        for child in children:
            child_questions = Question.objects.filter(categories=child).distinct().count()
            print(f"    - {child.name} (ID: {child.id}) - {child_questions} questions")
    
    print("\n=== Testing AJAX Function Logic ===")
    
    # Simulate the AJAX function logic
    subcategories = Category.objects.filter(
        parent__isnull=True, 
        is_active=True
    ).annotate(
        questions_count=Count('questions', distinct=True)
    )
    
    print(f"Root categories with question count annotation: {subcategories.count()}")
    
    for category in subcategories:
        # Count questions in this category and all its subcategories
        subcategory_ids = [cat.id for cat in category.get_all_descendants()]
        subcategory_ids.append(category.id)
        
        total_questions = Question.objects.filter(
            categories__id__in=subcategory_ids
        ).distinct().count()
        
        has_children = category.children.exists()
        
        print(f"- {category.name}: {total_questions} total questions, has_children: {has_children}")

if __name__ == '__main__':
    test_categories()
