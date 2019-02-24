from django.conf import settings
from django.db import models
from django.utils.safestring import SafeString

from martor.models import MartorField
from stories.utils import markdownify

# Create your models here.

class AuthorQuerySet(models.QuerySet):
    pass


class AuthorManager(models.Manager):

    def get_queryset(self):
        return AuthorQuerySet(self.model, using=self._db)

    def for_user(self, user):
        qset = self.get_queryset()
        return qset.filter(user=user).order_by('name')


class Author(models.Model):

    # A User can have multiple author roles (or pseudonyms)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             blank=False, null=False)

    name = models.CharField(max_length=64, blank=False, null=False, unique=True)

    # Each user profile will have a field where they can tell other users
    #   something about themselves. This field will be empty when the user
    #   creates their account, so we specify `blank=True`.
    bio_text = MartorField(blank=True)

    # In addition to the `bio` field, each user may have a profile image or
    #   avatar. Similar to `bio`, this field is not required. It may be blank.
    avatar = models.URLField(blank=True)

    objects = AuthorManager()

    def __str__(self):
        return self.name

    def bio_html(self):
        """ Return the markdownified biography of this author """
        return SafeString(markdownify(self.bio_text))
