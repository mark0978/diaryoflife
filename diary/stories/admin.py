from django.contrib import admin

from markdownx.admin import MarkdownxModelAdmin

# Register your models here.

from .models import Story

admin.site.register(Story, MarkdownxModelAdmin)
