# Generated by Django 4.2.19 on 2025-06-03 05:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0024_choice_question_choiceselection_choice_question_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudySettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prolific_study_id', models.CharField(default='', max_length=128, verbose_name='only the *last* part of the completion URL')),
                ('system_prompt', models.TextField(blank=True, null=True)),
                ('user_prompt', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Study Configuration',
                'verbose_name_plural': 'Study Configuration',
            },
        ),
    ]
