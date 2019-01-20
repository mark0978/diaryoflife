from django.contrib import admin

from markdownx.admin import MarkdownxModelAdmin

# Register your models here.

from .models import Entry

admin.site.register(Entry, MarkdownxModelAdmin)
