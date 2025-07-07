import re
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from taxi.models import Category, Question, Choice

class Command(BaseCommand):
    help = 'Import questions from the Kildare area questions file'
    
    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to the questions file')
        parser.add_argument('--category', type=str, default='Area', help='Category name for the questions')
    
    def handle(self, *args, **options):
        file_path = options['file'] or os.path.join(settings.BASE_DIR, 'kildare_area_questions_corrected.txt')
        category_name = options['category']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        
        # Create or get categories
        area_category, created = Category.objects.get_or_create(
            name='Area',
            defaults={'description': 'Area knowledge questions for taxi drivers'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: Area'))
        
        fares_category, created = Category.objects.get_or_create(
            name='Fares',
            defaults={'description': 'Fares and regulations questions for taxi drivers'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: Fares'))
        
        # For now, we'll categorize all questions as Area since they're all area-related
        # In the future, you can add fares questions separately
        target_category = area_category
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Parse questions using regex
            questions = self.parse_questions(content)
            
            imported_count = 0
            skipped_count = 0
            
            for question_data in questions:
                if self.import_question(question_data, target_category):
                    imported_count += 1
                else:
                    skipped_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported {imported_count} questions. '
                    f'Skipped {skipped_count} questions.'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading file: {str(e)}'))
    
    def parse_questions(self, content):
        """Parse questions from the text content"""
        questions = []
        
        # Split content by question markers
        question_blocks = re.split(r'QUESTION \d+', content)
        
        for block in question_blocks[1:]:  # Skip the first empty block
            if not block.strip():
                continue
                
            question_data = self.parse_question_block(block)
            if question_data:
                questions.append(question_data)
        
        return questions
    
    def parse_question_block(self, block):
        """Parse a single question block"""
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        question_data = {
            'type': 'single',
            'question': '',
            'options': [],
            'correct_answer': ''
        }
        
        # Extract question type
        if 'Type:' in lines[0]:
            type_line = lines[0]
            if 'Multiple' in type_line:
                question_data['type'] = 'multiple'
            lines = lines[1:]
        
        # Extract question text
        if lines and 'Question:' in lines[0]:
            question_data['question'] = lines[0].replace('Question:', '').strip()
            lines = lines[1:]
        
        # Extract options
        options_started = False
        answer_found = False
        
        for line in lines:
            if line.startswith('Options:'):
                options_started = True
                continue
            elif line.startswith('Answer:'):
                question_data['correct_answer'] = line.replace('Answer:', '').strip()
                answer_found = True
                break
            elif options_started and re.match(r'^[A-D]\.\s+', line):
                # Extract option letter and text
                option_match = re.match(r'^([A-D])\.\s+(.+)$', line)
                if option_match:
                    option_letter = option_match.group(1)
                    option_text = option_match.group(2)
                    question_data['options'].append({
                        'letter': option_letter,
                        'text': option_text
                    })
        
        # Validate question data
        if (question_data['question'] and 
            len(question_data['options']) >= 2 and 
            question_data['correct_answer']):
            return question_data
        
        return None
    
    def import_question(self, question_data, category):
        """Import a single question to the database"""
        try:
            # Skip questions with unclear text
            if '[Could not parse question text clearly]' in question_data['question']:
                return False
            
            if 'Option 1' in str(question_data['options']):
                return False
            
            # Create question
            question = Question.objects.create(
                question_text=question_data['question'],
                question_type=question_data['type']
            )
            
            # Add category
            question.categories.add(category)
            
            # Create choices
            for option in question_data['options']:
                is_correct = option['letter'] == question_data['correct_answer']
                Choice.objects.create(
                    question=question,
                    option_label=option['letter'],
                    choice_text=option['text'],
                    is_correct=is_correct
                )
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing question: {str(e)}')
            )
            return False
