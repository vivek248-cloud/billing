from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django import template
from django.urls import reverse
from cloudinary.models import CloudinaryField

register = template.Library()
from decimal import Decimal

class CustomProject(models.Model):
    name = models.CharField(max_length=200)
    client_name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


# user



class Project(models.Model):
    STATUS_CHOICES = [
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('On Hold', 'On Hold'),
    ]
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, unique=True)
    client_name = models.CharField(max_length=200)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid_in_project = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Not Started')  # ✅ new

    def __str__(self):
        return self.name

    @property
    def total_expenses(self):
        return self.expenses_set.aggregate(total=models.Sum('amount'))['total'] or 0
    
    @property
    def remaining(self):
        budget = Decimal(str(self.budget))
        total_expenses = self.expenses_set.aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0.00')
        total_received = self.payments.aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0.00')

        total_expenses = Decimal(str(total_expenses))
        total_received = Decimal(str(total_received))

        budget += total_expenses  # Add expenses if intended

        return budget - total_received

    def update_estimated_cost(self):
        total_expenses = self.expenses_set.aggregate(models.Sum('amount'))['amount__sum'] or 0
        self.estimated_cost = round(total_expenses, 2)
        self.save()


class Expense(models.Model):
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    project = models.ForeignKey(Project, related_name='expenses_set', on_delete=models.CASCADE)
    area = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Changed to area for clarity
    unit = models.CharField(max_length=50, default='sq ft',null=True)  # Default unit for area
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    note = models.TextField(blank=True, null=True)  # Optional field for additional notes
    date = models.DateField(_("Date"), auto_now=False, auto_now_add=False, null=True, blank=True)

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.project.update_estimated_cost()

    def delete(self, *args, **kwargs):
        project = self.project
        super().delete(*args, **kwargs)
        project.update_estimated_cost()


class Payment(models.Model):
    project = models.ForeignKey(Project, related_name='payments', on_delete=models.CASCADE)
    date = models.DateField(_("Date"), auto_now=False, auto_now_add=False)
    amount = models.FloatField()
    payment_mode = models.CharField(
        max_length=50,
        choices=[
            ('cash', 'Cash'),
            ('cheque', 'Cheque'),
            ('online', 'Online')
        ]
    )

    def __str__(self):
        return f"{self.project.name} - {self.date} - {self.amount}"

   

    @property
    def total_payment(self):
        return sum(Decimal(p.amount) for p in self.project.payments.all())

    @property
    def total_expense(self):
        return sum(Decimal(e.amount) for e in self.project.expenses_set.all())

    @property
    def remaining_after_payment(self):
        budget = Decimal(self.project.budget or 0)
        total_expense = self.total_expense
        total_paid = self.total_payment
        return (budget + total_expense) - total_paid

    def get_absolute_url(self):
        return reverse('payment_invoice', args=[str(self.id)])




class DailyExpense(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    category = models.CharField(max_length=100)  # e.g. Food, Transport, Medical
    description = models.TextField(blank=True)
    remark = models.TextField(blank=True, null=True)  # Optional field for additional notes
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(_("Date"), auto_now=False, auto_now_add=False, null=True, blank=True)

    def __str__(self):
        return f"{self.category} - ₹{self.amount} ({self.project.client_name})"



class SiteImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='site_images')
    image = CloudinaryField('image', folder='billing-site-img')
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.project.client_name}"
