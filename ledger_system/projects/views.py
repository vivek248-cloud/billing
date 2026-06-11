from urllib.parse import urlencode
from django.utils import timezone

from django.db.models import Sum
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from openai import project
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
        return redirect('/billing/')

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



# # client_login
# from django.shortcuts import redirect

# def client_login(request):
#     error = ""
#     if request.method == 'POST':
#         uname = request.POST['username']
#         pwd = request.POST['password']

#         try:
#             # Use __iexact for case-insensitive username matching
#             project = Project.objects.get(client_name__iexact=uname, phone=pwd)
#             request.session['client_project_id'] = project.id

#             response = redirect('client_dashboard', phone=project.phone)

#             # ✅ Remember Me logic
#             if 'remember_me' in request.POST:
#                 response.set_cookie('saved_username', uname, max_age=2592000)  # 30 days
#                 response.set_cookie('saved_password', pwd, max_age=2592000)
#             else:
#                 response.delete_cookie('saved_username')
#                 response.delete_cookie('saved_password')

#             return response

#         except Project.DoesNotExist:
#             error = "Invalid username or password."

#     return render(request, 'projects/client_login.html', {'error': error})


from django.http import JsonResponse

from django.http import JsonResponse
from django.shortcuts import render
from .models import Project

def client_login(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        phone = request.POST.get('phone', '').strip()

        if not phone:
            return JsonResponse({
                'status': 'error',
                'message': 'Phone number is required'
            })

        try:
            project = Project.objects.get(phone=phone)

            return JsonResponse({
                'status': 'success',
                'client_name': project.client_name,
                'phone': project.phone
            })

        except Project.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Phone number not found'
            })

    return render(request, 'projects/client_login.html')

from django.shortcuts import redirect, get_object_or_404

def client_confirm_login(request):
    phone = request.GET.get('phone')

    if not phone:
        return redirect('client_login')

    project = get_object_or_404(Project, phone=phone)

    # ✅ SET SESSION PROPERLY
    request.session['client_project_id'] = project.id

    # 🔥 IMPORTANT FIXES
    request.session.modified = True
    request.session.save()   # force save session

    return redirect('client_dashboard', phone=project.phone)
    


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

from django.utils.dateparse import parse_date

def siteimage(request, phone):
    project = Project.objects.filter(phone=phone).first()
    if not project:
        return HttpResponseForbidden("Project not found.")
    
    if request.session.get('client_project_id') != project.id:
        return HttpResponseForbidden("Access denied.")

    # Expense and Payment logic (same as before)
    expenses = Expense.objects.filter(project=project)
    payments = Payment.objects.filter(project=project).order_by('date')

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

    # ✅ Site Image Filters
    from_date = parse_date(request.GET.get('img_from') or '')
    to_date = parse_date(request.GET.get('img_to') or '')
    site_images = SiteImage.objects.filter(project=project)

    if from_date:
        site_images = site_images.filter(uploaded_at__date__gte=from_date)
    if to_date:
        site_images = site_images.filter(uploaded_at__date__lte=to_date)

    site_images = site_images.order_by('-uploaded_at')

    context = {
        'project': project,
        'phone': phone,
        'client_name': project.client_name,
        'expenses': expenses,
        'payment_rows': payment_rows,
        'total_paid': cumulative_paid,
        'remaining': remaining,
        'remaining_after_payment': remaining_after_payment,
        'site_images': site_images,
        'img_from': request.GET.get('img_from', ''),
        'img_to': request.GET.get('img_to', ''),
    }

    return render(request, 'projects/siteimage.html', context)




def siteprocess(request, phone):
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
    site_images = SiteImage.objects.filter(project=project).order_by('-uploaded_at')
    preview_images = site_images[:3]  # ✅ only 3 for preview on dashboard

    context = {
        'project': project,
        'phone': phone,
        'client_name': project.client_name,
        'expenses': expenses,
        'payment_rows': payment_rows,
        'total_paid': cumulative_paid,
        'remaining': remaining,
        'remaining_after_payment': remaining_after_payment,
        'site_images': site_images,  # ✅ pass to template
        'preview_images': preview_images  # ✅ pass preview images to template
    }

    return render(request, 'projects/siteprocess.html', context)


# logout_view
def logout_view(request):
    request.session.flush()  # Clears all session data
    return redirect('home')



# from django.db.models import Case, When, Value, IntegerField

# @session_login_required
# def project_billing(request):
#     if not request.session.get('admin_logged_in'):
#         return redirect('/admin_login/')

