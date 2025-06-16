from urllib.parse import urlencode

from django.db.models import Sum
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from .models import*
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
from django.http import HttpResponseForbidden, FileResponse
import re
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login


from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime
from .models import Project, Expense,DailyExpense
from .forms import ExpenseForm, DailyExpenseForm # Make sure you have this form


from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime
from .models import Project, Expense, DailyExpense
from .forms import ExpenseForm, DailyExpenseForm

# home
def home(request):
    return render(request, 'projects/index.html')




# admin_login
def admin_login(request):
    if request.session.get('admin_logged_in'):
        return redirect('/dashboard/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            request.session['admin_logged_in'] = True

            response = redirect('/billing/')

            # Fix: Use consistent keys and save cookies only if "remember_me" checked
            if 'remember_me' in request.POST:
                response.set_cookie('admin_username', username, max_age=604800) # 7 days
                response.set_cookie('admin_password', password, max_age=604800) # 7 days
            else:
                response.delete_cookie('admin_username')
                response.delete_cookie('admin_password')

            return response
        else:
            messages.error(request, 'Invalid credentials, please try again.')
            return redirect('/admin-login/')

    return render(request, 'projects/admin_login.html')



# client_login
from django.shortcuts import redirect

def client_login(request):
    error = ""
    if request.method == 'POST':
        uname = request.POST['username']
        pwd = request.POST['password']

        try:
            # Use __iexact for case-insensitive username matching
            project = Project.objects.get(client_name__iexact=uname, phone=pwd)
            request.session['client_project_id'] = project.id

            response = redirect('client_dashboard', phone=project.phone)

            # ✅ Remember Me logic
            if 'remember_me' in request.POST:
                response.set_cookie('saved_username', uname, max_age=2592000)  # 30 days
                response.set_cookie('saved_password', pwd, max_age=2592000)
            else:
                response.delete_cookie('saved_username')
                response.delete_cookie('saved_password')

            return response

        except Project.DoesNotExist:
            error = "Invalid username or password."

    return render(request, 'projects/client_login.html', {'error': error})



# client_dashboard

def client_dashboard(request, phone):
    project = Project.objects.filter(phone=phone).first()

    if not project:
        return HttpResponseForbidden("Project not found.")
    
    if request.session.get('client_project_id') != project.id:
        return HttpResponseForbidden("Access denied.")

    expenses = Expense.objects.filter(project=project)
    payments = Payment.objects.filter(project=project).order_by('date')
    site_images = SiteImage.objects.filter(project=project).order_by('-uploaded_at')  # ✅

    total_expense = sum(exp.amount for exp in expenses)
    budget = project.budget or Decimal('0')

    cumulative_paid = Decimal('0.00')
    cumulative_paid_before = Decimal('0.00')
    payment_rows = []

    for payment in payments:
        amount = Decimal(str(payment.amount))
        cumulative_paid += amount
        payment_rows.append({
            'payment_obj': payment,
            'id': payment.id,
            'date': payment.date,
            'amount': amount,
            'payment_mode': payment.payment_mode,
            'cumulative_paid_before': cumulative_paid_before,
            'remaining_after_payment': (budget + total_expense) - cumulative_paid
        })
        cumulative_paid_before = cumulative_paid

    remaining = budget - total_expense
    remaining_after_payment = remaining - cumulative_paid

    context = {
        'project': project,
        'phone': phone,
        'client_name': project.client_name,
        'expenses': expenses,
        'payment_rows': payment_rows,
        'total_paid': cumulative_paid,
        'remaining': remaining,
        'remaining_after_payment': remaining_after_payment,
        'site_images': site_images  # ✅ pass to template
    }

    return render(request, 'projects/client_dashboard.html', context)




# logout_view
def logout_view(request):
    request.session.flush()  # Clears all session data
    return redirect('home')



from django.contrib.auth.decorators import login_required

# billing
@session_login_required
def project_billing(request):
    projects = Project.objects.all()
    if not request.session.get('admin_logged_in'):
        return redirect('/admin_login/')
    return render(request, 'projects/billing.html', {'projects': projects})

from django.shortcuts import get_object_or_404

from decimal import Decimal
from django.db.models import Sum
from django.core import signing
from django.urls import reverse

# views.py
from django.core import signing
from django.http import Http404, HttpResponseRedirect
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

def open_signed_invoice(request):
    token = request.GET.get("token")
    signer = TimestampSigner()
    try:
        # No expiry time, valid indefinitely
        real_url = signer.unsign(token)  # No max_age
        return HttpResponseRedirect(real_url)
    except (SignatureExpired, BadSignature):
        raise Http404("Invalid or tampered link.")

    

# def client_details(request, project_id):
#     project = get_object_or_404(Project, id=project_id)
#     expenses = Expense.objects.filter(project=project)
#     payments = Payment.objects.filter(project=project).order_by('date')
#     site_images = SiteImage.objects.filter(project=project)

#     total_expense = sum(exp.amount for exp in expenses)
#     budget = project.budget or Decimal('0')
#     remaining = budget - total_expense

#     cumulative_paid = Decimal('0.00')
#     cumulative_paid_before = Decimal('0.00')
#     payment_rows = []
#     signer = TimestampSigner()
#     for payment in payments:
#         amount = Decimal(str(payment.amount))
#         cumulative_paid += amount

#         # ✅ Generate the signed token
#         invoice_url = request.build_absolute_uri(payment.get_absolute_url())
#         signed_token = signer.sign(invoice_url)

#         # ✅ Create a full redirect URL
#         redirect_url = request.build_absolute_uri(reverse('open_signed_invoice')) + f"?token={signed_token}"
#         whatsapp_text = f"Here is your invoice: {redirect_url}"

#         payment_rows.append({
#             'payment_obj': payment,
#             'date': payment.date,
#             'amount': amount,
#             'whatsapp_text': whatsapp_text,
#             'payment_mode': payment.payment_mode,
#             'cumulative_paid_before': cumulative_paid_before,
#             'remaining_after_payment': (budget + total_expense) - cumulative_paid
#         })
#         cumulative_paid_before = cumulative_paid

#     context = {
#         'project': project,
#         'expenses': expenses,
#         'total_expense': total_expense,
#         'remaining': remaining,
#         'payment_rows': payment_rows,
#         'total_paid': cumulative_paid,
#         'site_images': site_images,
#     }

#     return render(request, 'projects/client_details.html', context)

from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.core.signing import TimestampSigner
from django.utils.dateparse import parse_date

from .models import Project, Expense, Payment, SiteImage

def client_details(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # ------- EXPENSE FILTERS -------
    expenses = Expense.objects.filter(project=project)
    desc = request.GET.get('desc')
    from_date = parse_date(request.GET.get('from_date') or '')
    to_date = parse_date(request.GET.get('to_date') or '')

    if desc:
        expenses = expenses.filter(description__icontains=desc)
    if from_date:
        expenses = expenses.filter(date__gte=from_date)
    if to_date:
        expenses = expenses.filter(date__lte=to_date)

    total_expense = sum(exp.amount for exp in expenses)
    budget = project.budget or Decimal('0')
    remaining = budget - total_expense

    # ------- PAYMENT FILTERS -------
    payments = Payment.objects.filter(project=project).order_by('date')
    payment_mode = request.GET.get('payment_mode')
    pay_from = parse_date(request.GET.get('pay_from') or '')
    pay_to = parse_date(request.GET.get('pay_to') or '')

    if payment_mode:
        payments = payments.filter(payment_mode=payment_mode)
    if pay_from:
        payments = payments.filter(date__gte=pay_from)
    if pay_to:
        payments = payments.filter(date__lte=pay_to)

    # ------- PAYMENT ROWS -------
    cumulative_paid = Decimal('0.00')
    cumulative_paid_before = Decimal('0.00')
    payment_rows = []
    signer = TimestampSigner()

    for payment in payments:
        amount = Decimal(str(payment.amount))
        cumulative_paid += amount

        invoice_url = request.build_absolute_uri(payment.get_absolute_url())
        signed_token = signer.sign(invoice_url)
        redirect_url = request.build_absolute_uri(reverse('open_signed_invoice')) + f"?token={signed_token}"
        whatsapp_text = f"Here is your invoice: {redirect_url}"

        payment_rows.append({
            'payment_obj': payment,
            'date': payment.date,
            'amount': amount,
            'whatsapp_text': whatsapp_text,
            'payment_mode': payment.payment_mode,
            'cumulative_paid_before': cumulative_paid_before,
            'remaining_after_payment': (budget + total_expense) - cumulative_paid
        })
        cumulative_paid_before = cumulative_paid

    site_images = SiteImage.objects.filter(project=project)

    context = {
        'project': project,
        'expenses': expenses,
        'total_expense': total_expense,
        'remaining': remaining,
        'payment_rows': payment_rows,
        'total_paid': cumulative_paid,
        'site_images': site_images,
    }

    return render(request, 'projects/client_details.html', context)


from .forms import SiteImageForm

def upload_site_image(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = SiteImageForm(request.POST, request.FILES)
        if form.is_valid():
            site_image = form.save(commit=False)
            site_image.project = project
            site_image.save()
            return redirect('client_details', project_id=project.id)
    else:
        form = SiteImageForm()
    return render(request, 'projects/upload_image.html', {'form': form, 'project': project})


def payment_invoice(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    project = payment.project

    invoice_number = f"INV-{project.id}-{payment.id}-{payment.date.strftime('%Y%m%d')}"
    invoice_date = payment.date.strftime('%d-%m-%Y')
    payments = Payment.objects.filter(project=project).order_by('date')
    expenses = Expense.objects.filter(project=project)

    # Calculate cumulative payments and build payment_rows
    cumulative_paid = Decimal('0.00')
    payment_rows = []
    for pay in payments:
        amount = Decimal(str(pay.amount))
        if pay.id == payment.id:
            remaining_after = (project.budget + project.total_expenses) - (cumulative_paid + amount)
            payment_rows.append({
                'date': pay.date,
                'amount': amount,
                'cumulative_paid_before': cumulative_paid,
                'remaining_after_payment': remaining_after,
                'payment_mode': pay.payment_mode,
            })
            break
        payment_rows.append({
            'date': pay.date,
            'amount': amount,
            'cumulative_paid_before': cumulative_paid,
            'remaining_after_payment': (project.budget + project.total_expenses) - (cumulative_paid + amount),
            'payment_mode': pay.payment_mode,
        })
        cumulative_paid += amount

    # Compute total expenses
    total_expense = sum([expense.amount for expense in expenses])
    total_received = sum([p.amount for p in payments])
    yet_to_receive = (project.budget + total_expense) - Decimal(total_received)


    context = {
        'payment': payment,
        'project': project,
        'expenses': expenses,
        'total_expense': total_expense,
        'payment_rows': payment_rows,
        'total_received': total_received,
        'yet_to_receive': yet_to_receive,
        'logo_url': '/static/images/logo.png',  # Adjust if you have a dynamic logo path
        'invoice_number': invoice_number,
        'invoice_date': invoice_date,
    }

    return render(request, 'projects/payment_invoice.html', context)


# add_project
def add_project(request):
    projects = Project.objects.all().order_by('id')
    error = None

    if request.method == 'POST':
        name = request.POST.get('name').strip()
        client_name = request.POST.get('client_name')
        phone = request.POST.get('phone').strip()
        budget = request.POST.get('budget', '0.00')
        estimated_cost = request.POST.get('estimated_cost', '0.00')

        # Check for duplicate name
        if Project.objects.filter(name=name).exists():
            error = f"A project with name '{name}' already exists."
        # Check for duplicate phone
        elif Project.objects.filter(phone=phone).exists():
            error = f"A project with phone number '{phone}' already exists."
        else:
            # Validate budget and estimated cost
            try:
                budget = Decimal(budget)
                estimated_cost = Decimal(estimated_cost)
            except Exception:
                error = "Invalid budget or estimated cost."

            # Create project if no errors
            if not error:
                try:
                    Project.objects.create(
                        name=name,
                        client_name=client_name,
                        phone=phone,
                        budget=budget,
                        estimated_cost=estimated_cost
                    )
                    return redirect('billing')
                except Exception as e:
                    error = f"Error creating project: {str(e)}"

    return render(request, 'projects/add_project.html', {'error': error, 'projects': projects})




# add_expense
from .forms import ExpenseForm2  # Assuming you have this

from decimal import Decimal
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from .models import Project, Expense
from .forms import ExpenseForm2

def add_expense(request, project_id=None):
    success = False
    selected_project_id = None
    total_expense = Decimal('0.00')  # default

    if request.method == 'POST':
        project_id = request.POST.get('project')
        selected_project_id = project_id
        project = get_object_or_404(Project, id=project_id)

        form = ExpenseForm2(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.project = project
            expense.amount = form.cleaned_data['area'] * form.cleaned_data['rate']
            expense.save()
            success = True
            return redirect(f"{request.path}?success=1&project={selected_project_id}")
    else:
        form = ExpenseForm2()
        selected_project_id = request.GET.get('project')

    # Get expenses and total expense if a project is selected
    if selected_project_id:
        expenses = Expense.objects.filter(project_id=selected_project_id).order_by('-date')
        total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    else:
        expenses = Expense.objects.none()

    projects = Project.objects.all()

    if request.GET.get('success'):
        success = True

    return render(request, 'projects/add_expense.html', {
        'projects': projects,
        'form': form,
        'success': success,
        'expenses': expenses,
        'total_expense': total_expense,
        'selected_project_id': int(selected_project_id) if selected_project_id else None,
    })


# remove_expense
def remove_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    expense.delete()
    return redirect('billing')

# remove_notes
def remove_notes(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    expense.note = ""  # Clear the note instead of deleting the object
    expense.save()
    return redirect('billing') 

# invoice_view
def invoice_view(request, project_id):
    print(f"Download invoice called for project_id: {project_id}")

    project = get_object_or_404(Project, id=project_id)
    print(f"Project found: {project.name}")

    # Check permissions
    if request.user.is_authenticated and request.user.is_staff:
        allowed = True
        print(f"User {request.user.username} is staff, allowed to download.")
    else:
        # Check client session
        session_project_id = request.session.get('client_project_id')
        allowed = (session_project_id == project.id)
        print(f"Session project id: {session_project_id}, Allowed: {allowed}")

    if not allowed:
        print("Access denied.")
        return HttpResponse("Access Denied", status=403)

    logo_url = request.build_absolute_uri(static('images/logo.PNG'))

    # Query expenses
    expense_rows = Expense.objects.filter(project=project)
    total_expense = Decimal(expense_rows.aggregate(Sum('amount'))['amount__sum'] or 0)
    print(f"Total expense: {total_expense}")

    # Query payments
    raw_payments = Payment.objects.filter(project=project).order_by('date')
    total_received = Decimal(raw_payments.aggregate(Sum('amount'))['amount__sum'] or 0)

    cumulative_paid = Decimal('0.00')
    cumulative_paid_before = Decimal('0.00')
    payment_rows = []

    latest_payment = Payment.objects.filter(project=project).order_by('-date').first()

    if latest_payment:
        invoice_number = f"INV-{project.id}-{latest_payment.id}-{latest_payment.date.strftime('%Y%m%d')}"
        invoice_date = latest_payment.date.strftime('%d-%m-%Y')
    else:
        invoice_number = f"INV-{project.id}-0000"
        invoice_date = datetime.now().strftime('%d-%m-%Y')

    for payment in raw_payments:
        payment_amount = Decimal(str(payment.amount))
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
        'invoice_number': invoice_number,
        'invoice_date': invoice_date,
    }

    

    return render(request, 'projects/invoice.html', context)


# download_invoice
def download_invoice(request, project_id):
    print(f"Download invoice called for project_id: {project_id}")

    project = get_object_or_404(Project, id=project_id)
    print(f"Project found: {project.name}")

    latest_payment = Payment.objects.filter(project=project).order_by('-date').first()

    if latest_payment:
        invoice_number = f"INV-{project.id}-{latest_payment.id}-{latest_payment.date.strftime('%Y%m%d')}"
        invoice_date = latest_payment.date.strftime('%d-%m-%Y')
    else:
        invoice_number = f"INV-{project.id}-0000"
        invoice_date = datetime.now().strftime('%d-%m-%Y')

    # Check permissions
    if request.user.is_authenticated and request.user.is_staff:
        allowed = True
        print(f"User {request.user.username} is staff, allowed to download.")
    else:
        # Check client session
        session_project_id = request.session.get('client_project_id')
        allowed = (session_project_id == project.id)
        print(f"Session project id: {session_project_id}, Allowed: {allowed}")

    if not allowed:
        print("Access denied.")
        return HttpResponse("Access Denied", status=403)

    logo_url = request.build_absolute_uri(static('images/logo.PNG'))

    # Query expenses
    expense_rows = Expense.objects.filter(project=project)
    total_expense = Decimal(expense_rows.aggregate(Sum('amount'))['amount__sum'] or 0)
    print(f"Total expense: {total_expense}")

    # Query payments
    raw_payments = Payment.objects.filter(project=project).order_by('date')
    total_received = Decimal(raw_payments.aggregate(Sum('amount'))['amount__sum'] or 0)

    cumulative_paid = Decimal('0.00')
    cumulative_paid_before = Decimal('0.00')
    payment_rows = []

    for payment in raw_payments:
        payment_amount = Decimal(str(payment.amount))
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
        'invoice_number': invoice_number,
        'invoice_date': invoice_date,
    }

    template = get_template('projects/invoice.html')
    html_content = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{project.client_name}.pdf"'

    pisa_status = pisa.CreatePDF(html_content, dest=response)

    if pisa_status.err:
        print("PDF generation error")
        return HttpResponse('Error generating PDF', status=500)

    return response

# edit_payment
def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    projects = Project.objects.all()
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_mode')
        project_id = request.POST.get('project')

        if amount and payment_method:
            try:
                payment.amount = float(amount)
                payment.payment_method = payment_method

                if project_id and int(project_id) != payment.project.id:
                    payment.project = Project.objects.get(id=project_id)

                payment.save()
                messages.success(request, "Payment updated successfully.")
                return redirect('client_details' , project_id=payment.project.id)
            except (ValueError, Project.DoesNotExist):
                messages.error(request, "Invalid input. Please check again.")
        else:
            messages.error(request, "Amount and payment method are required.")

    return render(request, 'projects/edit_payment.html', {
        'payment': payment,
        'projects': projects,
    })


# delete_payment
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, "Payment deleted successfully.")
    return redirect('add_payment')


from decimal import Decimal
from django.db.models import Sum
from django.contrib import messages
from django.utils import timezone
from .models import Project, Payment  # Adjust this import as per your structure

def add_payment(request):
    projects = Project.objects.all()
    selected_project_id = None
    total_paid = Decimal('0')
    amount_remaining = Decimal('0')
    project = None  # ✅ Initialize to avoid UnboundLocalError

    if request.method == 'POST':
        project_id = request.POST.get('project')
        amount = request.POST.get('amount')
        payment_mode = request.POST.get('payment_mode')

        if project_id and not amount and not payment_mode:
            # Just a dropdown selection
            try:
                project = Project.objects.get(id=project_id)
                selected_project_id = project.id
                total_paid_raw = project.payments.aggregate(total=Sum('amount'))['total']
                total_paid = Decimal(str(total_paid_raw)) if total_paid_raw is not None else Decimal('0')
                budget = project.budget or Decimal('0')
                amount_remaining = budget - total_paid
            except Project.DoesNotExist:
                messages.error(request, 'Selected project does not exist.')

        elif project_id and amount and payment_mode:
            try:
                project = Project.objects.get(id=project_id)
                selected_project_id = project.id

                amount_decimal = Decimal(amount)

                Payment.objects.create(
                    project=project,
                    amount=amount_decimal,
                    payment_mode=payment_mode,
                    date=timezone.now().date()
                )

                messages.success(request, f'Payment of ₹{amount_decimal} added successfully for project "{project.name}".')

                # Recalculate total and remaining
                total_paid_raw = project.payments.aggregate(total=Sum('amount'))['total']
                total_paid = Decimal(str(total_paid_raw)) if total_paid_raw is not None else Decimal('0')
                budget = project.budget or Decimal('0')
                amount_remaining = budget - total_paid

                return redirect(f"{request.path}?project={project.id}")

            except Project.DoesNotExist:
                messages.error(request, 'Selected project does not exist.')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')

        else:
            messages.error(request, 'Please fill all required fields.')

    elif request.method == 'GET':
        selected_project_id = request.GET.get('project')
        if selected_project_id:
            try:
                project = Project.objects.get(id=selected_project_id)
                selected_project_id = project.id
                total_paid_raw = project.payments.aggregate(total=Sum('amount'))['total']
                total_paid = Decimal(str(total_paid_raw)) if total_paid_raw is not None else Decimal('0')
                budget = project.budget or Decimal('0')
                amount_remaining = budget - total_paid
            except Project.DoesNotExist:
                selected_project_id = None

    # Payments list for display
    payments = Payment.objects.filter(project=project) if project else []

    context = {
        'projects': projects,
        'selected_project_id': int(selected_project_id) if selected_project_id else None,
        'selected_project': project,
        'total_paid': total_paid,
        'amount_remaining': amount_remaining,
        'payments': payments,  # Needed to display in template
    }

    return render(request, 'projects/add_payment.html', context)







# daily_expense
def remove_daily_expense(request, expense_id):
    expense = get_object_or_404(DailyExpense, id=expense_id)
    expense.delete()
    return redirect('daily_expense')





# daily_report
@session_login_required


def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    projects = Project.objects.all()  # In case you want to pass this to the template

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('client_details', project_id=expense.project.id)  # Make sure this URL name exists
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'projects/edit_expense.html', {
        'form': form,
        'projects': projects,
        'selected_project_id': expense.project.id
    })

def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    project_id = expense.project.id
    expense.delete()
    return redirect('client_details', project_id=project_id)  # Adjust as needed

def daily_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    edit_id = request.GET.get('edit')

    # Convert inputs
    filter_kwargs = {}

   

    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            filter_kwargs['date__gte'] = start_date_obj
        except ValueError:
            pass

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            filter_kwargs['date__lte'] = end_date_obj
        except ValueError:
            pass

    # Edit / delete / add logic remains unchanged...
    edit_expense = None
    edit_form = None
    if edit_id:
        try:
            edit_expense = DailyExpense.objects.get(id=edit_id)
            edit_form = DailyExpenseForm(instance=edit_expense)
        except DailyExpense.DoesNotExist:
            edit_expense = None

    if request.method == 'POST':
        if 'edit_expense_id' in request.POST:
            expense = get_object_or_404(DailyExpense, id=request.POST['edit_expense_id'])
            form = DailyExpenseForm(request.POST, instance=expense)
            if form.is_valid():
                form.save()
                # Remove 'edit' param after saving to avoid showing edit form again
                query_dict = request.GET.copy()
                query_dict.pop('edit', None)
                return redirect(f"{request.path}?{urlencode(query_dict)}")
            else:
                # Send form with errors back to template
                edit_form = form
                edit_expense = expense


        elif 'delete_expense_id' in request.POST:
            expense = get_object_or_404(DailyExpense, id=request.POST['delete_expense_id'])
            expense.delete()
            return redirect(request.get_full_path())

        elif 'add_daily_expense' in request.POST:
            form = DailyExpenseForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect(request.get_full_path())
            else:
                print("Add DailyExpense form is invalid:", form.errors)

    # Process data
    projects_data = []
    total_expenses_all_projects = Decimal('0.00')

    for project in Project.objects.all():
        total_budget = project.expenses_set.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        daily_expenses = DailyExpense.objects.filter(project=project, **filter_kwargs).order_by('date')
        running_total = Decimal('0.00')
        all_entries = []

        for dex in daily_expenses:
            running_total += dex.amount
            balance = total_budget - running_total
            all_entries.append({
                'expense': dex,
                'form': None,
                'running_total': running_total,
                'description': dex.description,
                'remark': dex.remark,
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
    
        'start_date': start_date,
        'end_date': end_date,
        'months': [f"{i:02d}" for i in range(1, 13)],
        'years': [str(y) for y in range(datetime.now().year - 2, datetime.now().year + 2)],
        'total_expenses_all_projects': total_expenses_all_projects,
        'projects': Project.objects.all(),
        'edit_id': edit_id,
        'edit_expense': edit_expense,
        'edit_form': edit_form,
    }

    return render(request, 'projects/daily.html', context)






from collections import defaultdict
from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import datetime

def daily_statistics(request):
    start_month = request.GET.get('start_month')
    end_month = request.GET.get('end_month')
    year = request.GET.get('year')
    project_id = request.GET.get('project_id')

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
    if project_id:
        filter_kwargs['project_id'] = project_id

    total_spending = DailyExpense.objects.filter(**filter_kwargs).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    category_data = DailyExpense.objects.filter(**filter_kwargs).values('category').annotate(total=Sum('amount')).order_by('-total')

    monthly_data = DailyExpense.objects.filter(**filter_kwargs).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')

    monthly_labels = [entry['month'].strftime('%b %Y') for entry in monthly_data]
    monthly_totals = [float(entry['total']) for entry in monthly_data]

    project_data = DailyExpense.objects.filter(**filter_kwargs).values('project__id', 'project__name', 'project__client_name').annotate(total=Sum('amount')).order_by('-total')

    expenses = DailyExpense.objects.filter(**filter_kwargs).select_related('project').order_by('project__name', 'date')

    expenses_by_project = defaultdict(list)
    for expense in expenses:
        expenses_by_project[expense.project.id].append(expense)


    # Build total budget per project
    project_budgets = {}
    for project in Project.objects.all():
        total_expense = project.expenses_set.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        project_budgets[project.id] = project.budget + total_expense


    context = {
        'total_spending': total_spending,
        'category_data': category_data,
        'monthly_labels': monthly_labels,
        'monthly_totals': monthly_totals,
        'project_data': project_data,
        'expenses': expenses_by_project,
        'project_budgets': project_budgets,
        'selected_start_month': start_month,
        'selected_end_month': end_month,
        'selected_year': year,
        'selected_project': int(project_id) if project_id else None,
        'projects': Project.objects.all(),
        'months': [f"{i:02d}" for i in range(1, 13)],
        'years': [str(y) for y in range(datetime.now().year - 2, datetime.now().year + 2)],
    }

    return render(request, 'projects/daily_statistics.html', context)




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



# update_project_status
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





# Custom error handlers


def custom_404(request, exception):
    return render(request, 'projects/404.html', status=404)

def custom_500(request):
    return render(request, 'projects/500.html', status=500)
