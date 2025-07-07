from django.contrib import admin
from .models import Category, Question, Choice, QuestionTestResult

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['get_indented_name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'parent']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['parent__name', 'name']
    
    def get_indented_name(self, obj):
        """Display category name with indentation based on level"""
        indent = "—" * obj.get_level() * 2
        return f"{indent} {obj.name}"
    get_indented_name.short_description = 'Category Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'parent', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    max_num = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'question_type', 'get_categories', 'created_at']
    list_filter = ['question_type', 'categories']
    search_fields = ['question_text']
    filter_horizontal = ['categories']
    inlines = [ChoiceInline]
    
    def question_text_short(self, obj):
        return obj.question_text[:100] + "..." if len(obj.question_text) > 100 else obj.question_text
    question_text_short.short_description = 'Question Text'
    
    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])
    get_categories.short_description = 'Categories'

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['question', 'option_label', 'choice_text', 'is_correct']
    list_filter = ['is_correct', 'option_label']
    search_fields = ['choice_text', 'question__question_text']

@admin.register(QuestionTestResult)
class QuestionTestResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_short', 'is_correct', 'test_date']
    list_filter = ['is_correct', 'test_date', 'user']
    search_fields = ['user__username', 'question__question_text']
    readonly_fields = ['test_date']
    
    def question_short(self, obj):
        return f"Q{obj.question.id}: {obj.question.question_text[:50]}..."
    question_short.short_description = 'Question'
