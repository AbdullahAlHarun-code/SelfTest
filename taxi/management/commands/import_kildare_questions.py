import re
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from taxi.models import Category, Question, Choice

class Command(BaseCommand):
    help = 'Clear all questions and import only Kildare area questions'
    
    def handle(self, *args, **options):
        # Clear all existing questions and choices
        self.stdout.write('Clearing all existing questions...')
        Question.objects.all().delete()
        Choice.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('All questions cleared.'))
        
        # Create or get Area category
        area_category, created = Category.objects.get_or_create(
            name='Area',
            defaults={'description': 'Area knowledge questions for taxi drivers'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created category: Area'))
        
        # Path to the Kildare questions file
        file_path = os.path.join(settings.BASE_DIR, 'kildare_area_questions_corrected.txt')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Parse questions using regex
            questions = self.parse_questions(content)
            
            imported_count = 0
            skipped_count = 0
            
            for question_data in questions:
                if self.import_question(question_data, area_category):
                    imported_count += 1
                    if imported_count % 10 == 0:
                        self.stdout.write(f'Imported {imported_count} questions...')
                else:
                    skipped_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported {imported_count} Kildare area questions. '
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
        
        for i, block in enumerate(question_blocks[1:], 1):  # Skip the first empty block
            if not block.strip():
                continue
                
            question_data = self.parse_question_block(block, i)
            if question_data:
                questions.append(question_data)
        
        return questions
    
    def parse_question_block(self, block, question_number):
        """Parse a single question block"""
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        question_data = {
            'number': question_number,
            'type': 'single',
            'question': '',
            'options': [],
            'correct_answer': ''
        }
        
        i = 0
        # Skip type line if present
        if i < len(lines) and 'Type:' in lines[i]:
            if 'Multiple' in lines[i]:
                question_data['type'] = 'multiple'
            i += 1
        
        # Extract question text
        if i < len(lines) and 'Question:' in lines[i]:
            question_data['question'] = lines[i].replace('Question:', '').strip()
            i += 1
        
        # Skip until we find Options:
        while i < len(lines) and not lines[i].startswith('Options:'):
            i += 1
        
        if i < len(lines):
            i += 1  # Skip "Options:" line
        
        # Extract options
        while i < len(lines) and not lines[i].startswith('Answer:'):
            line = lines[i]
            option_match = re.match(r'^([A-D])\.\s+(.+)$', line)
            if option_match:
                option_letter = option_match.group(1)
                option_text = option_match.group(2)
                question_data['options'].append({
                    'letter': option_letter,
                    'text': option_text
                })
            i += 1
        
        # Extract answer
        if i < len(lines) and lines[i].startswith('Answer:'):
            question_data['correct_answer'] = lines[i].replace('Answer:', '').strip()
        
        # Validate question data
        if (question_data['question'] and 
            len(question_data['options']) >= 2 and 
            question_data['correct_answer'] and
            not '[Could not parse question text clearly]' in question_data['question'] and
            not any('Option 1' in str(opt) for opt in question_data['options'])):
            return question_data
        
        return None
    
    def import_question(self, question_data, category):
        """Import a single question to the database"""
        try:
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
                self.style.ERROR(f'Error importing question {question_data.get("number", "")}: {str(e)}')
            )
            return False
