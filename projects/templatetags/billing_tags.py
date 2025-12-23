from django import template
from decimal import Decimal
from django.db.models import Sum

register = template.Library()


@register.simple_tag
def billing_summary(projects, status):
    """
    status values expected (must match Project.STATUS_CHOICES):
    'Not Started', 'In Progress', 'Completed', 'On Hold'
    """

    total_budget = Decimal('0.00')
    total_paid = Decimal('0.00')
    project_count = 0

    for project in projects:
        if project.status != status:
            continue

        project_count += 1

        # 🔹 Expenses
        expenses = project.expenses_set.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        expenses = Decimal(str(expenses))

        # 🔹 Payments
        payments = project.payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        payments = Decimal(str(payments))

        # 🔹 Budget
        budget = Decimal(str(project.budget or 0))

        total_budget += budget + expenses
        total_paid += payments

    return {
        'count': project_count,
        'budget': total_budget,
        'paid': total_paid,
        'remaining': total_budget - total_paid
    }





# # projects/templatetags/billing_tags.py
# from django import template
# from decimal import Decimal
# from django.db.models import Sum

# register = template.Library()


# @register.simple_tag
# def billing_summary(projects, status=None):
#     total_budget = Decimal('0.00')
#     total_paid = Decimal('0.00')
#     project_count = 0

#     for project in projects:
#         # Filter by status
#         if status == 'Completed' and project.status != 'Completed':
#             continue
#         if status is None and project.status == 'Completed':
#             continue

#         project_count += 1

#         # 🔹 Expenses
#         expenses = project.expenses_set.aggregate(
#             total=Sum('amount')
#         )['total']
#         expenses = Decimal(expenses) if expenses is not None else Decimal('0.00')

#         # 🔹 Payments
#         payments = project.payments.aggregate(
#             total=Sum('amount')
#         )['total']
#         payments = Decimal(payments) if payments is not None else Decimal('0.00')

#         # 🔹 Budget
#         budget = Decimal(project.budget)

#         total_budget += budget + expenses
#         total_paid += payments

#     return {
#         'count': project_count,
#         'budget': total_budget,
#         'paid': total_paid,
#         'remaining': total_budget - total_paid
#     }
