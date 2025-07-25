# Generated by Django 5.2.4 on 2025-07-20 16:21

import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='media_file',
            field=models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/posts'), upload_to='posts/'),
        ),
        migrations.AlterField(
            model_name='post',
            name='media_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
