import os
import sys
import django

# Add the project directory to Python path
sys.path.append(r'g:\MyCode\App Taxi Exam')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxi.models import Question, Choice
from django.contrib.auth.models import User

# Check if question 736 exists
print("Checking question 736...")
try:
    question = Question.objects.get(id=736)
    print(f"Found question: {question.question_text[:100]}")
    print(f"Type: {question.question_type}")
    
    # Check choices
    choices = question.choices.all()
    print(f"Number of choices: {choices.count()}")
    for choice in choices:
        print(f"  {choice.option_label}. {choice.choice_text} (Correct: {choice.is_correct})")
        
except Question.DoesNotExist:
    print("Question 736 not found")
    # Show available questions
    questions = Question.objects.all()[:10]
    print(f"Available questions (total: {Question.objects.count()}):")
    for q in questions:
        print(f"  ID: {q.id}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
