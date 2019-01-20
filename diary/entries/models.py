from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

from markdownx.models import MarkdownxField

# Create your models here.

class EntryQuerySet(models.QuerySet):
    pass

class EntryManager(models.Manager):
    def get_queryset(self):
        return EntryQuerySet(self.model, using=self._db)

    def recent(self):
        """ Order the list of visible Entries by their published date (descending) """
        return self.visible().order_by('-published_at')

    def visible(self):
        """ Return a QS of all the entries that have not been hidden """
        return self.get_queryset().filter(hidden_at=None)


class Entry(models.Model):
    """ Holds a single diary entry """
    author = models.ForeignKey('authors.Author', verbose_name=_("Pseudonym"),
                               on_delete=models.PROTECT)
    title = models.CharField(max_length=64, null=False, blank=False)
    text = MarkdownxField(null=False, blank=False)
    published_at = models.DateTimeField(default=None, null=True, blank=True, db_index=True)
    hidden_at = models.DateTimeField(default=None, null=True, blank=True)

    objects=EntryManager()


class Flag(models.Model):
    """ When an entry is  flagged, it gets one of these records"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    entry = models.ForeignKey(Entry, null=False, db_index=True, on_delete=models.PROTECT)
    flagged_at = models.DateTimeField(auto_now_add=True, null=False)


class UpVotes(models.Model):
    """ When an entry is UpVoted, it gets one of these records"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    entry = models.ForeignKey(Entry, null=False, db_index=True, on_delete=models.PROTECT)
    flagged_at = models.DateTimeField(auto_now_add=True, null=False)


class DownVotes(models.Model):
    """ When an entry is DownVoted, it gets one of these records"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    entry = models.ForeignKey(Entry, null=False, db_index=True, on_delete=models.PROTECT)
    voted_at = models.DateTimeField(auto_now_add=True, null=False)


class Comment(models.Model):
    """ A comment added to any entry, these are not threaded (for now) """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    text = models.TextField(null=False, blank=False)
    written_at = models.DateTimeField(auto_now_add=True)
    hidden_at = models.DateTimeField(default=None, null=True)
