from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse

from model_mommy import mommy

from authors.models import Author
from authors.forms import AuthorForm
from stories.models import Story

# Create your tests here.

class TestAuthorModel(TestCase):

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


class TestAuthorForm(TestCase):

    def setUp(self):
        self.author = mommy.make(Author, name="Bob")

    def assertFieldsConfigured(self, form):
        """ We override some field widths, make sure those are set as expected"""
        self.assertEqual(form.fields['name'].widget.attrs['size'],
                         Author._meta.get_field('name').max_length)
        self.assertEqual(form.fields['bio_text'].widget.attrs['cols'],
                         Author._meta.get_field('name').max_length)

    def test_create(self):

        # First test a blank form
        form = AuthorForm(user=self.author.user)
        self.assertFieldsConfigured(form)
        self.assertEqual(self.author.user, form.user)

        form = AuthorForm(data={
            "name": "BobbaFet",
            "bio_text": "My **Bio**",
        }, user=self.author.user)

        self.assertFieldsConfigured(form)
        self.assertEqual(self.author.user, form.user)

        saved = form.save()
        self.assertDictEqual({}, form.errors)
        self.assertIsNotNone(saved.id)
        self.assertEqual(saved.user, self.author.user)

    def test_required(self):
        form  = AuthorForm(data={}, user=self.author.user)

        self.assertFieldsConfigured(form)
        self.assertEqual(self.author.user, form.user)

        self.assertFalse(form.is_valid())
        self.assertDictEqual({'name': ['This field is required.']}, form.errors)

    def test_commit_equal_false_does_not_create_author(self):
        # If we save the form without commit=True, it won't actually send it to the DB
        form = AuthorForm(user=self.author.user)

        form = AuthorForm(data={
            "name": "BobbaFet",
            "bio_text": "My **Bio**",
        }, user=self.author.user)

        saved = form.save(commit=False)
        self.assertIsNone(saved.id)


class TestViews(TestCase):

    def setUp(self):
        self.author = mommy.make(Author, bio_text='A Bio')
        self.author2 = mommy.make(Author, bio_text='A Bio', user=self.author.user)

        self.author.user.set_password('PASSWORD')
        self.author.user.save()

        self.story1 = mommy.make(Story, text='This is text', author=self.author,
                                 published_at=timezone.now())
        self.unpublished = mommy.make(Story, text='This is text', author=self.author)
        self.story2 = mommy.make(Story, text='This is text',
                                 published_at=timezone.now())

    def test_detail(self):
        client = Client()
        response = client.get(reverse('authors:detail', args=(self.author.id,)))

        stories = response.context.get('stories_by_author')
        self.assertEqual(self.author, response.context.get('object'))
        self.assertEqual([self.story1], list(stories))

    def test_my_pseudonyms(self):
        client = Client()
        url = reverse('authors:my-pseudonyms')

        # Login is required, we should redirect
        response = client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/accounts/signin/?next=/authors/my-pseudonyms/', response.url)

        # Log the user in
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        response = client.get(url)
        authors = response.context.get('object_list')

        self.assertEqual(set((self.author.id, self.author2.id,)),
                         set([a.id for a in authors]))

    def test_create_and_edit(self):
        client = Client()
        url = reverse('authors:create')

        # Login is required, we should redirect
        response = client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/accounts/signin/?next=%s' % url, response.url)

        # Log the user in
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        response = client.get(url)
        form = response.context.get('form')
        self.assertEqual(self.author.user, form.user)

        # An empty form should fail to save
        response = client.post(url, data={})
        form = response.context.get('form')
        self.assertEqual({'name': ['This field is required.']}, form.errors)

        response = client.post(url, data={
            "name": "Author Name",
            "bio_text": "This is the bio"
        })
        author = Author.objects.get(name='Author Name')

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("authors:detail", args=(author.id,)),
                         response.url)

        client = Client()
        url = reverse('authors:edit', args=(author.id,))

        # Login is required, we should redirect
        response = client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/accounts/signin/?next=%s' % url, response.url)

        # Log the user in
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        response = client.get(url)
        form = response.context.get('form')
        self.assertEqual(author.user, form.user)
        self.assertEqual(author, form.instance)

        response = client.post(url, data={
            "name": "Another Name",
            "bio_text": "This is the new bio"
        })

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("authors:detail", args=(author.id,)),
                         response.url)

        author.refresh_from_db()
        self.assertEqual("Another Name", author.name)
        self.assertEqual("This is the new bio", author.bio_text)
