# Generated by Django 4.0.2 on 2022-02-25 21:14

from django.db import migrations, models
import django_docx_template.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DocxTemplate',
            fields=[
                ('slug', models.SlugField(blank=True, primary_key=True, serialize=False, verbose_name='slug')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('docx', models.FileField(upload_to=django_docx_template.models.upload_to_hook)),
                ('data_source_class', models.CharField(blank=True, max_length=250, null=True, verbose_name='DataSource class')),
            ],
        ),
    ]