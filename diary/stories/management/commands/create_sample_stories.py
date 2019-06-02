from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import IntegrityError, connections, transaction
from django.utils import timezone

from stories.models import Story
from model_mommy import mommy

class Command(BaseCommand):
    help = 'Creates authors and stories so we have some sample data to test the API with for next/previous page.'

    def handle(self, *args, **kwargs):

        with transaction.atomic():
            chapter1 = mommy.make(Story, title="A story in 3 parts", tagline="Chapter 1", published_at=timezone.now()-timedelta(days=2))
            chapter2 = mommy.make(Story, title="A story in 3 parts", tagline="Chapter 2", published_at=timezone.now()-timedelta(days=1),
                                  preceded_by=chapter1, author=chapter1.author)
            chapter3 = mommy.make(Story, title="A story in 3 parts", tagline="Chapter 3", published_at=timezone.now(),
                                  preceded_by=chapter2, author=chapter1.author)
            inspiring = mommy.make(Story, title="A very inspiring story", tagline="Oh what a joy!", published_at=timezone.now()-timedelta(days=7))
            for i in range(0,7):
                mommy.make(Story, title="%d Inspired by:%d" % (i, inspiring.id), published_at=timezone.now()-timedelta(minutes=i),
                           inspired_by=inspiring)

        self.stdout.write("Create one 3 chapter story, 1 inspiring story, and 7 stories inspired by the inspiring story")
