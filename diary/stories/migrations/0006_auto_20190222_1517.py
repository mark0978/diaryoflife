# Generated by Django 2.1.7 on 2019-02-22 15:17

from django.db import migrations, models
import django.db.models.deletion
import martor.models


class Migration(migrations.Migration):

    dependencies = [
        ('licenses', '0001_initial'),
        ('stories', '0005_auto_20190221_1920'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='about',
            field=martor.models.MartorField(blank=True),
        ),
        migrations.AddField(
            model_name='story',
            name='license',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='licenses.License'),
        ),
        migrations.AddField(
            model_name='story',
            name='source',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='story',
            name='teaser',
            field=models.TextField(max_length=140, null=True),
        ),
    ]