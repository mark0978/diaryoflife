from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse

from model_mommy import mommy

from stories.models import Story
from stories.forms import StoryForm

# Create your tests here.

class TestStoryModel(TestCase):

    def setUp(self):
        self.published0 = mommy.make(Story, text="**Published 0**",
                                     published_at=timezone.now()-timedelta(seconds=5))
        self.published1 = mommy.make(Story, text="Published 1",
                                     published_at=timezone.now()-timedelta(seconds=4))
        self.published2 = mommy.make(Story, text="**Published 2**",
                                     published_at=timezone.now(),
                                     author=self.published1.author)

        self.unpublished = mommy.make(Story, text="**UnPublished 1**", published_at=None,
                                      inspired_by=self.published1)
        self.hidden = mommy.make(Story, text="--Hidden 1--", inspired_by=self.published1,
                                 hidden_at=timezone.now())

    def test_published(self):
        stories = Story.objects.published()
        self.assertEqual(set((self.published0.id, self.published1.id, self.published2.id)),
                         set([x.id for x in stories]))

    def test_recent(self):
        stories = Story.objects.recent()
        self.assertListEqual([self.published2.id, self.published1.id, self.published0.id],
                             [x.id for x in stories])

    def test_by_author(self):
        stories = Story.objects.by_author(author=self.published1.author)
        self.assertEqual(set((self. published1, self.published2,)),
                         set(stories))

    def test_read_time(self):
        self.assertEqual("Short read", self.published0.read_time())

    def test_html(self):
        self.assertEqual("<p><strong>Published 0</strong></p>", self.published0.html())
        self.assertEqual("<p>Published 1</p>", self.published1.html())

    def test__str__(self):
        self.assertEqual(self.published1.title, str(self.published1))


class TestStoryForm(TestCase):

    def assertFieldsConfigured(self, form):
        """ We override some field widths, make sure those are set as expected"""
        self.assertEqual(form.fields['title'].widget.attrs['size'],
                         Story._meta.get_field('title').max_length)
        self.assertEqual(form.fields['tagline'].widget.attrs['size'],
                         Story._meta.get_field('tagline').max_length)
        self.assertEqual(form.fields['text'].widget.attrs['cols'],
                         Story._meta.get_field('title').max_length)

    def test_field_setup_no_inspired_by(self):
        story = mommy.make(Story)
        form = StoryForm(user=story.author.user)

        self.assertFieldsConfigured(form)
        # Make sure the inspired_by field is NOT present
        self.assertListEqual(['author', 'title', 'tagline', 'text', 'private'],
                             list(form.fields.keys()))

        self.assertNotIn('inspired_by', form.fields)

    def test_field_setup_inspired_by(self):
        inspiration = mommy.make(Story, text='Inspiring')
        form = StoryForm(user=inspiration.author.user, initial={'inspired_by': inspiration})

        self.assertFieldsConfigured(form)
        self.assertListEqual(['author', 'title', 'tagline', 'text', 'inspired_by', 'private'],
                             list(form.fields.keys()))

    def test_field_setup_from_model(self):
        inspiration = mommy.make(Story, text='Inspiring')
        story = mommy.make(Story, text='Something', inspired_by=inspiration)
        form = StoryForm(user=story.author.user, instance=story)

        self.assertFieldsConfigured(form)
        self.assertIn('inspired_by', form.fields)


    def test_save(self):
        # If we edit an existing form, can we re-save it without change?
        story = mommy.make(Story, text='Nothing')

        form = StoryForm(user=story.author.user, instance=story)
        # This is a hack to get the data=request.POST dict for save checking
        form = StoryForm(data=form.initial, user=story.author.user, instance=story)

        saved = form.save()
        for field in Story._meta.fields:
            name = field.name
            self.assertEqual(getattr(saved, name), getattr(story, name))


        # If we create a new story with the form, does it save as expected
        form = StoryForm(data={
            'title': 'This is the title',
            'author': story.author.id,
            'text': 'This is the text',
            'inspired_by': story.id,
            'private': True
        }, user=story.author.user)
        saved = form.save()
        self.assertEqual(saved.inspired_by.id, story.id) # Should be inspired by story
        self.assertIsNone(saved.published_at)
        self.assertIsNotNone(saved.id)


        # Save a new story without an inspired_by field
        form = StoryForm(data={
            'title': 'This is the title',
            'author': story.author.id,
            'text': 'This is the text',
            'private': False
        }, user=story.author.user)
        saved = form.save()
        self.assertIsNone(saved.inspired_by) # Not inspired by anything
        self.assertIsNotNone(saved.published_at) # And published
        self.assertIsNotNone(saved.id)


