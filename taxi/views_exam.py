from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, F
import random
import json
from .models import Category, Question, Choice, MockExam, MockExamQuestion

@login_required
def mock_test_categories(request):
    """Display all categories for mock test with proper hierarchy and multi-select"""
    if request.method == 'POST':
        # Handle multi-category test start
        selected_categories = request.POST.getlist('selected_categories')
        if not selected_categories:
            messages.error(request, "Please select at least one category.")
            return redirect('mock_test_categories')
        
        # Convert to integers
        try:
            category_ids = [int(cat_id) for cat_id in selected_categories]
        except ValueError:
            messages.error(request, "Invalid category selection.")
            return redirect('mock_test_categories')
        
        # Start mock test with multiple categories
        return start_multi_category_mock_test(request, category_ids)
    
    # GET request - show category selection interface
    # Get all categories with question counts
    all_categories = Category.objects.filter(
        is_active=True
    ).distinct().annotate(
        questions_count=Count('questions', distinct=True)
    ).order_by('name')
    
    # Function to recursively build category tree
    def build_category_tree(parent=None, level=0):
        result = []
        categories = all_categories.filter(parent=parent)
        
        for category in categories:
            # Get all subcategories recursively
            subcategories_tree = build_category_tree(category, level + 1)
            
            # Count questions in this category and all its subcategories
            subcategory_ids = [cat.id for cat in category.get_all_descendants()]
            subcategory_ids.append(category.id)
            
            # Count questions directly in this category and its subcategories
            questions_count = Question.objects.filter(
                categories__id__in=subcategory_ids
            ).distinct().count()
            
            # Check if this category or any subcategory has questions
            has_subcategory_with_questions = any(
                subcat.get('has_questions', False) for subcat in subcategories_tree
            )
            
            # Build category data
            category_data = {
                'id': category.id,
                'name': category.name,
                'level': level,
                'questions_count': questions_count,
                'has_questions': questions_count > 0,
                'has_subcategory_with_questions': has_subcategory_with_questions,
                'subcategories': subcategories_tree
            }
            result.append(category_data)
        
        return result
    
    # Build the category tree starting from root categories
    category_tree = build_category_tree()
    
    context = {
        'category_tree': category_tree,
        'title': 'Mock Test - Select Category'
    }
    
    return render(request, 'exam/mock_test_categories.html', context)

@login_required
def start_mock_test(request, category_id):
    """Start a new mock test for the selected category"""
    category = get_object_or_404(Category, id=category_id, is_active=True)
    
    # Get questions from this category and all its subcategories
    category_ids = [category.id]
    for subcat in category.get_all_descendants():
        category_ids.append(subcat.id)
    
    # Get all questions for these categories
    questions = Question.objects.filter(categories__id__in=category_ids).distinct()
    
    # Check if we have enough questions
    if questions.count() < 1:  # Ensure we have at least one question
        messages.error(request, f"No questions found in '{category.name}' category or its subcategories.")
        return redirect('mock_test_categories')
    
    # Determine minimum number of questions based on category level
    min_questions = max(1, min(5, questions.count()))
    
    if questions.count() < min_questions:
        messages.warning(request, f"Only {questions.count()} questions available in this category. Starting test with all available questions.")
    
    # Select random questions (maximum 20, or all if less than 20)
    question_count = min(20, questions.count())
    selected_questions = list(questions)
    random.shuffle(selected_questions)
    selected_questions = selected_questions[:question_count]
    
    # Create a new mock exam
    mock_exam = MockExam.objects.create(
        user=request.user,
        category=category,
        total_questions=question_count
    )
    
    # Create the exam questions in a random order
    for i, question in enumerate(selected_questions, 1):
        MockExamQuestion.objects.create(
            mock_exam=mock_exam,
            question=question,
            order=i
        )
    
    return redirect('take_mock_test', exam_id=mock_exam.id, question_number=1)