#     projects = (
#         Project.objects
#         .annotate(
#             completed_order=Case(
#                 When(status='Completed', then=Value(1)),
#                 default=Value(0),
#                 output_field=IntegerField()
#             )
#         )
#         .order_by('completed_order', '-id')  # ✅ logic here
#     )

#     return render(request, 'projects/billing.html', {
#         'projects': projects
#     })


from django.db.models import Case, When, Value, IntegerField, Q

@session_login_required
def project_billing(request):
    if not request.session.get('admin_logged_in'):
        return redirect('/admin_login/')

    query = request.GET.get('q', '')  # 🔍 search input

    projects = (
        Project.objects
        .annotate(
            completed_order=Case(
                When(status='Completed', then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        )
    )

    # ✅ APPLY SEARCH FILTER
    if query:
        projects = projects.filter(
            Q(client_name__icontains=query) |
            Q(name__icontains=query) |
            Q(phone__icontains=query)
        )

    projects = projects.order_by('completed_order', '-id')

    # -------- Activities (same as before) --------
    today = timezone.localdate()
    activities = []

    recent_payments = Payment.objects.select_related('project').order_by('-date')[:5]
    for pay in recent_payments:
        activities.append({
            'icon': 'bi-currency-rupee',
            'color': 'success',
            'title': 'Payment Received',
            'desc': f'{pay.project.name} – ₹{pay.amount}',
            'time': 'Today' if pay.date == today else pay.date.strftime('%d %b %Y'),
            'sort_time': pay.date
        })

    recent_expenses = Expense.objects.select_related('project').order_by('-date')[:5]
    for exp in recent_expenses:
        activities.append({
            'icon': 'bi-receipt',
            'color': 'warning',
            'title': 'Expense Added',
            'desc': f'{exp.project.name} – ₹{exp.amount}',
            'time': 'Today' if exp.date == today else exp.date.strftime('%d %b %Y'),
            'sort_time': exp.date
        })

    activities = sorted(activities, key=lambda x: x['sort_time'], reverse=True)[:5]

    return render(request, 'projects/billing.html', {
        'projects': projects,
        'activities': activities,
        'query': query  # ✅ send back to template
    })





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
from urllib.parse import quote
from datetime import datetime

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

        phone = project.phone.strip().replace("+", "").replace(" ", "")

        share_url = request.build_absolute_uri(
            reverse('payment_invoice_share', args=[payment.id])
        )

        whatsapp_message = (
            f"Hi {project.client_name} \n\n"
            f"Use your phone number to login and view the invoice for your recent payment of ₹{amount}.\n\n"
            f"Here is your invoice:\n{share_url}"
        )

        # ✅ Encode ONLY message
        encoded_message = quote(whatsapp_message)

        whatsapp_link = f"https://wa.me/{phone}?text={encoded_message}"

        payment_rows.append({
            'payment_obj': payment,
            'date': payment.date,
            'amount': amount,
            'whatsapp_link': whatsapp_link,
            'payment_mode': payment.payment_mode,
            'cumulative_paid_before': cumulative_paid_before,
            'remaining_after_payment': (budget + total_expense) - cumulative_paid
        })

        cumulative_paid_before = cumulative_paid

    # ------- SITE IMAGES FILTER -------
    site_images = SiteImage.objects.filter(project=project)
    image_from = request.GET.get('image_from')
    image_to = request.GET.get('image_to')

    if image_from:
        site_images = site_images.filter(uploaded_at__date__gte=image_from)
    if image_to:
        site_images = site_images.filter(uploaded_at__date__lte=image_to)

    context = {
        'project': project,
        'expenses': expenses,
        'total_expense': total_expense,
        'remaining': remaining,
        'payment_rows': payment_rows,
        'total_paid': cumulative_paid,
        'site_images': site_images,
        'image_from': image_from,
        'image_to': image_to,
    }

    return render(request, 'projects/client_details.html', context)



from django.shortcuts import render, get_object_or_404, redirect
from .forms import SiteImageForm
from .models import Project
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

def compress_image(file, quality=30):
    image_temp = Image.open(file)
    image_temp = image_temp.convert('RGB')  # Ensure it's JPEG compatible
    output_io = BytesIO()
    image_temp.save(output_io, format='JPEG', quality=quality, optimize=True)
    output_io.seek(0)

    # Keep original name but change extension to .jpg
    original_name = file.name.rsplit('.', 1)[0] + '.jpg'

    return InMemoryUploadedFile(
        output_io, 'ImageField', original_name, 'image/jpeg', sys.getsizeof(output_io), None
    )

def upload_site_image(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        form = SiteImageForm(request.POST, request.FILES)
        if form.is_valid():
            site_image = form.save(commit=False)
            site_image.project = project

            # 👇 This is critical to ensure image is written to disk
            site_image.image = request.FILES['image']

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

    is_admin = request.session.get('admin_logged_in', False)
    is_shared = not is_admin

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
        'is_shared': is_shared,
        'is_admin': is_admin,
    }

    return render(request, 'projects/payment_invoice.html', context)


def payment_invoice_share(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    project = payment.project

    invoice_number = f"INV-{project.id}-{payment.id}-{payment.date.strftime('%Y%m%d')}"
    invoice_date = payment.date.strftime('%d-%m-%Y')

    payments = Payment.objects.filter(project=project).order_by('date')
    expenses = Expense.objects.filter(project=project)

    cumulative_paid = Decimal('0.00')
    payment_rows = []

    for pay in payments:
        amount = Decimal(str(pay.amount))

        payment_rows.append({
            'date': pay.date,
            'amount': amount,
            'cumulative_paid_before': cumulative_paid,
            'remaining_after_payment': (project.budget + project.total_expenses) - (cumulative_paid + amount),
            'payment_mode': pay.payment_mode,
        })

        cumulative_paid += amount

        if pay.id == payment.id:
            break

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
        'invoice_number': invoice_number,
        'invoice_date': invoice_date,
        'logo_url': '/static/images/logo.png',

        # 🔒 FORCE READONLY
        'is_shared': True,
        'is_admin': False,
    }

    return render(request, 'projects/payment_invoice_share.html', context)


# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Payment, PaymentNote

@csrf_exempt
def autosave_payment_note(request):
    if request.method == "POST":
        payment_id = request.POST.get("payment_id")
        content = request.POST.get("content")

        try:
            payment = Payment.objects.get(id=payment_id)

            # update or create (1 note per payment)
            note, created = PaymentNote.objects.update_or_create(
                payment=payment,
                defaults={
                    "content": content,
                    "created_by": request.user if request.user.is_authenticated else None
                }
            )

            return JsonResponse({"status": "success"})

        except Payment.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Invalid payment"})

    return JsonResponse({"status": "error"})


from django.contrib import messages
from decimal import Decimal
from django.shortcuts import render, redirect
from .models import Project


def add_project(request):
    projects = Project.objects.all().order_by('id')

    if request.method == 'POST':
        name = request.POST.get('name').strip()
        client_name = request.POST.get('client_name')
        phone = request.POST.get('phone').strip()
        budget = request.POST.get('budget', '0.00')
        estimated_cost = request.POST.get('estimated_cost', '0.00')


        Activity.objects.create(
                title="Project Created",
                description=f"Project '{name}' created with budget ₹{budget}",
                action="create",
                project=project
        )
        
        # Check duplicate project name
        if Project.objects.filter(name=name).exists():
            messages.error(request, f"A project with name '{name}' already exists.")

        # Check duplicate phone
        elif Project.objects.filter(phone=phone).exists():
            messages.error(request, f"A project with phone number '{phone}' already exists.")

        else:
            try:
                budget = Decimal(budget)
                estimated_cost = Decimal(estimated_cost)

                Project.objects.create(
                    name=name,
                    client_name=client_name,
                    phone=phone,
                    budget=budget,
                    estimated_cost=estimated_cost
                )

                messages.success(request, "Project created successfully!")
                return redirect('add_project')

            except Exception:
                messages.error(request, "Invalid budget or estimated cost.")

    return render(request, 'projects/add_project.html', {
        'projects': projects
    })

# edit_project

# from decimal import Decimal
from django.urls import reverse

def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name').strip()
        client_name = request.POST.get('client_name')
        phone = request.POST.get('phone').strip()
        budget = request.POST.get('budget', '0.00')
        status = request.POST.get('status')

        # Duplicate checks
        if Project.objects.filter(name=name).exclude(id=pk).exists():
            messages.error(request, f"A project with name '{name}' already exists.")

        elif Project.objects.filter(phone=phone).exclude(id=pk).exists():
            messages.error(request, f"A project with phone '{phone}' already exists.")

        else:
            try:
                # Store old values
                old_name = project.name
                old_client = project.client_name
                old_phone = project.phone
                old_budget = project.budget
                old_status = project.status

                # Update values
                project.name = name
                project.client_name = client_name
                project.phone = phone
                project.budget = Decimal(budget)
                project.status = status

                project.save()
                project.update_estimated_cost()

                # Build change summary
                changes = []

                if old_name != project.name:
                    changes.append(
                        f"Project renamed from '{old_name}' to '{project.name}'"
                    )

                if old_client != project.client_name:
                    changes.append(
                        f"Client changed from '{old_client}' to '{project.client_name}'"
                    )

                if old_phone != project.phone:
                    changes.append(
                        f"Phone updated from {old_phone} to {project.phone}"
                    )

                if old_budget != project.budget:
                    changes.append(
                        f"Budget changed from ₹{old_budget:,.0f} to ₹{project.budget:,.0f}"
                    )

                if old_status != project.status:
                    changes.append(
                        f"Status changed from '{old_status}' to '{project.status}'"
                    )

                # Activity Log
                Activity.objects.create(
                    title=f"Project Updated • {project.name}",
                    description=" | ".join(changes) if changes else "Project information updated",
                    action="update",
                    project=project
                )

                messages.success(request, "Project updated successfully!")

                return redirect(
                    f"{reverse('add_project')}?project={project.id}"
                )

            except Exception:
                messages.error(request, "Invalid budget value.")

    return render(request, 'projects/edit_project.html', {
        'project': project,
        'statuses': Project.STATUS_CHOICES
    })


def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # Store details before deletion
    project_name = project.name
    client_name = project.client_name
    phone = project.phone
    budget = project.budget
    status = project.status

    # Activity Log
    Activity.objects.create(
        title=f"Project Deleted • {project_name}",
        description=(
            f"Client: {client_name} | "
            f"Phone: {phone} | "
            f"Budget: ₹{budget:,.0f} | "
            f"Status: {status}"
        ),
        action="delete",
        project=project
    )

    project.delete()

    messages.success(request, f"Project '{project_name}' deleted successfully!")

    return redirect('add_project')


# add_expense
from decimal import Decimal
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Project, Expense
from .forms import ExpenseForm2


from decimal import Decimal
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Project, Expense, Activity
from .forms import ExpenseForm2







from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def add_expense(request, project_id=None):
    selected_project_id = None
    total_expense = Decimal('0.00')

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

            Activity.objects.create(
                title="Expense Added",
                description=f"{expense.description} - ₹{expense.amount} added to {project.name}",
                action="create",
                project=project
            )

            messages.success(request, f"₹{expense.amount} expense added successfully!")
            return redirect(f"{request.path}?project={project.id}")

        else:
            messages.error(request, "Invalid expense data. Please check inputs.")

    else:
        form = ExpenseForm2()
        selected_project_id = request.GET.get('project')

    # Fetch expenses
    if selected_project_id:
        expenses_qs = Expense.objects.filter(
            project_id=selected_project_id
        ).order_by('-date')
        total_expense = expenses_qs.aggregate(
            Sum('amount')
        )['amount__sum'] or Decimal('0.00')
    else:
        expenses_qs = Expense.objects.none()

    # Pagination — 15 per page
    page_num  = request.GET.get('page', 1)
    paginator = Paginator(expenses_qs, 15)

    try:
        page_obj = paginator.page(page_num)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    projects = Project.objects.all()

    return render(request, 'projects/add_expense.html', {
        'projects':            projects,
        'form':                form,
        'expenses':            page_obj,
        'page_obj':            page_obj,
        'paginator':           paginator,
        'total_expense':       total_expense,
        'total_count':         paginator.count,
        'selected_project_id': int(selected_project_id) if selected_project_id else None,
    })




from django.contrib import messages

@session_login_required



def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    projects = Project.objects.all()

    if request.method == 'POST':

        # Store old values before update
        old_description = expense.description
        old_amount = expense.amount
        old_area = expense.area
        old_rate = expense.rate
        old_project = expense.project

        form = ExpenseForm(request.POST, instance=expense)

        if form.is_valid():
            updated_expense = form.save()

            # Build audit trail
            changes = []

            if old_description != updated_expense.description:
                changes.append(
                    f"Description changed from '{old_description}' to '{updated_expense.description}'"
                )

            if old_amount != updated_expense.amount:
                changes.append(
                    f"Amount changed from ₹{old_amount} to ₹{updated_expense.amount}"
                )

            if old_area != updated_expense.area:
                changes.append(
                    f"Area changed from {old_area} to {updated_expense.area}"
                )

            if old_rate != updated_expense.rate:
                changes.append(
                    f"Rate changed from ₹{old_rate} to ₹{updated_expense.rate}"
                )

            if old_project != updated_expense.project:
                changes.append(
                    f"Project changed from '{old_project.name}' to '{updated_expense.project.name}'"
                )

            Activity.objects.create(
                title=f"Expense Updated • {updated_expense.description}",
                description=" | ".join(changes) if changes else "Expense information updated",
                action="update",
                project=updated_expense.project
            )

            redirect_url = request.POST.get(
                'redirect_url',
                f"{reverse('add_expense')}?project={updated_expense.project.id}"
            )

            messages.success(
                request,
                f"Expense '{updated_expense.description}' updated successfully!"
            )

            return redirect(redirect_url)

        else:
            messages.error(request, "Invalid data. Please check the fields.")

    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'projects/edit_expense.html', {
        'form': form,
        'projects': projects,
        'selected_project_id': expense.project.id
    })



from django.contrib import messages

def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)

    project = expense.project
    project_id = project.id

    # Store values before deletion
    description = expense.description
    amount = expense.amount
    area = expense.area
    rate = expense.rate
    expense_date = expense.date

    # Activity Log
    Activity.objects.create(
        title=f"Expense Deleted • {description}",
        description=(
            f"Expense '{description}' was removed. "
            f"Amount: ₹{amount}, "
            f"Area: {area}, "
            f"Rate: ₹{rate}, "
            f"Date: {expense_date.strftime('%d-%m-%Y')}"
        ),
        action="delete",
        project=project
    )

    expense.delete()

    messages.success(
        request,
        f"Expense '{description}' deleted successfully!"
    )

    return redirect('client_details', project_id=project_id)


