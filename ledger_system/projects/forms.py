# your_app/forms.py
from django import forms
from .models import Expense, DailyExpense

class ExpenseForm2(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'area', 'rate', 'note', 'date', 'unit']  # note added here too if you want
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'area': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),  # optional if you want note in form
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        area = cleaned_data.get('area') or 0
        rate = cleaned_data.get('rate') or 0

        # Calculate amount and add it to cleaned_data
        cleaned_data['amount'] = area * rate
        return cleaned_data



class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [ 'description', 'area', 'unit', 'rate', 'amount', 'date']



class DailyExpenseForm(forms.ModelForm):
    class Meta:
        model = DailyExpense
        fields = ['project',  'category', 'description', 'remark', 'amount', 'date']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'remark': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'  # This is crucial!
            ),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only set initial date for non-bound forms (GET requests)
        if not self.is_bound and self.instance and self.instance.date:
            self.fields['date'].initial = self.instance.date.strftime('%Y-%m-%d')