@login_required
def take_mock_test(request, exam_id, question_number):
    """Take a mock test - display question and process answers"""
    mock_exam = get_object_or_404(
        MockExam, 
        id=exam_id, 
        user=request.user, 
        completed=False
    )
    
    try:
        question_number = int(question_number)
        
        # Validate question number
        if question_number < 1 or question_number > mock_exam.total_questions:
            raise ValueError("Invalid question number")
        
        # Get the exam question
        exam_question = get_object_or_404(
            MockExamQuestion,
            mock_exam=mock_exam,
            order=question_number
        )
        
        if request.method == 'POST':
            # Process answer submission
            selected_choice_ids = request.POST.getlist('selected_choices')
            
            if not selected_choice_ids:
                messages.error(request, "You must select at least one answer.")
                return redirect('take_mock_test', exam_id=exam_id, question_number=question_number)
            
            # Get all correct choices for this question
            correct_choices = exam_question.question.choices.filter(is_correct=True)
            
            # Check if the answer is correct
            if exam_question.question.question_type == 'single':
                # For single-choice questions, one correct answer must be selected
                is_correct = (len(selected_choice_ids) == 1 and 
                              int(selected_choice_ids[0]) in correct_choices.values_list('id', flat=True))
            else:
                # For multiple-choice questions, all correct choices must be selected
                # and no incorrect choices can be selected
                selected_choices = set(int(c) for c in selected_choice_ids)
                correct_choice_ids = set(correct_choices.values_list('id', flat=True))
                is_correct = selected_choices == correct_choice_ids
            
            # Save the answer
            exam_question.selected_choices.clear()
            for choice_id in selected_choice_ids:
                choice = get_object_or_404(Choice, id=choice_id, question=exam_question.question)
                exam_question.selected_choices.add(choice)
            
            exam_question.is_correct = is_correct
            exam_question.save()
            
            # Determine the next step
            if question_number < mock_exam.total_questions:
                # Go to the next question
                return redirect('take_mock_test', exam_id=exam_id, question_number=question_number + 1)
            else:
                # Last question, complete the exam
                return redirect('complete_mock_test', exam_id=exam_id)
        
        # Prepare the context for rendering the question
        context = {
            'mock_exam': mock_exam,
            'exam_question': exam_question,
            'question': exam_question.question,
            'choices': exam_question.question.choices.all(),
            'current_question': question_number,
            'total_questions': mock_exam.total_questions,
            'title': f'Mock Test - Question {question_number}'
        }
        
        return render(request, 'exam/take_mock_test.html', context)
    
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('mock_test_categories')
    except Exception as e:
        messages.error(request, f"Error loading question: {str(e)}")
        return redirect('mock_test_categories')

@login_required
def complete_mock_test(request, exam_id):
    """Complete the mock test and show results"""
    mock_exam = get_object_or_404(
        MockExam, 
        id=exam_id, 
        user=request.user
    )
    
    if mock_exam.completed:
        # Exam already completed, show results
        return redirect('view_mock_test_result', exam_id=exam_id)
    
    # Calculate results
    correct_answers = mock_exam.exam_questions.filter(is_correct=True).count()
    
    # Update the mock exam
    mock_exam.completed = True
    mock_exam.end_time = timezone.now()
    mock_exam.correct_answers = correct_answers
    mock_exam.save()
    
    # Update question success rates for all questions in this exam
    for exam_question in mock_exam.exam_questions.all():
        # Create a QuestionTestResult for each question to update statistics
        if exam_question.is_correct is not None:  # Skip unanswered questions
            from .models import QuestionTestResult
            result = QuestionTestResult.objects.create(
                user=request.user,
                question=exam_question.question,
                is_correct=exam_question.is_correct
            )
            # Add the selected choices
            result.selected_choices.set(exam_question.selected_choices.all())
            
            # Update the question's mark category
            exam_question.question.update_mark_category(request.user)
    
    return redirect('view_mock_test_result', exam_id=exam_id)

@login_required
def view_mock_test_result(request, exam_id):
    """View the results of a completed mock test"""
    mock_exam = get_object_or_404(
        MockExam, 
        id=exam_id, 
        user=request.user
    )
    
    if not mock_exam.completed:
        messages.warning(request, "This test is not yet completed.")
        return redirect('take_mock_test', exam_id=exam_id, question_number=1)
    
    # Get all the exam questions with their results
    exam_questions = mock_exam.exam_questions.all().order_by('order')
    
    context = {
        'mock_exam': mock_exam,
        'exam_questions': exam_questions,
        'score_percentage': mock_exam.score_percentage,
        'correct_answers': mock_exam.correct_answers,
        'total_questions': mock_exam.total_questions,
        'title': 'Mock Test Results'
    }
    
    return render(request, 'exam/mock_test_result.html', context)

@login_required
def user_results(request):
    """View all user's mock test results"""
    user_exams = MockExam.objects.filter(
        user=request.user,
        completed=True
    ).order_by('-end_time')
    
    # Get some statistics
    total_tests = user_exams.count()
    avg_score = user_exams.aggregate(avg_score=Avg('correct_answers'))['avg_score'] or 0
    avg_percentage = 0
    if total_tests > 0:
        total_questions = sum(exam.total_questions for exam in user_exams)
        total_correct = sum(exam.correct_answers for exam in user_exams)
        avg_percentage = round((total_correct / total_questions) * 100, 1) if total_questions > 0 else 0
    
    context = {
        'user_exams': user_exams,
        'total_tests': total_tests,
        'avg_percentage': avg_percentage,
        'title': 'My Test Results'
    }
    
    return render(request, 'exam/user_results.html', context)