# remove_expense
def remove_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)

    expense.delete()

    messages.success(request, "Expense removed successfully!")

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




# edit_payment
def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    projects = Project.objects.all()

    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_mode = request.POST.get('payment_mode')
        project_id = request.POST.get('project')

        if amount and payment_mode:
            try:
                # Store old values
                old_amount = Decimal(str(payment.amount))
                old_mode = payment.payment_mode
                old_project = payment.project

                # Update values
                payment.amount = Decimal(amount)
                payment.payment_mode = payment_mode

                if project_id:
                    payment.project = Project.objects.get(id=project_id)

                payment.save()

                # Build activity details
                changes = []

                if old_amount != payment.amount:
                    changes.append(
                        f"Amount: ₹{old_amount:,.0f} → ₹{payment.amount:,.0f}"
                    )

                if old_mode != payment.payment_mode:
                    changes.append(
                        f"Mode: {old_mode.upper()} → {payment.payment_mode.upper()}"
                    )

                if old_project != payment.project:
                    changes.append(
                        f"Project: {old_project.name} → {payment.project.name}"
                    )

                Activity.objects.create(
                    title=f"Payment Updated • #{payment.id}",
                    description=(
                        " | ".join(changes)
                        if changes
                        else f"Payment #{payment.id} was saved without changes."
                    ),
                    action="update",
                    project=payment.project
                )

                messages.success(
                    request,
                    f"Payment ₹{payment.amount:,.0f} updated successfully."
                )

                return redirect(
                    f"{reverse('add_payment')}?project={payment.project.id}"
                )

            except (ValueError, Project.DoesNotExist):
                messages.error(
                    request,
                    "Invalid input. Please check again."
                )
        else:
            messages.error(
                request,
                "Amount and payment method are required."
            )

    return render(request, 'projects/edit_payment.html', {
        'payment': payment,
        'projects': projects,
    })





