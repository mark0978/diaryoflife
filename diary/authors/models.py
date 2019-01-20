from django.conf import settings
from django.db import models

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             blank=False, null=False)
    name = models.CharField(max_length=64, blank=False, null=False, unique=True)


    def __str__(self):
        return self.name


    objects = AuthorManager()
