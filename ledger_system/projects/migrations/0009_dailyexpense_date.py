# Generated by Django 5.2 on 2025-05-03 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_alter_expense_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyexpense',
            name='date',
            field=models.DateField(blank=True, null=True, verbose_name='Date'),
        ),
    ]
