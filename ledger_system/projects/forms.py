# your_app/forms.py
from django import forms
from .models import Expense, DailyExpense

class ExpenseForm2(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'area', 'rate', 'note']  # exclude 'amount' from input

    def clean(self):
        cleaned_data = super().clean()
        area = cleaned_data.get('area') or 0
        rate = cleaned_data.get('rate') or 0

        # Calculate amount as area * rate
        cleaned_data['amount'] = area * rate
        return cleaned_data

    



class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['project', 'description', 'amount', 'date']



class DailyExpenseForm(forms.ModelForm):
    class Meta:
        model = DailyExpense
        fields = ['project', 'category', 'description', 'amount', 'date']