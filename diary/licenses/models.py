from django.conf import settings
from django.db import models

# Create your models here.

class LicenseQuerySet(models.QuerySet):
    pass

class LicenseManager(models.Manager):
    def get_queryset(self):
        return LicenseQuerySet(self.model, using=self._db)

    def active(self, **kwargs):
        """ Return the list of available licenses to publish a story under. """
        return self.get_queryset().filter(unpublished_at__isnull=True)
    

class License(models.Model):
    """ Stories can be licensed under different license schemes (Project Gutenberg has their own special license, for example) """
    name = models.CharField(max_length=64, unique=True)
    text = models.TextField(blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             blank=False, null=False)
    published_at = models.DateTimeField(blank=True, null=True, default=None)
    
    # Can this license be used right now
    unpublished_at = models.DateTimeField(blank=True, null=True, default=None)
    
    objects = LicenseManager()
    
    def __str__(self):
        return self.name
    
