# Generated by Django 5.2.4 on 2025-07-20 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_post_media_file_alter_post_media_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='caption',
            field=models.TextField(blank=True, db_index=True, null=True),
        ),
    ]