@login_required
def user_report(request):
    """Generate a report on user's performance by category"""
    # Get all categories where the user has taken tests
    from django.db.models import Count, Avg, Case, When, IntegerField, Sum
    
    # Get all mock exams by this user
    user_exams = MockExam.objects.filter(user=request.user, completed=True)
    
    # Get performance by category
    categories_data = []
    if user_exams.exists():
        category_stats = user_exams.values(
            'category__id', 'category__name'
        ).annotate(
            exam_count=Count('id'),
            avg_score=Avg(F('correct_answers') * 100.0 / F('total_questions')),
            total_questions=Sum('total_questions'),
            total_correct=Sum('correct_answers')
        ).order_by('-avg_score')
        
        for stat in category_stats:
            categories_data.append({
                'id': stat['category__id'],
                'name': stat['category__name'],
                'exam_count': stat['exam_count'],
                'avg_score': round(stat['avg_score'], 1),
                'total_questions': stat['total_questions'],
                'total_correct': stat['total_correct'],
            })
    
    # Get performance by question category (mark subcategories)
    mark_category = Category.objects.filter(name='mark', parent__isnull=True).first()
    mark_subcategories = []
    
    if mark_category:
        # Get the user's mark subcategories
        subcategories = Category.objects.filter(parent=mark_category)
        
        for subcat in subcategories:
            # Get questions that belong to this subcategory
            question_count = Question.objects.filter(
                categories=subcat,
                test_results__user=request.user
            ).distinct().count()
            
            if question_count > 0:
                mark_subcategories.append({
                    'name': subcat.name,
                    'question_count': question_count,
                })
    
    mark_subcategories.sort(key=lambda x: x['name'])
    
    context = {
        'categories_data': categories_data,
        'mark_subcategories': mark_subcategories,
        'title': 'My Performance Report'
    }
    
    return render(request, 'exam/user_report.html', context)

@login_required
def start_multi_category_mock_test(request, category_ids):
    """Start a new mock test for multiple selected categories"""
    categories = Category.objects.filter(id__in=category_ids, is_active=True)
    
    if not categories.exists():
        messages.error(request, "No valid categories selected.")
        return redirect('mock_test_categories')
    
    # Get questions from all selected categories and their subcategories
    all_category_ids = []
    category_names = []
    
    for category in categories:
        category_names.append(category.name)
        all_category_ids.append(category.id)
        # Add subcategories
        for subcat in category.get_all_descendants():
            all_category_ids.append(subcat.id)
    
    # Remove duplicates
    all_category_ids = list(set(all_category_ids))
    
    # Get all questions for these categories
    questions = Question.objects.filter(categories__id__in=all_category_ids).distinct()
    
    # Check if we have enough questions
    if questions.count() < 1:
        messages.error(request, f"No questions found in selected categories: {', '.join(category_names)}")
        return redirect('mock_test_categories')
    
    # Select random questions (maximum 20, or all if less than 20)
    question_count = min(20, questions.count())
    selected_questions = list(questions)
    random.shuffle(selected_questions)
    selected_questions = selected_questions[:question_count]
    
    # Create a new mock exam (use first category as primary)
    mock_exam = MockExam.objects.create(
        user=request.user,
        category=categories.first(),
        total_questions=question_count
    )
    
    # Add questions to the exam
    for i, question in enumerate(selected_questions):
        MockExamQuestion.objects.create(
            exam=mock_exam,
            question=question,
            order=i + 1
        )
    
    messages.success(request, f"Mock test started with {question_count} questions from {len(categories)} categories: {', '.join(category_names)}")
    
    # Redirect to the first question
    return redirect('take_mock_test', exam_id=mock_exam.id, question_number=1)

@login_required
@login_required
def get_subcategories_ajax(request):
    """AJAX endpoint to get subcategories based on parent category"""
    try:
        parent_id = request.GET.get('parent_id')
        
        if parent_id:
            try:
                parent_id = int(parent_id)
                subcategories = Category.objects.filter(
                    parent_id=parent_id, 
                    is_active=True
                ).annotate(
                    questions_count=Count('questions', distinct=True)
                )
            except ValueError:
                return JsonResponse({'error': 'Invalid parent_id'}, status=400)
        else:
            # Get root categories (no parent)
            subcategories = Category.objects.filter(
                parent__isnull=True, 
                is_active=True
            ).annotate(
                questions_count=Count('questions', distinct=True)
            )
        
        # Format for JSON response
        data = []
        for category in subcategories:
            # Count questions in this category and all its subcategories
            try:
                subcategory_ids = [cat.id for cat in category.get_all_descendants()]
                subcategory_ids.append(category.id)
                
                total_questions = Question.objects.filter(
                    categories__id__in=subcategory_ids
                ).distinct().count()
                
                data.append({
                    'id': category.id,
                    'name': category.name,
                    'questions_count': total_questions,
                    'has_questions': total_questions > 0,
                    'has_children': category.children.exists()
                })
            except Exception as e:
                print(f"Error processing category {category.id}: {e}")
                continue
        
        return JsonResponse({'subcategories': data})
    
    except Exception as e:
        print(f"Error in get_subcategories_ajax: {e}")
        return JsonResponse({'error': str(e)}, status=500)
