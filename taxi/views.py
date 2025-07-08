from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from .models import Category, Question, Choice, QuestionTestResult

def user_login(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')

def user_logout(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    """Dashboard view with statistics"""
    from django.db.models import Count
    
    total_categories = Category.objects.count()
    root_categories = Category.objects.filter(parent=None).count()
    sub_categories = Category.objects.exclude(parent=None).count()
    active_categories = Category.objects.filter(is_active=True).count()
    recent_categories = Category.objects.annotate(
        questions_count=Count('questions')
    ).order_by('-created_at')[:5]
    
    # Question statistics
    total_questions = Question.objects.count()
    single_questions = Question.objects.filter(question_type='single').count()
    multiple_questions = Question.objects.filter(question_type='multiple').count()
    recent_questions = Question.objects.order_by('-created_at')[:5]
    
    context = {
        'total_categories': total_categories,
        'root_categories': root_categories,
        'sub_categories': sub_categories,
        'active_categories': active_categories,
        'recent_categories': recent_categories,
        'total_questions': total_questions,
        'single_questions': single_questions,
        'multiple_questions': multiple_questions,
        'recent_questions': recent_questions,
        'all_categories': Category.objects.all().order_by('parent__name', 'name'),  # For modal
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
def category_list(request):
    """Category list view with search functionality"""
    from django.db.models import Count
    
    categories = Category.objects.select_related('parent').annotate(
        questions_count=Count('questions')
    ).order_by('parent__name', 'name')
    all_categories = Category.objects.all().order_by('parent__name', 'name')  # All categories for modal
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        categories = categories.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    # Status filter
    status = request.GET.get('status')
    if status == 'true':
        categories = categories.filter(is_active=True)
    elif status == 'false':
        categories = categories.filter(is_active=False)
    
    context = {
        'categories': categories,
        'all_categories': all_categories,
    }
    
    return render(request, 'admin/category_list.html', context)

@login_required
def category_create(request):
    """Create or update category"""
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        name = request.POST.get('name')
        parent_id = request.POST.get('parent')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        if not name:
            messages.error(request, 'Category name is required.')
            return redirect('category_list')
        
        # Check for duplicate names at the same level
        parent = None
        if parent_id:
            try:
                parent = Category.objects.get(id=parent_id)
            except Category.DoesNotExist:
                messages.error(request, 'Invalid parent category.')
                return redirect('category_list')
        
        # Check for existing name at same level
        existing = Category.objects.filter(name=name, parent=parent)
        if category_id:
            existing = existing.exclude(id=category_id)
        
        if existing.exists():
            messages.error(request, f'Category "{name}" already exists at this level.')
            return redirect('category_list')
        
        try:
            if category_id:
                # Update existing category
                category = get_object_or_404(Category, id=category_id)
                category.name = name
                category.parent = parent
                category.description = description
                category.is_active = is_active
                category.save()
                messages.success(request, f'Category "{name}" updated successfully.')
            else:
                # Create new category
                category = Category.objects.create(
                    name=name,
                    parent=parent,
                    description=description,
                    is_active=is_active
                )
                messages.success(request, f'Category "{name}" created successfully.')
        
        except Exception as e:
            messages.error(request, f'Error saving category: {str(e)}')
    
    return redirect('category_list')

@login_required
def category_delete(request, category_id):
    """Delete category"""
    if request.method == 'POST':
        try:
            category = get_object_or_404(Category, id=category_id)
            category_name = category.name
            category.delete()
            messages.success(request, f'Category "{category_name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting category: {str(e)}')
    
    return redirect('category_list')

@login_required
def question_list(request):
    """Question list view with search and filter functionality"""
    questions = Question.objects.prefetch_related('categories', 'choices').order_by('-created_at')
    all_categories = Category.objects.all().order_by('name')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        questions = questions.filter(question_text__icontains=search)
    
    # Type filter
    question_type = request.GET.get('type')
    if question_type:
        questions = questions.filter(question_type=question_type)
    
    # Category filter
    category = request.GET.get('category')
    if category:
        questions = questions.filter(categories__id=category)
    
    context = {
        'questions': questions,
        'all_categories': all_categories,
    }
    
    return render(request, 'admin/question_list.html', context)

@login_required
def question_create(request):
    """Create new question"""
    if request.method == 'POST':
        return save_question(request)
    
    context = {
        'all_categories': Category.objects.all().order_by('name'),
        'choices': [],
    }
    
    return render(request, 'admin/question_form.html', context)

@login_required
def question_edit(request, question_id):
    """Edit existing question"""
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        return save_question(request, question)
    
    # Get choices ordered by option_label
    choices = question.choices.order_by('option_label')
    
    # Get selected category IDs for easier template handling
    selected_category_ids = list(question.categories.values_list('id', flat=True))
    print(f"Selected category IDs: {selected_category_ids}")
    
    context = {
        'question': question,
        'choices': choices,
        'all_categories': Category.objects.all().order_by('name'),
        'selected_category_ids': selected_category_ids,
    }
    
    return render(request, 'admin/question_form.html', context)

@login_required
def question_detail(request, question_id):
    """Question detail view"""
    question = get_object_or_404(Question.objects.prefetch_related('categories', 'choices'), id=question_id)
    
    # Get related questions from same categories
    related_questions = Question.objects.filter(
        categories__in=question.categories.all()
    ).exclude(id=question.id).distinct()[:5]
    
    # Count correct answers
    correct_answers_count = question.choices.filter(is_correct=True).count()
    total_choices = question.choices.count()
    
    context = {
        'question': question,
        'related_questions': related_questions,
        'correct_answers_count': correct_answers_count,
        'total_choices': total_choices,
    }
    
    return render(request, 'admin/question_detail.html', context)

@login_required
def question_delete(request, question_id):
    """Delete question"""
    if request.method == 'POST':
        try:
            question = get_object_or_404(Question, id=question_id)
            question_text = question.question_text[:50]
            question.delete()
            messages.success(request, f'Question "{question_text}..." deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting question: {str(e)}')
    
    return redirect('question_list')

def save_question(request, question=None):
    """Save question with choices"""
    try:
        # Debug information about the request
        print(f"POST data received: {request.POST}")
        print(f"FILES data received: {request.FILES}")
        
        with transaction.atomic():
            # Get form data
            question_text = request.POST.get('question_text')
            question_type = request.POST.get('question_type')
            
            # Get categories from the standard multi-select
            categories = request.POST.getlist('categories')
            print(f"[DEBUG] Categories from request: {categories}")
            
            # Check backup categories if main selection is empty
            backup_categories = request.POST.get('backup_categories')
            if not categories and backup_categories:
                backup_categories = [cat_id for cat_id in backup_categories.split(',') if cat_id.strip()]
                print(f"[DEBUG] Using backup categories: {backup_categories}")
                categories = backup_categories
            
            # Validate required fields
            if not question_text:
                messages.error(request, 'Question text is required.')
                return redirect('question_create')
            
            # Create or update question
            if question is None:
                question = Question.objects.create(
                    question_text=question_text,
                    question_type=question_type
                )
                action = 'created'
            else:
                question.question_text = question_text
                question.question_type = question_type
                question.save()
                action = 'updated'
            
            # Set categories
            print(f"[DEBUG] Before clearing categories, question {question.id} had: {list(question.categories.values_list('id', 'name'))}")
            question.categories.clear()
            print(f"[DEBUG] After clearing categories: {list(question.categories.values_list('id', 'name'))}")
            
            print(f"[DEBUG] Has category_field marker: {'has_category_field' in request.POST}")
            print(f"[DEBUG] Raw categories from POST: {request.POST.getlist('categories')}")
            
            if categories:
                # Print for debugging
                print(f"[DEBUG] Categories selected: {categories}")
                for cat_id in categories:
                    try:
                        cat_id = int(cat_id)  # Ensure ID is an integer
                        category = Category.objects.get(id=cat_id)
                        question.categories.add(category)
                        print(f"[DEBUG] Added category: {category.name} (ID: {category.id})")
                    except Category.DoesNotExist:
                        print(f"[DEBUG] Category ID {cat_id} does not exist")
                    except ValueError as e:
                        print(f"[DEBUG] Invalid category ID: {cat_id}, error: {e}")
                    except Exception as e:
                        print(f"[DEBUG] Error adding category {cat_id}: {e}")
            
            # After all categories have been added, verify what's now in the database
            print(f"[DEBUG] Final categories for question {question.id}: {list(question.categories.values_list('id', 'name'))}")
            
            # Handle choices
            question.choices.all().delete()  # Remove existing choices
            
            choice_labels = ['A', 'B', 'C', 'D']
            correct_choices = []
            
            for label in choice_labels:
                choice_text = request.POST.get(f'choice_text_{label}')
                is_correct = request.POST.get(f'correct_{label}') == 'on'
                
                if choice_text and choice_text.strip():
                    Choice.objects.create(
                        question=question,
                        option_label=label,
                        choice_text=choice_text.strip(),
                        is_correct=is_correct
                    )
                    
                    if is_correct:
                        correct_choices.append(label)
            
            # Validate choices
            choice_count = question.choices.count()
            if choice_count < 2:
                raise ValueError(f'At least 2 choices are required. You provided {choice_count}. Make sure each choice has text entered.')
            
            if not correct_choices:
                raise ValueError('At least one correct answer must be selected.')
            
            if question_type == 'single' and len(correct_choices) > 1:
                raise ValueError('Single answer questions can only have one correct choice.')
            
            messages.success(request, f'Question {action} successfully.')
            return redirect('question_detail', question_id=question.id)
            
    except Exception as e:
        messages.error(request, f'Error saving question: {str(e)}')
        if question and question.id:
            return redirect('question_edit', question_id=question.id)
        else:
            return redirect('question_create')

def question_test(request, question_id):
    """Test a specific question"""
    try:
        # Basic validation - check if question exists
        question = get_object_or_404(Question, id=question_id)
        
        # Check if the question has any choices
        choice_count = question.choices.count()
        if choice_count == 0:
            return JsonResponse({
                'success': False,
                'error': f'This question has no choices. Please add choices before testing.'
            }, status=400)
        
        if request.method == 'POST':
            # Process test submission
            selected_choice_ids = request.POST.getlist('selected_choices')
            
            if not selected_choice_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'Please select at least one answer.'
                })
            
            # Get selected choices
            selected_choices = question.choices.filter(id__in=selected_choice_ids)
            correct_choices = question.choices.filter(is_correct=True)
            
            # Check if there are any correct choices defined
            if not correct_choices:
                return JsonResponse({
                    'success': False,
                    'error': 'This question has no correct answers defined.'
                }, status=400)
            
            # Determine if answer is correct
            if question.question_type == 'single':
                # For single answer questions, check if the selected choice is correct
                is_correct = (len(selected_choices) == 1 and 
                             selected_choices.first() in correct_choices)
            else:
                # For multiple answer questions, check if all correct choices are selected
                # and no incorrect choices are selected
                selected_choice_set = set(selected_choices)
                correct_choice_set = set(correct_choices)
                is_correct = selected_choice_set == correct_choice_set
            
            # Save test result only if user is authenticated
            stats = {'total_tests': 0, 'correct_tests': 0, 'incorrect_tests': 0, 'success_rate': 0}
            if request.user.is_authenticated:
                # Create the test result
                test_result = QuestionTestResult.objects.create(
                    user=request.user,
                    question=question,
                    is_correct=is_correct
                )
                test_result.selected_choices.set(selected_choices)
                
                # Try to get updated stats
                try:
                    stats = question.get_test_stats(request.user)
                    
                    # Update mark category based on success rate
                    updated_category = question.update_mark_category(request.user)
                    if updated_category:
                        print(f"Updated mark category for question {question.id} to: {updated_category.name}")
                    
                except Exception as stats_error:
                    print(f"Error getting stats or updating mark category: {stats_error}")
                    # Continue with default stats
            
            # Prepare response data with complete question information
            response_data = {
                'success': True,
                'is_correct': is_correct,
                'question': {
                    'id': question.id,
                    'text': question.question_text,
                    'type': question.question_type,
                },
                'all_choices': [{'id': c.id, 'label': c.option_label, 'text': c.choice_text, 'is_correct': c.is_correct}
                              for c in question.choices.all().order_by('option_label')],
                'correct_choices': [{'id': c.id, 'label': c.option_label, 'text': c.choice_text} 
                                   for c in correct_choices],
                'selected_choices': [{'id': c.id, 'label': c.option_label, 'text': c.choice_text} 
                                    for c in selected_choices],
                'explanation': 'Correct answer!' if is_correct else 'Incorrect answer.',
                'stats': stats
            }
            
            return JsonResponse(response_data)
        
        # GET request - return question data for the modal
        choices = list(question.choices.order_by('option_label'))
        
        # Default stats
        stats = {'total_tests': 0, 'correct_tests': 0, 'incorrect_tests': 0, 'success_rate': 0}
        
        # Try to get user stats if authenticated
        if request.user.is_authenticated:
            try:
                stats = question.get_test_stats(request.user)
            except Exception as stats_error:
                print(f"Error getting stats: {stats_error}")
                # Continue with default stats
        
        # Prepare the response with choices
        response_data = {
            'question': {
                'id': question.id,
                'text': question.question_text,
                'type': question.question_type,
                'choices': [{'id': c.id, 'label': c.option_label, 'text': c.choice_text} 
                           for c in choices]
            },
            'stats': stats
        }
        
        return JsonResponse(response_data)
        
    except Question.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': f'Question with ID {question_id} does not exist.'
        }, status=404)
        
    except Exception as e:
        import traceback
        error_msg = f"Error in question_test view: {str(e)}"
        print(error_msg)  # This will show in Django console
        traceback.print_exc()  # This will show full traceback in console
        
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=500)

