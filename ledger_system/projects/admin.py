# Register your models here.

from django.contrib import admin
from .models import  Project, Expense,Payment,DailyExpense,CustomProject


admin.site.site_header = "The Elite Dream Builders Admin"
admin.site.site_title = "Elite Dream Admin"
admin.site.index_title = "Welcome to The Elite Dream Builders Dashboard"

admin.site.register(Project)
admin.site.register(Expense)
admin.site.register(Payment)
admin.site.register(DailyExpense)
admin.site.register(CustomProject)
