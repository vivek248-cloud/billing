

from django.db.models import Sum
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from .models import Project, Expense,Payment,DailyExpense,CustomProject
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.templatetags.static import static
from django.utils import timezone
from calendar import monthrange
from itertools import zip_longest
from .forms import ExpenseForm,ExpenseForm2

from .decorators import session_login_required
from .decorators import session_login_required

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import re
from django.contrib import messages

# home
def home(request):
    return render(request, 'projects/index.html')

# def admin_login(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         # Validate password format
#         if not re.match(r'^[a-zA-Z0-9]+$', password):
#             messages.error(request, 'Password must be alphanumeric.')
#             return redirect('admin_login')

#         # Authenticate admin
#         user = authenticate(request, username=username, password=password)
#         if user is not None and user.is_superuser:
#             login(request, user)
#             request.session['admin_logged_in'] = True
#             return redirect('billing')
#         else:
#             messages.error(request, 'Invalid superuser credentials.')

#     return render(request, 'projects/admin_login.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login

def admin_login(request):
    # If the user is already logged in, redirect to the dashboard
    if request.session.get('admin_logged_in'):
        return redirect('/dashboard/')  # Adjust this to your dashboard path

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:  # Ensure the user is admin
            login(request, user)
            request.session['admin_logged_in'] = True  # Set session variable to indicate admin is logged in
            return redirect('/billing/')  # Redirect to the billing page
        else:
            messages.error(request, 'Invalid credentials, please try again.')
            return redirect('/admin-login/')

    return render(request, 'projects/admin_login.html')  # Show login form


def client_login(request):
    error = ""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')  # This is client's phone

        try:
            project = Project.objects.get(client_name=username, phone=password)
            return render(request, 'projects/client_dashboard.html', {'project': project})
        except Project.DoesNotExist:
            error = "Invalid username or password."

    return render(request, 'projects/client_login.html', {'error': error})






def logout_view(request):
    request.session.flush()  # Clears all session data
    return redirect('home')




# @login_required(login_url='/login/')
# def project_billing(request):
#     projects = Project.objects.all()
#     # Calculate total expenses for each project
#     if request.session.get('admin_logged_in') or request.session.get('user_logged_in'):
#         return render(request, 'projects/billing.html', {'projects': projects})
#     return redirect('home')
    


from django.contrib.auth.decorators import login_required

@session_login_required
def project_billing(request):
    projects = Project.objects.all()
    return render(request, 'projects/billing.html', {'projects': projects})


