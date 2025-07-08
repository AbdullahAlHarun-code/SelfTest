from django.core.management.base import BaseCommand
from taxi.models import Category

class Command(BaseCommand):
    help = 'Create mark categories and subcategories for test success rates'

    def handle(self, *args, **options):
        # Create or get the main "mark" category
        mark_category, created = Category.objects.get_or_create(
            name='mark',
            defaults={
                'description': 'Categories based on test success rates',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created main "mark" category'))
        else:
            self.stdout.write(self.style.WARNING('Main "mark" category already exists'))
        
        # Define subcategories
        subcategories = [
            ('Below 70%', 'Success rate below 70%'),
            ('70% but below 80%', 'Success rate 70% to 79%'),
            ('80% but below 90%', 'Success rate 80% to 89%'),
            ('90% and over', 'Success rate 90% and above'),
        ]
        
        # Create subcategories
        created_count = 0
        for name, description in subcategories:
            subcategory, created = Category.objects.get_or_create(
                name=name,
                parent=mark_category,
                defaults={
                    'description': description,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created subcategory: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Subcategory already exists: {name}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} new subcategories. '
                f'Total mark subcategories: {mark_category.subcategories.count()}'
            )
        )
