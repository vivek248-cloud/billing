# Generated by Django 5.2 on 2025-04-29 06:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_expense_area_expense_rate'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Date')),
                ('amount', models.FloatField()),
                ('payment_mode', models.CharField(choices=[('cash', 'Cash'), ('cheque', 'Cheque'), ('online', 'Online')], max_length=50)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.project')),
            ],
        ),
    ]
