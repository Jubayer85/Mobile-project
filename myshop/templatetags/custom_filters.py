from django import template

register = template.Library()

@register.filter
def divide(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def calculate_emi(price, months=12):
    """Calculate EMI amount"""
    try:
        return float(price) / float(months)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def calculate_discount(original, selling):
    """Calculate discount amount"""
    try:
        return float(original) - float(selling)
    except (ValueError, TypeError):
        return 0

@register.filter
def calculate_discount_percentage(original, selling):
    """Calculate discount percentage"""
    try:
        original_price = float(original)
        selling_price = float(selling)
        if original_price > 0:
            discount = ((original_price - selling_price) / original_price) * 100
            return round(discount)
        return 0
    except (ValueError, TypeError):
        return 0

@register.filter
def get_emi_amount(price, months=12):
    """Get EMI amount (alias for calculate_emi)"""
    try:
        return float(price) / float(months)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0