# delete_payment
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    if request.method == 'POST':

        project = payment.project

        # Store values before delete
        amount = payment.amount
        payment_mode = payment.payment_mode
        payment_date = payment.date

        Activity.objects.create(
            title=f"Payment Deleted • ₹{amount:,.0f}",
            description=(
                f"Payment of ₹{amount:,.0f} via "
                f"{payment_mode.upper()} was removed from "
                f"project '{project.name}'. "
                f"Payment Date: {payment_date.strftime('%d-%m-%Y')}"
            ),
            action="delete",
            project=project
        )

        payment.delete()

        messages.success(
            request,
            f"Payment of ₹{amount:,.0f} deleted successfully."
        )

        return redirect(
            f"{reverse('add_payment')}?project={project.id}"
        )

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

               # Calculate updated totals
                total_paid_raw = project.payments.aggregate(
                    total=Sum('amount')
                )['total']

                total_paid = Decimal(str(total_paid_raw)) if total_paid_raw else Decimal('0')

                remaining_amount = (
                    Decimal(project.budget)
                    + Decimal(project.total_expenses)
                    - total_paid
                )

                Activity.objects.create(
                    title=f"Payment Received • ₹{amount_decimal:,.0f}",
                    description=(
                        f"Received ₹{amount_decimal:,.0f} via "
                        f"{payment_mode.upper()} for project "
                        f"'{project.name}'. "
                        f"Remaining balance: ₹{remaining_amount:,.0f}"
                    ),
                    action="create",
                    project=project
                )

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







