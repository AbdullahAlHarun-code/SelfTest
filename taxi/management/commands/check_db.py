from django.core.management.base import BaseCommand
from taxi.models import Question, Choice, QuestionTestResult
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Check and fix database issues with questions'

    def handle(self, *args, **options):
        self.stdout.write('Starting database check...')
        
        # Check if there are any questions
        total_questions = Question.objects.count()
        self.stdout.write(f'Total questions: {total_questions}')
        
        # Check questions without choices
        questions_without_choices = []
        for q in Question.objects.all():
            if q.choices.count() == 0:
                questions_without_choices.append(q.id)
        
        self.stdout.write(f'Found {len(questions_without_choices)} questions without choices: {questions_without_choices}')
        
        # Check questions without correct answers
        questions_without_correct_answers = []
        for q in Question.objects.prefetch_related('choices').all():
            if not q.choices.filter(is_correct=True).exists():
                questions_without_correct_answers.append(q.id)
        
        self.stdout.write(f'Found {len(questions_without_correct_answers)} questions without correct answers: {questions_without_correct_answers}')
        
        # Check for specific question IDs
        for question_id in [735, 736]:
            try:
                q = Question.objects.get(id=question_id)
                self.stdout.write(f'Question {question_id} found:')
                self.stdout.write(f'  Text: {q.question_text[:50]}...')
                self.stdout.write(f'  Type: {q.question_type}')
                
                choices = q.choices.all()
                self.stdout.write(f'  Choices: {choices.count()}')
                for choice in choices:
                    self.stdout.write(f'    {choice.option_label}. {choice.choice_text} ({"Correct" if choice.is_correct else "Incorrect"})')
            except Question.DoesNotExist:
                self.stdout.write(f'Question {question_id} does not exist')
        
        # Fix issues if needed
        if options.get('fix', False):
            # Add sample choices to questions without choices
            for q_id in questions_without_choices:
                q = Question.objects.get(id=q_id)
                self.stdout.write(f'Adding sample choices to question {q_id}')
                
                # Create 4 choices
                for i, label in enumerate(['A', 'B', 'C', 'D']):
                    Choice.objects.create(
                        question=q,
                        option_label=label,
                        choice_text=f'Sample choice {label}',
                        is_correct=(i == 0)  # Make first choice correct
                    )
                
            # Fix questions without correct answers
            for q_id in questions_without_correct_answers:
                q = Question.objects.get(id=q_id)
                if q.choices.exists():
                    # Make first choice correct
                    first_choice = q.choices.first()
                    self.stdout.write(f'Making choice {first_choice.option_label} correct for question {q_id}')
                    first_choice.is_correct = True
                    first_choice.save()
                
            self.stdout.write(self.style.SUCCESS('Database fixes applied'))
        
        self.stdout.write(self.style.SUCCESS('Database check completed'))
