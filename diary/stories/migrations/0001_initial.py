# Generated by Django 2.1.5 on 2019-01-23 21:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import martor.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authors', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DownVotes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voted_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flagged_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=64)),
                ('text', martor.models.MartorField()),
                ('published_at', models.DateTimeField(blank=True, db_index=True, default=None, null=True)),
                ('hidden_at', models.DateTimeField(blank=True, default=None, null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='authors.Author', verbose_name='Pseudonym')),
                ('inspired_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='stories.Story')),
            ],
        ),
        migrations.CreateModel(
            name='UpVotes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flagged_at', models.DateTimeField(auto_now_add=True)),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='stories.Story')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='flag',
            name='entry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='stories.Story'),
        ),
        migrations.AddField(
            model_name='flag',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='downvotes',
            name='entry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='stories.Story'),
        ),
        migrations.AddField(
            model_name='downvotes',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]
