# projects/templatetags/extra_filters.py
from decimal import Decimal
from django import template
from django.db.models import Sum

register = template.Library()

@register.filter
def sub(value, arg):
    """Custom filter to subtract arg from value."""
    try:
        return value - arg
    except (TypeError, ValueError):
        return value  # return the original value in case of error


@register.filter
def total_payment(payments):
    return sum(payment.amount for payment in payments)





@register.filter
def total_budget_with_expense(project):
    total_expenses = project.expenses_set.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    return project.budget + total_expenses

@register.filter
def remaining_after_payment(project):
    total_expense = sum(Decimal(exp.amount) for exp in project.expenses_set.all())
    total_payment = sum(Decimal(pay.amount) for pay in project.payments.all())
    total_budget = Decimal(project.budget)

    balance = total_budget + total_expense - total_payment

    return balance

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def dict_get(dict_obj, key):
    return dict_obj.get(key)
