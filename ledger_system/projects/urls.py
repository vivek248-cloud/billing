
from django.urls import path
from . import views


urlpatterns = [
    path('home/', views.home, name='home'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('client/login/', views.client_login, name='client_login'),

    path('logout/', views.logout_view, name='logout'),


    # client dashboard
    path('client/dashboard/<str:phone>/', views.client_dashboard, name='client_dashboard'),


    # update project status
    path('project/<int:project_id>/update-status/', views.update_project_status, name='update_project_status'),

    path('client/<int:project_id>/', views.client_details, name='client_details'),

    # Payment Invoice
    path('payment-invoice/<int:payment_id>/', views.payment_invoice, name='payment_invoice'),


    path('expense/edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('expense/delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),

    path('billing/', views.project_billing, name='billing'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('add_project/', views.add_project, name='add_project'),
    path('remove_expense/<int:expense_id>/', views.remove_expense, name='remove_expense'),
    path('projects/<int:project_id>/download_invoice/', views.download_invoice, name='download_invoice'),
    path('invoice/<int:project_id>/', views.invoice_view, name='invoice'),
    path('edit-payment/<int:payment_id>/', views.edit_payment, name='edit_payment'),
    path('billing/<int:project_id>/', views.project_billing, name='project_billing'),
    path('delete-payment/<int:payment_id>/', views.delete_payment, name='delete_payment'),
    # path('add-payment/<int:project_id>/', views.add_payment, name='add_payment'),
    path('add_payment/', views.add_payment, name='add_payment'),


    path('projects/<int:project_id>/add-expense/', views.add_expense, name='add_expense'),
    # path('daily-expense',views.daily_expense_report, name='daily_expense'),
    # path('add-daily-expense/<int:project_id>/', views.add_daily_expense, name='add_daily_expense'),
    path('remove_daily_expense/<int:expense_id>/', views.remove_daily_expense, name='remove_daily_expense'),
    # path('add_custom_project/', views.add_custom_project, name='add_custom_project'),
    path('remove-note/<int:expense_id>/', views.remove_notes, name='remove_notes'),
    path('daily-expense',views.daily_report,name='daily_expense'),

    path('daily-statistics/', views.daily_statistics, name='daily_statistics'),

]

