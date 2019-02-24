from django.db import models
from django.contrib import admin
from martor.widgets import AdminMartorWidget

# Register your models here.

from .models import Story

class StoryAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': AdminMartorWidget},
    }
    list_display = ('title', 'tagline', 'teaser')


admin.site.register(Story, StoryAdmin)