from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

def update_project_status(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        status = request.POST.get('status')

        if status in dict(Project.STATUS_CHOICES):

            # Store old status
            old_status = project.status

            # Update status
            project.status = status
            project.save()

            # Activity Log
            Activity.objects.create(
                title=f"Project Status Updated • {project.name}",
                description=(
                    f"Status changed from "
                    f"'{old_status}' → '{status}'"
                ),
                action="update",
                project=project
            )

            # Special Completed Event
            if status == "Completed" and old_status != "Completed":

                Activity.objects.create(
                    title=f"Project Completed 🎉 • {project.name}",
                    description=(
                        f"Project '{project.name}' has been marked "
                        f"as Completed successfully."
                    ),
                    action="update",
                    project=project
                )

                messages.success(request, "PROJECT_COMPLETED")

            else:
                messages.success(
                    request,
                    f"Project status updated from "
                    f"{old_status} to {status}."
                )

            return redirect('billing')

    return render(request, 'projects/update_status.html', {
        'project': project
    })





from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from decimal import Decimal
import calendar

@session_login_required
def analysis_dashboard(request):
    if not request.session.get('admin_logged_in'):
        return redirect('/admin_login/')

    # 🔹 BASE QUERYSETS
    all_projects = Project.objects.all()
    payments = Payment.objects.all()

    # 🔹 GET FILTERS
    month = request.GET.get('month')
    year = request.GET.get('year')

    filter_applied = bool(month or year)

    # 🔹 APPLY PAYMENT FILTERS
    if month:
        payments = payments.filter(date__month=int(month))
    if year:
        payments = payments.filter(date__year=int(year))

    # 🔹 PROJECTS USED FOR FINANCIALS
    if filter_applied:
        project_ids = payments.values_list('project_id', flat=True).distinct()
        projects = Project.objects.filter(id__in=project_ids)
    else:
        projects = all_projects

    # 🔹 KPI COUNTS
    total_projects = projects.count()
    completed_projects = projects.filter(status='Completed').count()
    ongoing_projects = projects.exclude(status='Completed').count()

    # 🔹 TOTAL PAID (SAFE DECIMAL)
    total_paid = Decimal(
        str(payments.aggregate(total=Sum('amount'))['total'] or 0)
    )

    total_budget = Decimal('0.00')
    total_remaining = Decimal('0.00')

    # 🔹 FINANCIAL TOTALS
    for project in projects:
        expenses = Decimal(
            str(project.expenses_set.aggregate(
                total=Sum('amount')
            )['total'] or 0)
        )

        budget = Decimal(str(project.budget)) + expenses

        paid = Decimal(
            str(payments.filter(project=project).aggregate(
                total=Sum('amount')
            )['total'] or 0)
        )

        total_budget += budget
        total_remaining += (budget - paid)

    # 🔹 STATUS PIE CHART
    status_chart = projects.values('status').annotate(
        count=Count('id')
    )

    # 🔹 MONTHLY PAYMENTS CHART
    monthly_payments = (
        payments
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    monthly_payments = [
        {
            'month': m['month'].strftime('%Y-%m'),
            'total': float(m['total'] or 0)
        }
        for m in monthly_payments
    ]


    # 🔹 MONTH DROPDOWN (Jan 1, Feb 2...)
    months = [
        {'value': i, 'label': f"{calendar.month_abbr[i]} ({i})"}
        for i in range(1, 13)
    ]

    # 🔹 YEAR DROPDOWN
    years = Payment.objects.dates('date', 'year')

    context = {
        # KPI
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'ongoing_projects': ongoing_projects,
        'total_budget': total_budget,
        'total_paid': total_paid,
        'total_remaining': total_remaining,

        # Charts
        'status_chart': list(status_chart),
        'monthly_payments': list(monthly_payments),

        # Filters
        'months': months,
        'years': [y.year for y in years],
    }

    return render(request, 'projects/analysis.html', context)




# custom session exprired page

def session_expired(request):
    """
    Shown when session is invalid / expired
    """
    return render(request, 'projects/session_expired.html')



# views.py
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap

def custom_sitemap_view(request):
    response = sitemap(request, sitemaps={'static': StaticViewSitemap()})
    response['X-Robots-Tag'] = 'index, follow'  # ✅ Allow indexing
    return response










from django.db.models import Q

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def activity_page(request):
    query      = request.GET.get('q', '').strip()
    from_date  = request.GET.get('from_date', '')
    to_date    = request.GET.get('to_date', '')
    action_filter = request.GET.get('action', '')
    page_num   = request.GET.get('page', 1)

    activities = Activity.objects.select_related('project').order_by('-created_at')

    # ── Search ──
    if query:
        activities = activities.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(action__icontains=query)
        )

    # ── Date filter ──
    if from_date:
        activities = activities.filter(created_at__date__gte=from_date)

    if to_date:
        activities = activities.filter(created_at__date__lte=to_date)

    # ── Action filter ──
    if action_filter in ['create', 'update', 'delete']:
        activities = activities.filter(action=action_filter)

    # ── Counts (on full filtered queryset) ──
    total_count    = activities.count()
    create_count   = activities.filter(action='create').count()
    update_count   = activities.filter(action='update').count()
    delete_count   = activities.filter(action='delete').count()
    critical_count = update_count + delete_count

    # ── Pagination — 20 per page ──
    paginator = Paginator(activities, 20)

    try:
        page_obj = paginator.page(page_num)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'projects/activity.html', {
        'activities':     page_obj,
        'page_obj':       page_obj,
        'paginator':      paginator,
        'total_count':    total_count,
        'create_count':   create_count,
        'update_count':   update_count,
        'delete_count':   delete_count,
        'critical_count': critical_count,
        'query':          query,
        'from_date':      from_date,
        'to_date':        to_date,
        'action_filter':  action_filter,
    })




