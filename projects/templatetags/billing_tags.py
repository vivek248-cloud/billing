# projects/templatetags/billing_tags.py
from django import template
from decimal import Decimal
from django.db.models import Sum

register = template.Library()


@register.simple_tag
def billing_summary(projects, status=None):
    total_budget = Decimal('0.00')
    total_paid = Decimal('0.00')
    project_count = 0

    for project in projects:
        # Filter by status
        if status == 'Completed' and project.status != 'Completed':
            continue
        if status is None and project.status == 'Completed':
            continue

        project_count += 1

        # 🔹 Expenses
        expenses = project.expenses_set.aggregate(
            total=Sum('amount')
        )['total']
        expenses = Decimal(expenses) if expenses is not None else Decimal('0.00')

        # 🔹 Payments
        payments = project.payments.aggregate(
            total=Sum('amount')
        )['total']
        payments = Decimal(payments) if payments is not None else Decimal('0.00')

        # 🔹 Budget
        budget = Decimal(project.budget)

        total_budget += budget + expenses
        total_paid += payments

    return {
        'count': project_count,
        'budget': total_budget,
        'paid': total_paid,
        'remaining': total_budget - total_paid
    }
