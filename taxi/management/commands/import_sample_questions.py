from django.core.management.base import BaseCommand
from django.conf import settings
from taxi.models import Category, Question, Choice
import re
import os

class Command(BaseCommand):
    help = 'Import Kildare area questions specifically'
    
    def handle(self, *args, **options):
        # Create categories
        area_category, created = Category.objects.get_or_create(
            name='Area',
            defaults={'description': 'Area knowledge questions for taxi drivers'}
        )
        
        fares_category, created = Category.objects.get_or_create(
            name='Fares',
            defaults={'description': 'Fares and regulations questions for taxi drivers'}
        )
        
        # Sample area questions from the file
        area_questions = [
            {
                'question': 'What towns do you pass from Celbridge to Allenwood?',
                'options': [
                    {'letter': 'A', 'text': 'Clane and Prosperous'},
                    {'letter': 'B', 'text': 'Maynooth and Kilcock'},
                    {'letter': 'C', 'text': 'Maynooth and Rathcoffee'},
                    {'letter': 'D', 'text': 'Lexlip and Maynooth'}
                ],
                'correct': 'A'
            },
            {
                'question': 'What road is beechmount housing estate on in Newbridge?',
                'options': [
                    {'letter': 'A', 'text': 'Green Rd'},
                    {'letter': 'B', 'text': 'Langton Park Dublin Rd Ballymany'},
                    {'letter': 'C', 'text': 'Station Road'},
                    {'letter': 'D', 'text': 'Main Street'}
                ],
                'correct': 'A'
            },
            {
                'question': 'What road is globe retail park on in Naas?',
                'options': [
                    {'letter': 'A', 'text': 'Sallins Rd'},
                    {'letter': 'B', 'text': 'Dublin Rd Maudlins Ave Monread Road'},
                    {'letter': 'C', 'text': 'Kilcullen Road'},
                    {'letter': 'D', 'text': 'Tipper Road'}
                ],
                'correct': 'B'
            },
            {
                'question': 'What road is Maynooth Post Primary School on?',
                'options': [
                    {'letter': 'A', 'text': 'Dunboyne Rd'},
                    {'letter': 'B', 'text': 'Moyglare Rd'},
                    {'letter': 'C', 'text': 'Parson St'},
                    {'letter': 'D', 'text': 'Kilcock Rd'}
                ],
                'correct': 'B'
            },
            {
                'question': 'What road is St Conleths GAA on in Newbridge?',
                'options': [
                    {'letter': 'A', 'text': 'Henry Road'},
                    {'letter': 'B', 'text': 'Main St'},
                    {'letter': 'C', 'text': 'Station Road'},
                    {'letter': 'D', 'text': 'Standhouse Road'}
                ],
                'correct': 'B'
            },
            {
                'question': 'What road is Newbridge Golf Club on?',
                'options': [
                    {'letter': 'A', 'text': 'Ring of Roseberry'},
                    {'letter': 'B', 'text': 'Blackberry Road'},
                    {'letter': 'C', 'text': 'Barrettstown Road'},
                    {'letter': 'D', 'text': 'Station Road'}
                ],
                'correct': 'B'
            },
            {
                'question': 'What road do you take from Naas to the Curragh?',
                'options': [
                    {'letter': 'A', 'text': 'Ballyclane Road'},
                    {'letter': 'B', 'text': 'Blessington Road'},
                    {'letter': 'C', 'text': 'Dublin Road'},
                    {'letter': 'D', 'text': 'Abbey Street'}
                ],
                'correct': 'B'
            },
            {
                'question': 'What road do you take from Naas town to Punchestown?',
                'options': [
                    {'letter': 'A', 'text': 'Sallins Road'},
                    {'letter': 'B', 'text': 'Blessington Road'},
                    {'letter': 'C', 'text': 'Monread Road'},
                    {'letter': 'D', 'text': 'Tipper Road'}
                ],
                'correct': 'B'
            },
            {
                'question': 'Where is Playbarn Kids centre?',
                'options': [
                    {'letter': 'A', 'text': 'Johnstown'},
                    {'letter': 'B', 'text': 'Naas'},
                    {'letter': 'C', 'text': 'Sallins'},
                    {'letter': 'D', 'text': 'Kill'}
                ],
                'correct': 'A'
            },
            {
                'question': 'What road is Tesco Extra in Maynooth on?',
                'options': [
                    {'letter': 'A', 'text': 'Dublin Rd and Leinster Park'},
                    {'letter': 'B', 'text': 'Maynooth and Kilcock'},
                    {'letter': 'C', 'text': 'Maynooth and Rathcoffee'},
                    {'letter': 'D', 'text': 'Lexlip and Maynooth'}
                ],
                'correct': 'A'
            },
            {
                'question': 'Where is the K Club?',
                'options': [
                    {'letter': 'A', 'text': 'Naas'},
                    {'letter': 'B', 'text': 'Kilmeage'},
                    {'letter': 'C', 'text': 'Kill'},
                    {'letter': 'D', 'text': 'Straffan'}
                ],
                'correct': 'D'
            },
            {
                'question': 'Which of these towns has no train station?',
                'options': [
                    {'letter': 'A', 'text': 'Kilcock'},
                    {'letter': 'B', 'text': 'Naas'},
                    {'letter': 'C', 'text': 'Sallins'},
                    {'letter': 'D', 'text': 'Clane'}
                ],
                'correct': 'B'
            },
            {
                'question': 'Which roads must you take driving from Celbridge to Lucan?',
                'options': [
                    {'letter': 'A', 'text': 'R405 R120'},
                    {'letter': 'B', 'text': 'R403'},
                    {'letter': 'C', 'text': 'R835'},
                    {'letter': 'D', 'text': 'R10'}
                ],
                'correct': 'B'
            },
            {
                'question': 'What road would you take from Naas to Dublin?',
                'options': [
                    {'letter': 'A', 'text': 'N81'},
                    {'letter': 'B', 'text': 'M9'},
                    {'letter': 'C', 'text': 'M7'},
                    {'letter': 'D', 'text': 'N7'}
                ],
                'correct': 'B'
            },
            {
                'question': 'If travelling from Athy to Waterford which roads would you take?',
                'options': [
                    {'letter': 'A', 'text': 'N78 M9'},
                    {'letter': 'B', 'text': 'N78'},
                    {'letter': 'C', 'text': 'N76'},
                    {'letter': 'D', 'text': 'N80'}
                ],
                'correct': 'A'
            }
        ]
        
        # Sample fares questions
        fares_questions = [
            {
                'question': 'What is the maximum fare that can be charged for a journey within Dublin city center during peak hours?',
                'options': [
                    {'letter': 'A', 'text': '€15.00'},
                    {'letter': 'B', 'text': '€20.00'},
                    {'letter': 'C', 'text': '€25.00'},
                    {'letter': 'D', 'text': 'No maximum limit'}
                ],
                'correct': 'D'
            },
            {
                'question': 'When must the taxi meter be switched on?',
                'options': [
                    {'letter': 'A', 'text': 'Only for long journeys'},
                    {'letter': 'B', 'text': 'At the start of every journey'},
                    {'letter': 'C', 'text': 'Only during peak hours'},
                    {'letter': 'D', 'text': 'Only for airport trips'}
                ],
                'correct': 'B'
            },
            {
                'question': 'What is the standard waiting time charge per minute?',
                'options': [
                    {'letter': 'A', 'text': '€0.30'},
                    {'letter': 'B', 'text': '€0.50'},
                    {'letter': 'C', 'text': '€0.75'},
                    {'letter': 'D', 'text': '€1.00'}
                ],
                'correct': 'B'
            },
            {
                'question': 'Are taxi drivers required to accept card payments?',
                'options': [
                    {'letter': 'A', 'text': 'Yes, always'},
                    {'letter': 'B', 'text': 'No, cash only'},
                    {'letter': 'C', 'text': 'Only for fares over €10'},
                    {'letter': 'D', 'text': 'It depends on the taxi company'}
                ],
                'correct': 'A'
            },
            {
                'question': 'What percentage tip is customary for taxi drivers in Ireland?',
                'options': [
                    {'letter': 'A', 'text': '5-10%'},
                    {'letter': 'B', 'text': '10-15%'},
                    {'letter': 'C', 'text': '15-20%'},
                    {'letter': 'D', 'text': 'No tip expected'}
                ],
                'correct': 'B'
            }
        ]
        
        # Import area questions
        area_count = 0
        for q_data in area_questions:
            question = Question.objects.create(
                question_text=q_data['question'],
                question_type='single'
            )
            question.categories.add(area_category)
            
            for option in q_data['options']:
                Choice.objects.create(
                    question=question,
                    option_label=option['letter'],
                    choice_text=option['text'],
                    is_correct=option['letter'] == q_data['correct']
                )
            area_count += 1
        
        # Import fares questions
        fares_count = 0
        for q_data in fares_questions:
            question = Question.objects.create(
                question_text=q_data['question'],
                question_type='single'
            )
            question.categories.add(fares_category)
            
            for option in q_data['options']:
                Choice.objects.create(
                    question=question,
                    option_label=option['letter'],
                    choice_text=option['text'],
                    is_correct=option['letter'] == q_data['correct']
                )
            fares_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully imported {area_count} area questions and {fares_count} fares questions!'
            )
        )
