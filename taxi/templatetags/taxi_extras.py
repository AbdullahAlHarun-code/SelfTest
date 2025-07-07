from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def repeat_string(string, times):
    """Repeat a string a given number of times"""
    try:
        return str(string) * int(times)
    except (ValueError, TypeError):
        return ''

@register.filter
def category_indent(level):
    """Generate indentation for category levels"""
    try:
        return "—" * int(level) * 2
    except (ValueError, TypeError):
        return ''

@register.filter
def in_categories(category_id, categories):
    """Check if a category ID is in a list of categories"""
    try:
        return int(category_id) in [int(cat.id) for cat in categories]
    except (ValueError, AttributeError, TypeError):
        return False