# 1
def add_project(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        client_name = request.POST.get('client_name')
        phone = request.POST.get('phone')
        
        # Get budget and estimated cost from the form data
        budget = request.POST.get('budget', '0.00')  # Default to '0.00' if not provided
        estimated_cost = request.POST.get('estimated_cost', '0.00')  # Default to '0.00' if not provided

        # Ensure that budget and estimated cost are valid Decimals
        try:
            budget = Decimal(budget)
            estimated_cost = Decimal(estimated_cost)
        except ValueError:
            return render(request, 'projects/add_project.html', {'error': 'Invalid budget or estimated cost'})

        # Create the project
        try:
            Project.objects.create(
                name=name,
                client_name=client_name,
                budget=budget,
                estimated_cost=estimated_cost,
                phone=phone
            )
            return redirect('billing')
        except Exception as e:
            return render(request, 'projects/billing.html', {'error': f"Error creating project: {str(e)}"})

    return render(request, 'projects/billing.html')





def add_expense(request):
    if request.method == 'POST':
        project_id = request.POST.get('project')
        project = get_object_or_404(Project, id=project_id)
        
        form = ExpenseForm2(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.project = project
            expense.date = request.POST.get('date') or timezone.now().date()
            expense.amount = form.cleaned_data['amount']  # calculated in form
            expense.save()
    return redirect('billing')


def remove_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    expense.delete()
    return redirect('billing')

def remove_notes(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    expense.note = ""  # Clear the note instead of deleting the object
    expense.save()
    return redirect('billing') 


def invoice_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Fetch the expenses related to the project
    expenses = Expense.objects.filter(project=project)
    
    cumulative_paid = 0

    # Debugging: Print expenses to check the data
    print(expenses)  # Check if this prints the correct expenses data in the terminal

    # Calculate total expense
    total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Fetch payment details (assuming you have a model for payments)
    payment_rows = project.payments.all()  # Adjust this if the relation is different
    total_received = payment_rows.aggregate(Sum('amount'))['amount__sum'] or 0
    yet_to_receive = total_expense - total_received
    
    # Prepare context data
    context = {
        'project': project,
        'expenses': expenses,
        'total_expense': total_expense,
        'payment_rows': payment_rows,
        'total_received': total_received,
        'yet_to_receive': yet_to_receive
    }
    
    # Render the HTML template to a string
    template = get_template('projects/invoice.html')
    html = template.render(context)
    
    # Convert HTML to PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{project.id}.pdf"'
    
    # Use xhtml2pdf to generate the PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    # If error occurs, return an error message
    if pisa_status.err:
        return HttpResponse('We had some errors while generating the PDF.')
    
    return response



def download_invoice(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    logo_url = request.build_absolute_uri(static('images/logo.PNG'))

    # Expenses
    expense_rows = Expense.objects.filter(project=project)
    total_expense = Decimal(expense_rows.aggregate(Sum('amount'))['amount__sum'] or 0)

    # Payments and cumulative paid logic
    raw_payments = Payment.objects.filter(project=project).order_by('date')
    total_received = Decimal(raw_payments.aggregate(Sum('amount'))['amount__sum'] or 0)
    cumulative_paid = Decimal('0.00')
    cumulative_paid_before = Decimal('0.00')

    payment_rows = []
    for payment in raw_payments:
        payment_amount = Decimal(str(payment.amount))  # Convert float to Decimal safely
        cumulative_paid += payment_amount
        row = {
            'date': payment.date,
            'amount': payment_amount,
            'payment_mode': payment.payment_mode,
            'cumulative_paid_before': cumulative_paid_before,
            'remaining_after_payment': (Decimal(project.budget) + total_expense) - cumulative_paid
        }
        cumulative_paid_before = cumulative_paid
        
        payment_rows.append(row)

    yet_to_receive = (Decimal(project.budget) + total_expense) - cumulative_paid
    current_date = datetime.now().strftime('%Y-%m-%d')

    context = {
        'project': project,
        'expenses': expense_rows,
        'payment_rows': payment_rows,
        'total_expense': total_expense,
        'total_received': total_received,
        'yet_to_receive': yet_to_receive,
        'date': current_date,
        'logo_url': logo_url,
    }

    template = get_template('projects/invoice.html')
    html_content = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{project.name}.pdf"'

    pisa_status = pisa.CreatePDF(html_content, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    return response




def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    projects = Project.objects.all()  # Fetch all projects for the dropdown
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_mode')
        project_id = request.POST.get('project')  # Optionally handle project change
        
        if amount and payment_method:
            payment.amount = amount
            payment.payment_method = payment_method
            if project_id:  # Optionally update the project if the dropdown is used
                payment.project = Project.objects.get(id=project_id)
            payment.save()
            return redirect('billing')  # Or your main billing view name
    
    return render(request, 'projects/edit_payment.html', {
        'payment': payment,
        'projects': projects,
    })

# delete_payment

def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    project_id = payment.project.id  # to redirect back if needed
    if request.method == 'POST':
        payment.delete()
        return redirect('billing')  # your billing page name
    return redirect('billing')  # fallback

# add_payment


def add_payment(request):
    if request.method == 'POST':
        project_id = request.POST.get('project')
        amount = request.POST.get('amount')
        payment_mode = request.POST.get('payment_mode')

        if project_id and amount and payment_mode:
            project = get_object_or_404(Project, id=project_id)
            Payment.objects.create(
                project=project,
                amount=amount,
                payment_mode=payment_mode,
                date=timezone.now().date()
            )
    return redirect('billing')





def remove_daily_expense(request, expense_id):
    expense = get_object_or_404(DailyExpense, id=expense_id)
    expense.delete()
    return redirect('daily_expense')








from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime
from .models import Project, Expense,DailyExpense
from .forms import ExpenseForm, DailyExpenseForm # Make sure you have this form


from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime
from .models import Project, Expense, DailyExpense
from .forms import ExpenseForm, DailyExpenseForm



def daily_report(request):
    start_month = request.GET.get('start_month')
    end_month = request.GET.get('end_month')
    year = request.GET.get('year')
    edit_id = request.GET.get('edit')

    start_month = int(start_month) if start_month and start_month != 'None' else None
    end_month = int(end_month) if end_month and end_month != 'None' else None
    year = int(year) if year and year != 'None' else None

    filter_kwargs = {}
    if year:
        filter_kwargs['date__year'] = year
    if start_month and end_month:
        filter_kwargs['date__month__gte'] = start_month
        filter_kwargs['date__month__lte'] = end_month
    elif start_month:
        filter_kwargs['date__month'] = start_month
    elif end_month:
        filter_kwargs['date__month'] = end_month

    if request.method == 'POST':
        if 'update_expense_id' in request.POST:
            expense = get_object_or_404(DailyExpense, id=request.POST['update_expense_id'])
            form = DailyExpenseForm(request.POST, instance=expense)
            if form.is_valid():
                form.save()
                return redirect(request.get_full_path())
        elif 'delete_expense_id' in request.POST:
            expense = get_object_or_404(DailyExpense, id=request.POST['delete_expense_id'])
            expense.delete()
            return redirect(request.get_full_path())
        elif 'add_expense' in request.POST:
            form = DailyExpenseForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect(request.get_full_path())

    projects_data = []
    total_expenses_all_projects = Decimal('0.00')

    for project in Project.objects.all():
        total_budget = project.budget or Decimal('0.00')

        daily_expenses = DailyExpense.objects.filter(project=project, **filter_kwargs).order_by('date')

        running_total = Decimal('0.00')
        all_entries = []

        for dex in daily_expenses:
            running_total += dex.amount
            balance = running_total

            all_entries.append({
                'expense': dex,
                'form': None,
                'running_total': running_total,
                'description': dex.description,
                'spend': dex.amount,
                'date': dex.date,
                'balance': balance,
                'source': 'DailyExpense'
            })

        total_spent = sum([entry['spend'] for entry in all_entries])
        total_expenses_all_projects += total_spent

        projects_data.append({
            'project': project,
            'daily_expenses': all_entries,
            'total_expenses_project': total_budget,
            'total_spent': total_spent
        })

    context = {
        'projects_data': projects_data,
        'selected_start_month': start_month,
        'selected_end_month': end_month,
        'selected_year': year,
        'months': [f"{i:02d}" for i in range(1, 13)],
        'years': [str(y) for y in range(datetime.now().year - 2, datetime.now().year + 2)],
        'total_expenses_all_projects': total_expenses_all_projects,
        'projects': Project.objects.all(),
    }

    return render(request, 'projects/daily.html', context)


# 2








# def add_custom_project(request):
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         client_name = request.POST.get('client_name')
#         budget = request.POST.get('budget')

#         # Safely convert budget to Decimal if provided
#         try:
#             budget = Decimal(budget) if budget else Decimal('0.00')
#         except:
#             budget = Decimal('0.00')  # fallback in case of error

#         project = Project.objects.create(name=name, budget=budget, client_name=client_name)
#         return redirect('daily_expense')  # or wherever you want

#     return render(request, 'projects/add_project.html')




def update_project_status(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Project.STATUS_CHOICES):
            project.status = status
            project.save()
            messages.success(request, "Project status updated successfully!")
            return redirect('billing')

    return render(request, 'projects/update_status.html', {'project': project})

def client_dashboard(request, phone):
    # Get all projects associated with this phone number
    project = Project.objects.filter(phone=phone)
    client_name = project.first().client_name if project.exists() else "Unknown Client"
    expense_rows = Expense.objects.filter(project=project)
    context = {
        'project': project,
        'phone': phone,
        'client_name': client_name,
        'expenses': expense_rows,
    }
    return render(request, 'projects/client_dashboard.html', context)


# Custom error handlers


def custom_404(request, exception):
    return render(request, 'projects/404.html', status=404)

def custom_500(request):
    return render(request, 'projects/500.html', status=500)