import os
import subprocess
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from django.contrib import messages

BACKUP_DIR = "/var/backups/edb"
BACKUP_SCRIPT = "/root/edb/billing/backup_db.sh"


def superuser_required(view_func):
    decorated_view_func = login_required(user_passes_test(lambda u: u.is_superuser)(view_func))
    return decorated_view_func


import re
from datetime import datetime

import os
import re
import json
import platform
import psutil
import django
from datetime import datetime, timedelta
from collections import defaultdict

from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

BACKUP_DIR = getattr(settings, 'BACKUP_DIR', os.path.join(settings.BASE_DIR, 'backups'))


def get_db_size():
    """Get database size in MB."""
    try:
        db_engine = settings.DATABASES['default']['ENGINE']
        with connection.cursor() as cursor:
            if 'postgresql' in db_engine:
                cursor.execute("SELECT pg_database_size(current_database());")
                size_bytes = cursor.fetchone()[0]
            elif 'mysql' in db_engine:
                db_name = settings.DATABASES['default']['NAME']
                cursor.execute(
                    "SELECT SUM(data_length + index_length) "
                    "FROM information_schema.tables WHERE table_schema = %s;",
                    [db_name]
                )
                size_bytes = cursor.fetchone()[0] or 0
            elif 'sqlite' in db_engine:
                db_path = settings.DATABASES['default']['NAME']
                size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
            else:
                size_bytes = 0
        return round(size_bytes / (1024 * 1024), 2)
    except Exception:
        return 0


