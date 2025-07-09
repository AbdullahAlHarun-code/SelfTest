from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name
    
    def get_full_path(self):
        """Returns the full hierarchical path of the category"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return " -> ".join(path)
    
    def get_level(self):
        """Returns the level/depth of the category (0 for root categories)"""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level
    
    def get_children(self):
        """Returns direct child categories"""
        return self.subcategories.filter(is_active=True)
    
    def get_all_descendants(self):
        """Returns all descendant categories (children, grandchildren, etc.)"""
        descendants = []
        for child in self.get_children():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def is_root(self):
        """Returns True if this is a root category (no parent)"""
        return self.parent is None
    
    def is_leaf(self):
        """Returns True if this is a leaf category (no children)"""
        return not self.subcategories.exists()

class Question(models.Model):
    SINGLE = 'single'
    MULTIPLE = 'multiple'
    QUESTION_TYPES = [
        (SINGLE, 'Single Correct Answer'),
        (MULTIPLE, 'Multiple Correct Answers'),
    ]

    question_text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default=SINGLE)
    categories = models.ManyToManyField(Category, related_name='questions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.question_text[:100] + "..." if len(self.question_text) > 100 else self.question_text
    
    def get_test_stats(self, user=None):
        """Get test statistics for this question"""
        stats = {'total_tests': 0, 'correct_tests': 0, 'incorrect_tests': 0, 'success_rate': 0}
        
        test_results = self.test_results.all()
        if user:
            test_results = test_results.filter(user=user)
        
        stats['total_tests'] = test_results.count()
        stats['correct_tests'] = test_results.filter(is_correct=True).count()
        stats['incorrect_tests'] = stats['total_tests'] - stats['correct_tests']
        
        if stats['total_tests'] > 0:
            stats['success_rate'] = round((stats['correct_tests'] / stats['total_tests']) * 100, 1)
        
        return stats

    def update_mark_category(self, user):
        """Update the mark category based on user's success rate for this question"""
        try:
            # Get user's test statistics for this question
            stats = self.get_test_stats(user)
            success_rate = stats['success_rate']
            
            print(f"DEBUG: Question {self.id} - User {user.username} - Success rate: {success_rate}%")
            print(f"DEBUG: Stats: {stats}")
            
            # Only update if there are test results
            if stats['total_tests'] == 0:
                print(f"DEBUG: No test results for question {self.id}")
                return None
            
            # Get the main mark category
            mark_category = Category.objects.filter(name='mark', parent__isnull=True).first()
            if not mark_category:
                print(f"DEBUG: Mark category not found!")
                return None
            
            print(f"DEBUG: Found mark category: {mark_category.name}")
            
            # Determine which subcategory based on success rate
            if success_rate < 70:
                target_subcategory_name = 'Below 70%'
            elif success_rate < 80:
                target_subcategory_name = '70% but below 80%'
            elif success_rate < 90:
                target_subcategory_name = '80% but below 90%'
            else:
                target_subcategory_name = '90% and over'
            
            print(f"DEBUG: Target subcategory: {target_subcategory_name}")
            
            # Get the target subcategory
            target_subcategory = Category.objects.filter(
                name=target_subcategory_name,
                parent=mark_category
            ).first()
            
            if not target_subcategory:
                print(f"DEBUG: Target subcategory '{target_subcategory_name}' not found!")
                return None
            
            print(f"DEBUG: Found target subcategory: {target_subcategory.name}")
            
            # Remove any existing mark subcategories from this question
            existing_mark_subcategories = self.categories.filter(parent=mark_category)
            if existing_mark_subcategories.exists():
                print(f"DEBUG: Removing existing mark subcategories: {[cat.name for cat in existing_mark_subcategories]}")
                self.categories.remove(*existing_mark_subcategories)
            
            # Add the new mark subcategory
            print(f"DEBUG: Adding new mark subcategory: {target_subcategory.name}")
            self.categories.add(target_subcategory)
            
            print(f"DEBUG: Successfully updated mark category for question {self.id}")
            return target_subcategory
            
        except Exception as e:
            print(f"Error updating mark category: {e}")
            return None


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    option_label = models.CharField(max_length=1)  # A, B, C, D
    choice_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('question', 'option_label')  # A, B, C, D unique per question

    def __str__(self):
        return f"{self.option_label}. {self.choice_text}"


class QuestionTestResult(models.Model):
    """Track individual question test results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='test_results')
    selected_choices = models.ManyToManyField(Choice, related_name='selected_in_tests')
    is_correct = models.BooleanField()
    test_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-test_date']
    
    def __str__(self):
        return f"{self.user.username} - Question {self.question.id} - {'Correct' if self.is_correct else 'Incorrect'}"


class MockExam(models.Model):
    """Represents a mock exam session"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mock_exams')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='mock_exams')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-start_time']
        
    def __str__(self):
        status = "Completed" if self.completed else "In Progress"
        return f"{self.user.username} - {self.category.name} - {status}"
    
    @property
    def score_percentage(self):
        """Calculate the percentage score for this mock exam"""
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 1)
    
    @property
    def duration(self):
        """Calculate the duration of the mock exam"""
        if not self.end_time:
            return None
        
        duration = self.end_time - self.start_time
        # Format as hours:minutes:seconds
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s"


class MockExamQuestion(models.Model):
    """Individual questions in a mock exam"""
    mock_exam = models.ForeignKey(MockExam, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.IntegerField()  # Position in the exam sequence
    selected_choices = models.ManyToManyField(Choice, blank=True, related_name='selected_in_mock_exams')
    is_correct = models.BooleanField(null=True, blank=True)  # Null if not answered yet
    
    class Meta:
        ordering = ['order']
        unique_together = ('mock_exam', 'order')  # Ensure questions have unique ordering
    
    def __str__(self):
        return f"Exam #{self.mock_exam.id} - Q{self.order}: {self.question.question_text[:50]}..."