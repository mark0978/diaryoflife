from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from model_mommy import mommy

from authors.models import Author

# Create your tests here.

class TestStoryModel(TestCase):

    def setUp(self):
        self.author = mommy.make(Author, name="Bob")
        self.author_with_avatar = mommy.make(Author, bio_text="**My** name is Eugene!",
                                             name="Eugene", avatar="https://imgur.com",
                                             user=self.author.user)
        self.other_author = mommy.make(Author, name="Other")

    def test_bio_html(self):
        self.assertEqual("<p><strong>My</strong> name is Eugene!</p>", self.author_with_avatar.bio_html())

    def test__str__(self):
        self.assertEqual("Bob", str(self.author))

    def test_for_user(self):
        authors = Author.objects.for_user(self.author.user)
        # These are ordered by name so we check the ordering as well as the presence (and absence)
        self.assertListEqual([self.author, self.author_with_avatar],
                        [a for a in authors])