def get_system_metrics():
    """Gather system-level metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {
            "cpu_usage": cpu_percent,
            "memory_total": round(memory.total / (1024 ** 3), 2),
            "memory_used": round(memory.used / (1024 ** 3), 2),
            "memory_percent": memory.percent,
            "disk_total": round(disk.total / (1024 ** 3), 2),
            "disk_used": round(disk.used / (1024 ** 3), 2),
            "disk_percent": disk.percent,
        }
    except Exception:
        return {
            "cpu_usage": 0,
            "memory_total": 0,
            "memory_used": 0,
            "memory_percent": 0,
            "disk_total": 0,
            "disk_used": 0,
            "disk_percent": 0,
        }


@superuser_required
def settings_page(request):

    files_data = []
    total_size = 0
    latest_backup_time = None
    backup_sizes_over_time = defaultdict(float)
    backup_count_by_month = defaultdict(int)

    if os.path.exists(BACKUP_DIR):
        files = sorted(os.listdir(BACKUP_DIR), reverse=True)

        for file in files:
            if not file.endswith(".gz"):
                continue

            file_path = os.path.join(BACKUP_DIR, file)

            try:
                stat = os.stat(file_path)
            except OSError:
                continue

            file_size = stat.st_size
            total_size += file_size

            match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2})', file)
            if match:
                created_time = datetime.strptime(match.group(1), "%Y-%m-%d_%H-%M")
            else:
                created_time = datetime.fromtimestamp(stat.st_mtime)

            if not latest_backup_time or created_time > latest_backup_time:
                latest_backup_time = created_time

            # Aggregate for charts
            month_key = created_time.strftime("%b %Y")
            backup_sizes_over_time[month_key] += round(file_size / 1024, 2)
            backup_count_by_month[month_key] += 1

            # Time-ago helper
            delta = datetime.now() - created_time
            if delta.days > 0:
                time_ago = f"{delta.days}d ago"
            elif delta.seconds >= 3600:
                time_ago = f"{delta.seconds // 3600}h ago"
            elif delta.seconds >= 60:
                time_ago = f"{delta.seconds // 60}m ago"
            else:
                time_ago = "Just now"

            files_data.append({
                "name": file,
                "size": round(file_size / 1024, 2),
                "size_mb": round(file_size / (1024 * 1024), 2),
                "date": created_time.strftime("%d %b %Y %I:%M %p"),
                "time_ago": time_ago,
                "timestamp": created_time.isoformat(),
            })

    # Backup health
    backup_status = "healthy"
    backup_message = "All systems operational"
    if latest_backup_time:
        hours_since = (datetime.now() - latest_backup_time).total_seconds() / 3600
        if hours_since > 48:
            backup_status = "warning"
            backup_message = f"Last backup was {int(hours_since)}h ago"
        elif hours_since > 168:
            backup_status = "danger"
            backup_message = "Backup critically overdue"
    else:
        backup_status = "danger"
        backup_message = "No backups found"

    # Format storage intelligently
    if total_size >= 1024 * 1024:
        storage_display = f"{round(total_size / (1024 * 1024), 2)} MB"
    elif total_size >= 1024:
        storage_display = f"{round(total_size / 1024, 2)} KB"
    else:
        storage_display = f"{total_size} B"

    # Chart data
    chart_labels = list(backup_sizes_over_time.keys())[-12:]
    chart_sizes = [backup_sizes_over_time[k] for k in chart_labels]
    chart_counts = [backup_count_by_month[k] for k in chart_labels]

    # System info
    system_metrics = get_system_metrics()
    db_size = get_db_size()

    context = {
        "admin_user": request.user,
        "files": files_data,
        "total_backup_count": len(files_data),
        "total_storage": round(total_size / 1024, 2),
        "storage_display": storage_display,
        "backup_status": backup_status,
        "backup_message": backup_message,
        "latest_backup": latest_backup_time.strftime("%d %b %Y %I:%M %p") if latest_backup_time else "Never",
        "latest_backup_ago": files_data[0]["time_ago"] if files_data else "N/A",

        # Charts
        "chart_labels": json.dumps(chart_labels),
        "chart_sizes": json.dumps(chart_sizes),
        "chart_counts": json.dumps(chart_counts),

        # System
        "system_metrics": system_metrics,
        "db_size": db_size,
        "django_version": django.get_version(),
        "python_version": platform.python_version(),
        "server_os": f"{platform.system()} {platform.release()}",
        "total_users": User.objects.count(),
        "db_engine": settings.DATABASES['default']['ENGINE'].split('.')[-1],
    }

    return render(request, "projects/settings.html", context)


@superuser_required
def api_system_health(request):
    """AJAX endpoint for real-time health polling."""
    metrics = get_system_metrics()
    metrics["db_size"] = get_db_size()
    metrics["timestamp"] = datetime.now().isoformat()
    return JsonResponse(metrics)






@superuser_required
def download_backup(request, filename):
    file_path = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    raise Http404("File not found")


@superuser_required
def run_backup_now(request):
    try:
        subprocess.run(["bash", BACKUP_SCRIPT], check=True)
        messages.success(request, "Backup created successfully!")
    except:
        messages.error(request, "Backup failed!")

    return redirect("settings")


# Custom error handlers


def custom_404(request, exception):
    return render(request, 'projects/404.html', status=404)

def custom_500(request):
    return render(request, 'projects/500.html', status=500)