def debug_questions(request):
    """Debug endpoint to check questions"""
    try:
        from django.http import HttpResponse
        
        questions = Question.objects.all()[:10]
        output = f"Total questions: {Question.objects.count()}\n\n"
        output += "First 10 questions:\n"
        
        for q in questions:
            output += f"ID: {q.id}, Text: {q.question_text[:50]}..., Type: {q.question_type}\n"
            output += f"  Choices: {q.choices.count()}\n"
            for choice in q.choices.all():
                output += f"    {choice.option_label}. {choice.choice_text} ({'✓' if choice.is_correct else '✗'})\n"
            output += "\n"
        
        return HttpResponse(output, content_type='text/plain')
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", content_type='text/plain')

def debug_question_test(request, question_id):
    """Debug endpoint to test a specific question and show any errors"""
    try:
        from django.http import HttpResponse
        import traceback
        
        question = Question.objects.prefetch_related('choices').get(id=question_id)
        
        # Basic info about the question
        output = f"Question {question_id} found:\n"
        output += f"Text: {question.question_text}\n"
        output += f"Type: {question.question_type}\n\n"
        
        # Choices
        output += f"Choices ({question.choices.count()}):\n"
        for choice in question.choices.all():
            output += f"  {choice.option_label}. {choice.choice_text} ({'Correct' if choice.is_correct else 'Incorrect'})\n"
        
        # Try getting stats
        output += "\nTrying to get stats:\n"
        try:
            stats = question.get_test_stats(request.user if request.user.is_authenticated else None)
            output += f"Stats: {stats}\n"
        except Exception as e:
            output += f"Error getting stats: {str(e)}\n"
            output += traceback.format_exc()
        
        return HttpResponse(output, content_type='text/plain')
    except Question.DoesNotExist:
        return HttpResponse(f"Question {question_id} does not exist", content_type='text/plain', status=404)
    except Exception as e:
        trace = traceback.format_exc()
        return HttpResponse(f"Error: {str(e)}\n\n{trace}", content_type='text/plain', status=500)

def simple_question_test(request, question_id):
    """Simplified test endpoint that only returns basic question data"""
    try:
        from django.http import JsonResponse
        
        question = Question.objects.prefetch_related('choices').get(id=question_id)
        
        # Basic question data
        response_data = {
            'question': {
                'id': question.id,
                'text': question.question_text,
                'type': question.question_type,
                'choices': []
            }
        }
        
        # Add choices
        for choice in question.choices.all():
            response_data['question']['choices'].append({
                'id': choice.id,
                'label': choice.option_label,
                'text': choice.choice_text
            })
            
        return JsonResponse(response_data)
    except Question.DoesNotExist:
        return JsonResponse({'error': f'Question {question_id} not found'}, status=404)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error in simple_question_test: {error_detail}")
        return JsonResponse({'error': str(e)}, status=500)
