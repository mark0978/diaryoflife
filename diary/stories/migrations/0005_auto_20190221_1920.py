# Generated by Django 2.1.7 on 2019-02-21 19:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0004_story_preceeded_by'),
    ]

    operations = [
        migrations.RenameField(
            model_name='story',
            old_name='preceeded_by',
            new_name='preceded_by',
        ),
    ]
