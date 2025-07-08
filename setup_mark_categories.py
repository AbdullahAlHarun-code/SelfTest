#!/usr/bin/env python
"""
Script to create mark categories for the taxi app
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxi.models import Category

def create_mark_categories():
    """Create mark categories and subcategories"""
    # Create or get the main mark category
    mark_category, created = Category.objects.get_or_create(
        name='mark',
        defaults={'description': 'Performance-based marking categories'}
    )
    
    if created:
        print(f"Created main category: {mark_category.name}")
    else:
        print(f"Main category already exists: {mark_category.name}")
    
    # Define subcategories
    subcategories = [
        'Below 70%',
        '70% but below 80%',
        '80% but below 90%',
        '90% and over'
    ]
    
    # Create subcategories
    for sub_name in subcategories:
        sub_category, created = Category.objects.get_or_create(
            name=sub_name,
            parent=mark_category,
            defaults={'description': f'Questions with success rate {sub_name.lower()}'}
        )
        
        if created:
            print(f"Created subcategory: {sub_category.name}")
        else:
            print(f"Subcategory already exists: {sub_category.name}")
    
    print("\nAll mark categories:")
    for cat in Category.objects.filter(name='mark'):
        print(f"- {cat.name}")
        for child in cat.children.all():
            print(f"  - {child.name}")
    
    return mark_category

if __name__ == '__main__':
    create_mark_categories()
