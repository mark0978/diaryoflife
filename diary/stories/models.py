from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _
from django.utils.safestring import SafeString

from martor.models import MartorField
from martor.utils import markdownify

# Create your models here.

class StoryQuerySet(models.QuerySet):
    pass


class StoryManager(models.Manager):
    def get_queryset(self):
        return StoryQuerySet(self.model, using=self._db)

    def recent(self):
        """ Order the list of visible Entries by their published date (descending) """
        return self.published().order_by('-published_at')

    def visible(self):
        """ Return a QS of all the stories that have not been hidden """
        return self.get_queryset().filter(hidden_at=None)

    def published(self, **kwargs):
        """ Return the story object if visible, otherwise None """
        return self.visible().filter(**kwargs).exclude(published_at__isnull=True)


class Story(models.Model):
    """ Holds a single story content """
    author = models.ForeignKey('authors.Author', verbose_name=_("Pseudonym"),
                               on_delete=models.PROTECT)
    title = models.CharField(max_length=64, null=False, blank=False)
    tagline = models.CharField(max_length=64, blank=True)
    text = MartorField(null=False, blank=False)
    published_at = models.DateTimeField(default=None, null=True, blank=True, db_index=True)
    hidden_at = models.DateTimeField(default=None, null=True, blank=True)
    inspired_by = models.ForeignKey('self', default=None, null=True, blank=True,
                                    on_delete=models.PROTECT)

    objects = StoryManager()

    def __str__(self):
        return self.title

    def read_time(self):
        return _("Short read")

    def html(self):
        """ Return the html version of the markdown.  Wraps it as a SafeString so it will
              display without being escaped.  This should probably be done and cached somewhere
              and let this method do a lookup for the cached version.  An alternative would be to
              double the storage in the DB but that could mean having to update the whole  DB if we
              fix something about martor.  Storing this in a memcached instance would probably
              be better """
        # TODO: Store the results in memcached for speed
        return SafeString(markdownify(self.text))



class Flag(models.Model):
    """ When an entry is  flagged, it gets one of these records"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    entry = models.ForeignKey(Story, null=False, db_index=True, on_delete=models.PROTECT)
    flagged_at = models.DateTimeField(auto_now_add=True, null=False)


class UpVotes(models.Model):
    """ When an entry is UpVoted, it gets one of these records"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    entry = models.ForeignKey(Story, null=False, db_index=True, on_delete=models.PROTECT)
    flagged_at = models.DateTimeField(auto_now_add=True, null=False)


class DownVotes(models.Model):
    """ When an entry is DownVoted, it gets one of these records"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    entry = models.ForeignKey(Story, null=False, db_index=True, on_delete=models.PROTECT)
    voted_at = models.DateTimeField(auto_now_add=True, null=False)
