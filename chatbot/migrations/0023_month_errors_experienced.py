# Generated by Django 4.2.2 on 2023-12-08 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0022_month_created_at_month_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='month',
            name='errors_experienced',
            field=models.IntegerField(default=0),
        ),
    ]