class TestStoryViews(TestCase):

    def setUp(self):
        self.author = mommy.make("authors.Author")
        self.author.user.set_password('PASSWORD')
        self.author.user.save()

        self.story1 = mommy.make(Story, text="Story 1",author=self.author,
                                 published_at=timezone.now()-timedelta(seconds=5))
        self.story2 = mommy.make(Story, text="Story 2", author=self.author,
                                 published_at=timezone.now()-timedelta(seconds=4))
        self.private_story = mommy.make(Story, text="Private", author=self.author,
                                        published_at=None)
        self.hidden_story = mommy.make(Story, text="Hidden", author=self.author,
                                       hidden_at=timezone.now(),
                                       published_at=timezone.now())


    def test_recent(self):
        client = Client()
        response = client.get(reverse('stories:recent'))

        stories = response.context[-1]['object_list']
        expected = [self.story2, self.story1]
        self.assertListEqual(expected, list(stories))

    def test_list_by_author(self):
        client = Client()
        response = client.get(reverse('stories:list-by-author', args=(self.author.id,)))

        stories = response.context[-1]['object_list']
        expected = [self.story2, self.story1]
        self.assertListEqual(expected, list(stories))

        # An author with a hidden story
        hidden = mommy.make(Story, text="Hidden", hidden_at=timezone.now(),
                           published_at=timezone.now())

        response = client.get(reverse('stories:list-by-author',
                                      args=(hidden.author.id,)))

        stories = response.context[-1]['object_list']
        expected = []
        self.assertListEqual(expected, list(stories))

        # An author with an unpublished story
        unpublished = mommy.make(Story, text="Hidden", published_at=None)

        response = client.get(reverse('stories:list-by-author',
                                      args=(unpublished.author.id,)))

        stories = response.context[-1]['object_list']
        expected = []
        self.assertListEqual(expected, list(stories))

    def test_create_requires_login(self):
        client = Client()

        # User NOT logged in, redirects to login
        url = reverse('stories:create')
        response = client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/accounts/signin/?next=%s' % url, response.url)

    def test_logged_in_returns_a_usable_form(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # Get the form from the server
        url = reverse('stories:create')
        response = client.get(url)
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')
        self.assertFalse(form.is_bound)
        self.assertNotIn('inspired_by', form.fields) # Not present if not "inspired_by" another

    def test_create_enforces_constraints(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # Submit the form without any data (should give us some form errors)
        url = reverse('stories:create')
        response = client.post(url, data={})
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')
        self.assertTrue(form.is_bound)
        self.assertDictEqual({
            'author': ['This field is required.'],
            'title': ['This field is required.'],
            'text': ['This field is required.']}, form.errors)

    def test_create_creates_story(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # Submit the form with valid data
        url = reverse('stories:create')
        response = client.get(url)
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')

        form_data ={
            'title': 'This is a new title',
            'text': '**This** is the text',
            'author': list(form.fields['author'].choices)[-1][0]
        }
        response = client.post(url, data=form_data)
        self.assertEqual(302, response.status_code)
        created_story = Story.objects.get(title="This is a new title",
                                          author=self.author)

        # Which should redirect us to read the story after we have saved it.
        self.assertEqual(reverse("stories:read", args=(created_story.id,)),
                         response.url)
        self.assertIsNotNone(created_story.published_at) # Not marked as private

    def test_inspired_by_gives_you_an_inspired_by_field_and_creates_a_story(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # Now see if inspired_by works by creating a NEW story inspired by the created_story
        url = reverse('stories:create') + "?inspired_by=%s" % self.story1.id
        response = client.get(url)
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')
        self.assertFalse(form.is_bound)
        self.assertIn('inspired_by', form.fields)
        self.assertEqual(form.initial['inspired_by'], self.story1)

        form_data ={
            'title': 'This is a new title',
            'text': '**This** is the text',
            'author': list(form.fields['author'].choices)[-1][0]
        }
        response = client.post(url, data=form_data)
        self.assertEqual(302, response.status_code)
        created_story = Story.objects.get(title="This is a new title",
                                          author=self.author)

        # Which should redirect us to read the story after we have saved it.
        self.assertEqual(reverse("stories:read", args=(created_story.id,)),
                         response.url)
        self.assertIsNotNone(created_story.published_at) # Not marked as private

    def test_edit_requires_login(self):
        client = Client()

        # User NOT logged in, redirects to login
        url = reverse('stories:edit', args=(self.story1.id,))
        response = client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/accounts/signin/?next=%s' % url, response.url)

    def test_the_ability_to_unpublish_a_published_story(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # And then we edit the story so we can unpublish it
        url = reverse("stories:edit", args=(self.story1.id,))
        response = client.get(url)
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')

        # Now, unpublish this story and see if the published_at field is cleared
        form_data = form.initial
        form_data['private'] = 1
        response = client.post(url, data=form_data)
        self.assertEqual(302, response.status_code)

        edited_story = Story.objects.get(title=form_data['title'], author=self.author)
        # And we redirect to the read the story page
        self.assertEqual(reverse("stories:read", args=(edited_story.id,)), response.url)

        self.assertIsNone(edited_story.published_at)


    def test_unpublishing_of_an_inspired_by_story_removes_field(self):

        # Log the user in
        client = Client()
        self.assertTrue(client.login(username=self.author.user.username, password='PASSWORD'))

        # Now see if inspired_by fails when the inspiring story is NOT published
        url = reverse('stories:create')
        response = client.get(url, data={'inspired_by': self.hidden_story.id})
        self.assertEqual(200, response.status_code)
        form = response.context.get('form')
        self.assertNotIn('inspired_by', form.fields)


    def test_read_hides_certain_stories(self):
        client = Client()

        response = client.get(reverse("stories:read", args=(self.private_story.id,)))
        self.assertContains(response, 'This entry is private')

        response = client.get(reverse("stories:read", args=(self.hidden_story.id,)))
        self.assertContains(response, 'This entry is hidden')

        response = client.get(reverse("stories:read", args=(self.story1.id,)))
        self.assertContains(response, self.story1.title)

