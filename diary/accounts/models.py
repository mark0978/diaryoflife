from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from userena.models import UserenaLanguageBaseProfile

# Create your models here.

class MyProfile(UserenaLanguageBaseProfile):
    user = models.OneToOneField(User,
                                unique=True,
                                verbose_name=_('user'),
                                related_name='my_profile',
                                on_delete=models.PROTECT)
