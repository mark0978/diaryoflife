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

    def published(self, **kwargs):
        """ Return a QS of all published articles that have not been hidden """
        return self.filter(hidden_at=None, **kwargs).exclude(published_at__isnull=True)


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
    language = models.CharField(_('language'),
                                max_length=5,
                                choices=settings.LANGUAGES,
                                default=settings.LANGUAGE_CODE[:2],
                                help_text=_('Story language.'))

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
    HATE_SPEECH = 1
    SPAM = 2
    EXPLICIT = 3

    FLAG_CHOICES = (
        (HATE_SPEECH, _("Hate Speech")),
        (SPAM, _("Spam")),
        (EXPLICIT, _("Sexually Explicit")),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    entry = models.ForeignKey(Story, null=False, db_index=True, on_delete=models.PROTECT)
    flagged_at = models.DateTimeField(auto_now_add=True, null=False)
    reason = models.IntegerField(choices=FLAG_CHOICES, default=0)


class UpVotes(models.Model):
    """ When an entry is UpVoted, it gets one of these records"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    entry = models.ForeignKey(Story, null=False, db_index=True, on_delete=models.PROTECT)
    voted_at = models.DateTimeField(auto_now_add=True, null=False)


class DownVotes(models.Model):
    """ When an entry is DownVoted, it gets one of these records"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    entry = models.ForeignKey(Story, null=False, db_index=True, on_delete=models.PROTECT)
    voted_at = models.DateTimeField(auto_now_add=True, null=False)
