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